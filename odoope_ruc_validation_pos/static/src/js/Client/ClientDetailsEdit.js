odoo.define('odoope_ruc_validation_pos.ClientDetailsEdit', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');

    const RucValidationClientDetailsEdit = (ClientDetailsEdit) =>
        class extends ClientDetailsEdit {
            constructor() {
                super(...arguments);
            }

          
            async Ruc_DniData() {
                let change = this.changes
                if (change.vat || change.l10n_latam_identification_type_id && change.vat){
                    if (!change.l10n_latam_identification_type_id){
                        return this.showPopup('ErrorPopup', {
                            title: _('Select the type of customer identification document and then write the number'),
                        });
                    }
                    var type_doc_model = this.env.pos.db.l10n_latam_identification_by_id[change.l10n_latam_identification_type_id]
                    if (type_doc_model.l10n_pe_vat_code === '6') {
                        if (change.vat.length != 11){
                            return this.showPopup('ErrorPopup', {
                                title: _('The RUC of the client is not valid'),
                            });
                        };
                        if (!this.env.pos.company.l10n_pe_ruc_validation){
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('ALERT'),
                                body: this.env._t(
                                    'DNI validator disabled, register manually.'
                                ),
                            });
                            return false;
                        };
                        let ruc_data = await this.rpc({ 
                            model: 'res.partner',
                            method: 'l10n_pe_ruc_connection',
                            args: [change.vat]
                        })
                        if (ruc_data) {
                            this.props.partner['name'] = ruc_data && ruc_data.business_name;
                            this.props.partner['street'] = ruc_data && ruc_data.residence;
                            // this.props.partner['country_id'] =  this.env.pos.company.country_id ;
                            // this.props.partner['state_id'] = ruc_data.value && ruc_data.value.state_id || this.env.pos.company.state_id ;
                            // add values 
                            this.changes['name'] = ruc_data && ruc_data.business_name;
                            this.changes['street'] = ruc_data && ruc_data.residence;
                            this.changes['country_id'] = ruc_data.value && ruc_data.value.country_id || this.env.pos.company.country_id ;
                            this.changes['state_id'] =  ruc_data.value && ruc_data.value.state_id || this.env.pos.company.state_id ;
                            this.render()
                        }else{
                            alert("NO HAY CONEXIÓN O LOS DATOS NO EXISTEN, POR FAVOR REGISTRE LOS DATOS MANUALMENTE.")
                        }
                    }
                    if (type_doc_model.l10n_pe_vat_code === '1') {
                        if (change.vat.length != 8){
                            return this.showPopup('ErrorPopup', {
                                title: _('The DNI of the client is not valid'),
                            });
                        };
                        
                        if (!this.env.pos.company.l10n_pe_dni_validation){
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('ALERT'),
                                body: this.env._t(
                                    'DNI validator disabled, register manually.'
                                ),
                            });
                            return false;
                        };
                        let dni_data = await this.rpc({ 
                            model: 'res.partner',
                            method: 'l10n_pe_dni_connection',
                            args: [change.vat]
                        })
                        if(dni_data){
                            this.props.partner['name'] = dni_data && dni_data.nombre;
                            this.changes['name'] = dni_data && dni_data.nombre;
                            this.render()
                        } else{
                            alert("NO HAY CONEXIÓN O LOS DATOS NO EXISTEN, POR FAVOR REGISTRE LOS DATOS MANUALMENTE.")
                        }
                    }
                }

                
            }
            captureChange(event) {
                this.changes[event.target.name] = event.target.value;
                this.Ruc_DniData()
            }

        }
    Registries.Component.extend(ClientDetailsEdit, RucValidationClientDetailsEdit);

    return RucValidationClientDetailsEdit;
});
