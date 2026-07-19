# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campo de estado principal
    commercial_payment_state = fields.Selection([
        ('unpaid', 'No Pagado'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Totalmente Pagado')
    ], string='Estado de Pago (Comercial)', compute='_compute_commercial_payment_state', store=True, default='unpaid')

    # Campos de auditoría visual para ver qué pago disparó el estado
    last_payment_memo = fields.Char(string='Referencia de Pago', compute='_compute_payment_info', store=True)
    last_payment_journal = fields.Char(string='Banco/Diario', compute='_compute_payment_info', store=True)

    @api.depends('name', 'amount_total')
    def _compute_payment_info(self):
        """Busca el pago más reciente vinculado por memo para mostrar los datos en la vista."""
        for order in self:
            payment = self.env['account.payment'].search([
                ('memo', 'ilike', order.name),
                ('state', '=', 'posted')
            ], limit=1, order='create_date desc')
            
            if payment:
                order.last_payment_memo = payment.memo
                order.last_payment_journal = payment.journal_id.name
            else:
                order.last_payment_memo = False
                order.last_payment_journal = False

    @api.depends('amount_total', 'name')
    def _compute_commercial_payment_state(self):
        """Calcula el estado comparando el total de la orden vs la suma de pagos posted."""
        for order in self:
            # Buscamos TODOS los pagos que coincidan con el nombre de esta orden
            payments = self.env['account.payment'].search([
                ('memo', 'ilike', order.name),
                ('state', '=', 'posted')
            ])
            
            total_paid = sum(payments.mapped('amount'))
            
            # Lógica pura: si el total pagado es >= al total de la orden, es 'paid'
            if order.amount_total > 0 and total_paid >= order.amount_total:
                order.commercial_payment_state = 'paid'
            elif total_paid > 0:
                order.commercial_payment_state = 'partial'
            else:
                order.commercial_payment_state = 'unpaid'

    def action_register_commercial_payment(self):
        """Asistente para registrar el pago comercial."""
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
                'default_memo': _('Pago Comercial - %s') % self.name,
            },
        }
