# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commercial_payment_state = fields.Selection([
        ('unpaid', 'No Pagado'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Totalmente Pagado')
    ], string='Estado de Pago (Comercial)', compute='_compute_commercial_payment_state', store=True, default='unpaid')

    @api.depends('state', 'amount_total')
    def _compute_commercial_payment_state(self):
        """ Evalúa el estado buscando pagos publicados usando el campo 'memo' """
        if 'account.payment' not in self.env:
            for order in self:
                order.commercial_payment_state = 'unpaid'
            return

        for order in self:
            if order.state not in ('sale', 'done'):
                order.commercial_payment_state = 'unpaid'
                continue
            
            # Se utiliza 'memo' en lugar de 'communication' según el modelo detectado
            payments = self.env['account.payment'].search([
                ('memo', 'ilike', order.name),
                ('state', '=', 'posted')
            ])
            
            total_paid = sum(pay.amount for pay in payments)
            
            if total_paid >= order.amount_total:
                order.commercial_payment_state = 'paid'
            elif total_paid > 0:
                order.commercial_payment_state = 'partial'
            else:
                order.commercial_payment_state = 'unpaid'

    def action_register_commercial_payment(self):
        """ Abre el asistente nativo apuntando a la referencia 'memo' """
        self.ensure_one()
        
        journal = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1)
        
        return {
            'name': _('Registrar Pago Comercial'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'views': [(self.env.ref('account.view_account_payment_form').id, 'form')],
            'type': 'ir.actions.act_url' if False else 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_total,
                'default_journal_id': journal.id if journal else False,
                'default_memo': _('Pago Comercial - %s') % self.name, # Actualizado el contexto
            },
        }
