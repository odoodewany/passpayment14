odoo.define('l10n_pe_edi_pos.ElectronicInvoice', function (require) {

    
    const PaymentScreen = require('point_of_sale.PaymentScreen');
const { useListener } = require('web.custom_hooks');
const Registries = require('point_of_sale.Registries');

const PosInvPaymentScreen = (PaymentScreen) =>
    class extends PaymentScreen {
        constructor() {
            super(...arguments);
            // useListener('send-payment-adjust', this._sendPaymentAdjust);
        }

        async _finalizeValidation() {
            var self = this;
            if (this.currentOrder.is_paid_with_cash() && this.env.pos.config.iface_cashdrawer) {
                this.env.pos.proxy.printer.open_cashbox();
            }
            var domain = [['pos_reference', '=', this.currentOrder['name']]]
            var fields = this.currentOrder['name'];

            this.currentOrder.initialize_validation_date();
            this.currentOrder.finalized = true;

            let syncedOrderBackendIds = [];

            try {
                if (this.currentOrder.is_to_invoice()) {
                    syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                        this.currentOrder
                    );
                } else {
                    syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                }
            } catch (error) {
                if (error instanceof Error) {
                    throw error;
                } else {
                    await this._handlePushOrderError(error);
                }
            }
           
            if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                const result = await this._postPushOrderResolve(
                    this.currentOrder,
                    syncedOrderBackendIds
                );
                if (!result) {
                    await this.showPopup('ErrorPopup', {
                        title: 'Error: no internet connection.',
                        body: error,
                    });
                }
            }
            if (this.currentOrder.is_to_invoice() && this.env.pos.config.l10n_pe_edi_send_invoice) {
                this.rpc({
                    model: 'pos.order',
                    method: 'invoice_data',
                    args: [fields],
                })
                .then(function (output) {
                    if (output != false){
                        self.currentOrder.invoice_number = output['invoice_number'] 
                        self.currentOrder.type_of_invoice_document = output['type_of_invoice_document']
                        self.currentOrder.igv_percent = output['igv_percent']
                        self.currentOrder.amount_in_words = output['amount_in_words']
                        self.currentOrder.currency_name = output['currency_name']
                        self.currentOrder.authorization_message = output['authorization_message']
                        self.currentOrder.control_url = output['control_url']
                        self.currentOrder.barcode = output['barcode']
                        self.currentOrder.date_invoice = output['date_invoice']
                        self.currentOrder.invoice_date_due = output['invoice_date_due']
                        self.showScreen(self.nextScreen);
                    }
                        
                })
            }
            else{
                this.showScreen(this.nextScreen);
            }

            // If we succeeded in syncing the current order, and
            // there are still other orders that are left unsynced,
            // we ask the user if he is willing to wait and sync them.
            if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Remaining unsynced orders'),
                    body: this.env._t(
                        'There are unsynced orders. Do you want to sync these orders?'
                    ),
                });
                if (confirmed) {
                    // NOTE: Not yet sure if this should be awaited or not.
                    // If awaited, some operations like changing screen
                    // might not work.
                    this.env.pos.push_orders();
                }
            }
        }
    };

Registries.Component.extend(PaymentScreen, PosInvPaymentScreen);

return PosInvPaymentScreen;
    
        
    
});