odoo.define('odoope_ruc_validation_pos.ClientListScreen', function (require) {
    'use strict';

    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const Registries = require('point_of_sale.Registries');


    const RucValidationClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
            }         

            activateEditMode(event) {
                super.activateEditMode(event)
                const { isNewClient } = event.detail;
                if (isNewClient) {
                    this.state.editModeProps.partner.name= '';
                    this.state.editModeProps.partner.street= '';
                };
            }

          
        }
    Registries.Component.extend(ClientListScreen, RucValidationClientListScreen);

    return ClientListScreen;
});
