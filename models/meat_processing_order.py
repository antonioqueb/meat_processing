from odoo import models, fields, api, _
from . import compute_methods
from . import stock_move_methods

class MeatProcessingOrder(models.Model):
    _name = 'meat.processing.order'
    _description = 'Orden de Despiece de Carne'

    name = fields.Char(string='Nombre de la Orden', required=True, readonly=True, default=lambda self: _('Nuevo'))
    order_date = fields.Date(string='Fecha de Orden', required=True, default=fields.Date.today)
    product_ids = fields.Many2many('product.product', string='Canales', required=True)
    location_id = fields.Many2one('stock.location', string='Ubicación del Producto', required=True, ondelete='restrict', index=True)
    total_kilos = fields.Float(string='Total Kilos', required=False)
    processed_kilos = fields.Float(string='Kilos Procesados', compute='_compute_processed_kilos', store=True)
    remaining_kilos = fields.Float(string='Kilos Restantes', compute='_compute_remaining_kilos', store=True)
    waste_kilos = fields.Float(string='Kilos de Desperdicio', compute='_compute_waste_kilos', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('processing', 'En Proceso'),
        ('done', 'Finalizado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft')
    order_line_ids = fields.One2many('meat.processing.order.line', 'order_id', string='Líneas de Orden', required=True)
    total_amount = fields.Float(string='Monto Total', compute='_compute_total_amount', store=True)
    notes = fields.Text(string='Notas')

    can_confirm = fields.Boolean(string='Puede Confirmar', compute='_compute_can_confirm')
    can_done = fields.Boolean(string='Puede Finalizar', compute='_compute_can_done')
    can_cancel = fields.Boolean(string='Puede Cancelar', compute='_compute_can_cancel')
    can_set_to_draft = fields.Boolean(string='Puede Restablecer a Borrador', compute='_compute_can_set_to_draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code('meat.processing.order') or _('Nuevo')
        return super(MeatProcessingOrder, self).create(vals)

    def action_confirm(self):
        self.ensure_one()
        self.write({'state': 'processing'})

    def action_done(self):
        self.ensure_one()
        if self.state != 'processing':
            raise UserError('Solo se pueden finalizar órdenes en estado En Proceso.')
        self.write({'state': 'done'})
        self._create_stock_moves()
        self._create_production_orders()

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})

    def action_set_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
