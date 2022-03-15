odoo.define('pos_set_default_customer.GetCustomer', function(require) {
    "use strict";

    var models = require('point_of_sale.models');

    // var _super_order = models.Order.prototype;
    // models.Order = models.Order.extend({
    //     initialize: function() {
    //         _super_order.initialize.apply(this, arguments);
    //         if (this.pos.config.default_partner_id) {
    //             this.set_client(this.pos.db.get_partner_by_id(this.pos.config.default_partner_id[0]));
    //         }
    //     },
    // });
    let _super_PosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({

        async add_new_order() {
            _super_PosModel.add_new_order.apply(this, arguments);
            const order = this.get_order();
            const client = order.get_client();
            if (!client && this.config.default_partner_id) {
                let client_default = this.db.get_partner_by_id(this.config.default_partner_id[0]);
                if (!client_default) {
                    this.chrome.showPopup('ErrorPopup', {
                        title: this.env._t('Warning !!!'),
                        body: this.config.default_partner_id[1] + this.env._t(' set to Default Customer of new Order, but it Arichived it. Please Unarchive')
                    })
                } else {
                    order.set_client(client_default);
                }
            }
        },
    });
});