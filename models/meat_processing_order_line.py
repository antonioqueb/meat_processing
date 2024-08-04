from odoo import models, fields, api

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

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
