from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Orden de Procesamiento de Carne'

    name = fields.Char(string='Nombre de la Orden', required=True, default=lambda self: _('Nuevo'))
    order_date = fields.Date(string='Fecha de Orden', required=True, default=fields.Date.today)
    product_ids = fields.Many2many('product.product', string='Canales', required=True)
    total_kilos = fields.Float(string='Total Kilos', required=False)  # Permitir nulo en el modelo
    processed_kilos = fields.Float(string='Kilos Procesados', compute='_compute_processed_kilos', store=True)
    remaining_kilos = fields.Float(string='Kilos Restantes', compute='_compute_remaining_kilos', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('processing', 'En Proceso'),
        ('done', 'Finalizado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft')
    order_line_ids = fields.One2many('meat.processing.order.line', 'order_id', string='Líneas de Orden')
    total_amount = fields.Float(string='Monto Total', compute='_compute_total_amount', store=True)
    notes = fields.Text(string='Notas')

    # Campos para la visibilidad de los botones
    can_confirm = fields.Boolean(string='Puede Confirmar', compute='_compute_can_confirm')
    can_done = fields.Boolean(string='Puede Finalizar', compute='_compute_can_done')
    can_cancel = fields.Boolean(string='Puede Cancelar', compute='_compute_can_cancel')
    can_set_to_draft = fields.Boolean(string='Puede Restablecer a Borrador', compute='_compute_can_set_to_draft')

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

    def action_confirm(self):
        self.ensure_one()
        self.write({'state': 'processing'})

    def action_done(self):
        self.ensure_one()
        if self.state != 'processing':
            raise UserError('Solo se pueden finalizar órdenes en estado En Proceso.')
        self.write({'state': 'done'})

        self._create_stock_moves()
        self._create_production_orders()

    def _create_stock_moves(self):
        location_src_id = self.env.ref('stock.stock_location_stock').id
        location_production_id = self._get_location_production_id()

        # Crear movimientos de inventario para los productos procesados
        moves = []
        for product in self.product_ids:
            move = self.env['stock.move'].create({
                'name': _('Consumo de %s') % product.display_name,
                'product_id': product.id,
                'product_uom_qty': product.weight,
                'product_uom': product.uom_id.id,
                'location_id': location_src_id,
                'location_dest_id': location_production_id,
                'state': 'draft',
            })
            moves.append(move)
        
        for move in moves:
            move._action_confirm()
            move._action_assign()
            move._action_done()

    def _get_location_production_id(self):
        # Intenta obtener la ubicación de producción usando diferentes métodos
        try:
            return self.env.ref('stock.stock_location_production').id
        except ValueError:
            # Si no se encuentra la ubicación por defecto, usa una búsqueda alternativa
            production_location = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
            if production_location:
                return production_location.id
            else:
                raise UserError('No se encontró una ubicación de producción válida en el sistema.')

    def _create_production_orders(self):
        self.ensure_one()
        if not self.product_ids:
            raise UserError('La orden de procesamiento debe tener al menos un producto.')

        for line in self.order_line_ids:
            # Crear la BoM y asociar las líneas de BoM
            bom = self.env['mrp.bom'].create({
                'product_tmpl_id': line.product_id.product_tmpl_id.id,
                'product_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'type': 'normal',
            })

            # Crear las líneas de BoM con el canal como ingrediente
            for product in self.product_ids:
                self.env['mrp.bom.line'].create({
                    'bom_id': bom.id,
                    'product_id': product.id,
                    'product_qty': product.weight,
                    'product_uom_id': product.uom_id.id,
                })

            production = self.env['mrp.production'].create({
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'bom_id': bom.id,
                'location_src_id': self._get_location_production_id(),
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
    _description = 'Línea de Orden de Procesamiento de Carne'

    name = fields.Char(string='Nombre de la Línea de Orden')
    order_id = fields.Many2one('meat.processing.order', string='Orden', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    quantity = fields.Float(string='Cantidad', required=True)
    unit_price = fields.Float(string='Precio Unitario', required=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    uom_id = fields.Many2one('uom.uom', string='Unidad de Medida', required=True, default=lambda self: self.env.ref('uom.product_uom_kgm').id)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
