# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from uuid import uuid4
import pytz

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        _logger.info('****************_prepare_invoice_vals()**********************')
        _logger.info(res)
        move_type = res.get('move_type', False)
        if move_type and move_type == 'out_refund':
            reversed_entry_id = self.mapped('lines.refunded_orderline_id.order_id')
            _logger.info('****************reversed_entry_id()**********************')
            _logger.info(reversed_entry_id)
            res.update({
                'journal_id': self.session_id.config_id.credit_note_journal_id.id,
                'reversed_entry_id': reversed_entry_id[0].account_move.id if reversed_entry_id and len(reversed_entry_id.ids) else False
            })
        _logger.info('****************last _prepare_invoice_vals()**********************')
        _logger.info(res)
        return res

PosOrder()