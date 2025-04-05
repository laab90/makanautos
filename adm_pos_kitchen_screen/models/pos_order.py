from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

class PosOrder(models.Model):

    _inherit = "pos.order"
    
    start_date = fields.Datetime(string="Start date")
    end_date = fields.Datetime(string="End date")
    kitchen_state = fields.Char(compute="compute_kitchen_state", store=True, default="pending")

    @api.depends('lines.kitchen_state')
    def compute_kitchen_state(self):
        for order in self:
            order.kitchen_state = 'pending'
            if len(order.lines.filtered(lambda r: r.kitchen_state == 'in_progress')) > 0:
                order.kitchen_state = 'in_progress'
            if len(order.lines.filtered(lambda r: r.kitchen_state == 'done')) == len(order.lines):
                order.kitchen_state = 'done'

class PosOrderLine(models.Model):

    _inherit = "pos.order.line"
    
    start_date = fields.Datetime(string="Start date")
    end_date = fields.Datetime(string="End date")
    avg_completion_time = fields.Integer(related="product_id.avg_completion_time", string="Avg completion time")
    completion_time = fields.Integer(string="Completion time", compute="compute_kitchen_state", store=True)
    kitchen_state = fields.Selection(compute="compute_kitchen_state", store=True, selection=[('pending', 'Pending'), ('in_progress', 'In progres'), ('done', 'Done')], default="pending")

    @api.depends('start_date', 'end_date')
    def compute_kitchen_state(self):
        for line in self:
            line.kitchen_state = 'pending'
            if line.start_date:
                line.kitchen_state = 'in_progress'
            if line.end_date:
                line.kitchen_state = 'done'
            if line.start_date and line.end_date:
                time_delta = (line.end_date - line.start_date)
                total_seconds = time_delta.total_seconds()
                line.completion_time = total_seconds/60

    def write(self, values):
        result = super(PosOrderLine, self).write(values)
        if 'end_date' in values:
            for line in self:
                self.env.cr.execute('SELECT AVG(completion_time) FROM pos_order_line WHERE completion_time != 0 and product_id = %s' %(line.product_id.id))
                result = self._cr.fetchone()
                line.product_id.write({'avg_completion_time': result[0]})