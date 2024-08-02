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

    @api.depends('order_line_ids.subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.subtotal for line in order.order_line_ids)

    def action_confirm(self):
        self.state = 'processing'

    def action_done(self):
        for order in self:
            if order.state != 'processing':
                raise UserError('Solo se pueden finalizar órdenes en estado En Proceso.')
            order.state = 'done'
            for product in order.product_ids:
                stock_quant = self.env['stock.quant'].search([('product_id', '=', product.id)], limit=1)
                if stock_quant:
                    stock_quant.sudo().unlink()
            for line in order.order_line_ids:
                self.env['stock.quant'].create({
                    'product_id': line.product_id.id,
                    'location_id': stock_quant.location_id.id,
                    'quantity': line.quantity,
                    'uom_id': self.env.ref('uom.product_uom_kgm').id,
                })

    def action_cancel(self):
        self.state = 'cancelled'

    def action_set_to_draft(self):
        self.state = 'draft'


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
