# -*- coding: utf-8 -*-
from odoo import models

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            # Buscamos la orden que coincida con la referencia del pago
            order = self.env['sale.order'].search([('name', 'ilike', payment.ref)], limit=1)
            if order:
                # Forzamos la actualización de los campos computados
                order._compute_payment_info()
        return res
