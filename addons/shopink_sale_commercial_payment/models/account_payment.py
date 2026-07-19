def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            # BUSCAMOS POR EL CAMPO 'ref' (Referencia) que es donde Odoo pone el memo
            search_term = payment.ref or payment.memo
            if search_term:
                order = self.env['sale.order'].search([('name', 'ilike', search_term)], limit=1)
                if order:
                    order.invalidate_recordset(['commercial_payment_state', 'last_payment_memo', 'last_payment_journal'])
                    order.recompute(['commercial_payment_state', 'last_payment_memo', 'last_payment_journal'])
        return res
