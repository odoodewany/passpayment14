# -*- coding: utf-8 -*-

import calendar
import time
from collections import defaultdict
from datetime import datetime, timedelta

import pytz

from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class InvoiceReportXls(models.AbstractModel):
    _name = 'report.report_sale.sale_register_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, lines):
        comp = lines.company_id.name

        sheet = workbook.add_worksheet('Registro de ventas')

        sheet.set_column(0, 2, 9)  # corr y fechas
        sheet.set_column(3, 3, 10)  # tipo
        sheet.set_column(4, 5, 8)  # serie numero
        sheet.set_column(6, 6, 10)  # tipo
        sheet.set_column(7, 7, 15)  # prov numero
        sheet.set_column(8, 8, 40)  # prov razon social
        sheet.set_column(9, 15, 12)  # base imponible igv y total

        format21 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'text_wrap': True, 'valign': 'vcenter'})
        format21_left = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bold': True})

        format21_blue = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'fg_color': '#68a3fc'})
        format21_green = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'fg_color': '#85de8e'})

        font_size_8_c = workbook.add_format(
            {'font_size': 8, 'align': 'center'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r_b = workbook.add_format(
            {'font_size': 8, 'align': 'right', 'bold': True})
        monetary_size_8_r = workbook.add_format(
            {'num_format': '"S/." #,##0.00', 'font_size': 8, 'align': 'right', 'valign': 'vcenter'})

        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz)
        time = pytz.utc.localize(datetime.now()).astimezone(tz)

        format21.set_border()
        format21_blue.set_border()
        format21_green.set_border()
        font_size_8_c.set_border()

        sheet.merge_range(0, 0, 0, 1, 'REGISTRO DE VENTAS', format21_left)
        sheet.write(2, 0, 'PERIODO', format21_left)
        sheet.write(2, 1, lines.month + '/' + lines.year, format21_left)
        sheet.write(3, 0, 'RUC', format21_left)
        sheet.write(3, 1, lines.company_id.vat, format21_left)
        sheet.write(4, 0, 'RAZÓN SOCIAL', format21_left)
        sheet.write(4, 1, lines.company_id.partner_id.name, format21_left)

        sheet.merge_range(
            6, 0, 8, 0, 'NÚMERO CORRELATIVO DEL REGISTRO O CÓDIGO ÚNICO DE LA OPERACIÓN', format21)
        sheet.merge_range(
            6, 1, 8, 1, 'FECHA DE EMISIÓN DEL COMPROBANTE DE PAGO O DOCUMENTO', format21)
        sheet.merge_range(
            6, 2, 8, 2, 'FECHA DE VENCIMIENTO DEL COMPROBATE DE PAGO O DOCUMENTO', format21)
        sheet.merge_range(
            6, 3, 6, 5, 'COMPROBANTE DE PAGO O DOCUMENTO', format21)
        sheet.merge_range(7, 3, 8, 3, 'TIPO', format21)
        sheet.merge_range(
            7, 4, 8, 4, 'N° DE SERIE O N° DE SERIE DE LA MÁQUINA REGISTRADORA', format21)
        sheet.merge_range(
            7, 5, 8, 5, 'NÚMERO', format21)
        sheet.merge_range(6, 6, 6, 8, 'INFORMACIÓN DEL CLIENTE', format21)
        sheet.merge_range(7, 6, 7, 7, 'DOCUMENTO DE IDENTIDAD', format21)
        sheet.write(8, 6, 'TIPO', format21)
        sheet.write(8, 7, 'NÚMERO', format21)
        sheet.merge_range(
            7, 8, 8, 8, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL', format21)
        sheet.merge_range(
            6, 9, 8, 9, 'VALOR FACTURADO DE LA EXPORTACIÓN', format21)
        sheet.merge_range(
            6, 10, 8, 10, 'BASE IMPONIBLE DE LA OPERACIÓN GRAVADA', format21)
        sheet.merge_range(
            6, 11, 7, 12, 'IMPORTE DE LA OPERACIÓN EXONERADA O INAFECTA', format21)
        sheet.write(8, 11, 'EXONERADA', format21)
        sheet.write(8, 12, 'INAFECTA', format21)
        sheet.merge_range(6, 13, 8, 13, 'ISC', format21)
        sheet.merge_range(6, 14, 8, 14, 'IGV Y/O IPM', format21)
        sheet.merge_range(
            6, 15, 8, 15, 'OTROS TRIBUTOS Y CARGOS QUE NO FORMAN PARTE DE LA BASE IMPONIBLE', format21)
        sheet.merge_range(
            6, 16, 8, 16, 'IMPORTE TOTAL DEL COMPROBANTE DE PAGO', format21)
        sheet.merge_range(6, 17, 8, 17, 'TIPO DE CAMBIO', format21)
        sheet.merge_range(
            6, 18, 6, 21, 'REFERENCIA DEL COMPROBANTE DE PAGO O DOCUMENTO ORIGINAL QUE SE MODIFICA', format21)
        sheet.merge_range(7, 18, 8, 18, 'FECHA', format21)
        sheet.merge_range(7, 19, 8, 19, 'TIPO', format21)
        sheet.merge_range(7, 20, 8, 20, 'SERIE', format21)
        sheet.merge_range(
            7, 21, 8, 21, 'N° DEL COMPROBANTE DE PAGO O DOCUMENTO', format21)

        # Data
        month = int(lines.month)
        year = int(lines.year)
        days = calendar.monthrange(year, month)
        init_date = datetime(year, month, 1)
        end_date = datetime(year, month, days[1])


        invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            
            ('state', '=', 'posted'),
            ('company_id', '=', lines.company_id.id),
        ], order="invoice_date asc")

        print(invoices)

        # Data Render

        entrie_row = 9

        for invoice in invoices:
            currency_rate = invoice.env['res.currency.rate'].search([
                ('name', '<=', invoice.date),
                ('currency_id', '=', invoice.currency_id.id),
            ], order='name desc', limit=1)
            res = ''
            refund_date = ''
            refund_document_type_code = ''
            refund_number = ''
            refund_serie = ''
            if currency_rate:
                res = "{0:.3f}".format(currency_rate.rate)
            else:
                res = "{0:.3f}".format(invoice.currency_id.rate)

            try:
                serie, numero = invoice.name.split('-')
            except:
                serie = numero = '-'

            refund = invoice.reversed_entry_id
            if refund:
                refund_date = refund.date
                refund_document_type_code = refund.l10n_pe_edi_reversal_type_id.name  # 'refund.type_document_id.code'
                try:
                    refund_serie, refund_number = refund.name.split('-')
                except:
                    refund_serie = refund_number = '-'
            igv = 0.0
            isc = 0.0
            # for tax_line in invoice.tax_line_ids:
            #     igv += tax_line.amount if 'IGV' in tax_line.name else 0.0
            #     isc += tax_line.amount if 'ISC' in tax_line.name else 0.0
            sheet.write(entrie_row, 0, invoice.id, font_size_8_c)
            sheet.write(entrie_row, 1, invoice.date, font_size_8_c)
            sheet.write(entrie_row, 2, invoice.invoice_date_due, font_size_8_c)
            sheet.write(entrie_row, 3, invoice.l10n_latam_document_type_id.name, font_size_8_c)
            sheet.write(entrie_row, 4, serie, font_size_8_c)
            sheet.write(entrie_row, 5, numero, font_size_8_c)
            sheet.write(entrie_row, 6,
                        invoice.partner_id.l10n_latam_identification_type_id.name, font_size_8_c)
            sheet.write(entrie_row, 7, invoice.partner_id.vat, font_size_8_c)
            sheet.write(entrie_row, 8, invoice.partner_id.name, font_size_8_c)
            sheet.write(entrie_row, 9, '', font_size_8_c)
            sheet.write(entrie_row, 10, invoice.amount_untaxed, font_size_8_c)
            sheet.write(entrie_row, 11, '0.0', font_size_8_c)
            sheet.write(entrie_row, 12, '0.0', font_size_8_c)
            # sheet.write(entrie_row, 13, isc, font_size_8_c)
            # sheet.write(entrie_row, 14, igv, font_size_8_c)
            sheet.write(entrie_row, 15, '0.0', font_size_8_c)
            sheet.write(entrie_row, 16, invoice.amount_total, font_size_8_c)
            sheet.write(entrie_row, 17, res, font_size_8_c)
            sheet.write(entrie_row, 18, refund_date, font_size_8_c)
            sheet.write(entrie_row, 19,
                        refund_document_type_code, font_size_8_c)
            sheet.write(entrie_row, 20, refund_serie, font_size_8_c)
            sheet.write(entrie_row, 21, refund_number, font_size_8_c)
            entrie_row += 1

        # Format

        sheet.set_column('A:AB', 30)
