# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID
from . import models

def post_init_hook(env):
    """
    Este método se ejecuta inmediatamente al instalar el módulo.
    Configura el país, activa VES como moneda base y prepara USD.
    """

    # 1. Asegurar la existencia y activación del idioma Español de Venezuela
    lang_code = 'es_VE'
    lang_ids = env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)])

    if lang_ids:
        if not lang_ids.active:
            # CAMBIO AQUÍ: Se reemplaza toggle_active() por action_unarchive() para Odoo 19
            lang_ids.action_unarchive()
    else:
        env['res.lang'].create({
            'code': lang_code,
            'name': 'Spanish (VE) / Español (VE)',
            'direction': 'ltr',
            'date_format': '%d/%m/%Y',
            'time_format': '%H:%M:%S',
            'grouping': '[3, 3, 0]',
            'decimal_point': ',',
            'thousands_sep': '.',
            'active': True,
        })

    # 2. Buscar país (Venezuela) y Monedas (VES y USD)
    main_company = env['res.company'].browse(1)
    venezuela = env['res.country'].search([('code', '=', 'VE')], limit=1)
    ves_currency = env['res.currency'].search([('name', '=', 'VES')], limit=1)
    usd_currency = env['res.currency'].search([('name', '=', 'USD')], limit=1)

    # 3. Activar la moneda USD en el sistema
    if usd_currency and not usd_currency.active:
        usd_currency.write({'active': True})

    # 4. Asegurar que VES esté activa y setearla como la moneda base de la compañía
    if ves_currency:
        if not ves_currency.active:
            ves_currency.write({'active': True})

        company_vals = {'currency_id': ves_currency.id}
        if venezuela:
            company_vals.update({'country_id': venezuela.id})

        main_company.write(company_vals)

    # 5. Configurar el idioma del usuario Administrador a es_VE
    admin_user = env['res.users'].browse(SUPERUSER_ID)
    admin_user.write({'lang': lang_code})
