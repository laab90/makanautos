odoo.define('pos_invoice_download.models', function (require) {
    var models = require('point_of_sale.models');
    const { Gui } = require('point_of_sale.Gui');
    var core    = require('web.core');
    var Class = require('web.Class');
    var devices = require('point_of_sale.devices');
    var _t      = core._t;
    var rpc = require('web.rpc');


    var posModelSuper = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({

        push_and_invoice_order: function (order) {
            var self = this;
            return new Promise((resolve, reject) => {
                if (!order.get_client()) {
                    reject({ code: 400, message: 'Missing Customer', data: {} });
                } else {
                    var order_id = self.db.add_order(order.export_as_JSON());
                    self.flush_mutex.exec(async () => {
                        try {
                            const server_ids = await self._flush_orders([self.db.get_order(order_id)], {
                                timeout: 30000,
                                to_invoice: true,
                            });
                            if (server_ids.length) {
                                console.log('*********************push_and_invoice_order********************************')
                                const [orderWithInvoice] = await self.rpc({
                                    method: 'read',
                                    model: 'pos.order',
                                    args: [server_ids, ['account_move']],
                                    kwargs: { load: false },
                                });
                                console.log('*****************[orderWithInvoice]**************')
                                console.log([orderWithInvoice])
                                rpc.query({
                                    model: 'pos.order',
                                    method: 'get_fel',
                                    args: [{'move_id': orderWithInvoice.account_move}],
                                }).then(res => {
                                        //resolveInvoiced(order_server_id);
                                        //resolveDone();
                                        window.location.href = res.url
                                        return res;
                                });
                                await self
                                    .do_action('account.account_invoices', {
                                        additional_context: {
                                            active_ids: [orderWithInvoice.account_move],
                                        },
                                    })
                                    .catch(() => {
                                        reject({ code: 401, message: 'Backend Invoice', data: { order: order } });
                                    });
                            } else {
                                reject({ code: 401, message: 'Backend Invoice', data: { order: order } });
                            }
                            resolve(server_ids);
                        } catch (error) {
                            reject(error);
                        }
                    });
                }
            });
        },

    });

});
