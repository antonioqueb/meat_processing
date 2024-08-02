from odoo import models, fields

class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Meat Processing Order'

    name = fields.Char(string='Order Name')

class MeatProcessingOrderLine(models.Model):
    _name = 'meat.processing.order.line'
    _description = 'Meat Processing Order Line'

    name = fields.Char(string='Order Line Name')
    order_id = fields.Many2one('meat.processing.order', string='Order')
