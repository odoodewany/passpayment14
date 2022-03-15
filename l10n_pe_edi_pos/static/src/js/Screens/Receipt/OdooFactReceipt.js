odoo.define('l10n_pe_edi_pos.OrderReceipt', function (require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

    const L10nPeEdiPosReceipt = (OrderReceipt) =>
        class extends OrderReceipt {
            constructor() {
                super(...arguments);
            }

            willUpdateProps(nextProps) {
                if (nextProps.order) { // restaurant has error when back to floor sreeen, order is null and nextProps.order is not found
                    super.willUpdateProps(nextProps)
                } else {
                    console.warn('Your POS active iface_print_skip_screen, please turn it off. This feature make lose order')
                }
            }
        }

    Registries.Component.extend(OrderReceipt, L10nPeEdiPosReceipt);
    if (self.odoo.session_info && self.odoo.session_info['config']['l10n_pe_edi_send_invoice']) {
        OrderReceipt.template = 'L10nPeEdiPosReceipt';
    }
    Registries.Component.add(L10nPeEdiPosReceipt);
    return OrderReceipt;
});

