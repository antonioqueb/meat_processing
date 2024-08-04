from odoo import models, api

class MeatProcessingOrder(models.Model):
    _inherit = 'meat.processing.order'

    @api.depends('order_line_ids.subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.subtotal for line in order.order_line_ids)

    @api.depends('order_line_ids.quantity')
    def _compute_processed_kilos(self):
        for order in self:
            order.processed_kilos = sum(line.quantity for line in order.order_line_ids)

    @api.depends('total_kilos', 'processed_kilos')
    def _compute_remaining_kilos(self):
        for order in self:
            order.remaining_kilos = (order.total_kilos or 0.0) - order.processed_kilos

    @api.depends('processed_kilos', 'order_line_ids.used_kilos')
    def _compute_waste_kilos(self):
        for order in self:
            total_used_kilos = sum(line.used_kilos for line in order.order_line_ids)
            order.waste_kilos = total_used_kilos - order.processed_kilos

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
