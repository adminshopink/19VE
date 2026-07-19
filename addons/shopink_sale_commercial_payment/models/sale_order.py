# Añadimos el parámetro 'search' y 'inverse' opcionales para mayor estabilidad
    commercial_payment_state = fields.Selection([
        ('unpaid', 'No Pagado'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Totalmente Pagado')
    ], string='Estado de Pago (Comercial)', compute='_compute_commercial_payment_state', store=True, default='unpaid')

    @api.depends('state', 'amount_total', 'name') # 'name' es clave porque el memo lo busca por el nombre de la orden
    def _compute_commercial_payment_state(self):
        for order in self:
            if order.state not in ('sale', 'done'):
                order.commercial_payment_state = 'unpaid'
                continue
            
            # Buscamos pagos en estado 'posted'
            payments = self.env['account.payment'].search([
                ('memo', 'ilike', order.name),
                ('state', '=', 'posted')
            ])
            
            total_paid = sum(payments.mapped('amount')) # .mapped es más eficiente que el sum() con generador
            
            if total_paid >= order.amount_total and order.amount_total > 0:
                order.commercial_payment_state = 'paid'
            elif total_paid > 0:
                order.commercial_payment_state = 'partial'
            else:
                order.commercial_payment_state = 'unpaid'
