# -*- coding: utf-8 -*-

from odoo import api,fields,models
import logging
_logger	 = logging.getLogger(__name__)
try:
	from woocommerce import API
except ImportError:
	_logger.info('**Please Install Woocommerce Python Api=>(cmd: pip3 install woocommerce)')


class OrderFeed(models.Model):
    _inherit = "order.feed"

    def get_account_tax(self, line_taxes, channel_id):
        if line_taxes:
            line_taxes=eval(line_taxes)
            if line_taxes:
                tax_record=self.env['account.tax']
                tax_mapping_obj= self.env['woo.comm.account.mapping']
                tax_list=[]
                domain=[]
                channel=str(self.channel)
                for tax in line_taxes:
                    flag = 0
                    if "id" in tax:
                        domain=[('channel_id','=',channel_id.id),('store_id','=',str(tax['id']))]
                        tax_rec = channel_id._match_mapping(tax_mapping_obj,domain )
                        if tax_rec:
                            tax_list.append(tax_rec.account_tax_id.id)
                            flag=1
                    if 'rate' in tax:
                        if not tax['rate'] == 0.0 and not flag:
                            domain=[]
                            name=""
                            tax_type="percent"
                            inclusive=False
                            if 'name' in tax:
                                name = tax['name']
                            else:
                                name = str(channel)+"_"+str(channel_id.id)+"_"+str(float(tax['rate']))
                            if 'is_tax_include_in_price' in tax:
                                inclusive=tax['is_tax_include_in_price']
                            if 'type' in tax:
                                tax_type=tax['type']
                                domain += [('tax_type','=',tax['type'])]
                            domain += [('wc_tax_id','=',(tax['rate']))]
                            tax_rec = channel_id._match_mapping(tax_mapping_obj, domain)
                            tax_rate = float(tax['rate'])
                            if tax_rec:

                                tax_list.append(tax_rec.account_tax_id.id)
                            else:
                                tax_dict={
                                'name'            : name,
                                'amount_type'     : tax_type,
                                'price_include'   : inclusive,
                                'amount'          : tax_rate,
                                }
                                tax_id = tax_record.search([('name','=',tax_dict['name'])])
                                if not tax_id:
                                    tax_id=tax_record.create(tax_dict)
                                    tax_map_vals={
                                    'channel_id'      : channel_id.id,
                                    'account_tax_id'        : tax_id.id,
                                    'wc_tax_id' : tax_id.amount,
                                    'tax_type'        : tax_id.amount_type,
                                    'is_tax_include_in_price': tax_id.price_include,
                                    'tax_id'     : tax_id.id,
                                    }
                                    channel_id._create_mapping(tax_mapping_obj,tax_map_vals)
                                tax_list.append(tax_id.id)
                return [(6,0,tax_list)]
        return False