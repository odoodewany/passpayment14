# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

{
    'name': 'Factura electronica para Punto de venta',
    'version': '0.1',
    'author': 'OPeru',
    'summary': 'Electronic invoicing for Point of sale / Odoo Peru ',
    'description': '''  ''',
    'website': 'hhttp://www.operu.pe/facturacion-electronica',
    'depends': ['base',
                'point_of_sale',
                'l10n_pe_edi_odoofact',
                ],
    'qweb': [
        'static/src/xml/Screens/ClientListScreen/ClientLine.xml',
        'static/src/xml/Screens/ClientListScreen/ClientDetailsEdit.xml',
        'static/src/xml/Screens/ClientListScreen/ClientListScreen.xml',
        'static/src/xml/Screens/Payment/PaymentInvoiceJournal.xml',
        'static/src/xml/Screens/Payment/PaymentScreen.xml',
        'static/src/xml/Screens/Receipt/OdooFactReceipt.xml',
    ],  
    "data": ['views/pos_config.xml',
            'views/res_config_settings_views.xml',
            'views/import_libraries.xml',
            ], 
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'images': ['static/description/banner.png'],
    'live_test_url': 'http://operu.pe/manuales',
    'license': 'OPL-1',
    'price': 119.00,
    'currency': 'USD',
    'sequence': 1,
    'support': 'modulos@operu.pe',
}
