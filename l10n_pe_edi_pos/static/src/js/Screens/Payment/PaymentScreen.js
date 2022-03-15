odoo.define('l10n_pe_edi_pos.PaymentScreen', function (require) {
    "use strict";
    
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const {useListener} = require('web.custom_hooks');
    const {useState} = owl.hooks;

    const L10nPEPosPaymentScreen = PaymentScreen =>
    class extends PaymentScreen {
        constructor() {
            super(...arguments);
            useListener('click-journal', this.setJournal);
            if(this.env.pos.config.auto_check_invoice){
                this.currentOrder.set_to_invoice(true);
                // if (this.currentOrder.payment_journal_id){
                //     this.currentOrder.set_to_invoice(true);
                // }
            }
        }
        setJournal(event) {
            let selectedOrder = this.currentOrder;
            selectedOrder.payment_journal_id = event.detail.id
            selectedOrder.trigger('change', selectedOrder);
        }

        async _isOrderValid() {
            
            if (this.currentOrder && this.env.pos.config.l10n_pe_edi_send_invoice ) {
                let client = this.currentOrder.get_client();
                let order = this.currentOrder;
                let type_document ;
                _.each(order.pos.journals, function(doc) {
                    if (order.payment_journal_id == doc.id ){
                        type_document = doc.l10n_latam_document_type_id[0]
                    }
                })
                if (!type_document){
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('ALERT'),
                        body: this.env._t(
                            'Please select a Document type.'
                        ),
                    });
                    return false;
                }

                // if (type_document){
              
                var type_document_model = this.env.pos.db.l10n_latam_document_by_id[type_document]
                if (client){
                    var type_identification =client.l10n_latam_identification_type_id[0];
                    if (!type_identification){
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('ALERT'),
                            body: this.env._t(
                                'Select the Identification type of the client: ' + client['name']
                            ),
                        });
                        return false;
                        
                    }
                    var type_identification_model = this.env.pos.db.l10n_latam_identification_by_id[type_identification]
                    if (type_document_model.code == "03"){
                        if(type_identification_model.l10n_pe_vat_code == '1'){
                            if (client['vat'].length != 8){
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('ALERT'),
                                    body: this.env._t("The DNI of the client: ") + client['name'] + this.env._t(', is not valid.'),
                                });
                                return false;
                            } 
                        }
                        if(type_identification_model.l10n_pe_vat_code == '6'){
                            if (client['vat'].length != 11){
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('ALERT'),
                                    body: this.env._t("The RUC  of the client: ") + client['name'] + this.env._t(', is not valid.'),
                                });
                                return false;
                            }
                            
                        }
                        
                    }
                    if (type_document_model.code == "01"){
                        if(type_identification_model.l10n_pe_vat_code != '6'){
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('ALERT'),
                                body: this.env._t('The document type \'Factura\' is valid only for clients with valid RUC.'),
                            });
                            return false;
                            
                        }
                        else{
                            if (client['vat'].length != 11){
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('ALERT'),
                                    body: this.env._t('The RUC of the client: ') + client['name'] + this.env._t(', is not valid.'),
                                });
                                return false;
                            }
                        }
                        
                    } 
                }

                // }
            }
            const isValid = await super._isOrderValid()
            return  isValid
        }
        
    }
    Registries.Component.extend(PaymentScreen, L10nPEPosPaymentScreen);

    return PaymentScreen;

   });