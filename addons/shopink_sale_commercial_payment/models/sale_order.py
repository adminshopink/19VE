# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    last_payment_memo = fields.Char(string='Referencia de Pago', compute='_compute_payment_info', store=True)
    last_payment_journal = fields.Char(string='Banco/Diario', compute='_compute_payment_info', store=True)
    commercial_payment_state = fields.Selection([
        ('unpaid', 'No Pagado'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Totalmente Pagado')
    ], string='Estado de Pago (Comercial)', compute='_compute_payment_info', store=True, default='unpaid')

    # ESTA ES LA FUNCIÓN QUE TE FALTABA Y QUE EL XML ESTÁ BUSCANDO
    def action_register_commercial_payment(self):
        self.ensure_one()
        return {
            'name': _('Registrar Pago Comercial'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_amount': self.amount_total,
                'default_ref': self.name,  # Esto pone el S00001 automáticamente en el memo
            },
        }

    @api.depends('name', 'amount_total')
    def _compute_payment_info(self):
        for order in self:
            # NOTA: Asegúrate de que el campo en account.payment se llame 'ref' o 'memo'
            # Odoo estándar usa 'ref' (Referencia)
            payment = self.env['account.payment'].search([
                ('ref', 'ilike', order.name),
                ('state', '=', 'posted')
            ], limit=1, order='create_date desc')
            
            if payment:
                order.last_payment_memo = payment.ref
                order.last_payment_journal = payment.journal_id.name
                order.commercial_payment_state = 'paid' if payment.amount >= order.amount_total else 'partial'
            else:
                order.last_payment_memo = False
                order.last_payment_journal = False
                order.commercial_payment_state = 'unpaid'
