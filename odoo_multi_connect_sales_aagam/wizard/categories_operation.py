# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class ImportCategories(models.TransientModel):
    _inherit = ['import.operation']
    _name = "import.categories"

    category_ids = fields.Text('Categories ID(s)')
    parent_categ_id = fields.Many2one('woo.comm.product.category.mapping', 'Parent Category')

class ExportCategories(models.TransientModel):
    _inherit = ['export.operation']
    _name = "export.categories"

    @api.model
    def default_get(self,fields):
        res = super(ExportCategories,self).default_get(fields)
        if not res.get('category_ids') and self._context.get('active_model')=='product.category':
            res['category_ids'] = self._context.get('active_ids')
        return res

    category_ids = fields.Many2many('product.category', 'Category')
