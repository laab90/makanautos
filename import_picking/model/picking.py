# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import Warning, UserError, ValidationError
from odoo import models, fields, exceptions, api, _

import logging
_logger = logging.getLogger(__name__)
import io

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')



class import_pickingss(models.TransientModel):
    _name = "import.picking"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type')
    location_id = fields.Many2one(
        'stock.location', "Source Location Zone",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        required=True,
        )
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location Zone",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        required=True,
        )
    picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')], related='picking_type_id.code')
    import_prod_option = fields.Selection([('barcode', 'Barcode'),('code', 'Code'),('name', 'Name')],string='Import Product By ',default='name')
    file_name = fields.Char()


    sample_option = fields.Selection([('csv', 'CSV'),('xls', 'XLS')],string='Sample Type',default='csv')
    down_samp_file = fields.Boolean(string='Download Sample Files')
    

#
    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        res = {}
        if not self.picking_type_id:
            return res
        self.location_id = self.picking_type_id.default_location_src_id.id
        self.location_dest_id = self.picking_type_id.default_location_dest_id.id
        
    
    def create_picking(self, values):
        picking_obj = self.env['stock.picking']
        picking_search = picking_obj.search([
                                             ('name', '=', values.get('name'))
                                              ])
        if picking_search:
            if picking_search.partner_id.name == values.get('customer'):
                lines = self.make_picking_line(values, picking_search)
                return lines
            else:
                raise UserError(_('Customer name is different for "%s" .\n Please define same.') % values.get('name'))
        else:
            partner_id = self.find_partner(values.get('customer'))

            if values.get('date'):
                pick_date = self._get_date(values.get('date'))
            else:
                pick_date = ''

            pick_id = picking_obj.create({
                                         'name' : values.get('name'),
                                        'partner_id' : partner_id.id,
                                        'scheduled_date' : pick_date,
                                        'picking_type_id': values.get('picking_type_id'),
                                        'location_id':values.get('location_id'),
                                        'location_dest_id':values.get('location_dest_id'),
                                        'origin' : values.get('origin'),
                                        })
            lines = self.make_picking_line(values, pick_id)
            return lines
#            
#            

    
    def make_picking_line(self, values, pick_id):
        product_obj = self.env['product.product']
        stock_move_obj = self.env['stock.move']
        if self.import_prod_option == 'barcode':
            product_id=product_obj.search([('barcode',  '=',values.get('product'))])
        elif self.import_prod_option == 'code':
            product_id=product_obj.search([('default_code', '=',values.get('product'))])
        else:
            product_id=product_obj.search([('name', '=',values.get('product'))])

        if not product_id:
            raise UserError(_('Product is not available "%s".') % values.get('product'))
        
        for product_id in product_id:
            res = stock_move_obj.create({
                    'product_id' : product_id.id,
                    'name':product_id.name,
                    'product_uom_qty' : values.get('quantity'),
                    'picking_id':pick_id.id,
                    'location_id':pick_id.location_id.id,
                    'date':pick_id.scheduled_date,
                    'location_dest_id':pick_id.location_dest_id.id,
                    'product_uom':product_id.uom_id.id
                    })
        return True

    
    def find_partner(self, name):
        partner_obj = self.env['res.partner']
        partner_search = partner_obj.search([('name', '=', name)])
        if partner_search:
            return partner_search
        else:
            partner_id = partner_obj.create({
                                             'name' : name})
            return partner_id
    
    
    def _get_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        try:
            i_date = datetime.strptime(date, DATETIME_FORMAT)
            return i_date
        except Exception:
            raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))

    
    def import_picking(self):
        if not self.file:
            raise UserError(_("Please select a file first then proceed"))
        
        if self.import_option == 'csv': 
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['csv','CSV']:
                raise ValidationError(_('Please upload only csv file.!'))
        
            keys = ['name', 'customer', 'origin', 'date', 'product', 'quantity']	 				
            data = base64.b64decode(self.file)
            file_input = io.StringIO(data.decode("utf-8"))
            file_input.seek(0)
            reader_info = []
            reader = csv.reader(file_input, delimiter=',')
 
            try:
                reader_info.extend(reader)
            except Exception:
                raise UserError(_("Not a valid file!"))
            values = {}
            for i in range(len(reader_info)):
                field = map(str, reader_info[i])
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                            values.update({'picking_type_id':self.picking_type_id.id,
                                    'location_id':self.location_id.id,
                                    'location_dest_id':self.location_dest_id.id})
                            res = self.create_picking(values)
        else:
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['xls','xlsx','XLS','XLSX']:
                raise ValidationError(_('Please upload only xls file.!'))
             
            fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            if not workbook:
                raise UserError(_("Cannot find file"))
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    a1 = int(float(line[3]))
                    a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                    date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                    values.update( {
                                    'name': line[0],
									'customer': line[1],
									'origin':line[2],
                                    'product': line[4],
									'quantity': line[5],
                                    'date': date_string,
                                    'picking_type_id':self.picking_type_id.id,
                                    'location_id':self.location_id.id,
                                    'location_dest_id':self.location_dest_id.id
                                    
						
                                    })
                    res = self.create_picking(values)
                    
                    
    
    
    
    def download_auto(self):
        return {
             'type' : 'ir.actions.act_url',
             'url': '/web/binary/download_document?model=import.picking&id=%s'%(self.sudo().id),
             'target': 'new',
             }
    
    
