# -*- coding: utf-8 -*-

{
    'name': 'Journal Sequence For Odoo 14',
    'version': '14.0.6.0.0',
    'category': 'Accounting',
    'summary': 'Journal Sequence For Odoo 14, Odoo Journal sequence, Odoo 14 Journal Sequence, Journal Entry Sequence, Odoo Invoice Sequence',
    'description': 'Journal Sequence For Odoo 14, Odoo Journal sequence, Odoo 14 Journal Sequence, Journal Entry Sequence, Odoo Invoice Sequence',
    'sequence': '1',
    'author': 'Odoo Developers',
    'support': 'developersodoo@gmail.com',
    'live_test_url': 'https://www.youtube.com/watch?v=z-xZwCah7wM',
    'depends': ['account', 'l10n_latam_invoice_document', 'l10n_pe_edi_odoofact', 'sale'],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/account_journal.xml',
        'views/account_move.xml',
    ],
    'license': 'OPL-1',
    'price': 12,
    'currency': 'USD',
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': "create_journal_sequences",
    'images': ['static/description/banner.png'],
}
