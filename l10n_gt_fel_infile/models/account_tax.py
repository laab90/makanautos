# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.exceptions import UserError, ValidationError

import math
import logging


TYPE_TAX_USE = [
    ('sale', 'Sales'),
    ('purchase', 'Purchases'),
    ('none', 'None'),
]

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    fel_rounding = fields.Float('Redondeo FEL', digits=(12, 6))

ResCurrency()

class AccountTax(models.Model):
    _inherit = 'account.tax'


AccountTax()