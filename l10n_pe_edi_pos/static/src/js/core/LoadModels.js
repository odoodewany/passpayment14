odoo.define('l10n_pe_edi_pos.model', function(require) {
    var models = require('point_of_sale.models');
    models.load_fields('res.company', ['street','l10n_pe_edi_ose_id','l10n_pe_edi_send_invoice']);
    models.load_fields('res.partner', ['l10n_latam_identification_type_id']);
    models.load_fields('pos.config', ['default_partner_id','l10n_pe_edi_send_invoice']);
    var rpc = require('web.rpc');
    var core = require('web.core');
    var qweb = core.qweb;
 
    models.load_models([{
        model: 'account.journal',
        fields: ['name','l10n_latam_document_type_id','display_name'],
        domain: function(self) {
            return [
                ['id', 'in', self.config.invoice_journal_ids]
            ]
        },
        loaded: function(self, journals) {
            self.payment_journals = [];
            self.journals = journals;
            self.journal_by_id = {};
            for (var i = 0; i < journals.length; i++) {
                self.journal_by_id[journals[i]['id']] = journals[i];
            }
        },
    },
    {
        model:  'l10n_pe_edi.supplier',
        fields: ['name', 'control_url', 'authorization_message','code'],
        loaded: function(self,suppliers){
            self.suppliers = suppliers;
            self.company.l10n_pe_edi_ose = null;
            for (var i = 0; i < suppliers.length; i++) {
                if (suppliers[i].id === self.company.l10n_pe_edi_ose_id[0]){
                    self.company.l10n_pe_edi_ose = suppliers[i];
                }
            }
        },
    },
    {
        model:  'l10n_latam.identification.type',
        fields: ['name','l10n_pe_vat_code'],
        loaded: function(self,l10n_latam_identification){ 
            self.l10n_latam_identification=l10n_latam_identification;
            self.db.save_l10n_latam_identification(l10n_latam_identification);
           
        }
    },
    {
        model:  'l10n_latam.document.type',
        fields: ['name','code'],
        loaded: function(self,l10n_latam_document){ 
            self.l10n_latam_document=l10n_latam_document;
            self.db.save_l10n_latam_document(l10n_latam_document);
           
        }
    }
    ]);

});