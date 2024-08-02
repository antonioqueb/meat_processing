# meat_processing/models/meat_processing.py
from odoo import models, fields, api

class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Meat Processing Order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    product_id = fields.Many2one('product.product', string='Carcass', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, copy=False, index=True, default='draft')

    line_ids = fields.One2many('meat.processing.order.line', 'order_id', string='Order Lines', copy=True, auto_join=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('meat.processing.order') or _('New')
        result = super(MeatProcessingOrder, self).create(vals)
        return result

    def action_start_processing(self):
        self.state = 'processing'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

class MeatProcessingOrderLine(models.Model):
    _name = 'meat.processing.order.line'
    _description = 'Meat Processing Order Line'

    order_id = fields.Many2one('meat.processing.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True)
