# -*- coding: utf-8 -*-
from odoo import models, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def write(self, vals):
        # Ejecutamos la escritura original primero
        res = super(AccountPayment, self).write(vals)
        
        # CAMBIO: Usamos 'posted' que es el estado real de los pagos confirmados
        if 'state' in vals and vals['state'] == 'posted':
            for payment in self:
                if payment.memo:
                    order = self.env['sale.order'].search([('name', 'ilike', payment.memo)], limit=1)
                    if order:
                        # Forzamos la actualización de la orden
                        order.invalidate_recordset(['commercial_payment_state'])
                        order.recompute(['commercial_payment_state'])
        return res
