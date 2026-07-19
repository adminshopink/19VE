# models/sale_order.py

    @api.depends('name', 'amount_total')
    def _compute_payment_info(self):
        for order in self:
            # En lugar de usar 'ref' o 'payment_reference' que dan error,
            # buscamos en 'name' (que es el número de asiento/referencia del pago)
            # Esto es más universal en Odoo.
            payment = self.env['account.payment'].search([
                ('name', 'ilike', order.name),
                ('state', '=', 'posted')
            ], limit=1, order='create_date desc')
            
            if payment:
                order.last_payment_memo = payment.ref or payment.name
                order.last_payment_journal = payment.journal_id.name
                order.commercial_payment_state = 'paid' if payment.amount >= order.amount_total else 'partial'
            else:
                order.last_payment_memo = False
                order.last_payment_journal = False
                order.commercial_payment_state = 'unpaid'
