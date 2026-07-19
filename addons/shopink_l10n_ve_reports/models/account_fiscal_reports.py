# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import xlsxwriter

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
            raise UserError(_("No hay facturas encontradas en este rango de fechas."))

        # 2. Preparar el Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Libro Fiscal')
        
        # Formatos
        header_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D3D3D3'})
        
        # Encabezados (ajustados a tu necesidad básica; puedes ampliar esta lista)
        headers = ['Fecha', 'N° Factura', 'Nombre Cliente/Proveedor', 'RIF', 'Total Ventas', 'IVA Retenido', 'ISLR Retenido']
        for col, head in enumerate(headers):
            sheet.write(0, col, head, header_format)
        
        # 3. Llenar filas
        row = 1
        for m in moves:
            sheet.write(row, 0, str(m.date))
            sheet.write(row, 1, m.name or '')
            sheet.write(row, 2, m.partner_id.name or '')
            sheet.write(row, 3, m.partner_id.vat or '')
            sheet.write(row, 4, m.amount_total)
            # Aseguramos campos de retención (ajusta según los nombres reales en tu Odoo 19)
            sheet.write(row, 5, getattr(m, 'l10n_ve_iva_amount_retained', 0.0))
            sheet.write(row, 6, getattr(m, 'l10n_ve_islr_amount_retained', 0.0))
            row += 1

        workbook.close()
        output.seek(0)
        
        # 4. Crear archivo y retornar
        data = base64.b64encode(output.getvalue())
        attachment = self.env['ir.attachment'].create({
            'name': 'Libro_Fiscal.xlsx',
            'datas': data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
