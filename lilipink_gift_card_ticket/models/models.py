# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class lilipink_gift_card_ticket(models.Model):
#     _name = 'lilipink_gift_card_ticket.lilipink_gift_card_ticket'
#     _description = 'lilipink_gift_card_ticket.lilipink_gift_card_ticket'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
