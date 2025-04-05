# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

TYPE_FE = [
    ('FACT', 'Factura'),
    ('FESP', 'Factura Especial'),
    ('FCAM', 'Factura Cambiaria'),
    ('NDEB', 'Nota de Débito'),
    ('NCRE', 'Nota de Crédito'),
    ('NABN', 'Nota de Abono'),
    ('FAEX', 'Factura Exportación'),
    ('OTRO', 'Otro'),
]

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    active_fel = fields.Boolean('Active FEL', default=False)
    fe_type = fields.Selection(TYPE_FE, string='Type')
    fe_establishment_id = fields.Many2one('res.company.establishment', string='Establishment')