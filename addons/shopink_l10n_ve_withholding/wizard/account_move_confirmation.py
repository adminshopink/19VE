# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.models import TransientModel 

class AccountMoveConfirmationWizard(TransientModel):
    _name = 'account.move.confirmation.wizard'
    _description = 'Asistente de Confirmacion de Factura Digital'

    move_id = fields.Many2one('account.move', string='Factura', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='move_id.partner_id', string='Cliente')
    
    # CORRECCIÓN: Usar Monetary para coincidir con el tipo de campo en account.move
    currency_id = fields.Many2one('res.currency', related='move_id.currency_id', string='Moneda')
    amount_total = fields.Monetary(
        related='move_id.amount_total', 
        string='Monto Total', 
        currency_field='currency_id'
    )

    def action_force_post(self):
        self.ensure_one()
        return self.move_id.with_context(skip_confirmation_wizard=True).action_post()
