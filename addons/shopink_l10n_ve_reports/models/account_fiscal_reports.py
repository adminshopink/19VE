# -*- coding: utf-8 -*-
from odoo import models, fields, api
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
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'posted'),
        ]
        
        if self.report_type == 'sale':
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
            moves = self.env['account.move'].search(domain, order='date asc, name asc')
            return self._generate_sale_book(moves)
        else:
            domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))
            moves = self.env['account.move'].search(domain, order='date asc, name asc')
            return self._generate_purchase_book(moves)

    def _generate_sale_book(self, moves):
        report_data = []
        operacion = 1
        
        for move in moves:
            tipo_trans = '01-REG'
            if move.state == 'cancel':
                tipo_trans = '03-ANU'
            elif move.move_type == 'out_refund':
                tipo_trans = '02-COMP'
                
            base_16, iva_16 = 0.0, 0.0
            base_8, iva_8 = 0.0, 0.0
            base_31, iva_31 = 0.0, 0.0
            exempt = 0.0

            for line in move.invoice_line_ids:
                if not line.tax_ids:
                    exempt += line.price_subtotal
                    continue
                for tax in line.tax_ids:
                    if tax.amount == 16.0:
                        base_16 += line.price_subtotal
                        iva_16 += line.price_total - line.price_subtotal
                    elif tax.amount == 8.0:
                        base_8 += line.price_subtotal
                        iva_8 += line.price_total - line.price_subtotal
                    elif tax.amount == 31.0:
                        base_31 += line.price_subtotal
                        iva_31 += line.price_total - line.price_subtotal

            rif = move.partner_id.vat or ''
            name = move.partner_id.name or ''
            
            row = {
                'N° operacion': operacion,
                'Fecha del documento': move.invoice_date or move.date,
                'RIF': rif,
                'Nombre/Razón social': name,
                'Tipo de Documento': 'FAC' if move.move_type == 'out_invoice' else 'NOT',
                'N° de Factura': move.name if move.move_type == 'out_invoice' else '',
                'N° Nota de Crédito': move.name if move.move_type == 'out_refund' else '',
                'N° Nota de Débito': '',
                'N° de control': move.payment_reference or '',
                'Tipo de transacción': tipo_trans,
                'N° Factura afectada': move.reversed_entry_id.name if move.reversed_entry_id else '--',
                'Total ventas': move.amount_total if move.state != 'cancel' else 0.0,
                'Total ventas con IVA': move.amount_total if move.state != 'cancel' else 0.0,
                'Total ventas exentas': exempt,
                'Base imponible (16%)': base_16,
                'Alicuota (16%)': 0.16,
                'IVA 16%': iva_16,
                'Base imponible (8%)': base_8,
                'Alicuota (8%)': 0.08,
                'IVA 8%': iva_8,
                'Base imponible (31%)': base_31,
                'Alicuota (31%)': 0.31,
                'IVA 31%': iva_31,
                'Igtf': 0.0,
                'Fecha Retención': getattr(move, 'l10n_ve_iva_holding_date', '') or '',
                'N° Retención': getattr(move, 'l10n_ve_iva_holding_number', '') or '',
                'IVA retenido': getattr(move, 'l10n_ve_iva_amount_retained', 0.0) or 0.0,
            }
            report_data.append(row)
            operacion += 1

        return self._create_download_action(report_data, "Libro_de_Ventas")

    def _generate_purchase_book(self, moves):
        report_data = []
        operacion = 1
        for move in moves:
            rif = move.partner_id.vat or ''
            name = move.partner_id.name or ''
            row = {
                'N° operacion': operacion,
                'Fecha del documento': move.invoice_date or move.date,
                'RIF': rif,
                'Nombre/Razón social': name,
                'Tipo de Documento': 'FAC' if move.move_type == 'in_invoice' else 'NOT',
                'N° de Factura': move.ref or '',
                'N° Nota de Crédito': move.name if move.move_type == 'in_refund' else '',
                'N° Nota de Débito': '',
                'N° de control': '', 
                'Tipo de transacción': '01-REG',
                'N° Factura afectada': '',
                'Total compras': move.amount_total,
                'Total compras con IVA': move.amount_total,
                'Total compras exentas': 0.0,
                'Base imponible (16%)': move.amount_untaxed,
                'Alicuota (16%)': 0.16,
                'IVA 16%': move.amount_tax,
                'Fecha Retención': getattr(move, 'l10n_ve_iva_holding_date', '') or '',
                'N° Retención': getattr(move, 'l10n_ve_iva_holding_number', '') or '',
                'IVA retenido': getattr(move, 'l10n_ve_iva_amount_retained', 0.0) or 0.0,
            }
            report_data.append(row)
            operacion += 1
            
        return self._create_download_action(report_data, "Libro_de_Compras")

    def _create_download_action(self, data, filename):
        if not data:
            raise UserError("No hay registros en el rango de fechas seleccionado.")
            
        output = io.StringIO()
        keys = data[0].keys()
        output.write('\t'.join(keys) + '\n')
        for row in data:
            output.write('\t'.join([str(row[k]) for k in keys]) + '\n')
            
        csv_data = output.getvalue().encode('utf-16')
        attachment = self.env['ir.attachment'].create({
            'name': f'{filename}.xls',
            'type': 'binary',
            'datas': base64.b64encode(csv_data),
            'mimetype': 'application/vnd.ms-excel',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
