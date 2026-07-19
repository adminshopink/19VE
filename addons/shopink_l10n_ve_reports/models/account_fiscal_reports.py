# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import io
import base64

_logger = logging.getLogger(__name__)

class L10nVeFiscalReportWizard(models.TransientModel):
    _name = 'l10n_ve.fiscal.report.wizard'
    _description = 'Asistente para Libros Fiscales Venezuela'

    date_from = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='Fecha Fin', required=True, default=fields.Date.context_today)
    # Simplificado para evitar conflictos
    report_type = fields.Selection([
        ('purchase', 'Libro de Compras'),
        ('sale', 'Libro de Ventas')
    ], string='Tipo de Libro', required=True, default='sale')

    def action_generate_xlsx(self):
        self.ensure_one()
        _logger.info("DEBUG: Botón presionado. Generando reporte...")
        
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('state', '=', 'posted')]
        
        if self.report_type == 'sale':
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
            filename = "Libro_de_Ventas"
        else:
            domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))
            filename = "Libro_de_Compras"
            
        moves = self.env['account.move'].search(domain)
        _logger.info(f"DEBUG: Facturas encontradas: {len(moves)}")
        
        if not moves:
            raise UserError(_("No hay facturas en este rango."))

        return self._generate_report(moves, filename)
    
    # ... (el resto de los métodos _generate_report y _create_download_action igual al anterior)
