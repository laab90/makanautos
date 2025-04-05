# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

MappingModelData = dict(
    template = dict(
        model='template.mapping',
        mapped_name='template_name',
        mapped_id = 'odoo_template_id'
    ),
    product = dict(
        model='product.mapping',
        mapped_name='product_name',
        mapped_id = 'erp_product_id'
    ),
    category = dict(
        model='woo.comm.product.category.mapping',
        mapped_name='product_category_id',
        mapped_id = 'categ_id'
    ),
    attribute = dict(
        model='woo.comm.attribute.mapping',
        mapped_name='product_attribute_id',
        mapped_id = 'attribute_id'
    ),
    attribute_value = dict(
        model='woo.comm.attribute.value.mapping',
        mapped_name='product_attribute_value_id',
        mapped_id = 'attribute_value_id'
    )
)


class ChannelOperation(models.TransientModel):
    _name = "channel.operation"

    set_from_date = fields.Datetime.to_string(fields.Datetime.from_string(fields.Datetime.now())
        + relativedelta(months = -1)
    )
    ax_to_date = fields.Datetime.to_string(
        fields.Datetime.from_string(
            fields.Datetime.now()
        )+ relativedelta(minutes = -5)
    )
    channel_id = fields.Many2one('woo.comm.channel.sale',
        string='Channel',
        required=1,
        domain=[('state','=','validate')]
    )
    channel  = fields.Selection(
        related='channel_id.channel'
    )
    api_record_limit = fields.Integer(
        related='channel_id.api_record_limit'
    )
    import_order_date = fields.Datetime(
        related='channel_id.import_order_date',
        string = 'Order Created After'
    )
    update_order_date = fields.Datetime(
        related='channel_id.update_order_date',
        string = 'Order Updated After'
    )
    import_product_date = fields.Datetime(
        related='channel_id.import_product_date',
        string = 'Product Created After'
    )
    update_product_date = fields.Datetime(
        related='channel_id.update_product_date',
        string = 'Product Updated After'
    )
    import_customer_date = fields.Datetime(
        related='channel_id.import_customer_date',
        string = 'Customer Created After'
    )
    update_customer_date = fields.Datetime(
        related='channel_id.update_customer_date',
        string = 'Customer Updated After'
    )

    from_date = fields.Datetime(
        'From Date',
        default= set_from_date,
        help='From Date'
    )
    to_date = fields.Datetime(
        'To Date',
        default= ax_to_date,
        help='To Date'
    )

    # unused
    @api.model
    def _get_store_selection_domain(self):
        res = []
        if self._context.get('active_model')=='woo.comm.channel.sale':
            if self._context.get('active_id'):
                res+=[('channel_id','=',self._context.get('active_id'))]
        if self._context.get('ax_channel_id'):
            res+=[('channel_id', '=',self._context.get('ax_channel_id'))]
        return res


    @api.model
    def default_get(self,fields):
        res=super(ChannelOperation,self).default_get(fields)
        if not res.get('channel_id') and self._context.get('active_model')=='woo.comm.channel.sale':
            if self._context.get('active_id'):
                res['channel_id']=self._context.get('active_id')
        return res

    # unused
    def _get_channel_obj(self):
        channel_obj = self.env["woo.comm.channel.sale"].browse(
                self._context.get('active_id'))
        return channel_obj


    @api.model
    def post_feed_import_process(self, channel_id, feed_res):
        create_ids,update_ids,map_create_ids,map_update_ids =[],[],[],[]
        create_ids += feed_res.get('create_ids',[])
        update_ids += feed_res.get('update_ids',[])
        context = dict(self._context)
        context['get_mapping_ids'] = 1
        message = ''
        if channel_id.auto_evaluate_feed:
            for feed_id in (create_ids+update_ids):
                try:
                    mapping_res = feed_id.with_context(context).import_items()
                    map_create_ids += mapping_res.get('create_ids')
                    map_update_ids += mapping_res.get('update_ids')
                except Exception as e:
                    _logger.info("==%r=post_feed_import_process==="%(e))
                    message += '%s'%(e)

        return dict(
            create_ids=create_ids,
            update_ids=update_ids,
            map_create_ids=map_create_ids,
            map_update_ids=map_update_ids,
            message=message,
        )

    # unused
    @api.model
    def exclude_export_data(self,object_ids,channel_id,operation,model='template',domain=[]):
        ex_update_ids=[]
        ex_create_ids=[]

        domain = domain or []
        match=[]
        model_data = MappingModelData.get(model)
        mapping_obj = self.env[model_data.get('model')]
        domain+=[(model_data.get('mapped_id'), 'in',object_ids.ids)]
        mapped=model_data.get('mapped_name')
        if mapped:
            match = channel_id._match_mapping(mapping_obj,domain).mapped(mapped)
        if operation =='export':
            ex_create_ids += match
            object_ids = object_ids.filtered(lambda obj:obj not in match )
        else:
            ex_update_ids += list(set(object_ids)-set(match))
            object_ids = match
        return dict(
            ex_update_ids=ex_update_ids,
            ex_create_ids=ex_create_ids,
            object_ids=object_ids,
        )

    # unused
    @staticmethod
    def export_message(ex_create_ids=[],ex_update_ids=[],create_ids=[],update_ids=[]):
        message=''
        if len(ex_create_ids):
           message += '<br/> Total %s  product template are already exported .'%(len(ex_create_ids))
        if len(ex_update_ids):
           message += '<br/> Total %s  product template not updated because there mapping not exits .'%(len(ex_update_ids))
        if len(create_ids):
           message += '<br/> Total %s  product template exported.'%(len(create_ids))
        if len(update_ids):
           message += '<br/> Total %s  product template updated.' %(len(update_ids))
        return message


class ImportOperation(models.TransientModel):
    _inherit = ['channel.operation']
    _name = "import.operation"

    operation = fields.Selection(
        [
            ('import', "Import"),
            ('update', 'Update')
        ],
        default='import',
        required=1
    )


class ExportOperation(models.TransientModel):
    _inherit = ['channel.operation']
    _name = "export.operation"

    operation = fields.Selection(
        [
            ('export', 'Export'),
            ('update', 'Update')
        ],
        default='export',
        required=1
    )
