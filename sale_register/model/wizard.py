# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import base64


class Year(models.Model):
    _name = 'date.year'

    name = fields.Char(string="Año", required=True)


class SaleRegisterWizard(models.TransientModel):
    _name = "wizard.sale.register"
    _description = "Registro de Ventas"

    def _default_month(self):
        return datetime.now().month

    def _default_year(self):
        return str(datetime.now().year)

    month = fields.Selection(string="Mes", selection=[
        ('1', 'ENERO'),
        ('2', 'FEBRERO'),
        ('3', 'MARZO'),
        ('4', 'ABRIL'),
        ('5', 'MAYO'),
        ('6', 'JUNIO'),
        ('7', 'JULIO'),
        ('8', 'AGOSTO'),
        ('9', 'SETIEMBRE'),
        ('10', 'OCTUBRE'),
        ('11', 'NOVIEMBRE'),
        ('12', 'DICIEMBRE')])
    year = fields.Char(
        string=u'Año',
        limit=4,
        default=_default_year,
        required=True,
    )
    company_id = fields.Many2one(
        string=u'Compañia',
        comodel_name='res.company', required=True,
        domain=lambda self: [('id','in', self.env.user.company_ids.ids)],
        default=lambda self: self.env.user.company_id.id,
    )

    # my_file = fields.Binary('File data', readonly=True, help='File(jpg, csv, xls, exe, any binary or text format)')
    ventas_reg = fields.Binary('File', readonly=True)
    ventas_reg_fname = fields.Char('Filename', readonly=True)

    
    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'month': dict(self._fields['month'].selection).get(self.month),
                'year': self.year,
            },
        }
        
        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref('sale_register.sale_register').report_action(self, data=data)

    
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.stock.history'
        datas['form'] = self.read()[0]

        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        if context.get('xls_export'):
            return self.env.ref('sale_register.sale_register_xls').report_action(self, data=datas)

    
    def generate_txt_report(self):
        data = self.read()[0]
        month = data['month']
        year = data['year']

        # report_name = 'Registro de ventas PLE'
        company = self[0].env.user.company_id
        mont_02 = str(int(month)).rjust(2, '0')
        filename = 'LE%s%s%s%s0100001111.TXT' % (
            str(company.vat), str(year[1]), mont_02, '0014')

        lines = []
        invoices = self.env['account.move'].search(
            [('state', 'in', ['open', 'paid']), ('type', '=', 'out_invoice')], order='date asc')
        for invoice in invoices:
            date_m = datetime.strptime(
                invoice.date, '%Y-%m-%d').strftime('%m')
            date_y = datetime.strptime(
                invoice.date, '%Y-%m-%d').strftime('%Y')
            if int(date_m) == int(month) and date_y == year[1]:
                lines.append(invoice)
        lines = sorted(lines, key=lambda x: str(x['number']))
        print("---->", lines, year[1])

        periodo_ple = year[1] + mont_02 + '00'
        w_data = ""
        index = 1
        T10 = ['', 'FT', 'RH', 'BV', 'LQ', 'BA', 'CP', 'NA', 'ND', 'GS',
               'RA', 'PB', 'TK', 'LB', 'RC', '', '', '', '', '',
               '', '', '', '', '', '', '', '', '', '',
               '', '', '', '', '', '', '', '', '', '',
               '', '', '', '', '', '', '', '', '', '',
               'RL', '', '', '', '', '', '', '', '', '']
        for each in lines:
            w_data = w_data + periodo_ple + '|'
            cuo = each.move_id.name[-2:] + mont_02 + str(index).rjust(4, '0')
            w_data = w_data + cuo + '|'
            w_data = w_data + 'M001' + '|'
            # w_data = w_data + '04-' + str(int(month)).rjust(2, '0') + str(index).rjust(4, '0') + '|'
            # w_data = w_data + 'M0001' + '|'
            if each.date:
                year, month, day = each.date.split('-')
                w_data = w_data + '/'.join([day, month, year]) + '|'
            # else:
            #     w_data = w_data + '01/01/0001' + '|'
            if each.date_due:
                year, month, day = each.date_due.split('-')
                w_data = w_data + '/'.join([day, month, year]) + '|'
            else:
                w_data = w_data + '01/01/0001' + '|'
            # w_data = w_data + T10[int(each.type_document_id.code)] + '|'
            w_data = w_data + \
                str(int(each.type_document_id.code)).rjust(2, '0') + '|'
            w_data = w_data + ((str(each.serie_id.name) + '|')
                               if each.serie_id.name else '|')
            w_data = w_data + str(each.numero) + '|'
            w_data = w_data + '|'
            w_data = w_data + str(each.partner_id.catalog_06_id.code) + '|'
            w_data = w_data + str(each.partner_id.vat) + '|'
            w_data = w_data + str(each.partner_id.name) + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + str(each.amount_untaxed) + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + str(each.amount_tax) + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + '0.00' + '|'
            w_data = w_data + str(each.amount_total_signed) + '|'
            w_data = w_data + each.currency_id.name + '|'
            w_data = w_data + "{0:.3f}".format(each.currency_id.rate) + '|'
            w_data = w_data + '01/01/0001' + '|'
            w_data = w_data + '00' + '|'
            w_data = w_data + '-' + '|'
            w_data = w_data + '-' + '|'
            w_data = w_data + '|'
            w_data = w_data + '|'
            w_data = w_data + '|'
            w_data = w_data + '1' + '|'
            w_data = w_data + '\n'
            index += 1

        out = base64.encodestring(str.encode(w_data))
        self.write({'ventas_reg': out, 'ventas_reg_fname': filename})
        print("----->", filename, out)
        # path_file_not = os.path.join(my_path,path_file_not)
        return {
            # 'type': 'ir.actions.act_url',
            # 'target': 'new',
            # 'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=datas&download=true&filename='+filename,
            # 'url': '/web/binary/download_document?model=%s&field=datas&id=%s&filename=%s'%(self._name,self.id,filename),

            'name': filename,
            'res_id': self.id,
            'res_model': self._name,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('sale_register.save_file_wizard_view_done').id,
            'view_mode': 'form',
            'view_type': 'form',
        }


class SaleRegister(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """
    _name = 'report.sale.report_view'

    @api.model
    def get_report_values(self, docids, data=None):
        month = data['form']['month']
        year = data['form']['year']

        docs = []
        invoices = self.env['account.move'].search(
            [], order='date asc')
        # print("----> months", docs)
        # docs = sorted(docs, key=lambda x: x['date'])
        # invoices = invoices.search([('date.month','=',int(month))])
        for invoice in invoices:
            values = {
                'partner': invoice.partner_id.name,
                'date': invoice.date,
                'number': invoice.number,
                'user': invoice.user_id.name,
                'total1': invoice.amount_total_signed,
                'total': invoice.amount_total_signed,
                'residual': invoice.amount_residual_signed,
            }
            docs.append(values)
        docs = sorted(docs, key=lambda x: x['date'])

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'month': str(month),
            'year': str(year),
            'docs': docs,
        }
