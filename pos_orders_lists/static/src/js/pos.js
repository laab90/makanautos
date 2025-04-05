odoo.define('pos_orders_lists.pos_orders_lists', function (require) {
"use strict";

	const models = require('point_of_sale.models');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const { useState, useRef } = owl.hooks;
    const { posbus } = require('point_of_sale.utils');
    const { debounce } = owl.utils;

	models.load_models({
	    model: 'pos.order',
	    fields: ['id','pos_reference','date_order','partner_id','amount_total','name','session_id'],
	    domain: function(self){ 
	    	if(self.config.allow_load_orders){
		    	var from = moment(new Date()).subtract(self.config.wv_order_date,'d').format('YYYY-MM-DD')+" 00:00:00";
		    	return [['date_order','>',from],['session_id.config_id','in',self.config.wv_lodad_config]]; 
		    }
		    else{
		    	return [['id','=',0]];
		    }
	    },
	    loaded: function(self,old_order){
	    	console.log("Testing>>>>>>>>>>",old_order);
	    	self.old_order = old_order;
	    },
	});

    class OrderListScreenWidget extends PosComponent {
        constructor() {
            super(...arguments);
            this.state = {
            };
            this.updateClientList = debounce(this.updateClientList, 70);
        }

        back() {
            this.trigger('close-temp-screen');
        }


        get currentOrder() {
            return this.env.pos.get_order();
        }
        perform_search(query){
        var quotations = this.env.pos.old_order;
        var results = [];
            for(var i = 0; i < quotations.length; i++){
                var res = this.search_quotations(query, quotations[i]);
                if(res != false){
                    results.push(res);
                }
            }
            return results;
        }
        search_quotations(query,quotations){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r = re.exec(this._quotations_search_string(quotations));
            if(r){
                var id = Number(r[1]);
                return this.get_quotations_by_id(id);
            }
            return false;
        }
        get_quotations_by_id(id){
            var quotations = this.env.pos.old_order;
            for(var i=0;i<quotations.length;i++){
                if(quotations[i].id == id){
                    return quotations[i];
                }
            }
        }
        _quotations_search_string(quotations){
            var str =  quotations.name;
            if(quotations.partner_id){
                str += '|' + quotations.partner_id[1];
            }
            str = '' + quotations.id + ':' + str.replace(':','') + '\n';
            return str;
         }
        get clients() {
            if (this.state.query && this.state.query.trim() !== '') {
                return this.perform_search(this.state.query.trim());
            } else {
                return this.env.pos.old_order;
            }
        }
        updateClientList(event) {
            this.state.query = event.target.value;
            this.render();
        }

    }
    OrderListScreenWidget.template = 'OrderListScreenWidget';

    Registries.Component.add(OrderListScreenWidget);

    class POSOrderListButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            var self = this;
        	var quotation = this.env.pos.old_order;
        	var available_qt = []
        	for(var i=0;i<quotation.length;i++){
        		available_qt.push(quotation[i].id)
        	}
        	var config_id = self.env.pos.config.id
        	var from = moment(new Date()).subtract(self.env.pos.config.wv_order_date,'d').format('YYYY-MM-DD')+" 00:00:00";

			self.rpc({
                  model: 'pos.order',
                  method: 'search_read',
                  args: [[['date_order','>',from],['session_id.config_id','in',self.env.pos.config.wv_lodad_config],['id','!=',available_qt],['state','!=','done']],['id','name','pos_reference','date_order','partner_id','amount_total','session_id']],
            }).then(function (order) {
				for(var k=0;k<order.length;k++){
					self.env.pos.old_order.push(order[k]);
				}
				self.showTempScreen('OrderListScreenWidget');

            });
            
        }
        
    }
    POSOrderListButton.template = 'POSOrderListButton';

    ProductScreen.addControlButton({
        component: POSOrderListButton,
        condition: function() {
            return this.env.pos.config.allow_load_orders;
        },
    });

    Registries.Component.add(POSOrderListButton);

    class QuotationLine extends PosComponent {
        get_quotations_by_id(id){
             var quotations = this.env.pos.old_order;
             for(var i=0;i<quotations.length;i++){
                 if(quotations[i].id == id){
                     return quotations[i];
                 }
             }
        }
        load_quotation(quotation_id){
            var self = this;
            var quotation = self.get_quotations_by_id(quotation_id);
			self.rpc({
                  model: 'pos.order.line',
                  method: 'search_read',
                  args: [[['order_id','=',quotation_id]],['id','product_id','qty','price_unit','discount','price_subtotal_incl']],
            }).then(function (order_line) {
            	self.showPopup('PosOrderPopupWidget',{'order_line':order_line,'order_id':quotation_id,'order':quotation});
            });
        }
    }
    QuotationLine.template = 'QuotationLine';

    Registries.Component.add(QuotationLine);
    class PosOrderPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ inputValue: this.props.startingValue });
            this.inputRef = useRef('input');
            this.changes = {};
        }


    }
    PosOrderPopupWidget.template = 'PosOrderPopupWidget';
    Registries.Component.add(PosOrderPopupWidget);

  return{
  	PosOrderPopupWidget : PosOrderPopupWidget,
  	OrderListScreenWidget:OrderListScreenWidget,
  };  
});
