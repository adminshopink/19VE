# -*- coding: utf-8 -*-
from odoo import models, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def write(self, vals):
        # Capturamos el estado antes de guardar los cambios
        # Si el valor que viene en 'vals' cambia el estado a 'posted'
        res = super(AccountPayment, self).write(vals)
        
        if 'state' in vals and vals['state'] == 'paid':
            for payment in self:
                # Buscamos la orden que coincida con el memo
                if payment.memo:
                    order = self.env['sale.order'].search([('name', 'ilike', payment.memo)], limit=1)
                    if order:
                        # Forzamos el recálculo del campo computado
                        order.recompute(['commercial_payment_state'])
                        
        return res
