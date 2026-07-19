# -*- coding: utf-8 -*-
from odoo import models

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        # Primero ejecutamos la acción original para que el pago se confirme exitosamente
        res = super(AccountPayment, self).action_post()
        
        for payment in self:
            # Obtenemos la referencia de forma segura sin usar 'ref' directamente
            # Usamos 'payment_reference' o el 'name' del pago
            reference = payment.payment_reference if 'payment_reference' in payment._fields else payment.name
            
            # Buscamos la orden de venta
            order = self.env['sale.order'].search([('name', 'ilike', reference)], limit=1)
            
            if order:
                # Escribimos los campos en la orden de venta
                order.write({
                    'last_payment_memo': reference,
                    'last_payment_journal': payment.journal_id.name if payment.journal_id else False,
                    'commercial_payment_state': 'paid' if payment.amount >= order.amount_total else 'partial'
                })
        return res
