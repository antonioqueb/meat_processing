from odoo import api,models, fields



class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Meat Processing Order'

    name = fields.Char(string='Order Name', required=True)
    order_date = fields.Date(string='Order Date', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    order_line_ids = fields.One2many('meat.processing.order.line', 'order_id', string='Order Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    name = fields.Char(string='Order Name')
class MeatProcessingOrderLine(models.Model):
    _name = 'meat.processing.order.line'
    _description = 'Meat Processing Order Line'

    name = fields.Char(string='Order Line Name')
    order_id = fields.Many2one('meat.processing.order', string='Order', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price