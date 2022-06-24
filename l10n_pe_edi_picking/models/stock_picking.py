# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2019-TODAY Odoo Peru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

from email.policy import default
import json
import requests
import pytz

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from bs4 import BeautifulSoup
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    l10n_pe_edi_is_epicking = fields.Boolean(
        string="Is E-picking", default=False, copy=False)
    l10n_pe_edi_picking_sequence_id = fields.Many2one(
        'ir.sequence', string="E-Picking Sequence", copy=False)
    l10n_pe_edi_shop_id = fields.Many2one('l10n_pe_edi.shop', string='Shop')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ---------SEND OSE-------------------

    def _starting_point_state_id(self):
        if self.env.company.partner_id.state_id:
            return self.env.company.partner_id.state_id.id
        return False

    def _starting_point_province_id(self):
        if self.env.company.partner_id.city_id:
            return self.env.company.partner_id.city_id.id
        return False

    def _starting_point_district_id(self):
        if self.env.company.partner_id.l10n_pe_district:
            return self.env.company.partner_id.l10n_pe_district.id
        return False

    def _starting_point_ubigeo(self):
        if self.env.company.partner_id.l10n_pe_district:
            return self.env.company.partner_id.l10n_pe_district.code
        return False

    def _arrival_point_ubigeo(self):
        if self.env.company.partner_id.zip:
            return self.env.company.partner_id.zip
        return False

    def _starting_point_street(self):
        if self.env.company.partner_id.street:
            return self.env.company.partner_id.street
        return False

    def picking_driver_doc_type(self):
        partner = self.env['res.partner'].search(
            [('company_id', '=', self.env.company.id), ('is_driver', '=', True)], limit=1)
        if partner:
            return partner.l10n_latam_identification_type_id.id
        return False

    def picking_driver_doc_number(self):
        partner = self.env['res.partner'].search(
            [('company_id', '=', self.env.company.id), ('is_driver', '=', True)], limit=1)
        if partner:
            return partner.vat
        return False

    def picking_driver_name(self):
        partner = self.env['res.partner'].search(
            [('company_id', '=', self.env.company.id), ('is_driver', '=', True)], limit=1)
        if partner:
            return partner.name
        return False

    def picking_catalog_18_id(self):
        selection = self.env['l10n_pe_edi.catalog.18'].search(
            [('name', '=', 'Transporte privado')])
        if selection:
            return selection.id
        return False

    def picking_carrier_license_plate(self):
        partner = self.env['res.partner'].search(
            [('company_id', '=', self.env.company.id), ('is_driver', '=', True)], limit=1)
        if partner:
            return partner.placa
        return False

    def picking_carrier_doc_type(self):
        company_doc_type = self.env['l10n_latam.identification.type'].search([
                                                                             ('name', '=', 'RUC')])
        if company_doc_type:
            return company_doc_type.id
        return False

    def picking_carrier_doc_number(self):
        company = self.env['res.company'].search(
            [('name', '=', self.env.company.name)], limit=1)
        if company:
            return company.vat
        return False

    def picking_carrier_name(self):
        # return self.picking_type_id.company_id.name
        company = self.env['res.company'].search(
            [('name', '=', self.env.company.name)], limit=1)
        if company:
            return company.name
        return False
    # def deafult_partner_id(self):
    # 	partner = self.env['account.move'].search([('partner_id','=',self.env.user.partner_id.id)], limit=1)
    # 	if partner:
    # 		return partner.invoice_partner_display_name

    def default_number_packages(self):
        suma = 0
        for product in self.move_ids_without_package:
            suma = suma + product.product_uom_qty
        return suma

        # number_packages= self.env['account.move']
        # suma = 0
        # for product in number_packages.invoice_line_ids:
        # 	suma = suma + product
        # return suma

    # partner_id = fields.Many2one(
    #     'res.partner', 'Contact',
    #     check_company=True, default= deafult_partner_id,
    #     states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    move_ids_without_package = fields.One2many('stock.move', 'picking_id', string="Stock moves not in package",
                                               compute='_compute_move_without_package', inverse='_set_move_without_package')
    l10n_pe_edi_picking_company_partner_id = fields.Many2one(
        'res.partner', string="Company Partner", related='company_id.partner_id')
    l10n_pe_edi_picking_partner_id = fields.Many2one(
        'res.partner', string="Partner", compute='_compute_l10n_pe_edi_picking_partner', store=True)
    l10n_pe_edi_picking_name = fields.Char(
        string="E-Picking Name", readonly=True, copy=False)
    l10n_pe_edi_picking_serie = fields.Char(
        string="Serie", store=True, readonly=True, copy=False)
    l10n_pe_edi_picking_number = fields.Integer(
        string="Number", store=True, readonly=True, copy=False)
    l10n_pe_edi_picking_observations = fields.Char(
        string='Observations', size=1000, help="If you want line breaks for the printed or PDF representation use <br>", copy=False)
    l10n_pe_edi_picking_catalog_20_id = fields.Many2one(
        'l10n_pe_edi.catalog.20', string="Reason for transfer")
    l10n_pe_edi_picking_total_gross_weight = fields.Float(
        string="Total Gross Weight", default=0.0, help='Weight in Kg.')
    ''' l10n_pe_edi_picking_number_packages = fields.Float(string="Number Of Packages", default=default_number_packages) '''
    l10n_pe_edi_picking_number_packages = fields.Float(
        string="Number Of Packages", compute="_compute_number_packages")
    l10n_pe_edi_picking_catalog_18_id = fields.Many2one(
        'l10n_pe_edi.catalog.18', string="Transport Type", default=picking_catalog_18_id)
    l10n_pe_edi_picking_catalog_18_code = fields.Char(
        related='l10n_pe_edi_picking_catalog_18_id.code')
    l10n_pe_edi_picking_start_transport_date = fields.Date(
        string="Start Transport Date", copy=False, default=datetime.today().strftime('%Y-%m-%d'))
    l10n_pe_edi_picking_partner_for_carrier_driver = fields.Boolean(
        related='company_id.l10n_pe_edi_picking_partner_for_carrier_driver')
    l10n_pe_edi_picking_carrier_id = fields.Many2one(
        'res.partner', string="Carrier")
    l10n_pe_edi_picking_carrier_doc_type = fields.Many2one(
        'l10n_latam.identification.type', string="Carrier Document Type", default=picking_carrier_doc_type)
    l10n_pe_edi_picking_carrier_doc_number = fields.Char(
        string="Carrier Document Number", default=picking_carrier_doc_number)
    l10n_pe_edi_picking_carrier_name = fields.Char(
        string="Carrier Name", default=picking_carrier_name)
    l10n_pe_edi_picking_carrier_license_plate = fields.Char(
        string="License Plate", default=picking_carrier_license_plate)
    l10n_pe_edi_picking_driver_id = fields.Many2one(
        'res.partner', string="Driver")
    l10n_pe_edi_picking_driver_doc_type = fields.Many2one(
        'l10n_latam.identification.type', string="Driver Document Type", default=picking_driver_doc_type)
    l10n_pe_edi_picking_driver_doc_number = fields.Char(
        string="Driver Document Number", default=picking_driver_doc_number)
    l10n_pe_edi_picking_driver_name = fields.Char(
        string="Driver Name", default=picking_driver_name)
    l10n_pe_edi_multishop = fields.Boolean(
        'Multi-Shop', related='company_id.l10n_pe_edi_multishop')
    l10n_pe_edi_shop_id = fields.Many2one(
        'l10n_pe_edi.shop', string='Shop', related='picking_type_id.l10n_pe_edi_shop_id', store=True)
    l10n_pe_edi_picking_partner_for_starting_arrival_point = fields.Boolean(
        related='company_id.l10n_pe_edi_picking_partner_for_starting_arrival_point')
    l10n_pe_edi_picking_starting_point_id = fields.Many2one(
        'res.partner', string="Starting Point")
    l10n_pe_edi_picking_starting_point_country_id = fields.Many2one(
        'res.country', string="Starting Point Country", related='l10n_pe_edi_picking_company_partner_id.country_id')
    l10n_pe_edi_picking_starting_point_state_id = fields.Many2one(
        'res.country.state', string="Starting Point State", default=_starting_point_state_id)
    l10n_pe_edi_picking_starting_point_province_id = fields.Many2one(
        'res.city', string="Starting Point Province", default=_starting_point_province_id)
    l10n_pe_edi_picking_starting_point_district_id = fields.Many2one(
        'l10n_pe.res.city.district', string="Starting Point District", default=_starting_point_district_id)
    l10n_pe_edi_picking_starting_point_ubigeo = fields.Char(
        string="Starting Point Ubigeo", default=_starting_point_ubigeo)
    l10n_pe_edi_picking_starting_point_street = fields.Char(
        string="Starting Point Street", default=_starting_point_street)
    l10n_pe_edi_picking_arrival_point_id = fields.Many2one(
        'res.partner', string="Arrival Point")
    l10n_pe_edi_picking_arrival_point_country_id = fields.Many2one(
        'res.country', string="Arrival Point Country", related='l10n_pe_edi_picking_partner_id.country_id')
    l10n_pe_edi_picking_arrival_point_state_id = fields.Many2one(
        'res.country.state', string="Arrival Point State")
    l10n_pe_edi_picking_arrival_point_province_id = fields.Many2one(
        'res.city', string="Arrival Point Province")
    l10n_pe_edi_picking_arrival_point_district_id = fields.Many2one(
        'l10n_pe.res.city.district', string="Arrival Point District")
    l10n_pe_edi_picking_arrival_point_ubigeo = fields.Char(
        string="Arrival Point Ubigeo", default=_arrival_point_ubigeo)
    ''' l10n_pe_edi_picking_arrival_point_ubigeo = fields.Char(
        string="Arrival Point Ubigeo") '''
    l10n_pe_edi_picking_arrival_point_street = fields.Char(
        string="Arrival Point Street")
    l10n_pe_edi_is_epicking = fields.Boolean(
        string="Is E-picking", readonly=True, copy=False)
    l10n_pe_edi_ose_accepted = fields.Boolean(
        'Sent to PSE/OSE', related='l10n_pe_edi_request_id.ose_accepted', store=True)
    l10n_pe_edi_request_id = fields.Many2one(
        'l10n_pe_edi.request', string='PSE/OSE request', copy=False)
    l10n_pe_edi_response = fields.Text(
        'Response', related='l10n_pe_edi_request_id.response', store=True)
    l10n_pe_edi_sunat_accepted = fields.Boolean(
        'Accepted by SUNAT', related='l10n_pe_edi_request_id.sunat_accepted', store=True)

    # -----------COMPUTE & ONCHANGE----------------

    @api.depends('move_ids_without_package')
    def _compute_number_packages(self):
        for record in self:
            record.l10n_pe_edi_picking_number_packages = sum(
                record.move_ids_without_package.mapped("product_uom_qty"))

    def _compute_serie_number(self):
        for rec in self:
            if rec.l10n_pe_edi_picking_name:
                name = rec.l10n_pe_edi_picking_name.split('-')
                if len(name) == 2:
                    rec.l10n_pe_edi_picking_serie = name[0]
                    rec.l10n_pe_edi_picking_number = int(name[1])

    @api.depends('partner_id')
    def _compute_l10n_pe_edi_picking_partner(self):
        for rec in self:
            rec.l10n_pe_edi_picking_partner_id = rec.partner_id.commercial_partner_id

    @api.onchange('l10n_pe_edi_picking_starting_point_id')
    def _onchange_starting_point(self):
        if self.l10n_pe_edi_picking_starting_point_id and self.l10n_pe_edi_picking_starting_point_id.l10n_pe_district:
            self.l10n_pe_edi_picking_starting_point_district_id = self.l10n_pe_edi_picking_starting_point_id.l10n_pe_district.id
            self.l10n_pe_edi_picking_starting_point_street = self.l10n_pe_edi_picking_starting_point_id.street

    @api.onchange('l10n_pe_edi_picking_arrival_point_id')
    def _onchange_arrival_point(self):
        if self.l10n_pe_edi_picking_arrival_point_id and self.l10n_pe_edi_picking_arrival_point_id.l10n_pe_district:
            self.l10n_pe_edi_picking_arrival_point_district_id = self.l10n_pe_edi_picking_arrival_point_id.l10n_pe_district.id
            self.l10n_pe_edi_picking_arrival_point_street = self.l10n_pe_edi_picking_arrival_point_id.street

    @api.onchange('l10n_pe_edi_picking_starting_point_district_id')
    def _onchange_starting_point_district(self):
        if self.l10n_pe_edi_picking_starting_point_district_id:
            self.l10n_pe_edi_picking_starting_point_ubigeo = self.l10n_pe_edi_picking_starting_point_district_id.code
            if self.l10n_pe_edi_picking_starting_point_district_id.city_id:
                self.l10n_pe_edi_picking_starting_point_province_id = self.l10n_pe_edi_picking_starting_point_district_id.city_id.id

    @api.onchange('l10n_pe_edi_picking_arrival_point_district_id')
    def _onchange_arrival_point_district(self):
        if self.l10n_pe_edi_picking_arrival_point_district_id:
            self.l10n_pe_edi_picking_arrival_point_ubigeo = self.l10n_pe_edi_picking_arrival_point_district_id.code
            if self.l10n_pe_edi_picking_arrival_point_district_id.city_id:
                self.l10n_pe_edi_picking_arrival_point_province_id = self.l10n_pe_edi_picking_arrival_point_district_id.city_id.id

    @api.onchange('l10n_pe_edi_picking_starting_point_province_id')
    def _onchange_starting_point_province(self):
        if self.l10n_pe_edi_picking_starting_point_province_id and self.l10n_pe_edi_picking_starting_point_province_id.state_id:
            self.l10n_pe_edi_picking_starting_point_state_id = self.l10n_pe_edi_picking_starting_point_province_id.state_id.id
        res = {}
        res['domain'] = {}
        res['domain']['l10n_pe_edi_picking_starting_point_district_id'] = []
        if self.l10n_pe_edi_picking_starting_point_province_id:
            res['domain']['l10n_pe_edi_picking_starting_point_district_id'] += [
                ('city_id', '=', self.l10n_pe_edi_picking_starting_point_province_id.id)]
        return res

    @api.onchange('l10n_pe_edi_picking_arrival_point_province_id')
    def _onchange_arrival_point_province(self):
        if self.l10n_pe_edi_picking_arrival_point_province_id and self.l10n_pe_edi_picking_arrival_point_province_id.state_id:
            self.l10n_pe_edi_picking_arrival_point_state_id = self.l10n_pe_edi_picking_arrival_point_province_id.state_id.id
        res = {}
        res['domain'] = {}
        res['domain']['l10n_pe_edi_picking_arrival_point_district_id'] = []
        if self.l10n_pe_edi_picking_arrival_point_province_id:
            res['domain']['l10n_pe_edi_picking_arrival_point_district_id'] += [
                ('city_id', '=', self.l10n_pe_edi_picking_arrival_point_province_id.id)]
        return res

    @api.onchange('l10n_pe_edi_picking_starting_point_state_id')
    def _onchange_starting_point_state(self):
        if self.l10n_pe_edi_picking_starting_point_state_id and self.l10n_pe_edi_picking_starting_point_state_id.country_id:
            self.l10n_pe_edi_picking_starting_point_country_id = self.l10n_pe_edi_picking_starting_point_state_id.country_id.id
        res = {}
        res['domain'] = {}
        res['domain']['l10n_pe_edi_picking_starting_point_province_id'] = []
        if self.l10n_pe_edi_picking_starting_point_state_id:
            res['domain']['l10n_pe_edi_picking_starting_point_province_id'] += [
                ('state_id', '=', self.l10n_pe_edi_picking_starting_point_state_id.id)]
        return res

    @api.onchange('l10n_pe_edi_picking_arrival_point_state_id')
    def _onchange_arrival_point_state(self):
        if self.l10n_pe_edi_picking_arrival_point_state_id and self.l10n_pe_edi_picking_arrival_point_state_id.country_id:
            self.l10n_pe_edi_picking_arrival_point_country_id = self.l10n_pe_edi_picking_arrival_point_state_id.country_id.id
        res = {}
        res['domain'] = {}
        res['domain']['l10n_pe_edi_picking_arrival_point_province_id'] = []
        if self.l10n_pe_edi_picking_arrival_point_state_id:
            res['domain']['l10n_pe_edi_picking_arrival_point_province_id'] += [
                ('state_id', '=', self.l10n_pe_edi_picking_arrival_point_state_id.id)]
        return res

    @api.onchange('l10n_pe_edi_picking_carrier_id')
    def _onchange_carrier(self):

        # self.l10n_pe_edi_picking_carrier_doc_type = self.l10n_pe_edi_picking_carrier_id.l10n_latam_identification_type_id.id
        self.l10n_pe_edi_picking_carrier_doc_number = self.l10n_pe_edi_picking_carrier_id.vat
        # self.l10n_pe_edi_picking_carrier_name = self.l10n_pe_edi_picking_carrier_id.name

    @api.onchange('l10n_pe_edi_picking_driver_id')
    def _onchange_driver(self):
        if self.l10n_pe_edi_picking_driver_id:
            self.l10n_pe_edi_picking_driver_doc_type = self.l10n_pe_edi_picking_driver_id.l10n_latam_identification_type_id.id
            self.l10n_pe_edi_picking_driver_doc_number = self.l10n_pe_edi_picking_driver_id.vat
            self.l10n_pe_edi_picking_driver_name = self.l10n_pe_edi_picking_driver_id.name

    @api.onchange('l10n_pe_edi_picking_carrier_doc_type', 'l10n_pe_edi_picking_carrier_doc_number')
    def _onchange_carrier_doc_type(self):
        if not self.l10n_pe_edi_picking_partner_for_carrier_driver and self.l10n_pe_edi_picking_carrier_doc_type and self.l10n_pe_edi_picking_carrier_doc_number:
            if self.l10n_pe_edi_picking_carrier_doc_type.l10n_pe_vat_code == '1':
                result = self.env['res.partner'].l10n_pe_dni_connection(
                    self.l10n_pe_edi_picking_carrier_doc_number)
                # if result:
                # 	self.l10n_pe_edi_picking_carrier_name = str(result['nombre']).strip()
            if self.l10n_pe_edi_picking_carrier_doc_type.l10n_pe_vat_code == '6':
                result = self.env['res.partner'].l10n_pe_ruc_connection(
                    self.l10n_pe_edi_picking_carrier_doc_number)
                # if result:
                # 	self.l10n_pe_edi_picking_carrier_name = str(result['business_name']).strip()

    @api.onchange('l10n_pe_edi_picking_driver_doc_type', 'l10n_pe_edi_picking_driver_doc_number')
    def _onchange_driver_doc_type(self):
        if not self.l10n_pe_edi_picking_partner_for_carrier_driver and self.l10n_pe_edi_picking_driver_doc_type and self.l10n_pe_edi_picking_driver_doc_number:
            if self.l10n_pe_edi_picking_driver_doc_type.l10n_pe_vat_code == '1':
                result = self.env['res.partner'].l10n_pe_dni_connection(
                    self.l10n_pe_edi_picking_driver_doc_number)
                if result:
                    self.l10n_pe_edi_picking_driver_name = str(
                        result['nombre']).strip()
            if self.l10n_pe_edi_picking_driver_doc_type.l10n_pe_vat_code == '6':
                result = self.env['res.partner'].l10n_pe_ruc_connection(
                    self.l10n_pe_edi_picking_driver_doc_number)
                if result:
                    self.l10n_pe_edi_picking_driver_name = str(
                        result['business_name']).strip()

    # -----------METHODS---------------------------

    # @api.onchange('picking_type_id')
    # def _onchange_partner(self):
    # 	if self.partner_id:
    # 		self.l10n_pe_edi_picking_starting_point_state_id = self.picking_type_id.company_id.state_id.id
    # 		self.l10n_pe_edi_picking_starting_point_province_id = self.picking_type_id.company_id.city
    # 		self.l10n_pe_edi_picking_starting_point_district_id = self.picking_type_id.company_id.street2
    # 		self.l10n_pe_edi_picking_starting_point_ubigeo = self.picking_type_id.company_id.zip
    # 		self.l10n_pe_edi_picking_starting_point_street = self.picking_type_id.company_id.street_name

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.l10n_pe_edi_picking_arrival_point_state_id = self.partner_id.state_id.id
            self.l10n_pe_edi_picking_arrival_point_province_id = self.partner_id.city_id.id
            self.l10n_pe_edi_picking_arrival_point_district_id = self.partner_id.l10n_pe_district.id
            self.l10n_pe_edi_picking_arrival_point_ubigeo = self.partner_id.zip
            self.l10n_pe_edi_picking_arrival_point_street = self.partner_id.street_name

    @api.onchange('l10n_pe_edi_picking_catalog_18_id')
    def _onchange_picking_catalog_18_id(self):
        company = self.env.company
        partner = self.env['res.partner'].search(
            [('company_id', '=', company.id), ('is_driver', '=', True)], limit=1)
        company_doc_type = self.env['l10n_latam.identification.type'].search([
                                                                             ('name', '=', 'RUC')])
        if partner:
            if self.l10n_pe_edi_picking_catalog_18_id.id == self.env['l10n_pe_edi.catalog.18'].search([('name', '=', 'Transporte privado')], limit=1).id:
                self.l10n_pe_edi_picking_driver_doc_type = partner.l10n_latam_identification_type_id.id if partner.l10n_latam_identification_type_id else False
                self.l10n_pe_edi_picking_driver_doc_number = partner.vat
                self.l10n_pe_edi_picking_driver_name = partner.name
                self.l10n_pe_edi_picking_carrier_doc_type = company_doc_type.id
                self.l10n_pe_edi_picking_carrier_doc_number = company.vat
                self.l10n_pe_edi_picking_carrier_name = company.name
                self.l10n_pe_edi_picking_carrier_license_plate = partner.placa
            else:
                self.l10n_pe_edi_picking_carrier_doc_type = partner.l10n_latam_identification_type_id.id if partner.l10n_latam_identification_type_id else False
                self.l10n_pe_edi_picking_carrier_doc_number = partner.vat
                self.l10n_pe_edi_picking_carrier_name = partner.name
                self.l10n_pe_edi_picking_carrier_license_plate = partner.placa
                self.l10n_pe_edi_picking_driver_doc_type = False
                self.l10n_pe_edi_picking_driver_doc_number = False
                self.l10n_pe_edi_picking_driver_name = False

    @api.onchange('move_ids_without_package')
    def _onchange_move_ids_without_package(self):
        _logger.info("cambio en = - =")
        suma1 = 0
        suma2 = 0
        for product in self.move_ids_without_package:
            suma1 = suma1 + product.product_uom_qty
            suma2 = suma2 + product.quantity_done
        self.l10n_pe_edi_picking_number_packages = suma1

    def convert_date_to_timezone(self, date_time):
        if self.env.user.tz:
            tz = pytz.timezone(self.env.user.tz)
            return pytz.utc.localize(date_time).astimezone(tz)
        else:
            return date_time

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('e_picking_name', False):
                # Only goes off when the custom_search is in the context values.
                result.append((record.id, "{}".format(
                    record.l10n_pe_edi_picking_name)))
            else:
                result.append((record.id, record.name))
        return result

    def convert_to_epicking(self):
        # if self.state != 'done':
        #     raise UserError(_("This document cannot be converted to electronic picking. The picking should be done"))
        if self.picking_type_id.l10n_pe_edi_is_epicking:
            if self.l10n_pe_edi_picking_partner_id.l10n_latam_identification_type_id and self.l10n_pe_edi_picking_partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code in ['6', '1', '-', '4', '7', 'A', '0'] and self.l10n_pe_edi_picking_partner_id.vat:
                self.l10n_pe_edi_is_epicking = True
                if not self.l10n_pe_edi_picking_name:
                    self.l10n_pe_edi_picking_name = self.picking_type_id.l10n_pe_edi_picking_sequence_id.next_by_id()
            else:
                raise UserError(
                    _("This document cannot be converted to electronic picking. The client does not have a valid document type"))
        else:
            raise UserError(
                _("You cannot convert this document to electronic picking. Configure the settings of 'Picking operation type'"))
        self._compute_serie_number()

    def _get_picking_lines_values_odoofact(self, lines):
        data = []
        for item in lines:
            values = {
                'unidad_de_medida': item.product_uom_id and
                (item.product_uom_id.l10n_pe_edi_uom_code_id and item.product_uom_id.l10n_pe_edi_uom_code_id.code or False) or 'NIU',
                'codigo': item.product_id.default_code or '',
                'descripcion': item.product_id.display_name,
                'cantidad': item.qty_done,
            }
            data.append(values)
        return data

    @api.model
    def _get_partner_address(self, partner):
        res = ''
        if partner:
            if partner.street:
                res += partner.street
            if partner.street_number:
                res += ' ' + partner.street_number
            if partner.street_number2:
                res += ', ' + partner.street_number2
            # if partner.l10n_pe_district:
            #     res += ', ' + partner.l10n_pe_district.name
            # if partner.city_id:
            #     res += ', ' + partner.city_id.name
            # if partner.state_id:
            #     res += ', ' + partner.state_id.name
        return res

    def _get_picking_values_odoofact(self):
        values = {
            'company_id': self.company_id.id,
            'l10n_pe_edi_shop_id': self.l10n_pe_edi_shop_id and self.l10n_pe_edi_shop_id.id or False,
            'picking_id': self.id,
            'operacion': "generar_guia",
            'tipo_de_comprobante': 7,
            'serie': str(self.l10n_pe_edi_picking_serie),
            'numero': self.l10n_pe_edi_picking_number,
            'cliente_tipo_de_documento': str(self.l10n_pe_edi_picking_partner_id.l10n_latam_identification_type_id and self.l10n_pe_edi_picking_partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code) if self.l10n_pe_edi_picking_partner_id.l10n_latam_identification_type_id else '1',
            'cliente_numero_de_documento': self.l10n_pe_edi_picking_partner_id.vat,
            'cliente_denominacion': self.l10n_pe_edi_picking_partner_id.name,
            'cliente_direccion': self._get_partner_address(self.partner_id),
            'observaciones': ' '.join(BeautifulSoup(self.note, "html.parser").stripped_strings) or '',
            'fecha_de_emision': self.date_done and self.convert_date_to_timezone(self.date_done).strftime("%d-%m-%Y") or '',
            'motivo_de_traslado': self.l10n_pe_edi_picking_catalog_20_id and self.l10n_pe_edi_picking_catalog_20_id.code or '',
            'peso_bruto_total': self.l10n_pe_edi_picking_total_gross_weight or 0.0,
            'numero_de_bultos': self.l10n_pe_edi_picking_number_packages or 0,
            'tipo_de_transporte': self.l10n_pe_edi_picking_catalog_18_id and self.l10n_pe_edi_picking_catalog_18_id.code or '',
            'fecha_de_inicio_de_traslado': self.l10n_pe_edi_picking_start_transport_date and self.l10n_pe_edi_picking_start_transport_date.strftime('%d-%m-%Y') or '',
            'transportista_documento_tipo': self.l10n_pe_edi_picking_carrier_doc_type and self.l10n_pe_edi_picking_carrier_doc_type.l10n_pe_vat_code or '-',
            'transportista_documento_numero': self.l10n_pe_edi_picking_carrier_doc_number or '-',
            'transportista_denominacion': self.l10n_pe_edi_picking_carrier_name or '-',
            'transportista_placa_numero': self.l10n_pe_edi_picking_carrier_license_plate or '-',
            'conductor_documento_tipo': self.l10n_pe_edi_picking_driver_doc_type and self.l10n_pe_edi_picking_driver_doc_type.l10n_pe_vat_code or '-',
            'conductor_documento_numero': self.l10n_pe_edi_picking_driver_doc_number or '-',
            'conductor_denominacion': self.l10n_pe_edi_picking_driver_name or '-',
            'punto_de_partida_ubigeo': self.l10n_pe_edi_picking_starting_point_ubigeo,
            'punto_de_partida_direccion': self.l10n_pe_edi_picking_starting_point_street,
            'punto_de_llegada_ubigeo': self.l10n_pe_edi_picking_arrival_point_ubigeo,
            'punto_de_llegada_direccion': self.l10n_pe_edi_picking_arrival_point_street,
            'enviar_automaticamente_a_la_sunat': "true",
            'enviar_automaticamente_al_cliente': "false",
            'codigo_unico': '%s|%s|%s-%s' % ('odoo', self.company_id.partner_id.vat, self.l10n_pe_edi_picking_serie, str(self.l10n_pe_edi_picking_number)),
            'items': self._get_picking_lines_values_odoofact(self.move_line_ids_without_package.filtered(lambda x: x.qty_done > 0)),
        }
        return values

    def _get_picking_values_check_odoofact(self):
        """
        Prepare the dict of values to create the request for checking the document status. Valid for Nubefact.
        """
        self.ensure_one()
        values = {
            'company_id': self.company_id.id,
            'operacion': 'consultar_guia',
            'tipo_de_comprobante': 7,
            'serie': self.l10n_pe_edi_picking_serie,
            'numero': str(self.l10n_pe_edi_picking_number)
        }
        return values

    def _get_ose_supplier(self):
        if not self.company_id.l10n_pe_edi_ose_id:
            raise UserError(
                _('Please select a PSE/OSE supplier for the company %s') % (self.company_id.name,))
        return self.company_id.l10n_pe_edi_ose_id.code

    def action_document_send(self):
        if not self.l10n_pe_edi_is_epicking:
            raise UserError(_("The Picking is not a Electronic Document"))
        if not self.l10n_pe_edi_picking_carrier_doc_type and not self.l10n_pe_edi_picking_carrier_doc_number and self.l10n_pe_edi_picking_catalog_18_code == '01':
            raise UserError(
                _("Carrier doesn't have document number or document type assigned"))
        if not self.l10n_pe_edi_picking_driver_doc_type and not self.l10n_pe_edi_picking_driver_doc_number and self.l10n_pe_edi_picking_catalog_18_code == '02':
            raise UserError(
                _("Driver doesn't  have document number or document type assigned"))
        for picking in self:
            if picking.state == 'draft':
                continue
            if picking.company_id.l10n_pe_edi_multishop and not picking.l10n_pe_edi_shop_id:
                raise UserError(_("Review the Journal configuration and select a shop: \n Journal: %s") % (
                    move.journal_id.name))
            ose_supplier = picking._get_ose_supplier()
            vals = getattr(picking, '_get_picking_values_%s' % ose_supplier)()
            if not picking.l10n_pe_edi_request_id:
                l10n_pe_edi_request_id = self.env['l10n_pe_edi.request'].create({
                    'company_id': picking.company_id.id,
                    'document_number': picking.l10n_pe_edi_picking_name,
                    'l10n_pe_edi_shop_id': picking.l10n_pe_edi_shop_id and picking.l10n_pe_edi_shop_id.id or False,
                    'model': self._name,
                    'res_id': self.id,
                    'type': 'picking',
                    'document_date': picking.date_done})
                picking.write(
                    {'l10n_pe_edi_request_id': l10n_pe_edi_request_id})
            else:
                l10n_pe_edi_request_id = picking.l10n_pe_edi_request_id
            if not picking.l10n_pe_edi_ose_accepted:
                l10n_pe_edi_request_id.action_api_connect(vals)
            else:
                picking.action_document_check()

    def action_document_check(self):
        """
        Send the request for Checking document status for electronic pickings
        """
        for picking in self:
            ose_supplier = picking._get_ose_supplier()
            vals = getattr(picking, '_get_picking_values_check_%s' %
                           ose_supplier)()
            if picking.l10n_pe_edi_request_id:
                picking.l10n_pe_edi_request_id.action_api_connect(vals)

    @api.model
    def cron_send_pickings(self):
        picking_ids = self.env['stock.picking'].search([
            ('l10n_pe_edi_is_epicking', '=', True),
            ('state', 'not in', ['draft', 'cancel']),
            ('l10n_pe_edi_ose_accepted', '=', False)]).filtered(lambda inv: inv.scheduled_date != False)
        for picking in picking_ids:
            picking.action_document_send()

    @api.model
    def cron_check_pickings(self):
        picking_ids = self.env['stock.picking'].search([
            ('l10n_pe_edi_is_epicking', '=', True),
            ('state', 'not in', ['draft', 'cancel']),
            ('l10n_pe_edi_ose_accepted', '=', True),
            ('l10n_pe_edi_sunat_accepted', '=', False)]).filtered(lambda inv: inv.scheduled_date != False)
        for picking in picking_ids:
            picking.action_document_check()

    def action_open_edi_request(self):
        """ 
        This method opens the EDI request 
        """
        self.ensure_one()
        if self.l10n_pe_edi_request_id:
            return {
                'name': _('EDI Request'),
                'view_mode': 'form',
                'res_model': 'l10n_pe_edi.request',
                'res_id': self.l10n_pe_edi_request_id.id,
                'type': 'ir.actions.act_window',
            }
        return True
