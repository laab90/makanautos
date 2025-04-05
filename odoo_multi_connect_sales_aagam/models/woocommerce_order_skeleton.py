# -*- coding: utf-8 -*-
from odoo import fields , models,api
import calendar as cal

class OrderMapping(models.Model):
    _name="order.mapping"
    _inherit = ['woo.comm.channel.mapping']

    odoo_order_id = fields.Integer('Odoo Order ID', required=True)
    order_name = fields.Many2one('sale.order', 'Odoo Order')
    odoo_partner_id = fields.Many2one(related='order_name.partner_id')
    store_order_id =  fields.Char('Store Order ID', required=True)

    def unlink(self):
        for record in self:
            match = record.store_order_id and record.channel_id.match_order_feeds(record.store_order_id)
            if match: match.unlink()
        res = super(OrderMapping, self).unlink()
        return res

    @api.onchange('order_name')
    def change_odoo_id(self):
        self.odoo_order_id = self.order_name.id

    def _compute_name(self):
        for record in self:
            if record.order_name:
                record.name = record.order_name.name
            else:
                record.name = 'Deleted'


    @api.model
    def get_operation(self):
        cr = self._cr

        query = """
        SELECT count(*)  as  count
        from category_feed cf   
        """
                
        cr.execute(query)
        category_data = cr.dictfetchall()
        a_key = "count"
        values_of_category = [a_dict[a_key] for a_dict in category_data]


        query = """
        SELECT count(*)  as  count
        from product_feed pf   
        """
                
        cr.execute(query)
        product_data = cr.dictfetchall()
        a_key = "count"
        values_of_product = [a_dict[a_key] for a_dict in product_data]



        query = """
        SELECT count(*)  as  count
        from partner_feed paf   
        """
                
        cr.execute(query)
        partner_data = cr.dictfetchall()
        a_key = "count"
        values_of_customer = [a_dict[a_key] for a_dict in partner_data]

        query = """
        SELECT count(*)  as  count
        from order_feed cf   
        """
                
        cr.execute(query)
        order_data = cr.dictfetchall()
        a_key = "count"
        values_of_order = [a_dict[a_key] for a_dict in order_data]

        payroll_label = []
        payroll_dataset = []
        import_data = ['Category', 'Product', 'Customer','Order']


        data_set = {}
        data_set.update({
            'Category':values_of_category,
            'Product':values_of_product,
            'Customer':values_of_customer,
            'Order':values_of_order,
            })
        return data_set


    @api.model
    def get_export_operation(self):
        cr = self._cr

        query = """
        SELECT count(*)  as  count
        from category_feed cf   
        """
                
        cr.execute(query)
        category_data = cr.dictfetchall()
        a_key = "count"
        values_of_category = [a_dict[a_key] for a_dict in category_data]


        # query = """
        # SELECT count(*)  as  count
        # from product_feed pf   
        # """
                
        # cr.execute(query)
        # product_data = cr.dictfetchall()
        # a_key = "count"
        # values_of_product = [a_dict[a_key] for a_dict in product_data]



        # query = """
        # SELECT count(*)  as  count
        # from partner_feed paf   
        # """
                
        # cr.execute(query)
        # partner_data = cr.dictfetchall()
        # a_key = "count"
        # values_of_customer = [a_dict[a_key] for a_dict in partner_data]



        # query = """
        # SELECT count(*)  as  count
        # from order_feed cf   
        # """
                
        # cr.execute(query)
        # order_data = cr.dictfetchall()
        # a_key = "count"
        # values_of_order = [a_dict[a_key] for a_dict in order_data]



        # payroll_label = []
        # payroll_dataset = []
        # import_data = ['Category', 'Product', 'Customer','Order']


        data_set = {}
        data_set.update({
            'Category':values_of_category,
            # 'Product':values_of_product,
            # 'Customer':values_of_customer,
            # 'Order':values_of_order,
            })
        return data_set

    @api.model
    def get_month_import_order(self):
        cr = self._cr

        query = """
                    select so.date_order as date_time,sum(amount_total) as sum
                     from sale_order so group by so.date_order,so.state
                     having so.state ='sale'
                     order by so.date_order 

                    """
        cr.execute(query)
        partner_data = cr.dictfetchall()
        partner_day = []
        data_set = {}
        mycount = []
        list_value = []

        dict = {}
        count = 0
        Sum =0

        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                  'August', 'September', 'October', 'November', 'December']

        for data in partner_data:
            if data['date_time']:
                mydate = data['date_time'].month
                for month_idx in range(0, 13):
                    if mydate == month_idx:
                        value = cal.month_name[month_idx]
                        list_value.append(data['sum'])
                        Sum = sum(list_value)
                        dict.update({value:Sum})
                        keys, values = zip(*dict.items())
                        data_set.update({"data": dict})
        return data_set
 
               
