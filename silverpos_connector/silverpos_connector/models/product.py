# -*- encoding: UTF-8 -*-
##############################################################################
#
# Copyright (C) 2018-Today J2L Tech GT
# (<https://j2ltechgt.odoo.com>)
#
##############################################################################

from odoo import fields, api, models, tools


class ProductTemplate(models.Model):
    _inherit = "product.template"

    silverpos_id = fields.Integer('IdSilverPos', required=False, )
    silverpos_company_id = fields.Integer('Company', compute="_compute_company_id", store=False)

    @api.depends('company_id')
    def _compute_company_id(self):
        company_id = False
        for rec in self:
            if rec.company_id:
                company_id = rec.company_id.id
            rec.update({
                'silverpos_company_id': company_id,
            }) 
ProductTemplate()