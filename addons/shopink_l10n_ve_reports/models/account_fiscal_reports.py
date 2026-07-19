# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import base64

class L10nVeFiscalReportWizard(models.TransientModel):
    _name = 'l10n_ve.fiscal.report.wizard'
    _description = 'Asistente para Libros Fiscales Venezuela'

    date_from = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='Fecha Fin', required=True, default=fields.Date.context_today)
    report_type = fields.Selection([
        ('purchase', 'Libro de Compras'),
        ('sale', 'Libro de Ventas')
    ], string='Tipo de Libro', required=True, default='sale')

    def action_generate_xlsx(self):
        self.ensure_one()
        # Buscamos facturas publicadas en el rango de fechas
        domain = [
            ('date', '>=', self.date_from), 
            ('date', '<=', self.date_to), 
            ('state', '=', 'posted')
        ]
        
        if self.report_type == 'sale':
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
            filename = "Libro_de_Ventas"
        else:
            domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))
            filename = "Libro_de_Compras"
            
        moves = self.env['account.move'].search(domain, order='date asc, name asc')
        
        if not moves:
            raise UserError(_("No hay facturas registradas en el rango de fechas seleccionado."))

        return self._generate_report(moves, filename)

    def _generate_report(self, moves, filename):
        report_data = []
        for i, move in enumerate(moves, 1):
            row = {
                'N° Operacion': i,
                'Fecha': move.invoice_date or move.date,
                'Nombre': move.partner_id.name or '',
                'RIF': move.partner_id.vat or '',
                'N° Factura': move.name or '',
                'Total': move.amount_total,
                # Campos de retención de IVA
                'N° Comprobante IVA': move.l10n_ve_iva_holding_number or '',
                'Fecha Comprobante IVA': move.l10n_ve_iva_holding_date or '',
                'Monto IVA Retenido': move.l10n_ve_iva_amount_retained or 0.0,
                # Campos de retención de ISLR
                'N° Comprobante ISLR': move.l10n_ve_islr_withholding_number or '',
                'Monto ISLR Retenido': move.l10n_ve_islr_amount_retained or 0.0,
            }
            report_data.append(row)
        
        return self._create_download_action(report_data, filename)

    def _create_download_action(self, data, filename):
        # Creamos el contenido CSV (formato compatible con Excel)
        output = io.StringIO()
        keys = data[0].keys()
        output.write('\t'.join(keys) + '\n')
        for row in data:
            # Convertimos valores a texto, manejando nulos y tipos
            values = [str(row.get(k, '')).replace('\t', ' ') for k in keys]
            output.write('\t'.join(values) + '\n')
            
        csv_data = output.getvalue().encode('utf-16')
        
        # Creamos el archivo adjunto en Odoo
        attachment = self.env['ir.attachment'].create({
            'name': f'{filename}.xls',
            'type': 'binary',
            'datas': base64.b64encode(csv_data),
            'mimetype': 'application/vnd.ms-excel',
        })
        
        # Retornamos la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
