# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    last_payment_memo = fields.Char(string='Referencia de Pago', compute='_compute_payment_info', store=True)
    last_payment_journal = fields.Char(string='Banco/Diario', compute='_compute_payment_info', store=True)
    commercial_payment_state = fields.Selection([
        ('unpaid', 'No Pagado'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Totalmente Pagado')
    ], string='Estado de Pago (Comercial)', compute='_compute_payment_info', store=True, default='unpaid')

    @api.depends('name', 'amount_total')
    def _compute_payment_info(self):
        for order in self:
            # Depuración: Ver qué busca el sistema en los logs de Odoo.sh
            _logger.info(f"Buscando pagos para la orden: {order.name}")
            
            payment = self.env['account.payment'].search([
                ('memo', 'ilike', order.name),
                ('state', '=', 'posted')
            ], limit=1, order='create_date desc')
            
            if payment:
                _logger.info(f"¡Pago encontrado! ID: {payment.id}, Memo: {payment.memo}")
                order.last_payment_memo = payment.memo
                order.last_payment_journal = payment.journal_id.name
                
                # Definimos el estado basado en el pago encontrado
                if order.amount_total > 0 and payment.amount >= order.amount_total:
                    order.commercial_payment_state = 'paid'
                else:
                    order.commercial_payment_state = 'partial'
            else:
                _logger.info("No se encontraron pagos vinculados.")
                order.last_payment_memo = False
                order.last_payment_journal = False
                order.commercial_payment_state = 'unpaid'
