# -*- coding: utf-8 -*-
import logging
import requests
import csv
from io import StringIO
from datetime import datetime

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def action_sync_usd_ves_sheets(self):
        """
        Descarga el CSV de Google Sheets, extrae la tasa USD/VES
        y actualiza el histórico de tasas para la moneda USD en Odoo.
        """
        # Enlace público de Google Sheets en formato CSV
        url_sheets = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSXzkT-yiqr_exSRCS49aN4ON8zNpKMXl05ewz2ToBs-terE-All76LdR4Ch936sUpCrNfG9QUrOyHb/pub?gid=0&single=true&output=csv"
        
        try:
            response = requests.get(url_sheets, timeout=15)
            response.raise_for_status()
        except Exception as e:
            _logger.error("Error conectando a Google Sheets: %s", str(e))
            return False

        csv_data = csv.reader(StringIO(response.text))
        
        try:
            header = next(csv_data)
        except StopIteration:
            _logger.warning("El archivo de Google Sheets está vacío.")
            return False

        # La moneda que fluctúa en Odoo es el USD (El VES se mantiene como base = 1.0)
        usd_currency = self.search([('name', '=', 'USD')], limit=1)
        if not usd_currency:
            _logger.error("No se encontró la moneda USD en el sistema para asignarle la tasa.")
            return False

        for row in csv_data:
            if not row or len(row) < 2:
                continue
                
            fecha_str = row[0].strip()  # Ejemplo: '2026-07-16'
            tasa_str = row[1].strip().replace(',', '.') 
            
            try:
                tasa_valor = float(tasa_str)
                if tasa_valor <= 0:
                    continue
                
                try:
                    fecha_tasa = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                except ValueError:
                    fecha_tasa = fields.Date.today()

                # Odoo guarda la tasa de forma inversa (1 / valor_de_tasa_bcv)
                odoo_rate_value = 1.0 / tasa_valor

                existing_rate = self.env['res.currency.rate'].search([
                    ('currency_id', '=', usd_currency.id),
                    ('name', '=', fecha_tasa),
                    ('company_id', '=', self.env.company.id)
                ], limit=1)

                if existing_rate:
                    existing_rate.write({'company_rate': odoo_rate_value})
                    _logger.info("Tasa USD actualizada para la fecha %s: %s (Inversa: %s)", fecha_tasa, tasa_valor, odoo_rate_value)
                else:
                    self.env['res.currency.rate'].create({
                        'currency_id': usd_currency.id,
                        'name': fecha_tasa,
                        'company_rate': odoo_rate_value,
                        'company_id': self.env.company.id
                    })
                    _logger.info("Nueva tasa USD creada para la fecha %s: %s (Inversa: %s)", fecha_tasa, tasa_valor, odoo_rate_value)

            except ValueError:
                _logger.warning("No se pudo procesar la línea del CSV: %s", row)
                continue

        return True
