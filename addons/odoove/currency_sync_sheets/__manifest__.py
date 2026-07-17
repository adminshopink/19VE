# -*- coding: utf-8 -*-
{
    'name': 'Sincronización de Tasas desde Google Sheets',
    'version': '19.0.1.0.0',
    'summary': 'Automatiza la actualización de la tasa USD/VES usando un CSV de Google Sheets y configura el entorno en ES_VE',
    'category': 'Accounting',
    'author': 'shopink',
    'depends': [
        'base',
        'web',
        'crm',
        'sale_management',
        'purchase',
        'stock',
        'account_accountant',
        'l10n_ve', 
    ],
    'data': [
        'data/cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
