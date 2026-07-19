# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io

class L10nVeFiscalReportWizard(models.TransientModel):
    _name = 'l10n_ve.fiscal.report.wizard'
    _description = 'Wizard para Libros Fiscales'

    date_from = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='Fecha Fin', required=True, default=fields.Date.context_today)
    report_type = fields.Selection([('purchase', 'Compra'), ('sale', 'Venta')], string='Tipo', required=True, default='sale')

    def action_generate_xlsx(self):
        # 1. Definir búsqueda
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('state', '=', 'posted')]
        if self.report_type == 'sale':
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
        else:
            domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))
            
        moves = self.env['account.move'].search(domain)
        if not moves:
            raise UserError(_("No hay facturas encontradas."))

        # 2. Generar datos (CSV tabulado)
        output = io.StringIO()
        headers = ['Fecha', 'N° Factura', 'Nombre', 'RIF', 'Total', 'IVA Ret', 'ISLR Ret']
        output.write('\t'.join(headers) + '\n')
        
        for m in moves:
            row = [
                str(m.date), m.name or '', m.partner_id.name or '', m.partner_id.vat or '',
                str(m.amount_total), str(m.l10n_ve_iva_amount_retained), str(m.l10n_ve_islr_amount_retained)
            ]
            output.write('\t'.join(row) + '\n')

        # 3. Crear adjunto y retornar URL
        data = base64.b64encode(output.getvalue().encode('utf-16'))
        attachment = self.env['ir.attachment'].create({
            'name': 'reporte.xls',
            'datas': data,
            'mimetype': 'application/vnd.ms-excel',
        })
        return {'type': 'ir.actions.act_url', 'url': f'/web/content/{attachment.id}?download=true', 'target': 'new'}
