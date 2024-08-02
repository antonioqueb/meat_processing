# meat_processing/models/meat_processing.py
from odoo import models, fields, api, _

class OrdenProcesamientoCarne(models.Model):
    _name = 'meat.processing.order'
    _description = 'Orden de Procesamiento de Carne'

    name = fields.Char(string='Referencia de Orden', required=True, copy=False, readonly=True, index=True, default=lambda self: _('Nuevo'))
    date = fields.Datetime(string='Fecha', default=fields.Datetime.now, required=True)
    product_id = fields.Many2one('product.product', string='Canal', required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('processing', 'En Proceso'),
        ('done', 'Completado'),
        ('cancel', 'Cancelado')
    ], string='Estado', readonly=True, copy=False, index=True, default='draft')
    line_ids = fields.One2many('meat.processing.order.line', 'order_id', string='Líneas de Orden', copy=True, auto_join=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code('meat.processing.order') or _('Nuevo')
        result = super(OrdenProcesamientoCarne, self).create(vals)
        return result

    def action_start_processing(self):
        self.state = 'processing'
        self._create_production_order()

    def action_done(self):
        self.state = 'done'
        self._mark_production_done()

    def action_cancel(self):
        self.state = 'cancel'
        self._cancel_production_order()

    def _create_production_order(self):
        production_obj = self.env['mrp.production']
        move_obj = self.env['stock.move']
        for order in self:
            production = production_obj.create({
                'name': order.name,
                'product_id': order.product_id.id,
                'product_qty': 1.0,
                'product_uom_id': order.product_id.uom_id.id,
                'bom_id': False,
                'origin': order.name,
            })

            for line in order.line_ids:
                move_obj.create({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': order.product_id.property_stock_production.id,
                    'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                    'production_id': production.id,
                })

            production.action_confirm()
            production.action_assign()

    def _mark_production_done(self):
        for order in self:
            productions = self.env['mrp.production'].search([('origin', '=', order.name)])
            for production in productions:
                production.button_mark_done()

    def _cancel_production_order(self):
        for order in self:
            productions = self.env['mrp.production'].search([('origin', '=', order.name)])
            for production in productions:
                production.action_cancel()

class LineaOrdenProcesamientoCarne(models.Model):
    _name = 'meat.processing.order.line'
    _description = 'Línea de Orden de Procesamiento de Carne'

    order_id = fields.Many2one('meat.processing.order', string='Referencia de Orden', required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    quantity = fields.Float(string='Cantidad', required=True)
