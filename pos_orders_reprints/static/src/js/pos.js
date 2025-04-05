odoo.define('pos_orders_reprints.pos_orders_reprints', function (require) {
"use strict";

    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    const pos_orders = require('pos_orders_lists.pos_orders_lists');
    const PosOrderPopupWidget = pos_orders.PosOrderPopupWidget;
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');


     const RePrintBillScreenWidget = (ReceiptScreen) => {
        class RePrintBillScreenWidget extends ReceiptScreen {
            mounted() {
            }
            constructor() {
                super(...arguments);
                this.report = arguments[1].report
            }
            confirm() {
                this.props.resolve({ confirmed: true, payload: null });
                this.trigger('close-temp-screen');
            }
        }
        RePrintBillScreenWidget.template = 'RePrintBillScreenWidget';
        return RePrintBillScreenWidget;
    };

    Registries.Component.addByExtending(RePrintBillScreenWidget, ReceiptScreen);

    const PosOrderPopupWidget2 = (PosOrderPopupWidget) =>
    class extends PosOrderPopupWidget {
        print_normal_printer(order_id){
            var self = this;
            this.rpc({
                model: 'pos.config',
                method: 'get_order_detail',
                args: [order_id],
            }).then(function (result) {
                var order = self.env.pos.get_order();
                var order = {
                        widget:self.env,
                        order: result.order,
                        change: result.change,
                        orderlines: result.order_line,
                        discount_total: result.discount,
                        paymentlines: result.payment_lines,
                        receipt: order.export_for_printing(),
                    }
                    const report = self.env.qweb.renderToString(
                        'PosTicketReprint',order);
                    self.showTempScreen('RePrintBillScreenWidget',{"report":report});
                    self.trigger('close-popup');
            });
            
        }
        print_thermal_printer(order_id){
            var self = this;
            this.rpc({
                model: 'pos.config',
                method: 'get_order_detail',
                args: [order_id],
            }).then(function (result) {
                var order = self.env.pos.get_order();
                var order = {
                        widget:self.env,
                        order: result.order,
                        change: result.change,
                        orderlines: result.order_line,
                        discount_total: result.discount,
                        paymentlines: result.payment_lines,
                        receipt: order.export_for_printing(),
                    }
                    const report = self.env.qweb.renderToString(
                        'PosTicketReprint',order);
                   self.env.pos.proxy.printer.print_receipt(report);
                    
                    self.trigger('close-popup');
            });
            
        }

    }
    Registries.Component.extend(PosOrderPopupWidget, PosOrderPopupWidget2);

});
