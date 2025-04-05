# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime
import calendar
import dateutil.relativedelta


class ReportTrialBalance(models.AbstractModel):
    _name = 'report.l10n_gt_financial_reports.report_trialbalance'
    _description = 'Trial Balance Report'


    def _get_accounts(self, accounts, display_account,docs):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        print(tables, where_clause, where_params)
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
                   " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row
        account_res = []
        account_move = lambda domain : self.env['account.move.line'].search(domain)
        total_credito = total_debito = total_balance = total_saldo = 0.0
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['saldo','credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result:
                date_from = datetime(day=1, month=docs.date_from.month, year=docs.date_from.year)
                date_from = date_from - dateutil.relativedelta.relativedelta(months=1)
                date_to = datetime(day=calendar.monthrange(date_from.year,date_from.month)[1], month=date_from.month, year=date_from.year)
                cuenta = account_move([('account_id','=',account.id),('date','>=',date_from),('date','<=',date_to),('parent_state','=','posted')
                ,('company_id','=',docs.company_id.id),('display_type','=',False),('parent_state','!=','cancel'),('parent_state','!=','line_note'),('display_type','not in',['line_note','line_section'])])
                debito = sum(cuenta.filtered(lambda x: x.debit > 0).mapped('debit'))
                credito = sum(cuenta.filtered(lambda x: x.credit > 0).mapped('credit'))
                res['saldo'] = debito - credito
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = (res['saldo'] + res['debit']) - res['credit'] #account_result[account.id].get('balance')
                total_saldo += res['saldo']
                total_debito += res['debit']
                total_credito += res['credit']
                total_balance += res['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res, total_saldo, total_debito, total_credito, total_balance

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        folio = docs.folio
        display_account = data['form'].get('display_account')
        accounts = docs if model == 'account.account' else self.env['account.account'].search([])
        account_res, total_saldo, total_debito, total_credito, total_balance = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account,docs)
        if data['form']['date_from']:
            data['form']['date_from'] = datetime.strptime(data['form']['date_from'], '%Y-%m-%d').strftime('%d/%m/%Y')
        if data['form']['date_to']:
            data['form']['date_to'] = datetime.strptime(data['form']['date_to'], '%Y-%m-%d').strftime('%d/%m/%Y')
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': account_res,
            'folio': folio,
            'total_saldo': total_saldo,
            'total_debito': total_debito,
            'total_credito': total_credito,
            'total_balance': total_balance,
        }
