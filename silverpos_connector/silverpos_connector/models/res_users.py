# -*- encoding: UTF-8 -*-
##############################################################################
#
# Copyright (C) 2018-Today J2L Tech GT
# (<https://j2ltechgt.odoo.com>)
#
##############################################################################

from odoo import fields, api, models, tools


class ResUsers(models.Model):
    _inherit = "res.users"

    silverpos_id = fields.Integer('IdSilverPos', required=False, )

ResUsers()