odoo.define('l10n_pe_edi_pos.order', function (require) {

    const models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    let _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({ 
        init_from_JSON: function (json) {
            var result = _super_Order.init_from_JSON.apply(this, arguments);
           
            if (json.payment_journal_id) {
                this.invoice_journal_id = json.payment_journal_id;
            } 
            
                       
            return result;
        },
        export_as_JSON: function () {
            var json = _super_Order.export_as_JSON.apply(this, arguments);
       
            if (this.payment_journal_id) {
                json.invoice_journal_id = this.payment_journal_id;
            }
                     
            return json;
        },
        

    });
});