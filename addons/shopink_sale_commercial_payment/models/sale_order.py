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
        """ Evalúa el estado buscando pagos publicados usando el campo 'ref' """
        for order in self:
            if order.state not in ('sale', 'done'):
                order.commercial_payment_state = 'unpaid'
                continue
            
            # Buscamos en 'ref' (campo estándar de Odoo para el concepto del pago)
            # Usamos ilike con % para encontrar la orden incluso si el texto incluye "Pago Comercial -"
            payments = self.env['account.payment'].search([
                ('ref', 'ilike', order.name),
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
        """ Abre el asistente nativo usando 'ref' en el contexto """
        self.ensure_one()
        
        journal = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1)
        
        return {
            'name': _('Registrar Pago Comercial'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'views': [(self.env.ref('account.view_account_payment_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_total,
                'default_journal_id': journal.id if journal else False,
                'default_ref': _('Pago Comercial - %s') % self.name, # Cambiado default_memo a default_ref
            },
        }
