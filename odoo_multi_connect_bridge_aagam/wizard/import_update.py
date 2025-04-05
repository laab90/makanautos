# -*- coding: utf-8 -*-

from odoo import fields,api,models 
import logging
_logger = logging.getLogger(__name__)


class ImportOrUpdateProduct(models.TransientModel):
    _name = "import.or.update.product"

    import_update_operation = fields.Selection(
        [
            ('import','Import'),
            ('update','Update')
        ], string="Import/Update Operations", default="import")
    date = fields.Datetime("Date", default=lambda self: fields.datetime.now())
    first_time_import_boolean = fields.Boolean('First Time Import',
                                    help = "If you have large no. of products on your woocommerce  site then enable this It will import product page by page",
                                    default = False)

    def process_data(self):
        if 'active_id' in self._context:
            channel = self.env['woo.comm.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update_operation == 'import':
                    if self.first_time_import_boolean:
                        message = channel.import_woo_comm_all_product()
                    else:
                        channel.import_product_date = self.date
                        message = channel.import_woo_comm_products()
                else:
                    message = channel.update_woo_comm_products()
                return message
            raise Warning("No Channel Id")


class ImportOrUpdateOrder(models.TransientModel):
    _name = "import.or.update.order"

    import_update_operation = fields.Selection(
        [
            ('import','Import'),
            ('update','Update')
        ], string="Import Operations", default="import")
    date = fields.Datetime("Date" , default=lambda self: fields.datetime.now())
    first_time_import_boolean = fields.Boolean('First Time Import', help = "If you have large no. of orders on your woocommerce  site then enable this It will import orders page by page", default = True)

    def process_data(self):
        if 'active_id' in self._context:
            channel = self.env['woo.comm.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update_operation == 'import':
                    if self.first_time_import_boolean:
                        message = channel.import_woo_comm_all_sale_orders()
                    else:
                        channel.import_order_date = self.date
                        message = channel.import_woo_comm_sale_orders()
                else:
                    message = channel.update_woo_comm_sale_order()
                return message
            raise Warning("No Channel Id")


class ImportOrUpdateResPartner(models.TransientModel):
    _name = "import.or.update.res.partner"

    import_update_operation = fields.Selection(
        [
            ('import','Import'),
            ('update','Update')
        ], string="Import Operations", default="import")
    date = fields.Datetime("Date", default=lambda self: fields.datetime.now())
    first_time_import_boolean = fields.Boolean('First Time Import', help="If you have large no. of customers on your woocommerce  site then enable this It will import product page by page",default = False)

    def process_data(self):
        if 'active_id' in self._context:
            channel = self.env['woo.comm.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update_operation == 'import':
                    if self.first_time_import_boolean:
                        message = channel.import_woo_comm_all_res_partner()
                    else:
                        channel.import_customer_date = self.date
                        message = channel.import_woo_comm_res_partner()
                else:
                    channel.update_customer_date = self.date
                    message = channel.update_woo_comm_res_partner()
                return message
            raise Warning("No Channel Id")


class ImportOrUpdateCategory(models.TransientModel):
    _name = "import.or.update.category"

    import_update_operation = fields.Selection(
        [
            ('import','Import'),
            ('update','Update')
        ], string="Import Operations", default="import")

    def process_data(self):
        if 'active_id' in self._context:
            channel = self.env['woo.comm.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update_operation == 'import':
                    message = channel.import_woo_comm_categ()
                else:
                    message = channel.update_woo_comm_categ()
                return message
            raise Warning("No Channel Id")


class ExportOrUpdateCategory(models.TransientModel):
    _name = "export.or.update.category"

    import_update_operation = fields.Selection(
        [
            ('export','Export'),
            ('update','Update')
        ], string="Export Operations", default="export")


    def process_data(self):
        message = ''
        if 'active_id' in self._context:
            channel = self.env['woo.comm.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update_operation == 'export':
                    count = channel.export_woo_comm_categ(0)
                    message += str(count)+" Categories have been exported"
                    return channel.display_message(message)
                else:
                    message = channel.export_woo_comm_updated_categ()
                    return message
            raise Warning("No Channel Id")


class ExportOrUpdateProduct(models.TransientModel):
    _name = "export.or.update.product"

    import_update_operation = fields.Selection(
        [
            ('export','Export'),
            ('update','Update')
        ], string="Export Operations", default="export")

    def process_data(self):
        if 'active_id' in self._context:
            channel = self.env['woo.comm.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update_operation == 'export':
                    message = channel.export_woo_comm_product()
                else:
                    message = channel.export_woo_comm_updated_product()
                return message
            raise Warning("No Channel Id")
