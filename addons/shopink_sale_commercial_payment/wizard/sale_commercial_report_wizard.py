from odoo import models, fields, api

class SaleCommercialReportWizard(models.TransientModel):
    _name = 'sale.commercial.report.wizard'
    _description = 'Asistente de Reporte de Pagos Comerciales'

    date_from = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='Fecha Fin', required=True, default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='Vendedor')

    def action_print_report(self):
        # Aquí más adelante procesaremos la búsqueda en account.payment
        # usando self.date_from, self.date_to y self.user_id
        return {'type': 'ir.actions.act_window_close'}
