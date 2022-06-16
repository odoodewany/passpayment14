# -*- coding: utf-8 -*-

from odoo import models

from collections import defaultdict
import pytz
import time
from datetime import datetime, timedelta
import calendar


class InvoiceReportXls(models.AbstractModel):
    _name = 'report.sale_register.sale_register_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    # perform query from account_invoice
    def get_queries(self, month, year):
        # ('date.month','=',month)
        lines = []
        invoices = self.env['account.move'].search([], order='date asc')
        for invoice in invoices:
            date_m = datetime.strptime(invoice.date,'%Y-%m-%d').strftime('%m')
            date_y = datetime.strptime(invoice.date,'%Y-%m-%d').strftime('%Y')
            print("Month ----->",int(date_m), month, date_y, year.name)
            if int(date_m) == int(month) and date_y == year.name:
                lines.append(invoice)
        lines = sorted(lines, key=lambda x: str(x['number']))
        return lines
 
    def generate_xlsx_report(self, workbook, data, lines):
        print("--->", data, "---->", lines)
        month = lines.month
        year = lines.year 

        # call a function that get incoming and outgoing registers
        queries_result = self.get_queries(month, year)
        print(queries_result)
        
        # WRITE THE XLS REPORT 

        # INCOMING REPORT
        comp = self.env.user.company_id.name  

        sheet = workbook.add_worksheet('REPORTE VENTAS')
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        format_10_l = workbook.add_format({'font_size': 10, 'align': 'left'})
        format_10_r = workbook.add_format({'font_size': 10, 'align': 'right'})
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        green_mark = workbook.add_format({'font_size': 8, 'bg_color': 'green'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        green_mark.set_align('center')

        sheet.merge_range(0, 0, 0, 15, comp, format11) 
        sheet.merge_range(1, 0, 1, 15, 'REPORTE DE VENTAS MES DE '+ month, format11)
        sheet.merge_range(2, 0, 2, 15, '* SOLES *', format11) 

        sheet.write(4, 0, 'FECHA DOCUMENTO', format21)
        sheet.write(4, 1, 'TD', format21)
        sheet.write(4, 2, 'TD SUNAT', format21)
        sheet.write(4, 3, 'NUM. DOCUMENTO', format21)
        sheet.write(4, 4, 'REFERENCIA', format21)
        sheet.write(4, 5, 'NUM. DOC. REF.', format21)
        sheet.write(4, 6, 'RUC', format21)
        sheet.write(4, 7, 'NOMBRE / RAZÓN SOCIAL', format21)
        sheet.write(4, 8, 'BASE IMPONIBLE', format21)
        sheet.write(4, 9, 'IMPORTE INAFECTO', format21)
        sheet.write(4, 10, 'I.S.C.', format21)
        sheet.write(4, 11, 'I.G.V.', format21)
        sheet.write(4, 12, 'OTROS TRIBUTOS', format21)
        sheet.write(4, 13, 'IMPORTE TOTAL', format21)
        sheet.write(4, 14, 'COMPROBANTE CONTABLE', format21)
        sheet.write(4, 15, 'TIPO DE CAMBIO', format21)       

        prod_row = 6
        prod_col = 0

        sum_importe = 0
        sum_tax = 0
        sum_importe_total = 0
        sum_discount = 0
        sum_residual = 0

        T10 = ['','FT','RH','BV','LQ','BA','CP','NA','ND','GS',
                'RA','PB','TK','LB','RC','','','','','',
                '','','','','','','','','','',
                '','','','','','','','','','',
                '','','','','','','','','','',
                'RL','','','','','','','','','']
        index = 1

        for each in queries_result:
            sheet.write(prod_row, prod_col, each.date, format_10_l)
            sheet.write(prod_row, prod_col + 1, T10[int(each.type_document_id.code)], format_10_l) 
            sheet.write(prod_row, prod_col + 2, each.type_document_id.code, format_10_l) 
            if each.serie_id and each.numero:
                sheet.write(prod_row, prod_col + 3, each.serie_id.name + each.numero, format_10_l) 
            if each.origin:
                referencia = str(each.origin).split('/')
                sheet.write(prod_row, prod_col + 4, referencia[0], format_10_l) 
                sheet.write(prod_row, prod_col + 5, referencia[1], format_10_l) 
            sheet.write(prod_row, prod_col + 6, each.partner_id.vat, format_10_l) 
            sheet.write(prod_row, prod_col + 7, each.partner_id.name, format_10_l) 
            sheet.write(prod_row, prod_col + 8, each.amount_untaxed, format_10_r) 
            sheet.write(prod_row, prod_col + 9, '0.00', format_10_r) 
            sheet.write(prod_row, prod_col + 10, '0.00', format_10_r) 
            sheet.write(prod_row, prod_col + 11, each.amount_tax, format_10_r) 
            sheet.write(prod_row, prod_col + 12, '0.00', format_10_r) 
            sheet.write(prod_row, prod_col + 13, each.amount_total_signed, format_10_r) 
            comp_cont = '04-' + month + str(index).rjust(4, '0')
            sheet.write(prod_row, prod_col + 14, comp_cont, format_10_r) 

            prod_row = prod_row + 1
            index += 1

        sheet.merge_range(prod_row, 0, prod_row, prod_col + 14, "", font_size_8_l)
        sheet.write(prod_row, 15, 'TOTAL', format21)
        sheet.write(prod_row, 16, sum_importe, font_size_8_r)
        sheet.write(prod_row, 17, sum_tax, font_size_8_r)
        # sheet.write(prod_row, 18, sum_discount, font_size_8_r)
        sheet.write(prod_row, 18, sum_importe_total, font_size_8_r)
        sheet.write(prod_row, 19, sum_residual, font_size_8_r)
