odoo.define('pw_pos_auto_invoice.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const PosAutoInvoice = PaymentScreen =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
                if (this.env.pos.config.is_auto_invoice && this.env.pos.config.module_account) {
                    this.currentOrder.set_to_invoice(!this.currentOrder.is_to_invoice());
                    this.render();
                }
            }
        };

    Registries.Component.extend(PaymentScreen, PosAutoInvoice);

    return PaymentScreen;
});
