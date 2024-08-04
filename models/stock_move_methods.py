from odoo import models, _
from odoo.exceptions import UserError

class MeatProcessingOrder(models.Model):
    _inherit = 'meat.processing.order'

    def _check_product_availability(self, product, location, quantity):
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id)
        ])
        available_qty = sum(quant.quantity - quant.reserved_quantity for quant in quants)
        if available_qty < quantity:
            raise UserError(_('No hay suficiente cantidad de %s en %s. Cantidad disponible: %s, Cantidad requerida: %s') % (product.display_name, location.display_name, available_qty, quantity))

    def _create_stock_moves(self):
        location_src_id = self.location_id.id
        location_dest_id = self._get_location_production_id()

        for line in self.order_line_ids:
            for product in self.product_ids:
                self._check_product_availability(product, self.location_id, line.used_kilos)
                move = self.env['stock.move'].create({
                    'name': _('Consumo de %s para %s') % (product.display_name, line.product_id.display_name),
                    'product_id': product.id,
                    'product_uom_qty': line.used_kilos,
                    'product_uom': product.uom_id.id,
                    'location_id': location_src_id,
                    'location_dest_id': location_dest_id,
                    'state': 'draft',
                })
                move._action_confirm()
                move._action_assign()
                move._action_done()

    def _get_location_production_id(self):
        try:
            return self.env.ref('stock.stock_location_production').id
        except ValueError:
            production_location = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
            if production_location:
                return production_location.id
            else:
                raise UserError('No se encontró una ubicación de producción válida en el sistema.')

    def _create_production_orders(self):
        self.ensure_one()
        if not self.product_ids:
            raise UserError('La Orden de Despiece debe tener al menos un producto.')

        for line in self.order_line_ids:
            bom = self.env['mrp.bom'].create({
                'product_tmpl_id': line.product_id.product_tmpl_id.id,
                'product_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'type': 'normal',
            })

            self.env['mrp.bom.line'].create({
                'bom_id': bom.id,
                'product_id': self.product_ids[0].id,
                'product_qty': line.used_kilos,
                'product_uom_id': self.env.ref('uom.product_uom_kgm').id,
            })

            production = self.env['mrp.production'].create({
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'bom_id': bom.id,
                'location_src_id': self.location_id.id,
                'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                'origin': self.name,
            })

            production.action_confirm()
            production.action_assign()
            production.button_plan()
            production.button_mark_done()
