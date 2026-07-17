# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class L10nVeIslrConcept(models.Model):
    _name = 'l10n_ve.islr.concept'
    _description = 'Conceptos de Retención de ISLR Venezuela'

    name = fields.Char(string='Concepto/Actividad', required=True)
    code = fields.Char(string='Código de Actividad', help='Código oficial del SENIAT')
    withholding_percentage = fields.Float(string='% Retención', digits=(5, 2))
    subtracting_ut = fields.Float(string='Sustraendo en UT', default=0.0)
    person_type = fields.Selection([
        ('pn_r', 'Persona Natural Residente'),
        ('pn_nr', 'Persona Natural No Residente'),
        ('pj_d', 'Persona Jurídica Domiciliada'),
        ('pj_nd', 'Persona Jurídica No Domiciliada')
    ], string='Tipo de Persona', required=True)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Control de Retenciones
    l10n_ve_apply_withholding = fields.Boolean(
        string='Factura con Retención', 
        default=False,
        help='Marque esta casilla si la factura aplica para retención inmediata de IVA/ISLR.'
    )
    
    # Diario Puente Destino
    l10n_ve_bridge_journal_id = fields.Many2one(
        'account.journal', 
        string='Diario Puente de Retención',
        domain="[('type', 'in', ('bank', 'cash', 'general'))]"
    )

    # IVA Recibido (Clientes)
    l10n_ve_iva_holding_number = fields.Char(string='Núm. Comprobante IVA Cliente', copy=False)
    l10n_ve_iva_holding_date = fields.Date(string='Fecha Comprobante IVA Cliente', copy=False)
    l10n_ve_iva_amount_retained = fields.Monetary(string='Monto IVA Retenido', currency_field='company_currency_id', copy=False)
    l10n_ve_iva_bridge_move_id = fields.Many2one('account.move', string='Asiento Puente IVA', readonly=True, copy=False)

    # ISLR Emitido/Recibido (Resumen)
    l10n_ve_islr_withholding_number = fields.Char(string='Núm. Comprobante ISLR', copy=False)
    l10n_ve_islr_amount_retained = fields.Monetary(
        string='Monto ISLR Retenido',
        currency_field='company_currency_id',
        compute='_compute_l10n_ve_islr_amounts',
        store=True
    )

    @api.depends('invoice_line_ids.l10n_ve_islr_concept_id', 'amount_untaxed', 'l10n_ve_apply_withholding')
    def _compute_l10n_ve_islr_amounts(self):
        ut_value = 9.00  
        for move in self:
            total_retained = 0.0
            if move.l10n_ve_apply_withholding and move.move_type == 'in_invoice':
                for line in move.invoice_line_ids:
                    concept = line.l10n_ve_islr_concept_id
                    if concept:
                        line_retained = line.price_subtotal * (concept.withholding_percentage / 100.0)
                        subtracting_bs = concept.subtracting_ut * ut_value
                        line_retained -= subtracting_bs
                        if line_retained > 0:
                            total_retained += line_retained
            move.l10n_ve_islr_amount_retained = total_retained

    def action_post(self):
        """ Interceptamos la publicación para obligar al usuario a confirmar en el wizard
            si se trata de una factura de cliente bajo regulaciones digitales. """
        # Si ya viene aprobado desde el wizard de confirmación, salta el popup
        if self._context.get('skip_confirmation_wizard'):
            res = super(AccountMove, self).action_post()
            # Se ejecuta tu lógica nativa original del asiento puente
            for move in self:
                if move.move_type == 'out_invoice' and move.l10n_ve_apply_withholding:
                    if move.l10n_ve_iva_amount_retained > 0.0:
                        move._create_l10n_ve_iva_bridge_entry()
            return res

        # Si el usuario hace click directo en "Confirmar" desde el formulario
        for move in self:
            if move.move_type == 'out_invoice' and move.state == 'draft':
                return {
                    'name': _('Confirmación Obligatoria de Emisión Digital'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move.confirmation.wizard',
                    'view_mode': 'form',
                    'view_id': self.env.ref('shopink_l10n_ve_withholding.view_account_move_confirmation_wizard_form').id,
                    'target': 'new',
                    'context': {
                        'default_move_id': move.id,
                    }
                }

        # Flujo por defecto si es una factura de proveedor (in_invoice) o asientos diarios normales
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.move_type == 'out_invoice' and move.l10n_ve_apply_withholding:
                if move.l10n_ve_iva_amount_retained > 0.0:
                    move._create_l10n_ve_iva_bridge_entry()
        return res

    def button_cancel(self):
        """ Restricción Absoluta: Bloquea la anulación directa de facturas ya emitidas 
            bajo regulaciones de Factura Digital (Providencia SENIAT). """
        for move in self:
            if move.move_type == 'out_invoice' and move.state == 'posted':
                raise UserError(_(
                    "Por regulaciones de Facturación Digital (Providencia SENIAT), "
                    "las facturas emitidas no pueden ser canceladas ni modificadas. "
                    "Cualquier ajuste posterior debe realizarse mediante Notas de Crédito o Débito."
                ))
        return super(AccountMove, self).button_cancel()

    def _create_l10n_ve_iva_bridge_entry(self):
        """ Genera el asiento contable automático en el diario puente seleccionado """
        self.ensure_one()
        if not self.l10n_ve_bridge_journal_id:
            raise UserError("Por favor, seleccione el 'Diario Puente de Retención' antes de validar la factura.")

        if self.l10n_ve_iva_bridge_move_id:
            return

        partner_account = self.partner_id.property_account_receivable_id
        if not partner_account:
            raise UserError(f"El cliente {self.partner_id.name} no tiene una cuenta por cobrar configurada.")

        move_lines = [
            (0, 0, {
                'name': f'Retención IVA {self.l10n_ve_iva_holding_number or ""} de Factura {self.name}',
                'account_id': self.l10n_ve_bridge_journal_id.default_account_id.id or partner_account.id,
                'debit': self.l10n_ve_iva_amount_retained,
                'credit': 0.0,
            }),
            (0, 0, {
                'name': f'Cruze Retención IVA Factura {self.name}',
                'account_id': partner_account.id,
                'partner_id': self.partner_id.id,
                'debit': 0.0,
                'credit': self.l10n_ve_iva_amount_retained,
            }),
        ]

        bridge_move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.l10n_ve_bridge_journal_id.id,
            'date': self.l10n_ve_iva_holding_date or fields.Date.today(),
            'ref': f'COMPR. IVA: {self.l10n_ve_iva_holding_number or "N/A"}',
            'line_ids': move_lines,
        })
        bridge_move.action_post()
        self.write({'l10n_ve_iva_bridge_move_id': bridge_move.id})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_ve_islr_concept_id = fields.Many2one('l10n_ve.islr.concept', string='Concepto ISLR')
