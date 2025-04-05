odoo.define('odoo_multi_connect_sales_aagam.MyCustomAction',  function (require) {
"use strict";
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var rpc = require('web.rpc');
var ActionManager = require('web.ActionManager');
var view_registry = require('web.view_registry');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var session = require('web.session');
var web_client = require('web.web_client');
var _t = core._t;
var QWeb = core.qweb;

var MyCustomAction = AbstractAction.extend({
    template: 'DashboardView',
    cssLibs: [
        '/odoo_multi_connect_sales_aagam/static/css/nv.d3.css'
    ],
    jsLibs: [
//        '/odoo_multi_connect_sales_aagam/static/src/js/lib/d3.min.js',
        '/odoo_multi_connect_sales_aagam/static/src/js/Chart.js',
       
    ],
    events: {
        'click .import-data': 'action_import',
        'click .export-data': 'action_export',
        'click .instance': 'action_instance',
        'click .syncronization':'action_syncronization',
        'click .data-mapping': 'action_mapping',
        'click .configuration': 'action_configuration',
        'click .product': 'action_product',
        'click .total_order': 'action_order',
        'click .total_category': 'action_category',
        'click .total_customer': 'action_customer',

    },
    init: function(parent, context) {
        this._super(parent, context);
        var get_data = [];
        var self = this;

    },
//    willStart: function() {
//        var self = this;
//        return self.fetch_data();
//    },

    start: function() {
        var self = this;
        console.log("============", self)
        self._rpc({
        model: 'woo.comm.channel.sale',
        method: 'search_read',
        }).then(function(result){
            for(var i = 0; i<result.length; i++){
                self.get_data = result[i];
            }
        })
        self.render_dashboards();
        self.render_graphs();
        return this._super();
    },

    render_dashboards: function(value) {
        var self = this;
        var appointment_dashboard = QWeb.render('DashboardView', {
            widget: self,
        });
        rpc.query({
                model: 'woo.comm.channel.sale',
                method: 'search_read',
                args: []
            })
            .then(function (result){
            for(var i = 0; i<result.length; i++){
                var data = result[i];
                console.log("-----data---", data)
                self.$el.find('.total-product').text(data['channel_products'])
                self.$el.find('.total-order').text(data['channel_orders'])
                self.$el.find('.total-category').text(data['channel_categories'])
                self.$el.find('.total-customer').text(data['channel_customers'])
            }

            });


        return appointment_dashboard
    },

    action_import:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Woocommerce Import"),
            type: 'ir.actions.act_window',
            res_model: 'woo.comm.channel.sale',
            res_id: self.get_data['id'],
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form'],[false, 'list']],
            target: 'current'
        },)
    },

   action_export:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Woocommerce Export"),
            type: 'ir.actions.act_window',
            res_model: 'woo.comm.channel.sale',
            res_id: self.get_data['id'],
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form'],[false, 'list']],
            target: 'current'
        },)
    },

    action_instance:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Woocommerce Instance"),
            type: 'ir.actions.act_window',
            res_model: 'woo.comm.channel.sale',
            res_id: self.get_data['id'],
            view_mode: 'kanban',
            view_type: 'kanbam',
            views: [[false, 'kanban'],[false, 'form'],[false, 'list']],
            target: 'current'
        },)
    },

    action_syncronization:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Woocommerce Syncronization"),
            type: 'ir.actions.act_window',
            res_model: 'sync.channel',
            view_mode: 'list',
            view_type: 'list',
            views: [[false, 'list'],[false, 'form']],
            context: {
                        'group_by':['store_selection','action_on'],
                    },
            target: 'current'
        },)
    },

    action_configuration:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Woocommerce Configuration"),
            type: 'ir.actions.act_window',
            res_model: 'res.config.settings',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form'],[false, 'list']],
            target: 'current'
        },)
    },

    action_product:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Products"),
            type: 'ir.actions.act_window',
            res_model: 'template.mapping',
            view_mode: 'list',
            view_type: 'list',
            views: [[false, 'list'],[false, 'form']],

            target: 'current'
        },)
    },

    action_order:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Orders"),
            type: 'ir.actions.act_window',
            res_model: 'order.mapping',
            view_mode: 'list',
            view_type: 'list',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        },)
    },

    action_category:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Categories"),
            type: 'ir.actions.act_window',
            res_model: 'woo.comm.product.category.mapping',
            view_mode: 'list',
            view_type: 'list',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        },)
    },
    action_customer:function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Customers"),
            type: 'ir.actions.act_window',
            res_model: 'partner.mapping',
            view_mode: 'list',
            view_type: 'list',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        },)
    },
    getRandomColor: function () {
        var letters = '0123456789ABCDEF'.split('');
        var color = '#';
        for (var i = 0; i < 6; i++ ) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    },

    render_graphs: function(){
        var self = this;
        self.monthlyappointment();
        self.operation_graph();
        self.operation_export_graph();
    },


    operation_export_graph: function() {
        var self = this;
        var piectx = this.$el.find('#export_data')
        Chart.plugins.register({
          beforeDraw: function(chartInstance) {
            var ctx = chartInstance.chart.ctx;
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, chartInstance.chart.width, chartInstance.chart.height);
          }
        });
        var bg_color_list = []
        for (var i=0;i<=12;i++){
            bg_color_list.push(self.getRandomColor())
        }
        rpc.query({
                model: 'order.mapping',
                method: 'get_export_operation',
            })
            .then(function (result) {
                var import_data = ['Attribute', 'Product','Category'];
                var date_value = [];

                if (result.Category){
                    for(var i = 0; i < import_data.length; i++){
                        import_data[i] == result[import_data[i]]
                        var data_count = result[import_data[i]];
                        if(!data_count){
                                data_count = 0;
                        }
                        date_value[i] = data_count

                    }
                }
                var pieChart = new Chart(piectx, {
                        type: 'pie',
                        data: {
                            datasets: [{
                                data: result.payroll_dataset,
                                backgroundColor: bg_color_list,
                                label: 'Export Count'
                            }],
                            labels:import_data,
                        },
                        options: {
                            responsive: true
                        }
                    });
            });
    },

    operation_graph: function() {
        var self = this;
        var ctx = this.$el.find('#operation_data')
        Chart.plugins.register({
          beforeDraw: function(chartInstance) {
            var ctx = chartInstance.chart.ctx;
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, chartInstance.chart.width, chartInstance.chart.height);
          }
        });
        var bg_color_list = []
        for (var i=0;i<=12;i++){
            bg_color_list.push(self.getRandomColor())
        }
        rpc.query({
                model: 'order.mapping',
                method: 'get_operation',
            })
            .then(function (result) {
                var import_data = ['Category', 'Product','Customer','Order'];
                var date_value = [];

                if (result.Category){
                    for(var i = 0; i < import_data.length; i++){
                        import_data[i] == result[import_data[i]]
                        var data_count = result[import_data[i]];
                        if(!data_count){
                                data_count = 0;
                        }
                        date_value[i] = data_count

                    }
                }
                var myChart = new Chart(ctx, {
                type: 'bar',
                data: {

                    labels: import_data,
                    datasets: [{
                        label: ' Count',
                        data: date_value,
                        backgroundColor: bg_color_list,
                        borderColor: bg_color_list,
                        borderWidth: 1,
                        pointBorderColor: 'white',
                        pointBackgroundColor: 'red',
                        pointRadius: 1,

                        pointHoverRadius: 10,
                        pointHitRadius: 30,
                        pointBorderWidth: 1,
                        pointStyle: 'rectRounded'
                    }]
                },
                options: {
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                                // max: Math.max.apply(null,month_data),
                              }
                        }]
                    },
                    responsive: true,
                    maintainAspectRatio: true,
                    leged: {
                        display: true,
                        labels: {
                            fontColor: 'black'
                        }
                },
            },
        });
            });
    },


    monthlyappointment: function() {
        var self = this;
        var ctx = this.$el.find('#month_sale_order')
        Chart.plugins.register({
          beforeDraw: function(chartInstance) {
            var ctx = chartInstance.chart.ctx;
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, chartInstance.chart.width, chartInstance.chart.height);
          }
        });
        var bg_color_list = []
        for (var i=0;i<=12;i++){
            bg_color_list.push(self.getRandomColor())
        }
        rpc.query({
                model: 'order.mapping',
                method: 'get_month_import_order',
            })
            .then(function (result) {
                var data = result.data
                var months = []
                var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                                'August','September','October','November','December']
                var month_data = [];

                if (data){
                    for(var i = 0; i < months.length; i++){
                        months[i] == data[months[i]]
                        var day_data = months[i];
                        var month_count = data[months[i]];
                        if(!month_count){
                                month_count = 0;
                        }
                        month_data[i] = month_count

                    }
                }
                var myChart = new Chart(ctx, {
                type: 'bar',
                data: {

                    labels: months,
                    datasets: [{
                        label: ' Orders',
                        data: month_data,
                        backgroundColor: bg_color_list,
                        borderColor: bg_color_list,
                        borderWidth: 1,
                        pointBorderColor: 'white',
                        pointBackgroundColor: 'red',
                        pointRadius: 1,

                        pointHoverRadius: 10,
                        pointHitRadius: 30,
                        pointBorderWidth: 1,
                        pointStyle: 'rectRounded'
                    }]
                },
                options: {
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                                max: Math.max.apply(null,month_data),
                              }
                        }]
                    },
                    responsive: true,
                    maintainAspectRatio: true,
                    leged: {
                        display: true,
                        labels: {
                            fontColor: 'black'
                        }
                },
            },
        });
            });
    },


});

core.action_registry.add("woocommerce_dashboard", MyCustomAction);
return MyCustomAction
});