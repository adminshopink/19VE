# -*- coding: utf-8 -*-
{
    'name': 'Sincronización Tasa USD',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Actualiza automáticamente la tasa de cambio del USD desde un CSV público (Google Sheets)',
    'description': """
Sincronización diaria de la tasa de cambio USD
================================================
Este módulo agrega una acción programada (cron) que consulta un CSV público
(publicado desde Google Sheets) y actualiza la tasa de cambio del día para
la moneda USD en res.currency.rate.

Reemplaza el uso de un Server Action con código python "suelto", evitando
las limitaciones del entorno sandboxed (safe_eval) que a veces impide el
uso directo de librerías como `requests` en Odoo.sh.
""",
    'author': 'Tu Empresa',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
