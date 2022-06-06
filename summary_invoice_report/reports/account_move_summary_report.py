# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
from os import access
from termios import OFDEL

from odoo import api, fields, models, tools
from PIL import Image


class SummaryAccountMoveLine(models.TransientModel):
    _name = 'summary.account.move.line'
    _description = "Reporte por fechas"

    name = fields.Char('Nombre', default='Informe de lineas')
    initial_date = fields.Date('Fecha Inicio')
    end_date = fields.Date('Fecha Fin')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    partner_ids = fields.Many2many('res.partner', string='Clientes')

    move_line_ids = fields.Many2many(
        'account.move.line', string='Linea de factura')

    def calculate_and_view(self):
        self.move_line_ids = [(5, 0, 0)]

        query = [('product_id', '!=', False)]
        if self.initial_date:
            query.append(('date', '>=', self.initial_date))
        if self.end_date:
            query.append(('date', '<=', self.end_date))
        if self.partner_id:
            query.append(('partner_id', '=', self.partner_id.id))
        if self.partner_ids:
            query.append(('partner_id', 'in', self.partner_ids.ids))
        move_line_ids = self.env['account.move.line'].search(query)

        self.move_line_ids = [(6, 0, move_line_ids.ids)]

    def print_report(self):
        '''Imprime reporte excel de las lineas de factura de ODOO'''
        self.calculate_and_view()
        return self.env.ref('summary_invoice_report.action_report_summary_account_move_line').report_action(self)


class SummaryAccountMoveLineReport(models.AbstractModel):
    _name = 'report.summary_invoice_report.report_summary_account_move_line'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        format21_c_bold = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#EFEFEF', 'valign': 'vcenter', 'bold': True, 'text_wrap': True, 'border': True})
        format21_left_bold = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#EFEFEF', 'valign': 'vcenter', 'bold': True, 'text_wrap': True, 'border': True})
        format21_left = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'bold': False, 'text_wrap': True, 'border': True})

        sheet = workbook.add_worksheet('Reporte')
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 15, 30)

        company_id = self.env.user.company_id

        buf_image = io.BytesIO(base64.b64decode(company_id.logo))
        im = Image.open(buf_image)
        width, height = im.size
        image_width = width
        image_height = height
        cell_width = 48.0
        cell_height = 48.0

        x_scale = cell_width/image_width
        y_scale = cell_height/image_height
        sheet.insert_image('A1:A3', "logo.png", {
            'image_data': buf_image, 'x_scale': x_scale, 'y_scale': y_scale})

        sheet.merge_range(
            'A1:B3', self.env.user.company_id.name or "", format21_c_bold)
        sheet.merge_range(
            'C1:R3', 'REPORTE DE VENTAS', format21_c_bold)

        sheet.write('A4', 'Anulado', format21_left_bold)
        sheet.write('B4', 'Mes', format21_left_bold)
        sheet.write('C4', 'Año', format21_left_bold)
        sheet.write('D4', 'Vendedor', format21_left_bold)
        sheet.write('E4', 'Tipo de documento', format21_left_bold)
        sheet.write('F4', 'Nro de documento del cliente',
                    format21_left_bold)
        sheet.write('G4', 'Fecha de documento',
                    format21_left_bold)
        sheet.write('H4', 'Nro de documento del cliente',
                    format21_left_bold)
        sheet.write('I4', 'Razón social del cliente',
                    format21_left_bold)
        sheet.write('J4', 'Condición pago', format21_left_bold)
        sheet.write('K4', 'Moneda', format21_left_bold)
        sheet.write('L4', 'Código referencia', format21_left_bold)
        sheet.write('M4', 'Producto/Servicio', format21_left_bold)
        sheet.write('N4', 'Cantidad', format21_left_bold)
        sheet.write('O4', 'Precio unitario', format21_left_bold)
        sheet.write('P4', 'Subtotal', format21_left_bold)
        sheet.write('Q4', 'IGV', format21_left_bold)
        sheet.write('R4', 'Total', format21_left_bold)

        for summ in lines:
            for row, line in enumerate(summ.move_line_ids, 4):
                invoice_date_month = line.move_id.invoice_date.strftime(
                    '%m') if line.move_id.invoice_date else ''
                invoice_date_year = line.move_id.invoice_date.strftime(
                    '%Y') if line.move_id.invoice_date else ''
                state = 'SÍ' if line.move_id.state == 'cancel' else 'NO'
                invoice_user = line.move_id.invoice_user_id.name if line.move_id.invoice_user_id.name else ''
                document_type = line.partner_id.l10n_latam_identification_type_id.name if line.partner_id.l10n_latam_identification_type_id else ''
                vat = line.partner_id.vat if line.partner_id.vat else ''
                partner = line.partner_id.name if line.partner_id.name else ''
                invoice_document_type = line.move_id.move_type
                invoice_document_number = line.move_id.name
                invoice_date = line.move_id.invoice_date.strftime(
                    '%d/%m/%Y') if line.move_id.invoice_date else ''
                sheet.write(row, 0, state, format21_left)
                sheet.write(row, 1, invoice_date_month,
                            format21_left)
                sheet.write(row, 2, invoice_date_year,
                            format21_left)
                sheet.write(row, 3, invoice_user, format21_left)
                sheet.write(row, 4, invoice_document_type,
                            format21_left)
                sheet.write(row, 5, invoice_document_number,
                            format21_left)
                sheet.write(row, 6, invoice_date,
                            format21_left)
                sheet.write(row, 7, document_type,
                            format21_left)
                sheet.write(row, 8, vat,
                            format21_left)
                sheet.write(row, 9, partner,
                            format21_left)
                sheet.write(row, 10, line.move_id.payment_reference,
                            format21_left)
                sheet.write(row, 11, line.move_id.currency_id.name,
                            format21_left)
                sheet.write(row, 12, line.product_id.default_code,
                            format21_left)
                sheet.write(row, 13, line.product_id.name, format21_left)
                sheet.write(row, 14, line.quantity, format21_left)
                sheet.write(row, 15, line.price_unit, format21_left)
                sheet.write(row, 16, line.price_subtotal, format21_left)
                sheet.write(row, 17, line.price_total -
                            line.price_subtotal, format21_left)
                sheet.write(row, 18, line.price_total, format21_left)