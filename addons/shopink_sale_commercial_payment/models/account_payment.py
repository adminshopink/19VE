# -*- coding: utf-8 -*-
from odoo import models, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        # Ejecutamos la lógica estándar de publicación de Odoo
        res = super(AccountPayment, self).action_post()
        
        for payment in self:
            # Buscamos la orden de venta basándonos en la referencia guardada
            # Usamos un filtro para asegurar que solo buscamos si hay una referencia
            if payment.ref:
                # Extraemos el nombre de la orden si el formato es "Pago Comercial - S00001"
                # o simplemente buscamos la coincidencia si el memo/ref coincide
                order = self.env['sale.order'].search([('name', 'ilike', payment.ref)], limit=1)
                
                if order:
                    # Forzamos el recálculo del campo computado en la orden
                    order.recompute(['commercial_payment_state'])
        
        return res
