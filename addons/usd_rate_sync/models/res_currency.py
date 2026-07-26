# -*- coding: utf-8 -*-
import logging
from datetime import date

import requests

from odoo import api, models

_logger = logging.getLogger(__name__)

# URL del CSV público (Google Sheets publicado como CSV)
URL_CSV_TASA_USD = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vSXzkT-yiqr_exSRCS49aN4ON8"
    "zNpKMXl05ewz2ToBs-terE-All76LdR4Ch936sUpCrNfG9QUrOyHb/pub?gid=0&single=true&output=csv"
)


class ResCurrency(models.Model):
    _inherit = "res.currency"

    @api.model
    def cron_actualizar_tasa_usd(self):
        """Método invocado por el ir.cron. Nunca debe lanzar una excepción
        no controlada: si algo falla, se registra en el log y el cron
        continúa disponible para el próximo intento."""
        usd_currency = self.search([("name", "=", "USD")], limit=1)
        if not usd_currency:
            _logger.warning("USD_RATE_SYNC: no se encontró la moneda USD en el sistema.")
            return

        contenido = self._descargar_csv(URL_CSV_TASA_USD)
        if contenido is None:
            return  # el error ya quedó registrado en _descargar_csv

        tasa_encontrada = self._parsear_tasa(contenido)
        if not tasa_encontrada:
            _logger.error(
                "USD_RATE_SYNC: no se encontró una tasa válida (>500) en el CSV. "
                "Contenido recibido (primeros 200 caracteres): %s",
                contenido[:200],
            )
            return

        factor_inverso = 1.0 / tasa_encontrada
        fecha_hoy = date.today()

        Rate = self.env["res.currency.rate"]
        tasa_existente = Rate.search(
            [
                ("currency_id", "=", usd_currency.id),
                ("name", "=", fecha_hoy),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

        if tasa_existente:
            tasa_existente.write({"company_rate": factor_inverso})
        else:
            Rate.create(
                {
                    "currency_id": usd_currency.id,
                    "name": fecha_hoy,
                    "company_rate": factor_inverso,
                    "company_id": self.env.company.id,
                }
            )

        _logger.info(
            "USD_RATE_SYNC: tasa USD actualizada correctamente. Tasa origen=%s, company_rate=%s",
            tasa_encontrada,
            factor_inverso,
        )

    @api.model
    def _descargar_csv(self, url):
        try:
            respuesta = requests.get(url, timeout=15)
            respuesta.raise_for_status()
            return respuesta.text.strip()
        except requests.exceptions.RequestException as e:
            _logger.error("USD_RATE_SYNC: error al descargar el CSV: %s", e)
            return None

    @api.model
    def _parsear_tasa(self, contenido):
        """Recorre la primera fila del CSV buscando dinámicamente el valor
        numérico que representa la tasa (>500 como filtro de seguridad)."""
        lineas = contenido.split("\n")
        if not lineas:
            return 0.0

        columnas = lineas[0].split(",")

        # 1) Buscar valores con punto decimal
        for col in columnas:
            valor_limpio = col.replace('"', "").strip()
            if "." in valor_limpio:
                try:
                    posible_tasa = float(valor_limpio)
                    if posible_tasa > 500:
                        return posible_tasa
                except ValueError:
                    continue

        # 2) Si no se encontró, normalizar comas como separador decimal
        for col in columnas:
            valor_limpio = col.replace('"', "").strip().replace(",", ".")
            try:
                posible_tasa = float(valor_limpio)
                if posible_tasa > 500:
                    return posible_tasa
            except ValueError:
                continue

        return 0.0
