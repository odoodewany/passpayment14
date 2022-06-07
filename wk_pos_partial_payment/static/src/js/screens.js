/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

odoo.define('wk_pos_partial_payment.screens', function (require) {
    "use strict";

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var _t = core._t;

    const PosResPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            mounted(){
                super.mounted();
                var order = this.env.pos.get_order();
                if(order && order.get_total_with_tax() > 0)
                    $('.partial-payment-remark').show();
                else
                    $('.partial-payment-remark').hide();
                this.check_partial_payment_criteria();
            }
            focus_in_description(event){
                var self = this;
                $('body').off('keypress', self.keyboard_handler);
                $('body').off('keydown', self.keyboard_keydown_handler);
            }
            focus_out_description(event){
                var self = this;
                $('body').on('keypress', self.keyboard_handler);
                $('body').on('keydown', self.keyboard_keydown_handler);
            }
            keyup_description(event){
                this.check_partial_payment_criteria();
            }
            check_partial_payment_criteria(){
                var self = this;
                var $elvalidate = $('.next');
                var order = self.env.pos.get_order();
                var client = order.get_client();
                if(!self.env.pos.config.partial_payment)
                    $elvalidate.removeClass('highlight');
                else if(client != null && order.get_due()>0 && order.is_to_invoice() && $('#partial_payment_description').val()!=''){
                    if(client.property_payment_term_id && !client.prevent_partial_payment)
                        $elvalidate.addClass('highlight');
                    else
                        $elvalidate.removeClass('highlight');
                }
                else if(order.is_to_invoice() && $('#partial_payment_description').val()=='')
                    $elvalidate.removeClass('highlight');
                else if(order.get_due() != 0)
                    $elvalidate.removeClass('highlight');
                else if(order.get_due() == 0 && order.get_total_with_tax() != 0)
                    $elvalidate.addClass('highlight');
            }
            click_invoice(){
                this._super();
                this.check_partial_payment_criteria();
            }
            // validate_order(force_validation) {
            async validateOrder(isForceValidate) {
                var self = this;
                var order = self.env.pos.get_order();
                if (!self.env.pos.config.partial_payment)
                    super.validateOrder(isForceValidate);
                else{
                    console.log("is insideddddddddddddddddddddddd",$('#partial_payment_description').val(),this._isOrderValid(isForceValidate))
                    order.invoice_remark = $('#partial_payment_description').val();
                    if (order.get_orderlines().length === 0) {

                        this.showPopup('ErrorPopup',{
                            'title': _t('Empty Order'),
                            'body':  _t('There must be at least one product in your order before it can be validated'),
                        });
                        return false;
                    }
                    else if (!await self._isOrderValid(isForceValidate)) {
                        console.log("si insided")
                        if(!order.is_paid() && !order.is_to_invoice()){
                            self.showPopup('WkPPAlertPopUp',{
                                'title': _t('Cannot Validate This Order!!!'),
                                'body':  _t("You need to set Invoice for validating Partial Payments."),
                            });
                            return;
                        }if (order.is_to_invoice()) {
                            if(order.get_client() != null && order.get_due()>0){
                                if(order.get_client().prevent_partial_payment){
                                    self.showPopup('WkPPAlertPopUp',{
                                        'title': _t('Cannot Validate This Order!!!'),
                                        'body':  _t("Customer's Payment Term does not allow Partial Payments."),
                                    });
                                    return false;
                                }
                            }if($('#partial_payment_description').val()==''){
                                $("#partial_payment_description").css("background-color","burlywood");
                                setTimeout(function(){
                                    $("#partial_payment_description").css("background-color","");
                                },100);
                                setTimeout(function(){
                                    $("#partial_payment_description").css("background-color","burlywood");
                                },200);
                                setTimeout(function(){
                                    $("#partial_payment_description").css("background-color","");
                                },300);
                                setTimeout(function(){
                                    $("#partial_payment_description").css("background-color","burlywood");
                                },400);
                                setTimeout(function(){
                                    $("#partial_payment_description").css("background-color","");
                                },500);
                                return;
                            }
                        }
                        order.is_partially_paid = true;
                        await this._finalizeValidation();
                // super.validateOrder(isForceValidate);
                    // this.finalize_validation();
                    }else
                        await this._finalizeValidation();
                // super.validateOrder(isForceValidate);
                    // this.finalize_validation();
                }
            }
    
        }
    Registries.Component.extend(PaymentScreen, PosResPaymentScreen);

    return PaymentScreen;


    // screens.PaymentScreenWidget.include({
    //     events : _.extend({}, screens.PaymentScreenWidget.prototype.events, {
    //         'focusin #partial_payment_description': 'focus_in_description',
    //         'focusout #partial_payment_description': 'focus_out_description',
    //         'keyup #partial_payment_description': 'keyup_description',
    //     }),
    //     show: function(){
    //         this._super();
    //         var order = this.env.pos.get_order();
    //         if(order && order.get_total_with_tax() > 0)
    //             $('.partial-payment-remark').show();
    //         else
    //             $('.partial-payment-remark').hide();
    //         this.check_partial_payment_criteria();
        // },
        // focus_in_description: function(event){
        //     var self = this;
        //     $('body').off('keypress', self.keyboard_handler);
        //     $('body').off('keydown', self.keyboard_keydown_handler);
        // },
        // focus_out_description: function(event){
        //     var self = this;
        //     $('body').on('keypress', self.keyboard_handler);
        //     $('body').on('keydown', self.keyboard_keydown_handler);
        // },
        // keyup_description: function(event){
        //     this.check_partial_payment_criteria();
        // },
        // check_partial_payment_criteria: function(){
        //     var self = this;
        //     var $elvalidate = $('.next');
        //     var order = self.env.pos.get_order();
        //     var client = order.get_client();
        //     if(!self.env.pos.config.partial_payment)
        //         $elvalidate.removeClass('highlight');
        //     else if(client != null && order.get_due()>0 && order.is_to_invoice() && $('#partial_payment_description').val()!=''){
        //         if(client.property_payment_term_id && !client.prevent_partial_payment)
        //             $elvalidate.addClass('highlight');
        //         else
        //             $elvalidate.removeClass('highlight');
        //     }
        //     else if(order.is_to_invoice() && $('#partial_payment_description').val()=='')
        //         $elvalidate.removeClass('highlight');
        //     else if(order.get_due() != 0)
        //         $elvalidate.removeClass('highlight');
        //     else if(order.get_due() == 0 && order.get_total_with_tax() != 0)
        //         $elvalidate.addClass('highlight');
        // },
        // click_invoice: function(){
        //     this._super();
        //     this.check_partial_payment_criteria();
        // },
        // validate_order: function(force_validation) {
        //     var self = this;
        //     var order = self.env.pos.get_order();
        //     if (!self.env.pos.config.partial_payment)
        //         super.validateOrder(isForceValidate);
        //     else{
        //         order.invoice_remark = $('#partial_payment_description').val();
        //         if (order.get_orderlines().length === 0) {
        //             this.showPopup('error',{
        //                 'title': _t('Empty Order'),
        //                 'body':  _t('There must be at least one product in your order before it can be validated'),
        //             });
        //             return false;
        //         }
        //         else if (!this.order_is_valid(force_validation)) {
        //             if(!order.is_paid() && !order.is_to_invoice()){
        //                 self.showPopup('partial_payment_block',{
        //                     'title': _t('Cannot Validate This Order!!!'),
        //                     'body':  _t("You need to set Invoice for validating Partial Payments."),
        //                 });
        //                 return;
        //             }if (order.is_to_invoice()) {
        //                 if(order.get_client() != null && order.get_due()>0){
        //                     if(order.get_client().prevent_partial_payment){
        //                         self.showPopup('partial_payment_block',{
        //                             'title': _t('Cannot Validate This Order!!!'),
        //                             'body':  _t("Customer's Payment Term does not allow Partial Payments."),
        //                         });
        //                         return false;
        //                     }
        //                 }if($('#partial_payment_description').val()==''){
        //                     $("#partial_payment_description").css("background-color","burlywood");
        //                     setTimeout(function(){
        //                         $("#partial_payment_description").css("background-color","");
        //                     },100);
        //                     setTimeout(function(){
        //                         $("#partial_payment_description").css("background-color","burlywood");
        //                     },200);
        //                     setTimeout(function(){
        //                         $("#partial_payment_description").css("background-color","");
        //                     },300);
        //                     setTimeout(function(){
        //                         $("#partial_payment_description").css("background-color","burlywood");
        //                     },400);
        //                     setTimeout(function(){
        //                         $("#partial_payment_description").css("background-color","");
        //                     },500);
        //                     return;
        //                 }
        //             }
        //             order.is_partially_paid = true;
        //             this.finalize_validation();
        //         }else
        //             this.finalize_validation();
        //     }
        // },
    // });
        });
