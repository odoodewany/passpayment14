odoo.define('wk_pos_partial_payment.WkPPAlertPopUp', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class WkPPAlertPopUp extends AbstractAwaitablePopup {
        getPayload() {
            return null;
        }
    }
    WkPPAlertPopUp.template = 'WkPPAlertPopUp';
    WkPPAlertPopUp.defaultProps = {
        title: 'Confirm ?',
        cancelText: 'Cancel',
        confirmText: 'Ok',

        body: '',
    };

    Registries.Component.add(WkPPAlertPopUp);

    return WkPPAlertPopUp;


});