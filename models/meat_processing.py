from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Orden de Despiece de Carne'

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
    raw_material_lot_ids = fields.Many2many('stock.lot', string='Lotes de Materia Prima')
    start_time = fields.Datetime(string='Hora de Inicio', default=fields.Datetime.now)
    responsible_id = fields.Many2one('res.users', string='Responsable', index=True)
    progress = fields.Float(string='Progreso', compute='_compute_progress', store=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Orden de Compra de Origen', readonly=True)

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
            order.remaining_kilos = max(0, (order.total_kilos or 0.0) - order.processed_kilos)

    @api.depends('processed_kilos', 'order_line_ids.used_kilos')
    def _compute_waste_kilos(self):
        for order in self:
            total_used_kilos = sum(line.used_kilos for line in order.order_line_ids)
            order.waste_kilos = max(0, total_used_kilos - order.processed_kilos)

    @api.depends('processed_kilos', 'total_kilos')
    def _compute_progress(self):
        for order in self:
            order.progress = (order.processed_kilos / order.total_kilos) * 100 if order.total_kilos > 0 else 0

    def action_confirm(self):
        self.write({'state': 'processing'})

    def action_done(self):
        _logger.info('Iniciando action_done para la orden: %s', self.name)
        if self.state != 'processing':
            raise UserError(_('Solo se pueden finalizar órdenes en estado En Proceso.'))
        
        self._validate_lots()
        self._create_stock_moves()
        self._create_production_orders()
        self.write({'state': 'done'})
        _logger.info('Orden %s finalizada con éxito', self.name)

    def _validate_lots(self):
        for line in self.order_line_ids:
            if not line.item_lot_ids:
                raise UserError(_('Debe proporcionar el número de lote o serie para %(product)s.') % {
                    'product': line.product_id.display_name
                })

    def _create_stock_moves(self):
        location_src_id = self.location_id.id
        location_dest_id = self._get_location_production_id()

        for line in self.order_line_ids:
            for product in self.product_ids:
                lot_to_use = self.raw_material_lot_ids.filtered(lambda l: l.product_id == product)
                if not lot_to_use:
                    raise UserError(_('No se encontraron lotes disponibles para el producto %(product)s.') % {
                        'product': product.display_name
                    })

                move = self.env['stock.move'].create({
                    'name': _('Consumo de %(product)s para %(line_product)s') % {
                        'product': product.display_name,
                        'line_product': line.product_id.display_name
                    },
                    'product_id': product.id,
                    'product_uom_qty': line.used_kilos,
                    'product_uom': product.uom_id.id,
                    'location_id': location_src_id,
                    'location_dest_id': location_dest_id,
                })
                move._action_confirm()
                move._action_assign()
                move._action_done()


    def _create_production_orders(self):
        for line in self.order_line_ids:
            if not line.product_id:
                raise UserError(_('La línea de orden no tiene un producto definido.'))

            # Buscar el BOM usando el producto
            bom = self.env['mrp.bom']._bom_find(
                product=line.product_id,
                picking_type=self.picking_type_id,
                company_id=self.company_id.id
            )

            if not bom:
                raise UserError(_('No se encontró una lista de materiales para el producto %s.') % line.product_id.display_name)

            # Validar ubicación de destino
            location_dest = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
            if not location_dest:
                raise UserError(_('La ubicación de destino no está configurada en el sistema.'))

            # Crear la orden de producción
            production = self.env['mrp.production'].create({
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'bom_id': bom.id,
                'location_src_id': self.location_id.id,
                'location_dest_id': location_dest.id,
                'origin': self.name,
            })

            # Confirmar y planificar la producción
            production.action_confirm()
            production.action_assign()
            production.button_plan()


    def _get_location_production_id(self):
        try:
            return self.env.ref('stock.stock_location_production').id
        except ValueError:
            production_location = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
            if production_location:
                return production_location.id
            else:
                raise UserError(_('No se encontró una ubicación de producción válida en el sistema.'))

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_to_draft(self):
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
    item_lot_ids = fields.Many2many('stock.lot', string='Lotes del Producto')
    lot_names = fields.Char(string='Lotes Seleccionados', compute='_compute_lot_names')

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.depends('item_lot_ids')
    def _compute_lot_names(self):
        for line in self:
            line.lot_names = ', '.join(line.item_lot_ids.mapped('name'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('quantity', '>', 0),
                ('location_id', '=', self.order_id.location_id.id),
                ('lot_id', '!=', False)
            ])
            suggested_lots = quants.mapped('lot_id')
            self.item_lot_ids = suggested_lots
            return {'domain': {'item_lot_ids': [('id', 'in', suggested_lots.ids)]}}
        else:
            self.item_lot_ids = False
            return {'domain': {'item_lot_ids': [('id', '=', False)]}}
