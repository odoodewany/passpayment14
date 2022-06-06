# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "POS Partial Payment",
  "summary"              :  """The module allows the customers to make partial payment for their orders and the user can validate the invoice for partial payment in POS session.""",
  "category"             :  "Point of Sale",
  "version"              :  "1.1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-POS-Partial-Payment.html",
  "description"          :  """Odoo POS Partial Payment
POS Partial payments 
Split payment POS
POS half payment
Validate partial invoice POS
POS partial invoice
Pay later POS
POS make payment later
POS pay later
POS Make partial payment
Allows part payment POS
Allows down-payment POS
POS partially paid order""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=wk_pos_partial_payment&custom_url=/pos/auto",
  "depends"              :  ['point_of_sale'],
  "data"                 :  [
                             'views/template.xml',
                             'views/pos_config_view.xml',
                             'views/account_view.xml',
                             'views/pos_order.xml',
                             'views/account_move_view.xml',
                            ],
  "qweb"                 :  ['static/src/xml/pos.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  45,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}