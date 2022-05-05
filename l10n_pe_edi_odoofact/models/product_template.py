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

from odoo import api, fields, models

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	def _default_company_id(self):
		current_company = self.env.company.id
		return current_company if current_company else False

	l10n_pe_edi_product_code_id = fields.Many2one("l10n_pe_edi.catalog.25", string='Product code SUNAT')
	company_id = fields.Many2one('res.company', 'Company', default=_default_company_id, index=1)
	available_in_pos = fields.Boolean(string='Available in POS', help='Check if you want this product to appear in the Point of Sale.', default=True)
	type = fields.Selection(default='product')
