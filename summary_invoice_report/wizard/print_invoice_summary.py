# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from email.policy import default
from odoo import models, fields, api, _
import xlwt
import io
import base64
from xlwt import easyxf
import datetime


class PrintInvoiceSummary(models.TransientModel):
	_name = "print.invoice.summary"

	@api.model
	def _get_from_date(self):
		company = self.env.user.company_id
		current_date = datetime.date.today()
		from_date = company.compute_fiscalyear_dates(current_date)['date_from']
		return from_date

	from_date = fields.Date(string='Fecha de Inicio', default=_get_from_date)
	to_date = fields.Date(string='Fecha Final', default=datetime.date.today())
	invoice_summary_file = fields.Binary('Informe de Resumen de Comprobantes')
	file_name = fields.Char('Nombre de Archivo')
	invoice_report_printed = fields.Boolean('Resumen de Comprobantes Impreso')
	invoice_status = fields.Selection([('all', 'Todos'), ('paid', 'Pagados'), ('un_paid', 'No Pagados'), ('sale', 'Incluir Notas')], default='all',
									  string='Estado del Comprobante')
	partner_id = fields.Many2one('res.partner', 'Cliente')
	invoice_objs = fields.Many2many('account.move', string='Comprobantes')
	amount_total_debit = fields.Float('Amount debit')
	amount_total_credit = fields.Float('Amount credit')

	def action_print_invoice_summary_csv(self):
		new_from_date = self.from_date.strftime('%Y-%m-%d')
		new_to_date = self.to_date.strftime('%Y-%m-%d')

		workbook = xlwt.Workbook()
		amount_tot = 0
		column_heading_style = easyxf('font:height 200;font:bold True; pattern: pattern solid, fore_color blue; font: color white;' "borders: top thin,bottom thin,left thin,right thin")
		worksheet = workbook.add_sheet('Resumen')
		worksheet.write(2, 0, 'R.U.C. : ' + self.env.user.company_id.vat, easyxf('font:height 200;font:bold True;align: horiz left;'))
		worksheet.write(3, 0, 'Fecha : ' + new_from_date + ' - ' + new_to_date, easyxf('font:height 200;font:bold True;align: horiz left;'))
		worksheet.write(4, 0, 'Empresa : ' + self.env.user.company_id.name, easyxf('font:height 200;font:bold True;align: horiz left;'))
		# worksheet.write(4, 2, new_from_date, easyxf('font:height 200;font:bold True;align: horiz center;'))
		# worksheet.write(4, 3, 'Al', easyxf('font:height 200;font:bold True;align: horiz center;'))
		# worksheet.write(4, 4, new_to_date, easyxf('font:height 200;font:bold True;align: horiz center;'))
		worksheet.write(6, 0, _('Nº LINEA'), column_heading_style)
		worksheet.write(6, 1, 'Asiento', column_heading_style)
		worksheet.write(6, 2, 'Fecha Emisión', column_heading_style)
		worksheet.write(6, 3, 'Fecha Vencimiento', column_heading_style)
		worksheet.write(6, 4, 'Tipo', column_heading_style)
		worksheet.write(6, 5, 'Nº Serie y Número', column_heading_style)
		worksheet.write(6, 6, 'Tipo y Nº Documento', column_heading_style)
		worksheet.write(6, 7, 'Razón Social', column_heading_style)
		worksheet.write(6, 8, 'Valor Facturado Exportación', column_heading_style)
		worksheet.write(6, 9, 'Base Imponible Gravada', column_heading_style)
		worksheet.write(6, 10, 'Operacion Exonerada', column_heading_style)
		worksheet.write(6, 11, 'Operacion Inafecta', column_heading_style)
		worksheet.write(6, 12, 'I.S.C.', column_heading_style)
		worksheet.write(6, 13, 'I.G.V  y/o  I.P.M.', column_heading_style)
		worksheet.write(6, 14, 'I.C.B.PER.', column_heading_style)
		worksheet.write(6, 15, 'Otros Tributos y cargos', column_heading_style)
		worksheet.write(6, 16, 'Importe Total', column_heading_style)
		worksheet.write(6, 17, 'T. Cambio', column_heading_style)
		worksheet.write(6, 18, 'Fecha Referencia', column_heading_style)
		worksheet.write(6, 19, 'Tipo', column_heading_style)
		worksheet.write(6, 20, 'Nº Serie y Nº Comp', column_heading_style)
		worksheet.write(6, 21, 'Fecha Detracción', column_heading_style)
		worksheet.write(6, 22, 'Tipo', column_heading_style)
		worksheet.write(6, 23, 'Constancia Detracción', column_heading_style)
		# worksheet.write(6, 5, _('Monto en (' + str(self.env.user.company_id.currency_id.name) + ')'), column_heading_style)

		worksheet.col(0).width = 3000
		worksheet.col(1).width = 3000
		worksheet.col(2).width = 5000
		worksheet.col(3).width = 5000
		worksheet.col(4).width = 2000
		worksheet.col(5).width = 5000
		worksheet.col(6).width = 6000
		worksheet.col(7).width = 8000
		worksheet.col(8).width = 5000
		worksheet.col(9).width = 5000
		worksheet.col(10).width = 5000
		worksheet.col(11).width = 5000
		worksheet.col(12).width = 5000
		worksheet.col(13).width = 5000
		worksheet.col(14).width = 5000
		worksheet.col(15).width = 5000
		worksheet.col(16).width = 5000
		worksheet.col(17).width = 4000
		worksheet.col(18).width = 5000
		worksheet.col(19).width = 2000
		worksheet.col(20).width = 5000
		worksheet.col(21).width = 5000
		worksheet.col(22).width = 2000
		worksheet.col(23).width = 5000

		# worksheet2 = workbook.add_sheet('Customer wise Invoice Summary')
		# worksheet2.write(1, 0, _('Customer'), column_heading_style)
		# worksheet2.write(1, 1, _('Paid Amount'), column_heading_style)
		# worksheet2.write(1, 2, _('Invoice Currency'), easyxf('font:height 200;font:bold True;align: horiz left;'))
		# worksheet2.write(1, 3, _('Amount in Company Currency (' + str(self.env.user.company_id.currency_id.name) + ')'),
		# 				 easyxf('font:height 200;font:bold True;align: horiz left;'))
		# worksheet2.col(0).width = 5000
		# worksheet2.col(1).width = 5000
		# worksheet2.col(2).width = 4000
		# worksheet2.col(3).width = 8000

		row = 7
		customer_row = 2
		
		for wizard in self:
			customer_payment_data = {}
			heading = 'Registro de Ventas'
			worksheet.write_merge(0, 0, 0, 23, heading, easyxf(
				'font:height 210; align: horiz center;pattern: pattern solid, fore_color black; font: color white; font:bold True;' "borders: top thin,bottom thin"))
			heading = 'Customer wise Invoice Summary'
			# worksheet2.write_merge(0, 0, 0, 3, heading, easyxf(
			# 	'font:height 200; align: horiz center;pattern: pattern solid, fore_color black; font: color white; font:bold True;' "borders: top thin,bottom thin"))
			if wizard.invoice_status == 'all':
				domain = [('invoice_date', '>=', wizard.from_date),
						 ('invoice_date', '<=', wizard.to_date),
						 ('l10n_pe_edi_is_einvoice', '=', True),
						 ('state', 'not in', ['draft', 'cancel'])]
			elif wizard.invoice_status == 'paid':
				domain = [('invoice_date', '>=', wizard.from_date),
						  ('invoice_date', '<=', wizard.to_date),
						  ('l10n_pe_edi_is_einvoice', '=', True),
						  ('payment_state', '=', 'paid')]
			elif wizard.invoice_status == 'un_paid':
				domain = [('invoice_date', '>=', wizard.from_date),
						  ('invoice_date', '<=', wizard.to_date),
						  ('l10n_pe_edi_is_einvoice', '=', True),
						  ('payment_state', '=', 'not_paid')]
			else:
				domain = [('invoice_date', '>=', wizard.from_date),
						 ('invoice_date', '<=', wizard.to_date),
						 ('state', 'not in', ['draft', 'cancel'])]

			if self.partner_id:
				domain +=[('partner_id', '=', self.partner_id.id)]

			invoice_objs = self.env['account.move'].search(domain)
			amount_tot_8 = amount_tot_9 = amount_tot_10 = amount_tot_11 = amount_tot_12 = amount_tot_13 = amount_tot_14 = amount_tot_15 = amount_tot_16 = 0.0
			index = 1
			for invoice in invoice_objs:
				invoice_date = invoice.invoice_date.strftime('%d/%m/%Y')
				amount = 0
				for journal_item in invoice.line_ids:
					amount += journal_item.debit
				worksheet.write(row, 0, index) #, easyxf('font:bold False;' "borders: left thin,right thin"))
				worksheet.write(row, 1, "%05d" % index)
				worksheet.write(row, 2, invoice_date)
				worksheet.write(row, 3, invoice.invoice_date_due.strftime('%d/%m/%Y'))
				worksheet.write(row, 4, invoice.l10n_latam_document_type_id.code if invoice.l10n_latam_document_type_id.code else '')
				worksheet.write(row, 5, invoice.name)
				worksheet.write(row, 6, invoice.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code + '-' + invoice.partner_id.vat if invoice.partner_id and invoice.partner_id.l10n_latam_identification_type_id and invoice.partner_id.vat else '')
				worksheet.write(row, 7, invoice.partner_id.name if invoice.partner_id else '')
				worksheet.write(row, 8, 0.00)
				worksheet.write(row, 9, invoice.l10n_pe_edi_amount_base)
				worksheet.write(row, 10, invoice.l10n_pe_edi_amount_exonerated)
				worksheet.write(row, 11, invoice.l10n_pe_edi_amount_unaffected)
				worksheet.write(row, 12, invoice.l10n_pe_edi_amount_isc)
				worksheet.write(row, 13, invoice.l10n_pe_edi_amount_igv)
				worksheet.write(row, 14, invoice.l10n_pe_edi_amount_icbper)
				worksheet.write(row, 15, invoice.l10n_pe_edi_amount_others)
				worksheet.write(row, 16, invoice.amount_total)
				worksheet.write(row, 17, invoice.currency_id.rate)
				worksheet.write(row, 18, invoice.l10n_pe_edi_reversal_date.strftime('%d/%m/%Y') if invoice.l10n_pe_edi_reversal_date else '')
				worksheet.write(row, 19, invoice.reversed_entry_id.l10n_latam_document_type_id.code if invoice.reversed_entry_id else '')
				worksheet.write(row, 20, invoice.reversed_entry_id.name if invoice.reversed_entry_id else '')
				worksheet.write(row, 21, '')
				worksheet.write(row, 22, invoice.invoice_detraction_type.code if invoice.invoice_detraction_type else '')
				worksheet.write(row, 23, invoice.invoice_detraction_amount if invoice.invoice_detraction_amount else '')
				
				amount_tot_9 += invoice.l10n_pe_edi_amount_base
				amount_tot_10 += invoice.l10n_pe_edi_amount_exonerated
				amount_tot_11 += invoice.l10n_pe_edi_amount_unaffected
				amount_tot_12 += invoice.l10n_pe_edi_amount_isc
				amount_tot_13 += invoice.l10n_pe_edi_amount_igv
				amount_tot_14 += invoice.l10n_pe_edi_amount_icbper
				amount_tot_15 += invoice.l10n_pe_edi_amount_others
				amount_tot_16 += invoice.amount_total
				# amount_tot += amount
				row += 1
				key = u'_'.join((invoice.partner_id.name, invoice.currency_id.name)).encode('utf-8')
				key = str(key, 'utf-8')
				if key not in customer_payment_data:
					customer_payment_data.update(
						{key: {'amount_total': invoice.amount_total, 'amount_company_currency': amount}})
				else:
					paid_amount_data = customer_payment_data[key]['amount_total'] + invoice.amount_total
					amount_currency = customer_payment_data[key]['amount_company_currency'] + amount
					customer_payment_data.update(
						{key: {'amount_total': paid_amount_data, 'amount_company_currency': amount_currency}})
				index += 1
			# worksheet.write(row + 2, 5, amount_tot, column_heading_style)
			# worksheet.write(row, 0, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 1, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 2, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 3, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 4, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 5, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 6, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 7, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 8, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			worksheet.write(row, 9, amount_tot_9, easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			worksheet.write(row, 10, amount_tot_10, easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			worksheet.write(row, 11, amount_tot_11, easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			worksheet.write(row, 12, amount_tot_12, easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			worksheet.write(row, 13, amount_tot_13, easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			worksheet.write(row, 14, amount_tot_14, easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			worksheet.write(row, 15, amount_tot_15, easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			worksheet.write(row, 16, amount_tot_16, easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 17, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 18, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 19, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 20, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 21, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 22, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))
			# worksheet.write(row, 23, '', easyxf('font:height 200;font:bold True;' "borders: top thin,bottom thin,left thin,right thin"))

			# for customer in customer_payment_data:
			# 	worksheet2.write(customer_row, 0, customer.split('_')[0])
			# 	worksheet2.write(customer_row, 1, customer_payment_data[customer]['amount_total'])
			# 	worksheet2.write(customer_row, 2, customer.split('_')[1])
			# 	worksheet2.write(customer_row, 3, customer_payment_data[customer]['amount_company_currency'])
			# 	customer_row += 1

			fp = io.BytesIO()
			workbook.save(fp)
			excel_file = base64.b64encode(fp.getvalue())
			wizard.invoice_summary_file = excel_file
			wizard.file_name = 'Informe de Resumen de Comprobantes.xls'
			wizard.invoice_report_printed = True
			fp.close()
			return {
				'view_mode': 'form',
				'res_id': wizard.id,
				'res_model': 'print.invoice.summary',
				'view_type': 'form',
				'type': 'ir.actions.act_window',
				'context': self.env.context,
				'target': 'new',
			}


	def _search_invoices(self):
		if self.invoice_status == 'all':
			domain = [('invoice_date', '>=', self.from_date),
					  ('invoice_date', '<=', self.to_date),
					  ('state', 'not in', ['draft', 'cancel'])]
		elif self.invoice_status == 'paid':
			domain = [('invoice_date', '>=', self.from_date),
					  ('invoice_date', '<=', self.to_date),
					  ('payment_state', '=', 'paid')]
		else:
			domain = [('invoice_date', '>=', self.from_date),
					  ('invoice_date', '<=', self.to_date),
					  ('payment_state', '=', 'not_paid')]

		if self.partner_id:
			domain += [('partner_id', '=', self.partner_id.id)]

		return self.env['account.move'].search(domain)

	def action_print_invoice_summary_pdf(self):

		if self.invoice_status == 'all':
			domain = [('invoice_date', '>=', self.from_date),
					  ('invoice_date', '<=', self.to_date),
					  ('state', 'not in', ['draft', 'cancel'])]
		elif self.invoice_status == 'paid':
			domain = [('invoice_date', '>=', self.from_date),
					  ('invoice_date', '<=', self.to_date),
					  ('payment_state', '=', 'paid')]
		else:
			domain = [('invoice_date', '>=', self.from_date),
					  ('invoice_date', '<=', self.to_date),
					  ('payment_state', '=', 'not_paid')]

		if self.partner_id:
			domain += [('partner_id', '=', self.partner_id.id)]

		self.invoice_objs = self._search_invoices()
		self.amount_total_debit = 0
		self.amount_total_credit = 0

		for invoice in self.invoice_objs:
			if invoice.move_type != 'out_refund':
				self.amount_total_debit += invoice.amount_total
			else:
				self.amount_total_credit += invoice.amount_total

		xml_id = 'summary_invoice_report.action_report_invoice_summary'
		res = self.env.ref(xml_id).report_action(self.ids, None)
		res['id'] = self.env.ref(xml_id).id
		return res
