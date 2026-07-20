# -*- coding: utf-8 -*-
{
    'name': 'Shopink - Localización Venezolana (Retenciones IVA e ISLR)',
    'version': '19.0.1.0.0',
    'summary': 'Gestión de retenciones de IVA recibidas e ISLR mediante diarios contables.',
    'category': 'Accounting/Localizations',
    'author': 'Shopink',
    'depends': [
        'account', 
        'web_studio', 
        'shopink_l10n_ve_partner'
    ],
    'data': [
        'security/security.xml', # Obligatorio primero para crear el grupo
        'security/ir.model.access.csv', # Luego se asignan los permisos al grupo
        'wizard/account_move_confirmation_views.xml',
        'views/l10n_ve_islr_concept_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
