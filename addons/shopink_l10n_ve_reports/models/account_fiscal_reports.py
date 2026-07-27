# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import xlsxwriter


class L10nVeFiscalReportWizard(models.TransientModel):
    _name = 'l10n_ve.fiscal.report.wizard'
    _description = 'Wizard para Libros Fiscales (Compras / Ventas)'

    date_from = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='Fecha Fin', required=True, default=fields.Date.context_today)
    report_type = fields.Selection(
        [('purchase', 'Compra'), ('sale', 'Venta')],
        string='Tipo', required=True, default='sale'
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_doc_type(self, move):
        """Devuelve (codigo, es_nota_credito, es_nota_debito)"""
        is_refund = move.move_type in ('out_refund', 'in_refund')
        is_debit_note = bool(getattr(move, 'debit_origin_id', False)) and not is_refund
        if is_refund:
            return 'NC', True, False
        if is_debit_note:
            return 'ND', False, True
        return 'FAC', False, False

    def _get_tax_breakdown(self, move):
        """Desglosa bases e IVA por alícuota (16% / 8%) a partir de las líneas
        de impuesto reales del asiento, y calcula el monto exento."""
        base16 = iva16 = base8 = iva8 = 0.0
        tax_lines = move.line_ids.filtered(
            lambda l: l.tax_line_id and l.tax_line_id.amount > 0
            and l.tax_line_id.type_tax_use in ('sale', 'purchase')
        )
        for l in tax_lines:
            rate = round(l.tax_line_id.amount, 2)
            base = abs(l.tax_base_amount)
            iva = abs(l.balance)
            if rate == 16:
                base16 += base
                iva16 += iva
            elif rate == 8:
                base8 += base
                iva8 += iva

        exento = round((move.amount_untaxed or 0.0) - base16 - base8, 2)
        if exento < 0:
            exento = 0.0

        return base16, iva16, base8, iva8, exento

    def _company_header_lines(self):
        company = self.env.company
        address_parts = [p for p in [company.street, company.street2, company.city] if p]
        address = ', '.join(address_parts) if address_parts else ''
        return company.name or '', address

    # ------------------------------------------------------------------
    # Generación del Excel
    # ------------------------------------------------------------------
    def action_generate_xlsx(self):
        self.ensure_one()

        is_sale = self.report_type == 'sale'
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'posted'),
        ]
        if is_sale:
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
        else:
            domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))

        moves = self.env['account.move'].search(domain, order='invoice_date, name')
        if not moves:
            raise UserError(_("No hay facturas encontradas en este rango de fechas."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet_name = 'Libro de Ventas' if is_sale else 'Libro de Compras'
        sheet = workbook.add_worksheet(sheet_name)

        # ---------------- Formatos ----------------
        title_format = workbook.add_format({'bold': True, 'font_size': 12})
        subtitle_format = workbook.add_format({'font_size': 10})
        group_header_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#BFBFBF'
        })
        header_format = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#D3D3D3', 'text_wrap': True
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'center'})
        text_format = workbook.add_format({'border': 1, 'align': 'left'})
        money_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        total_money_format = workbook.add_format({
            'border': 1, 'num_format': '#,##0.00', 'bold': True, 'bg_color': '#F2F2F2'
        })
        resumen_title_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D3D3D3'})
        resumen_label_format = workbook.add_format({'border': 1, 'align': 'left'})
        note_format = workbook.add_format({'italic': True, 'font_size': 8, 'font_color': '#666666'})

        # ---------------- Encabezado de empresa ----------------
        company_name, company_address = self._company_header_lines()
        sheet.merge_range(0, 2, 0, 10, company_name, title_format)
        sheet.merge_range(1, 2, 1, 10, f"Dirección: {company_address}", subtitle_format)
        sheet.merge_range(2, 2, 2, 10, sheet_name, title_format)
        sheet.merge_range(
            3, 2, 3, 10,
            "Desde %s Hasta %s" % (self.date_from.strftime('%d/%m/%Y'), self.date_to.strftime('%d/%m/%Y')),
            subtitle_format
        )

        # ---------------- Grupos de columnas (fila 6, índice 5) ----------------
        group_row = 5
        sheet.merge_range(group_row, 0, group_row, 10, 'DETALLE DEL DOCUMENTO', group_header_format)
        sheet.merge_range(group_row, 11, group_row, 13, 'TOTALES', group_header_format)
        sheet.merge_range(group_row, 14, group_row, 16, 'ALÍCUOTA GENERAL (16%)', group_header_format)
        sheet.merge_range(group_row, 17, group_row, 19, 'ALÍCUOTA REDUCIDA (8%)', group_header_format)
        sheet.merge_range(group_row, 20, group_row, 22, 'RETENCIONES', group_header_format)

        # ---------------- Encabezados de columna (fila 7, índice 6) ----------------
        header_row = 6
        if is_sale:
            headers = [
                'N° operación', 'Fecha del documento', 'RIF', 'Nombre/Razón social',
                'Tipo de Documento', 'N° de Factura', 'N° Nota de Crédito', 'N° Nota de Débito',
                'N° de control', 'Tipo de transacción', 'N° Factura afectada',
                'Total ventas', 'Total ventas con IVA', 'Total ventas exentas',
                'Base imponible (16%)', 'Alícuota (16%)', 'IVA 16%',
                'Base imponible (8%)', 'Alícuota (8%)', 'IVA 8%',
                'Fecha Retención', 'N° Retención', 'IVA retenido',
            ]
        else:
            headers = [
                'N° operación', 'Fecha del documento', 'RIF', 'Nombre/Razón social',
                'Tipo de Documento', 'N° de Factura', 'N° Nota de Crédito', 'N° Nota de Débito',
                'N° de control proveedor', 'Tipo de transacción', 'N° Factura afectada',
                'Total compras', 'Total compras con IVA', 'Total compras exentas',
                'Base imponible (16%)', 'Alícuota (16%)', 'IVA 16%',
                'Base imponible (8%)', 'Alícuota (8%)', 'IVA 8%',
                'Fecha Retención', 'N° Retención', 'IVA retenido',
            ]
        for col, head in enumerate(headers):
            sheet.write(header_row, col, head, header_format)

        col_widths = [10, 13, 15, 28, 10, 10, 12, 12, 12, 12, 14, 12, 14, 14, 13, 10, 10, 13, 10, 10, 12, 12, 12]
        for col, w in enumerate(col_widths):
            sheet.set_column(col, col, w)

        # ---------------- Filas de detalle ----------------
        row = header_row + 1
        op_number = 1

        total_base16 = total_iva16 = total_base8 = total_iva8 = 0.0
        total_exento = total_neto = total_con_iva = total_retenido = 0.0
        # Totales separados para el resumen (facturas/ND vs notas de crédito)
        fac_base16 = fac_iva16 = fac_base8 = fac_iva8 = fac_exento = 0.0
        nc_base16 = nc_iva16 = nc_base8 = nc_iva8 = nc_exento = 0.0

        for m in moves:
            doc_type, is_nc, is_nd = self._get_doc_type(m)
            base16, iva16, base8, iva8, exento = self._get_tax_breakdown(m)

            num_factura = m.name if doc_type == 'FAC' else ''
            num_nc = m.name if doc_type == 'NC' else ''
            num_nd = m.name if doc_type == 'ND' else ''

            factura_afectada = ''
            if is_nc and m.reversed_entry_id:
                factura_afectada = m.reversed_entry_id.name
            elif is_nd and getattr(m, 'debit_origin_id', False):
                factura_afectada = m.debit_origin_id.name

            control_number = getattr(m, 'l10n_ve_control_number', '') or ''

            sheet.write(row, 0, op_number, cell_format)
            sheet.write(row, 1, m.invoice_date.strftime('%d/%m/%Y') if m.invoice_date else '', cell_format)
            sheet.write(row, 2, m.partner_id.vat or '', cell_format)
            sheet.write(row, 3, m.partner_id.name or '', text_format)
            sheet.write(row, 4, doc_type, cell_format)
            sheet.write(row, 5, num_factura, cell_format)
            sheet.write(row, 6, num_nc, cell_format)
            sheet.write(row, 7, num_nd, cell_format)
            sheet.write(row, 8, control_number, cell_format)
            sheet.write(row, 9, '01-REG', cell_format)
            sheet.write(row, 10, factura_afectada, cell_format)
            sheet.write(row, 11, m.amount_untaxed, money_format)
            sheet.write(row, 12, m.amount_total, money_format)
            sheet.write(row, 13, exento, money_format)
            sheet.write(row, 14, base16, money_format)
            sheet.write(row, 15, 0.16, cell_format)
            sheet.write(row, 16, iva16, money_format)
            sheet.write(row, 17, base8, money_format)
            sheet.write(row, 18, 0.08, cell_format)
            sheet.write(row, 19, iva8, money_format)

            iva_ret_date = getattr(m, 'l10n_ve_iva_holding_date', False)
            iva_ret_num = getattr(m, 'l10n_ve_iva_holding_number', '') or ''
            iva_retenido = getattr(m, 'l10n_ve_iva_amount_retained', 0.0) or 0.0
            sheet.write(row, 20, iva_ret_date.strftime('%d/%m/%Y') if iva_ret_date else '', cell_format)
            sheet.write(row, 21, iva_ret_num, cell_format)
            sheet.write(row, 22, iva_retenido, money_format)

            total_base16 += base16
            total_iva16 += iva16
            total_base8 += base8
            total_iva8 += iva8
            total_exento += exento
            total_neto += m.amount_untaxed
            total_con_iva += m.amount_total
            total_retenido += iva_retenido

            if is_nc:
                nc_base16 += base16
                nc_iva16 += iva16
                nc_base8 += base8
                nc_iva8 += iva8
                nc_exento += exento
            else:
                fac_base16 += base16
                fac_iva16 += iva16
                fac_base8 += base8
                fac_iva8 += iva8
                fac_exento += exento

            row += 1
            op_number += 1

        # ---------------- Fila de totales ----------------
        totals_row = row
        sheet.write(totals_row, 11, total_neto, total_money_format)
        sheet.write(totals_row, 12, total_con_iva, total_money_format)
        sheet.write(totals_row, 13, total_exento, total_money_format)
        sheet.write(totals_row, 14, total_base16, total_money_format)
        sheet.write(totals_row, 16, total_iva16, total_money_format)
        sheet.write(totals_row, 17, total_base8, total_money_format)
        sheet.write(totals_row, 19, total_iva8, total_money_format)
        sheet.write(totals_row, 22, total_retenido, total_money_format)

        # ---------------- Resumen (estilo SENIAT) ----------------
        resumen_row = totals_row + 2
        sheet.merge_range(resumen_row, 0, resumen_row, 1, 'Resumen', resumen_title_format)
        sheet.merge_range(resumen_row, 2, resumen_row, 3, 'Facturas/Notas de Débito', resumen_title_format)
        sheet.merge_range(resumen_row, 4, resumen_row, 5, 'Notas de Crédito', resumen_title_format)
        sheet.merge_range(resumen_row, 6, resumen_row, 7, 'Total Neto', resumen_title_format)

        sub_header_row = resumen_row + 1
        etiqueta_debito = 'Débitos Fiscales' if is_sale else 'Créditos Fiscales'
        sheet.write(sub_header_row, 1, etiqueta_debito, resumen_label_format)
        for c in (2, 4, 6):
            sheet.write(sub_header_row, c, 'Base Imponible', resumen_label_format)
        for c in (3, 5, 7):
            sheet.write(sub_header_row, c, etiqueta_debito, resumen_label_format)

        lineas = [
            (1, 'Ventas Internas no Gravadas' if is_sale else 'Compras Internas no Gravadas',
             fac_exento, 0.0, nc_exento, 0.0),
            (2, 'Exportaciones Gravadas por Alícuota General (completar manualmente)', 0.0, 0.0, 0.0, 0.0),
            (3, 'Exportaciones Gravadas por Alícuota General más Adicional (completar manualmente)', 0.0, 0.0, 0.0, 0.0),
            (4, 'Ventas Internas Gravadas sólo por Alícuota General' if is_sale
                else 'Compras Internas Gravadas sólo por Alícuota General',
             fac_base16, fac_iva16, nc_base16, nc_iva16),
            (5, 'Ventas Internas Gravadas por Alícuota Reducida' if is_sale
                else 'Compras Internas Gravadas por Alícuota Reducida',
             fac_base8, fac_iva8, nc_base8, nc_iva8),
            (6, 'Ajustes a los Débitos/Créditos Fiscales de Periodos Anteriores (completar manualmente)', 0.0, 0.0, 0.0, 0.0),
        ]

        current_row = sub_header_row + 1
        total_base_neto = 0.0
        total_fiscal_neto = 0.0
        for num, label, base_fac, fiscal_fac, base_nc, fiscal_nc in lineas:
            base_neto = base_fac - base_nc
            fiscal_neto = fiscal_fac - fiscal_nc
            sheet.write(current_row, 0, num, cell_format)
            sheet.write(current_row, 1, label, resumen_label_format)
            sheet.write(current_row, 2, base_fac, money_format)
            sheet.write(current_row, 3, fiscal_fac, money_format)
            sheet.write(current_row, 4, base_nc, money_format)
            sheet.write(current_row, 5, fiscal_nc, money_format)
            sheet.write(current_row, 6, base_neto, money_format)
            sheet.write(current_row, 7, fiscal_neto, money_format)
            if num in (1, 4, 5):
                total_base_neto += base_neto
                total_fiscal_neto += fiscal_neto
            current_row += 1

        # Fila 7: Total Ventas/Compras y Débitos/Créditos Fiscales del Periodo
        sheet.write(current_row, 0, 7, cell_format)
        sheet.write(current_row, 1,
                     'Total Ventas y Débitos Fiscales del Periodo' if is_sale
                     else 'Total Compras y Créditos Fiscales del Periodo',
                     resumen_label_format)
        sheet.write(current_row, 2, fac_base16 + fac_base8 + fac_exento, money_format)
        sheet.write(current_row, 3, fac_iva16 + fac_iva8, money_format)
        sheet.write(current_row, 4, nc_base16 + nc_base8 + nc_exento, money_format)
        sheet.write(current_row, 5, nc_iva16 + nc_iva8, money_format)
        sheet.write(current_row, 6, total_base_neto, money_format)
        sheet.write(current_row, 7, total_fiscal_neto, money_format)
        current_row += 1

        # Fila 8: Total Retenciones
        sheet.write(current_row, 0, 8, cell_format)
        sheet.write(current_row, 1, 'Total Retenciones', resumen_label_format)
        sheet.write(current_row, 2, total_retenido, money_format)
        for c in (3, 4, 5, 6, 7):
            sheet.write(current_row, c, 0.0, money_format)
        current_row += 2

        note_text = (
            "Nota: las filas 2, 3 y 6 del resumen (exportaciones y ajustes de periodos anteriores) "
            "deben completarse manualmente; no se derivan de los documentos registrados en Odoo."
        )
        sheet.merge_range(current_row, 0, current_row, 15, note_text, note_format)

        workbook.close()
        output.seek(0)

        filename = "Libro_de_%s_%s_%s.xlsx" % (
            'Ventas' if is_sale else 'Compras',
            self.date_from.strftime('%Y%m%d'),
            self.date_to.strftime('%Y%m%d'),
        )
        data = base64.b64encode(output.getvalue())
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
