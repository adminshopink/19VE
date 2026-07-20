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
        # 1. Búsqueda de facturas
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('state', '=', 'posted')]
        if self.report_type == 'sale':
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
        else:
            domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))
            
        moves = self.env['account.move'].search(domain)
        if not moves:
            raise UserError(_("No hay facturas encontradas en este rango de fechas."))

        # 2. Creación del archivo Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Libro Fiscal')
        
        # Estilos
        header_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#D3D3D3'})
        cell_format = workbook.add_format({'border': 1, 'align': 'center'})
        money_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        
        # Encabezados de las 27 columnas
        headers = [
            'N° operacion', 'Fecha', 'RIF', 'Nombre/Razón social', 'Tipo Doc', 
            'N° Factura', 'N° Nota Crédito', 'N° Nota Débito', 'N° control', 
            'Tipo transacción', 'N° Factura afectada', 'Total ventas', 'Total ventas c/IVA', 
            'Total ventas exentas', 'Base Imp. 16%', 'Alicuota 16%', 'IVA 16%', 
            'Base Imp. 8%', 'Alicuota 8%', 'IVA 8%', 'Base Imp. 31%', 'Alicuota 31%', 
            'IVA 31%', 'Igtf', 'Fecha Retención', 'N° Retención', 'IVA retenido'
        ]
        
        # Escribir encabezados en la fila 9 (índice 8)
        for col, head in enumerate(headers):
            sheet.write(8, col, head, header_format)
        
        # 3. Llenar filas
        row = 9 # Empezamos en la fila 10
        for m in moves:
            sheet.write(row, 0, m.name or '', cell_format)
            sheet.write(row, 1, str(m.invoice_date or ''), cell_format)
            sheet.write(row, 2, m.partner_id.vat or '', cell_format)
            sheet.write(row, 3, m.partner_id.name or '', cell_format)
            sheet.write(row, 4, m.move_type, cell_format)
            sheet.write(row, 5, m.name or '', cell_format)
            sheet.write(row, 11, m.amount_total, money_format)
            # Retenciones básicas (si no existen, pone 0)
            sheet.write(row, 26, getattr(m, 'l10n_ve_iva_amount_retained', 0.0), money_format)
            row += 1

        workbook.close()
        output.seek(0)
        
        # 4. Retornar archivo
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
