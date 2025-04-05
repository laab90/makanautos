# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_duplicate_avoid = fields.Boolean("Avoid Duplicity (Default Code/ Barcode)")
    avoid_duplication_selection = fields.Selection(
        [
            ('barcode', 'Barcode/UPC/EAN/ISBN'),
            ('default_code', 'Default Code/SKU'),
            ('both', 'Both')
        ],
        string="Avoid Duplication With",
        default='both')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.default'].sudo().set('res.config.settings', 'is_duplicate_avoid', self.is_duplicate_avoid)
        self.env['ir.default'].sudo().set('res.config.settings', 'avoid_duplication_selection', self.avoid_duplication_selection)
        return True

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            {
                'is_duplicate_avoid': self.env['ir.default'].sudo().get('res.config.settings', 'is_duplicate_avoid'),
                'avoid_duplication_selection': self.env['ir.default'].sudo().get('res.config.settings', 'avoid_duplication_selection' or 'both')
            }
        )
        return res
