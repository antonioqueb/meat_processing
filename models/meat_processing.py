from odoo import models, fields

class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Meat Processing Order'

    name = fields.Char(string='Order Name')
