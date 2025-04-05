# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

SHORTNAMES = [
    ('IVA', 'IVA'),
    ('ISR', 'ISR'),
    ('PETROLEO', 'PETROLEO'),
    ('TURISMO HOSPEDAJE', 'TURISMO HOSPEDAJE'),
    ('TIMBRE DE PRENSA', 'TIMBRE DE PRENSA'),
    ('BOMBEROS', 'BOMBEROS'),
    ('TASA MUNICIPAL', 'TASA MUNICIPAL'),
    ('BEBIDAS ALCOHOLICAS', 'BEBIDAS ALCOHOLICAS'),
    ('TABACO', 'TABACO'),
    ('CEMENTO', 'CEMENTO'),
    ('BEBIDAS NO ALCOHOLICAS', 'BEBIDAS NO ALCOHOLICAS'),
    ('TARIFA PORTUARIA', 'TARIFA PORTUARIA')
]

class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    shortname = fields.Selection(SHORTNAMES, string='Shortname', default='IVA')
    withhold = fields.Boolean(string='withhold')

    @api.onchange('shortname')
    def _onchange_shortname(self):
        if self.shortname:
            self.name = self.shortname

    def _apply_withholding(self, group_id):
        return self.browse( group_id ).withhold


    