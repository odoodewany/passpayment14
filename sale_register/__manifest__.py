# -*- coding: utf-8 -*-

{
    'name': 'Reporte Ventas',
    'version': '1.0',
    'sequence': 0,
    'summary': 'Formato de sunat para reporte de ventas',
    'depends': [
        'account','report_xlsx'
    ],
    'data': [ 'security/ir.model.access.csv',
            'views/wizard_view.xml',
            'report/sale_register.xml',
            'views/report_trialbalance.xml'
            ],
    'application': True,
    'price': '0',
    "currency": 'PEN',
    'images': [],
    'license': 'LGPL-3',
    'support': 'desarrollo@holalciente.com'
}
