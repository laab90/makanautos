# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('iwesabe_hide_product_cost.group_not_create_res_partner'):
            raise UserError("Usted no tiene permiso para crear nuevos clientes o contactos.")
        return super(Partner, self).create(vals)





