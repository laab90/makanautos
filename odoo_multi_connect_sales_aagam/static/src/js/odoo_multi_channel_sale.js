odoo.define('odoo_multi_connect_sales_aagam.update_mapping', function (require) {
"use strict";
console.log("-----------------------")
var FormView = require('web.FormView');
var Dialog = require('web.Dialog');
 FormView.include({

        on_button_save: function(e) {
        console.log("===========")
            var self = this;
            console.log("--0-------seldf",self)
            return self._super.apply(this, arguments).done(function(id){
                var model = self.model;
                var param = {
                        'model': model, 
                        'id': self.datarecord.id ? self.datarecord.id : id
                        };
                self.rpc('/channel/update/mapping', param)
                .done(function(res) {
               
                });
            })
        },
    });

})