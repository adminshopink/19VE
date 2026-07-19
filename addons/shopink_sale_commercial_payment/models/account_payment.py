# -*- coding: utf-8 -*-
from odoo import models

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            # Buscamos la orden que coincida con el memo (en Odoo el campo es 'ref' o 'name')
            # Usamos 'name' del pago porque ahí suele estar la referencia bancaria
            order = self.env['sale.order'].search([('name', 'ilike', payment.ref or payment.name)], limit=1)
            
            if order:
                # Escribimos directo en los campos de la orden (sin funciones compute)
                order.write({
                    'last_payment_memo': payment.ref or payment.name,
                    'last_payment_journal': payment.journal_id.name,
                    'commercial_payment_state': 'paid' if payment.amount >= order.amount_total else 'partial'
                })
        return res
