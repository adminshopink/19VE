import requests
import datetime
from odoo import models, api
from odoo.exceptions import UserError

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def actualizar_tasa_bcv_shopink(self):
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not usd_currency:
            raise UserError("No se encontró la moneda USD configurada en el sistema.")

        url_csv_shopink = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSXzkT-yiqr_exSRCS49aN4ON8zNpKMXl05ewz2ToBs-terE-All76LdR4Ch936sUpCrNfG9QUrOyHb/pub?gid=0&single=true&output=csv"

        try:
            respuesta = requests.get(url_csv_shopink, timeout=10)
            contenido = respuesta.text.strip()
            
            lineas = contenido.split('\n')
            if not lineas:
                raise UserError("El archivo CSV está vacío.")
                
            columnas = lineas[0].split(',')
            tasa_encontrada = 0.0
            
            for col in columnas:
                valor_limpio = col.replace('"', '').strip()
                if '.' in valor_limpio:
                    try:
                        posible_tasa = float(valor_limpio)
                        if posible_tasa > 500:
                            tasa_encontrada = posible_tasa
                            break
                    except ValueError:
                        continue
                        
            if tasa_encontrada == 0.0:
                for col in columnas:
                    valor_limpio = col.replace('"', '').strip().replace(',', '.')
                    try:
                        posible_tasa = float(valor_limpio)
                        if posible_tasa > 500:
                            tasa_encontrada = posible_tasa
                            break
                    except ValueError:
                        continue
                        
            if tasa_encontrada > 0:
                factor_inverso = 1.0 / tasa_encontrada
                fecha_hoy = datetime.date.today()
                
                domain = [
                    ('currency_id', '=', usd_currency.id),
                    ('name', '=', fecha_hoy)
                ]
                if 'company_id' in self.env['res.currency.rate']._fields:
                    domain.append(('company_id', '=', self.env.company.id))
                    
                tasa_existente = self.env['res.currency.rate'].search(domain, limit=1)
                
                val_tasa = {'rate': factor_inverso}
                if 'company_rate' in self.env['res.currency.rate']._fields:
                    val_tasa['company_rate'] = factor_inverso

                if tasa_existente:
                    tasa_existente.write(val_tasa)
                else:
                    val_tasa.update({
                        'currency_id': usd_currency.id,
                        'name': fecha_hoy,
                    })
                    if 'company_id' in self.env['res.currency.rate']._fields:
                        val_tasa['company_id'] = self.env.company.id
                        
                    self.env['res.currency.rate'].create(val_tasa)
            else:
                raise UserError('No se encontró un formato de tasa válido mayor a 500 en el CSV.')
                
        except Exception as e:
            raise UserError('Error en la sincronización automática: %s' % str(e))
