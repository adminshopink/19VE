# -*- coding: utf-8 -*-
from odoo import models, fields, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campos normales (ya no computados)
    last_payment_memo = fields.Char(string='Referencia de Pago', readonly=True)
    last_payment_journal = fields.Char(string='Banco/Diario', readonly=True)
    commercial_payment_state = fields.Selection([
        ('unpaid', 'No Pagado'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Totalmente Pagado')
    ], string='Estado de Pago (Comercial)', default='unpaid', readonly=True)

    # ESTA FUNCIÓN ES LA QUE EL XML BUSCA. DEBE EXISTIR.
    def action_register_commercial_payment(self):
        self.ensure_one()
        return {
            'name': _('Registrar Pago'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_amount': self.amount_total,
                'default_ref': self.name,
            },
        }
