# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'
