# -*- coding: utf-8 -*-
import time
from datetime import datetime
from dateutil import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import time
import xlwt
import base64
from io import BytesIO


class WizardFinancialReports(models.TransientModel):
    _name = 'wizard.financial.reports'
    _description = "Wizard Financial Reports"

    
    #General Fields for all financial reports
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
    journal_ids = fields.Many2many('account.journal', 'rel_wizar_account_journal', 'wizard_id', 'account_journal_id', 'Journals', required=True)
    date_from = fields.Date('Date From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date To', required=True, default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    type_book = fields.Selection([
        ('journal_ledger', 'Journal Ledger'),
        ('general_ledger', 'General Ledger'),
        ('trial_balance', 'Trial Balance')], string="Financial Report Type", required=True, default="journal_ledger", readonly=True)
    type_report = fields.Selection([
        ('pdf', 'PDF'),
        ('xls', 'XLS')],string="Report Type", required=True, default="pdf")
    type_entries = fields.Selection([
        ('posted', 'Only Posted'),
        ('all', 'All')], string='Type Entries', default='posted')
    page_number = fields.Integer('Folio', required=False, default=1)

    def generate_journal_entries(self, domain=None):
        if domain:
            moves = []
            lines = []
            total_debit = total_credit = 0.0
            moves_ids = self.env['account.move'].search(domain, order='date asc')
            for move in moves_ids:
                lines = []
                res = {
                    'name': move.name,
                    'date': move.date.strftime("%d/%m/%Y"),
                    'lines': [],
                }
                for line in move.line_ids.sorted(key=lambda l: l.debit > 0.00):
                    line_res = {
                        'account_code': line.account_id.code,
                        'account_name': line.account_id.name,
                        'debit': line.debit or 0.00,
                        'credit': line.credit or 0.00,
                    }
                    lines.append(line_res)
                    total_debit += line.debit or 0.00
                    total_credit += line.credit or 0.00
                if lines:
                    res.update({
                        'lines': lines,
                    })
                    moves.append(res)
            return moves, total_debit, total_credit
    
    def print_journal_ledger(self):
        self.ensure_one()
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('company_id', '=', self.company_id.id)]
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        if self.type_entries == 'posted':
            domain.append(('state', '=', 'posted'))
        if self.type_entries == 'all':
            domain.append(('state', 'in', ('draf', 'posted', 'cancel')))
        values, total_debit, total_credit = self.generate_journal_entries(domain=domain)
        datas = {
            'values': values,
            'company': self.company_id.id,
            'company_name': self.company_id.name,
            'company_vat': self.company_id.vat,
            'report': 'LIBRO DIARIO',
            'dates': (("PERIODO: DEL %s AL %s") %(self.date_from.strftime("%d/%m/%Y"), self.date_to.strftime("%d/%m/%Y"))),
            'folio': self.page_number,
            'total_debit': total_debit,
            'total_credit': total_credit,
        }
        return self.env.ref('l10n_gt_financial_reports.report_journal_ledger_book').report_action(self, data=datas)

WizardFinancialReports()