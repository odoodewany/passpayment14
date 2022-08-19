# -*- coding: utf-8 -*-
from odoo import models, fields, api


class POSConfig(models.Model):
    _inherit = 'pos.config'

    iface_orderline_pos_order_notes = fields.Boolean(string='Orderline Notes', help='Allow custom notes on Orderlines.')

    @api.onchange('module_pos_restaurant')
    def _onchange_module_pos_restaurant(self):
        if not self.module_pos_restaurant:
            self.update({'iface_printbill': False,
                         'iface_splitbill': False,
                         'is_order_printer': False,
                         'is_table_management': False,
                         'iface_orderline_notes': False,
                         'iface_orderline_pos_order_notes': True})

        else:
            self.update({'iface_orderline_pos_order_notes': False})

''' class copy_PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_line(self, order_line):
        return {
            'product_id': order_line.product_id.id,
            'quantity': order_line.qty if self.amount_total >= 0 else -order_line.qty,
            'discount': order_line.discount,
            'price_unit': order_line.price_unit,
            'name': order_line.product_id.display_name,
            'tax_ids': [(6, 0, order_line.tax_ids_after_fiscal_position.ids)],
            'product_uom_id': order_line.product_uom_id.id,
        } '''
