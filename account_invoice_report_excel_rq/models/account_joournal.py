# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

from dateutil import rrule

class AccountJournal(models.Model):
    _inherit = "account.journal"

    resolution_ids = fields.One2many('account.document.resolution', 'journal_id', string="Resoluciones")
    cai = fields.Char('CAI', compute="_compute_resolution")
    prefix = fields.Char('Prefijo', compute="_compute_resolution")
    serie = fields.Char('Serie', compute="_compute_resolution")
    counter_start = fields.Integer('Inicio', compute="_compute_resolution")
    counter_finish = fields.Integer('Final', compute="_compute_resolution")
    date_due = fields.Date('Fecha Vencimiento', compute="_compute_resolution")


    @api.depends(
        'resolution_ids.name', 
        'resolution_ids.prefix', 
        'resolution_ids.serie', 
        'resolution_ids.counter_start', 
        'resolution_ids.counter_finish',
        'resolution_ids.date_due')
    def _compute_resolution(self):
        for rec in self:
            cai = ""
            prefix = ""
            serie = ""
            date_due =""
            start = finish = 0
            for res in rec.resolution_ids.filtered(lambda x: x.active == True):
                cai = res.name
                prefix = res.prefix
                serie = res.serie
                start = res.counter_start
                finish = res.counter_finish
                date_due = res.date_due
            rec.update({
                'cai': cai,
                'prefix': prefix,
                'serie': serie,
                'counter_start': start,
                'counter_finish': finish,
                'date_due': date_due,
            })

    @api.constrains('resolution_ids.active', 'resolution_ids.active')
    def _check_resolution_active(self):
        for rec in self:
            res_ids = self.env['account.document.resolution'].search([('journal_id', '=', rec.id), ('active', '=', True)])
            if res_ids and len(res_ids.ids) > 0:
                raise UserError(("Ya existe %s resolución(es) activa(s)") %(len(res_ids.ids)))

AccountJournal()

class AccountDocumentResolution(models.Model):
    _name = "account.document.resolution"

    journal_id = fields.Many2one('account.journal', 'Diario', ondelete="cascade")
    sequence = fields.Integer('Secuancia', default=10)
    name = fields.Char('CAI', required=True, copy=False)
    date_authorization = fields.Date('Fecha Autorizacion', required=True, copy=False)
    date_due = fields.Date('Fecha Vencimiento', required=True, copy=False)
    prefix = fields.Char('Prefijo')
    serie = fields.Char('Serie')
    counter_start = fields.Integer('Inicio', required=True)
    counter_finish = fields.Integer('Final', required=True)
    active = fields.Boolean('Activo', default=True)

AccountDocumentResolution()