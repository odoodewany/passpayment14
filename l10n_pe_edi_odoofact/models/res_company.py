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
from datetime import datetime
from dateutil.relativedelta import relativedelta
import paramiko

from odoo.fields import Date, Datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
	_inherit = 'res.company'
	
	l10n_pe_edi_ose_url = fields.Char('URL')
	l10n_pe_edi_ose_token = fields.Char('Token')
	l10n_pe_edi_ose_id = fields.Many2one('l10n_pe_edi.supplier', string='PSE / OSE Supplier')   
	l10n_pe_edi_ose_code = fields.Char('Code of PSE / OSE supplier', related='l10n_pe_edi_ose_id.code')
	l10n_pe_edi_resume_url = fields.Char('Resume URL')
	l10n_pe_edi_multishop = fields.Boolean('Multi-Shop')
	l10n_pe_edi_send_invoice = fields.Boolean('Send Invoices to PSE/OSE')
	l10n_pe_edi_shop_ids = fields.One2many('l10n_pe_edi.shop','company_id', string='Shops')
	l10n_pe_edi_send_invoice_interval_unit = fields.Selection([
		('hourly', 'Hourly'),
		('daily', 'Daily')],
		default='daily', string='Interval Unit for sending')
	l10n_pe_edi_send_invoice_next_execution_date = fields.Datetime(string="Next Execution")
	# SFS Path
	sfs_path = fields.Char('Ubicación SFS')
	sftp_write = fields.Boolean('SFS - Conexión a servidor externo')
	sftp_path = fields.Char('Ruta a servidor externo')
	sftp_host = fields.Char('Dirección IP del servidor')
	sftp_port = fields.Integer('Puerto SFTP', default=22)
	sftp_user = fields.Char('Usuario del servidor SFTP')
	sftp_password = fields.Char('Contraseña de usuario SFTP')

	def test_sftp_connection(self, context=None):
		self.ensure_one()
		# Check if there is a success or fail and write messages
		message_title = ""
		message_content = ""
		error = ""
		has_failed = False
		for rec in self:
			ip_host = rec.sftp_host
			port_host = rec.sftp_port
			username_login = rec.sftp_user
			password_login = rec.sftp_password
			# Connect with external server over SFTP, so we know sure that everything works.
			try:
				s = paramiko.SSHClient()
				s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				s.connect(ip_host, port_host, username_login, password_login, timeout=10)
				sftp = s.open_sftp()
				sftp.close()
				message_title = _("Connection Test Succeeded!\nEverything seems properly set up for FTP back-ups!")
			except Exception as e:
				_logger.critical('There was a problem connecting to the remote ftp: %s', str(e))
				error += str(e)
				has_failed = True
				message_title = _("Connection Test Failed!")
				if len(rec.sftp_host) < 8:
					message_content += "\nYour IP address seems to be too short.\n"
				message_content += _("Here is what we got instead:\n")
			finally:
				if s:
					s.close()
		if has_failed:
			raise Warning(message_title + '\n\n' + message_content + "%s" % str(error))
		else:
			raise Warning(message_title + '\n\n' + message_content)

	@api.model
	def run_send_invoice(self):
		""" This method is called from a cron job to send the invoices to PSE/OSE.
		"""
		records = self.search([('l10n_pe_edi_send_invoice_next_execution_date', '<=', fields.Datetime.now())])
		if records:
			to_update = self.env['res.company']
			for record in records:
				if record.l10n_pe_edi_send_invoice_interval_unit == 'hourly':
					next_update = relativedelta(hours=+1)
				elif record.l10n_pe_edi_send_invoice_interval_unit == 'daily':
					next_update = relativedelta(days=+1)
				else:
					record.l10n_pe_edi_send_invoice_next_execution_date = False
					return
				record.l10n_pe_edi_send_invoice_next_execution_date = datetime.now() + next_update
				to_update += record
			to_update.l10n_pe_edi_send_invoices()
	
	def l10n_pe_edi_send_invoices(self):
		for company in self:
			if not company.l10n_pe_edi_send_invoice:
				_logger.info('Send Invoices to PSE/OSE is not active')
				continue
			invoice_ids = self.env['account.move'].search([
				('l10n_pe_edi_is_einvoice','=',True),
				('state','not in',['draft','cancel']),
				('l10n_pe_edi_ose_accepted','=',False),
				('move_type','in',['out_invoice','out_refund']),
				('company_id','=', company.id),
				('l10n_pe_edi_cron_count','>',1)]).sorted('invoice_date')
			# l10n_pe_edi_cron_count starts in 5
			# Try until reaches 1
			# 0: Ok
			# 1: issue after max retry
			for move in invoice_ids:
				try:
					move.action_document_send()                    
					if move.l10n_pe_edi_ose_accepted:
						move.l10n_pe_edi_cron_count = 0
					else:
						move.l10n_pe_edi_cron_count -= 1
					self.env.cr.commit()
					_logger.debug('Batch of Electronic invoices is sent')
				except Exception:
					self.env.cr.rollback()
					move.l10n_pe_edi_cron_count -= 1
					self.env.cr.commit()
					_logger.exception('Something went wrong on Batch of Electronic invoices')