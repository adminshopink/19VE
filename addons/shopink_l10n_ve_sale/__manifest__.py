# -*- coding: utf-8 -*-
{
    'name': 'Shopink - Ventas Localización VE',
    'summary': 'Campos fiscales, reporte de cotización para Venezuela y botón de WhatsApp.',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'author': 'Shopink',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'shopink_l10n_ve_partner',
    ],
    'data': [
        'report/sale_report_templates.xml',
        'views/sale_order_views.xml',  # 👈 Aquí le decimos a Odoo que cargue el botón
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
