from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Orden de Procesamiento de Carne'

    name = fields.Char(string='Nombre de la Orden', required=True, default=lambda self: _('Nuevo'))
    order_date = fields.Date(string='Fecha de Orden', required=True, default=fields.Date.today)
    product_ids = fields.Many2many('product.product', string='Canales', required=True)
    total_kilos = fields.Float(string='Total Kilos', required=True)
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

        for product in self.product_ids:
            stock_quants = self.env['stock.quant'].search([('product_id', '=', product.id)])
            if stock_quants:
                stock_quants.sudo().unlink()
            else:
                stock_quants = self.env['stock.quant'].browse([])

        for line in self.order_line_ids:
            self.env['stock.quant'].create({
                'product_id': line.product_id.id,
                'location_id': stock_quants and stock_quants[0].location_id.id or self.env.ref('stock.stock_location_stock').id,
                'quantity': line.quantity,
                'uom_id': self.env.ref('uom.product_uom_kgm').id,
            })
        self._create_production_order()

    def _create_production_order(self):
        self.ensure_one()
        production_vals = {
            'product_id': self.product_ids[0].id,
            'product_qty': self.total_kilos,
            'product_uom_id': self.env.ref('uom.product_uom_kgm').id,
            'location_src_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'origin': self.name,
            # Eliminar o ajustar el campo date_planned_start si es necesario
            # 'date_planned_start': fields.Datetime.now(),
        }
        self.env['mrp.production'].create(production_vals)

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
