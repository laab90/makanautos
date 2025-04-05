# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    type_document = fields.Selection([
                                    ('CUI', 'Con DPI'),
                                    ('EXT', 'Con Pasaporte'),
                                    ('NIT', 'Con NIT')], string='Documento', default='NIT')