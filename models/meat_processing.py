from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Orden de Despiece de Carne'

    # Campos principales
    name = fields.Char(string='Nombre de la Orden', required=True, readonly=True, default=lambda self: _('Nuevo'))
    order_date = fields.Date(string='Fecha de Orden', required=True, default=fields.Date.today)
    product_ids = fields.Many2many('product.product', string='Canales', required=True)
    location_id = fields.Many2one('stock.location', string='Ubicación del Producto', required=True, ondelete='restrict', index=True)
    total_kilos = fields.Float(string='Total Kilos')
    processed_kilos = fields.Float(string='Kilos Procesados', compute='_compute_processed_kilos', store=True)
    remaining_kilos = fields.Float(string='Kilos Restantes', compute='_compute_remaining_kilos', store=True)
    waste_kilos = fields.Float(string='Kilos de Desperdicio', compute='_compute_waste_kilos', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('processing', 'En Proceso'),
        ('done', 'Finalizado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft')
    order_line_ids = fields.One2many('meat.processing.order.line', 'order_id', string='Líneas de Orden', required=True)
    total_amount = fields.Float(string='Monto Total', compute='_compute_total_amount', store=True)
    notes = fields.Text(string='Notas')
    raw_material_lot_ids = fields.Many2many('stock.lot', string='Lotes de Materia Prima')  # Se usa para seleccionar los lotes de los productos

    # Otros campos
    start_time = fields.Datetime(string='Hora de Inicio', default=fields.Datetime.now)
    responsible_id = fields.Many2one('res.users', string='Responsable', index=True)
    progress = fields.Float(string='Progreso', compute='_compute_progress', store=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Orden de Compra de Origen', readonly=True)
    
    # Campos booleanos para controles
    can_confirm = fields.Boolean(string='Puede Confirmar', compute='_compute_can_confirm')
    can_done = fields.Boolean(string='Puede Finalizar', compute='_compute_can_done')
    can_cancel = fields.Boolean(string='Puede Cancelar', compute='_compute_can_cancel')
    can_set_to_draft = fields.Boolean(string='Puede Restablecer a Borrador', compute='_compute_can_set_to_draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code('meat.processing.order') or _('Nuevo')
        return super(MeatProcessingOrder, self).create(vals)

    @api.depends('order_line_ids.subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.subtotal for line in order.order_line_ids)

    @api.depends('order_line_ids.quantity')
    def _compute_processed_kilos(self):
        for order in self:
            order.processed_kilos = sum(line.quantity for line in order.order_line_ids)

    @api.depends('total_kilos', 'processed_kilos')
    def _compute_remaining_kilos(self):
        for order in self:
            order.remaining_kilos = (order.total_kilos or 0.0) - order.processed_kilos

    @api.depends('processed_kilos', 'order_line_ids.used_kilos')
    def _compute_waste_kilos(self):
        for order in self:
            total_used_kilos = sum(line.used_kilos for line in order.order_line_ids)
            order.waste_kilos = total_used_kilos - order.processed_kilos

    @api.depends('state')
    def _compute_can_confirm(self):
        for order in self:
            order.can_confirm = order.state == 'draft'

    @api.depends('state')
    def _compute_can_done(self):
        for order in self:
            order.can_done = order.state == 'processing'

    @api.depends('state')
    def _compute_can_cancel(self):
        for order in self:
            order.can_cancel = order.state in ['draft', 'processing']

    @api.depends('state')
    def _compute_can_set_to_draft(self):
        for order in self:
            order.can_set_to_draft = order.state == 'cancelled'
    
    @api.depends('processed_kilos', 'total_kilos')
    def _compute_progress(self):
        for order in self:
            order.progress = (order.processed_kilos / order.total_kilos) * 100 if order.total_kilos > 0 else 0

    def action_confirm(self):
        self.ensure_one()
        self.write({'state': 'processing'})

    def action_done(self):
        self.ensure_one()
        _logger.info('Iniciando action_done para la orden: %s', self.name)
        if self.state != 'processing':
            raise UserError('Solo se pueden finalizar órdenes en estado En Proceso.')

        # Validar que todos los productos tienen lotes asignados
        for line in self.order_line_ids:
            _logger.info('Validando lotes para el producto %s en la línea de orden %s', line.product_id.display_name, line.name)
            if not line.item_lot_ids:
                _logger.warning('No se ha proporcionado el número de lote o serie para el producto %s en la línea de orden %s.', line.product_id.display_name, line.name)
                raise UserError(_('Debe proporcionar el número de lote o serie para el producto %s en la línea de orden %s.') % (line.product_id.display_name, line.name))

        self._create_stock_moves()
        self._create_production_orders()
        self.write({'state': 'done'})
        _logger.info('Orden %s finalizada con éxito', self.name)

    def _check_product_availability(self, product, location, quantity):
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id)
        ])
        available_qty = sum(quant.quantity - quant.reserved_quantity for quant in quants)
        _logger.info('Cantidad disponible de %s en %s: %s', product.display_name, location.display_name, available_qty)
        if available_qty < quantity:
            _logger.warning('No hay suficiente cantidad de %s en %s. Cantidad disponible: %s, Cantidad requerida: %s', product.display_name, location.display_name, available_qty, quantity)
            raise UserError(_('No hay suficiente cantidad de %s en %s. Cantidad disponible: %s, Cantidad requerida: %s') % (product.display_name, location.display_name, available_qty))

    def _create_stock_moves(self):
        location_src_id = self.location_id.id
        location_dest_id = self._get_location_production_id()

        for line in self.order_line_ids:
            for product in self.product_ids:
                self._check_product_availability(product, self.location_id, line.used_kilos)

                # Validar que los lotes están presentes
                if not self.raw_material_lot_ids:
                    _logger.warning('No se proporcionaron lotes para el producto %s en la línea de orden %s', product.display_name, line.name)
                    raise UserError(_('Debe proporcionar el número de lote o serie para el producto %s en la línea de orden %s.') % (product.display_name, line.name))

                # Obtener el lote correcto para el producto
                lot_to_use = self.raw_material_lot_ids.filtered(lambda l: l.product_id == product)
                if not lot_to_use:
                    raise UserError(_('No se encontraron lotes disponibles para el producto %s.') % product.display_name)

                _logger.info('Creando movimiento de stock para el producto %s con los lotes %s', product.display_name, lot_to_use.mapped('name'))
                move = self.env['stock.move'].create({
                    'name': _('Consumo de %s para %s') % (product.display_name, line.product_id.display_name),
                    'product_id': product.id,
                    'product_uom_qty': line.used_kilos,
                    'product_uom': product.uom_id.id,
                    'location_id': location_src_id,
                    'location_dest_id': location_dest_id,
                    'lot_ids': [(6, 0, lot_to_use.ids)],  # Usar el lote correcto
                    'state': 'draft',
                })
                move._action_confirm()
                move._action_assign()
                move._action_done()
                _logger.info('Movimiento de stock creado y finalizado para el producto %s', product.display_name)

    def _get_location_production_id(self):
        try:
            return self.env.ref('stock.stock_location_production').id
        except ValueError:
            production_location = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
            if production_location:
                return production_location.id
            else:
                raise UserError('No se encontró una ubicación de producción válida en el sistema.')

    def _create_production_orders(self):
        self.ensure_one()
        if not self.product_ids:
            raise UserError('La Orden de Despiece debe tener al menos un producto.')

        for line in self.order_line_ids:
            bom = self.env['mrp.bom'].create({
                'product_tmpl_id': line.product_id.product_tmpl_id.id,
                'product_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'type': 'normal',
            })

            self.env['mrp.bom.line'].create({
                'bom_id': bom.id,
                'product_id': self.product_ids[0].id,
                'product_qty': line.used_kilos,
                'product_uom_id': self.env.ref('uom.product_uom_kgm').id,
            })

            production = self.env['mrp.production'].create({
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'bom_id': bom.id,
                'location_src_id': self.location_id.id,
                'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                'origin': self.name,
            })

            production.action_confirm()
            production.action_assign()
            production.button_plan()
            production.button_mark_done()

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})

    def action_set_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})


class MeatProcessingOrderLine(models.Model):
    _name = 'meat.processing.order.line'
    _description = 'Línea de Orden de Despiece de Carne'

    name = fields.Char(string='Nombre de la Línea de Orden')
    order_id = fields.Many2one('meat.processing.order', string='Orden', required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True, ondelete='restrict', index=True)
    quantity = fields.Float(string='Cantidad', required=True, default=0.0)
    used_kilos = fields.Float(string='Kilos Utilizados', required=True, default=0.0)
    unit_price = fields.Float(string='Precio Unitario', required=True, default=0.0)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    uom_id = fields.Many2one('uom.uom', string='Unidad de Medida', required=True, default=lambda self: self.env.ref('uom.product_uom_kgm').id)
    item_lot_ids = fields.Many2many('stock.lot', string='Lotes del Producto')  # Campo ajustado

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            return {'domain': {'item_lot_ids': [('product_id', '=', self.product_id.id)]}}
        else:
            return {'domain': {'item_lot_ids': [('id', '=', False)]}}  # No mostrar lotes si no hay producto seleccionado
