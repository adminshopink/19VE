# -*- coding: utf-8 -*-
{
    'name': 'Shopink - Control de Pago Comercial en Ventas',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Reportes y estados de pago comerciales en Órdenes de Venta.',
    'author': 'Shopink',
    'depends': ['sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'wizard/sale_commercial_report_wizard_views.xml', # Añade esta línea
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
