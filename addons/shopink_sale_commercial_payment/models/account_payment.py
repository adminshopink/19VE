# -*- coding: utf-8 -*-
from odoo import models, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        # Ejecutamos el posteo original
        res = super(AccountPayment, self).action_post()
        
        # Después de confirmar, forzamos la actualización de la orden
        for payment in self:
            if payment.memo:
                # Buscamos la orden que coincida con el memo
                order = self.env['sale.order'].search([('name', 'ilike', payment.memo)], limit=1)
                if order:
                    # Invalidamos y recalculamos
                    order.invalidate_recordset(['commercial_payment_state'])
                    order.recompute(['commercial_payment_state'])
        return res
