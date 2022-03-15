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

import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form

class AccountJournal(models.Model):
	_inherit = "account.journal"
	
	l10n_pe_edi_contingency = fields.Boolean('Contingency', help='Check this for contingency invoices')
	l10n_pe_edi_shop_id = fields.Many2one('l10n_pe_edi.shop', string='Shop')
	l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Electronic document type', help='Catalog 01: Type of electronic document', compute='_get_document_type', readonly=False, store=True)
	l10n_pe_edi_is_einvoice = fields.Boolean('Is E-invoice')
	
	@api.depends('type')
	def _get_document_type(self):
		for journal in self:
			if journal.type == 'sale' and journal.company_id.country_id.code == "PE":
				journal.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('internal_type','=','invoice')], limit=1)
			else:
				journal.l10n_latam_document_type_id = False

	def _set_sequence_override_regex(self):
		if self.type == 'sale' and self.company_id.country_id.code == "PE":
			self.sequence_override_regex = r'^(?P<prefix1>.*?)(?P<seq>\d*)(?P<suffix>\D*?)$'
		else:
			self.sequence_override_regex = False

	@api.onchange('type', 'company_id')
	def _onchange_sequence_override_regex(self):
		''' Replace the 'sequence_override_regex' for peruvian format
			'PREFIX-NUMBER'. Ex: 'F001-0000050'
		'''
		for journal in self:
			journal._set_sequence_override_regex()
			

class AccountInvoiceReport(models.Model): 
	
	_inherit = 'account.invoice.report'

	l10n_pe_edi_price_unit_included = fields.Float(string='Price unit IGV included', readonly=True)
	l10n_pe_edi_sunat_accepted = fields.Boolean('Accepted by SUNAT', readonly=True) 
	
	_depends = {
		'account.move': [
			'name', 'state', 'move_type', 'partner_id', 'invoice_user_id', 'fiscal_position_id',
			'invoice_date', 'invoice_date_due', 'invoice_payment_term_id', 'partner_bank_id',
			'l10n_pe_edi_sunat_accepted',
		],
		'account.move.line': [
			'quantity', 'price_subtotal', 'amount_residual', 'balance', 'amount_currency',
			'move_id', 'product_id', 'product_uom_id', 'account_id', 'analytic_account_id',
			'journal_id', 'company_id', 'currency_id', 'partner_id', 'l10n_pe_edi_price_unit_included',
		],
		'product.product': ['product_tmpl_id'],
		'product.template': ['categ_id'],
		'uom.uom': ['category_id', 'factor', 'name', 'uom_type'],
		'res.currency.rate': ['currency_id', 'name'],
		'res.partner': ['country_id'],
	}

	@api.model
	def _select(self):
		return '''
			SELECT
				line.id,
				line.move_id,
				line.product_id,
				line.account_id,
				line.analytic_account_id,
				line.journal_id,
				line.company_id,
				line.company_currency_id,
				line.partner_id AS commercial_partner_id,
				line.l10n_pe_edi_price_unit_included * currency_table.rate AS l10n_pe_edi_price_unit_included,
				move.state,
				move.move_type,
				move.partner_id,
				move.invoice_user_id,
				move.fiscal_position_id,
				move.payment_state,
				move.invoice_date,
				move.invoice_date_due,
				move.l10n_pe_edi_sunat_accepted,
				uom_template.id                                             AS product_uom_id,
				template.categ_id                                           AS product_categ_id,
				line.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END)
																			AS quantity,
				-line.balance * currency_table.rate                         AS price_subtotal,
				-COALESCE(
				   -- Average line price
				   (line.balance / NULLIF(line.quantity, 0.0))
				   -- convert to template uom
				   * (NULLIF(COALESCE(uom_line.factor, 1), 0.0) / NULLIF(COALESCE(uom_template.factor, 1), 0.0)),
				   0.0) * currency_table.rate                               AS price_average,
				COALESCE(partner.country_id, commercial_partner.country_id) AS country_id
		'''
