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

import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class pos_config(models.Model):
	_inherit = "pos.config"

	def _default_invoice_journal_ids(self):
		return self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self.env.company.id)], limit=1)

	l10n_pe_edi_send_invoice = fields.Boolean(string='Electronic Invoicing',related="company_id.l10n_pe_edi_send_invoice",readonly=True,)
	invoice_journal_ids = fields.Many2many(
		'account.journal',
		'pos_config_invoice_journal_rel',
		'config_id',
		'journal_id',
		'Accounting Invoice Journal',
		help="Invoice journals for Electronic invoices.",
		default=_default_invoice_journal_ids)
	default_partner_id = fields.Many2one("res.partner", string="Client by default", help="This client will be set by default in the order")
	auto_check_invoice = fields.Boolean(string='Auto create Invoice')
	l10n_pe_edi_print_invoice = fields.Boolean(string='Print report', default=False)
	
	@api.onchange('modulel10n_pe_edi_send_invoice_account')
	def _onchange_module_einvoice(self):
		self.auto_check_invoice = self.l10n_pe_edi_send_invoice  
	
	
class ProductTemplate(models.Model):
	_inherit = 'pos.category'

	def _default_company_id(self):
		current_company = self.env.company.id
		return current_company if current_company else False

	company_id = fields.Many2one('res.company', 'Compañía', default=_default_company_id, index=1)

	def unlink(self):
		if self.search_count([('id', 'in', self.ids)]):
			_logger.info('Send pos_category for delete')
			_logger.info(self.ids)
			# if self.env['pos.session'].sudo().search_count([('state', '!=', 'closed')]):
			# 	raise UserError(_('You cannot delete a point of sale category while a session is still opened.'))
		return super(ProductTemplate, self).unlink()
	