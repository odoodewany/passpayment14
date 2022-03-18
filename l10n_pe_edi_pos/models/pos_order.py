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

from odoo import api, fields, models, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError,Warning

_logger = logging.getLogger(__name__)

class pos_order(models.Model):
	_inherit = "pos.order"

	invoice_journal_id = fields.Many2one('account.journal', 'Journal account', readonly=1)
	
	def _prepare_invoice_vals(self):
		values = super(pos_order, self)._prepare_invoice_vals()
		if self.config_id.l10n_pe_edi_send_invoice:
			if self.invoice_journal_id:
				values['journal_id'] = self.invoice_journal_id.id     
		return values

	@api.model
	def _order_fields(self, ui_order):
		order_fields = super(pos_order, self)._order_fields(ui_order)
		if ui_order.get('invoice_journal_id', False):
			order_fields['invoice_journal_id'] = ui_order.get('invoice_journal_id')        
		return order_fields

	@api.model
	def invoice_data(self,order):
		data = {}
		qr_data = ""
		try:
			pos_order = self.env['pos.order'].search([('pos_reference','=',order)])
			electronic = " Electrónica" if pos_order.account_move.journal_id.l10n_pe_edi_is_einvoice else ""
			data['invoice_number'] = pos_order.account_move.name
			data['type_of_invoice_document'] = (pos_order.account_move.l10n_latam_document_type_id.name + electronic).upper()
			data['igv_percent'] = pos_order.account_move.l10n_pe_edi_igv_percent
			data['amount_in_words'] = pos_order.account_move.l10n_pe_edi_amount_in_words
			data['currency_name'] = pos_order.account_move.currency_id.currency_unit_label or pos_order.account_move.currency_id.name
			data['authorization_message'] = pos_order.company_id.l10n_pe_edi_ose_id and pos_order.company_id.l10n_pe_edi_ose_id.authorization_message or ''
			data['control_url'] = pos_order.company_id.l10n_pe_edi_ose_id and pos_order.company_id.l10n_pe_edi_ose_id.control_url or 'NO VALID' 
			data['date_invoice']= pos_order.account_move.invoice_date
			data['invoice_date_due']= pos_order.account_move.invoice_date_due
			if pos_order.company_id.vat:
				qr_data += '|' + str(pos_order.company_id.vat)
			if pos_order.account_move.l10n_latam_document_type_id and pos_order.account_move.l10n_latam_document_type_id.code:
				qr_data += '|' + str(pos_order.account_move.l10n_latam_document_type_id.code)     
			if pos_order.account_move.l10n_pe_edi_serie:
				qr_data += '|' + str(pos_order.account_move.l10n_pe_edi_serie)
			if pos_order.account_move.l10n_pe_edi_number:
				qr_data += '|' + str(pos_order.account_move.l10n_pe_edi_number)
			if pos_order.account_move.l10n_pe_edi_amount_igv:
				qr_data += '|' + str(pos_order.account_move.l10n_pe_edi_amount_igv)
			if pos_order.account_move.amount_total:
				qr_data += '|' + str(pos_order.account_move.amount_total) 
			if pos_order.account_move.invoice_date:
				qr_data += '|' + str(pos_order.account_move.invoice_date)
			if pos_order.account_move.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code:
				qr_data += '|' + str(pos_order.account_move.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code) 
			if pos_order.account_move.partner_id.vat:
				qr_data += '|' + str(pos_order.account_move.partner_id.vat)
			base_url = pos_order.get_base_url()
			barcode= base_url + '/report/barcode/QR/' + qr_data
			data['barcode'] = barcode

		except Exception:
			data = False
		return data

