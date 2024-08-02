from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Meat Processing Order'

    name = fields.Char(string='Order Name', required=True, default=lambda self: _('New'))
    order_date = fields.Date(string='Order Date', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    order_line_ids = fields.One2many('meat.processing.order.line', 'order_id', string='Order Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    notes = fields.Text(string='Notes')

    @api.depends('order_line_ids.subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.subtotal for line in order.order_line_ids)

    def action_confirm(self):
        self.state = 'confirmed'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_set_to_draft(self):
        self.state = 'draft'


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
