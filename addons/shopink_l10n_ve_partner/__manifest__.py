# -*- coding: utf-8 -*-
{
    'name': 'Shopink - Contactos Localización VE',
    'summary': 'Campos de RIF, Cédula y Tipos de Persona para clientes y proveedores.',
    'version': '19.0.1.0.0',
    'category': 'Base',
    'author': 'Shopink',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'web_studio',
    ],
    'data': [
        'views/res_partner_views.xml', # <- Agregamos esta línea de forma limpia
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
