# -*- coding: utf-8 -*-

from odoo import fields, models


class WizardFolioGeneralLedger(models.TransientModel):
    _name = 'wizard.folio.general.ledger'
    _description = 'wizard.folio.general.ledger'

    folio = fields.Integer(string='Folio', required=False, default=1)

    def get_folio(self):
        context = self.env.context
        account_general_ledger = self.env['account.general.ledger']
        holder = account_general_ledger.with_context(is_daily_book=True,folio=self.folio).mayor_book_pdf(context['default_options'])
        return holder