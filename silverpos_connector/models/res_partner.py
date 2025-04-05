# -*- encoding: UTF-8 -*-
##############################################################################
#
# Copyright (C) 2018-Today J2L Tech GT
# (<https://j2ltechgt.odoo.com>)
#
##############################################################################

from odoo import fields, api, models, tools


class ResPartner(models.Model):
    _inherit = "res.partner"

    silverpos_id = fields.Integer('IdSilverPos', required=False, )
ResPartner()

class ProductCateg(models.Model):
    _inherit = "product.category"
    
    silverpos_id = fields.Integer('IdSilverPos', required=False)
    
    # Si quieres agregar un campo company_id a product.category:
    company_id = fields.Many2one('res.company', string='Company')
    
    silverpos_company_id = fields.Integer('Company', compute="_compute_company_id", store=False)

    @api.depends('company_id')
    def _compute_company_id(self):
        for rec in self:
            company_id_value = rec.company_id.id if rec.company_id else False
            rec.silverpos_company_id = company_id_value