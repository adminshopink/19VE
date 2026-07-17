# -*- coding: utf-8 -*-
{
    'name': 'Shopink - Localización Venezolana (Control de Facturación)',
    'version': '19.0.1.0.0',
    'summary': 'Asignación automática del Número de Control legal para facturas de clientes.',
    'category': 'Accounting/Localizations',
    'author': 'Shopink',
    'depends': ['account', 'web_studio'],
    'data': [
        'data/ir_sequence_data.xml',
        'views/account_move_views.xml', # <- Agregamos la vista estructural de forma limpia
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
