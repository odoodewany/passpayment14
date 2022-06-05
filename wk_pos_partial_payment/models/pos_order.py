# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import api, fields, models ,tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = "pos.order"

    invoice_remark = fields.Char(string="Invoice Remark",copy=False)
    is_partially_paid = fields.Boolean(string="Is Partially Paid", copy=False)
    wk_order_amount = fields.Float(string="Total",copy=False)

    @api.model
    def _order_fields(self,ui_order):
        fields_return = super(PosOrder,self)._order_fields(ui_order)
        fields_return.update({'invoice_remark':ui_order.get('invoice_remark', False)})
        fields_return.update({'is_partially_paid':ui_order.get('is_partially_paid', False)})
        return fields_return

    @api.model
    def create_from_ui(self, orders, draft=False):
        data = return_data = super(PosOrder, self).create_from_ui(orders,draft)
        if type(data) == dict:
            order_ids = [res.get('id') for res in return_data.get('order_ids')]
        else:
            order_ids = [res.get('id') for res in data]
        order_objs = self.browse(order_ids)
        for order in order_objs:
            if order.account_move:
                order.account_move.partial_payment_remark = order.invoice_remark
                if not order.amount_paid:
                    order.account_move.is_no_payment = True

                if order.is_partially_paid:
                    order.wk_order_amount = order.amount_total
                    order.amount_total = order.amount_paid

        return return_data



    def action_pos_order_paid(self):
        if self.is_partially_paid:
            self.write({'state': 'paid'})
        return super(PosOrder, self).action_pos_order_paid()
    