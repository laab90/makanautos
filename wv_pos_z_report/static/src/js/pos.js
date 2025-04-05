odoo.define('wv_pos_z_report', function(require){
    
    const models = require('point_of_sale.models');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const { useState, useRef } = owl.hooks;

    class WVPosSessionReportButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            var self = this;
            const saleDetails = await this.rpc({
                model: 'report.point_of_sale.report_saledetails',
                method: 'get_pos_sale_details2',
                args: [false, false, this.env.pos.config.id],
            });

            const report = this.env.qweb.renderToString(
                'XMLSaleDetailsReport',
                Object.assign({}, saleDetails, {
                    date: new Date().toLocaleString(),
                    pos: this.env.pos,
                })
            );
            if(this.env.pos.config.iface_print_via_proxy){
                const report2 = this.env.qweb.renderToString(
                    'XMLSaleDetailsReport',
                    Object.assign({}, saleDetails, {
                        date: new Date().toLocaleString(),
                        pos: this.env.pos,
                    })
                );
                const printResult = await this.env.pos.proxy.printer.print_receipt(report2);
                if (!printResult.successful) {
                    await this.showPopup('ErrorPopup', {
                        title: printResult.message.title,
                        body: printResult.message.body,
                    });
                }
            }

            await this.showTempScreen('SaleOrderBillScreenWidget',{"report":report});
            
        }
        
    }
    WVPosSessionReportButton.template = 'WVPosSessionReportButton';

    ProductScreen.addControlButton({
        component: WVPosSessionReportButton,
        condition: function() {
            return this.env.pos.config.allow_session_receipt;
        },
    });

    Registries.Component.add(WVPosSessionReportButton);


    const SaleOrderBillScreenWidget = (ReceiptScreen) => {
        class SaleOrderBillScreenWidget extends ReceiptScreen {
            constructor() {
                super(...arguments);
                this.report = arguments[1].report
            }
            mounted() {
            }
            confirm() {
                this.props.resolve({ confirmed: true, payload: null });
                this.trigger('close-temp-screen');
            }
        }
        SaleOrderBillScreenWidget.template = 'SaleOrderBillScreenWidget';
        return SaleOrderBillScreenWidget;
    };

    Registries.Component.addByExtending(SaleOrderBillScreenWidget, ReceiptScreen);
});
