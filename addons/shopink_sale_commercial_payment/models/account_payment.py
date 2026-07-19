class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        # Ejecutamos el posteo original
        res = super(AccountPayment, self).action_post()
        
        # Después de postear, forzamos la actualización de la orden
        for payment in self:
            if payment.memo:
                order = self.env['sale.order'].search([('name', 'ilike', payment.memo)], limit=1)
                if order:
                    order.invalidate_recordset(['commercial_payment_state'])
                    order.recompute(['commercial_payment_state'])
        return res
