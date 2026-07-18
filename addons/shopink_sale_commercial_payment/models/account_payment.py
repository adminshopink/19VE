# -*- coding: utf-8 -*-
from odoo import models, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        # Ejecutamos la lógica estándar de publicación de Odoo
        res = super(AccountPayment, self).action_post()
        
        for payment in self:
            # Usamos 'memo' que es el campo real en tu base de datos
            if payment.memo:
                # Buscamos la orden de venta que coincida con el contenido del campo memo
                order = self.env['sale.order'].search([('name', 'ilike', payment.memo)], limit=1)
                
                if order:
                    # Forzamos el recálculo del campo computado en la orden
                    order.recompute(['commercial_payment_state'])
        
        return res
