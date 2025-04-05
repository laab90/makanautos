# -*- coding: utf-8 -*-
from odoo import api, models, fields
from datetime import datetime, timedelta
from dateutil import tz

class ReportDailyGeneralLedger(models.AbstractModel):
    _name = 'report.l10n_gt_financial_reports.daily_general_ledger_tmp'
    _description = 'Report Daily General Ledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        #Para asegurarme de que si lo imprima procuro que docs tenga al menos un documento
        docs = self.env["account.move"].browse(data["docids"])

        return {
            'doc_ids': data["docids"],
            'doc_model': "account.move",
            "docs": docs,
            'lines': data["data"],
            "company": self.env.company,
            "currency_id": self.env.company.currency_id,
            "period_dates": {"from": data["date_from"], "to": data["date_to"]}
        }
