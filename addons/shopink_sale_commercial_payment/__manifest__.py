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
        'wizard/sale_commercial_report_wizard_views.xml',
    ],
    # Aquí insertamos la sección de assets
    'assets': {
        'web.assets_backend': [
            'shopink_sale_commercial_payment/static/src/css/hide_save.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
