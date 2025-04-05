# -*- coding: utf-8 -*-
# from odoo import http


# class LilipinkGiftCardTicket(http.Controller):
#     @http.route('/lilipink_gift_card_ticket/lilipink_gift_card_ticket', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lilipink_gift_card_ticket/lilipink_gift_card_ticket/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('lilipink_gift_card_ticket.listing', {
#             'root': '/lilipink_gift_card_ticket/lilipink_gift_card_ticket',
#             'objects': http.request.env['lilipink_gift_card_ticket.lilipink_gift_card_ticket'].search([]),
#         })

#     @http.route('/lilipink_gift_card_ticket/lilipink_gift_card_ticket/objects/<model("lilipink_gift_card_ticket.lilipink_gift_card_ticket"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lilipink_gift_card_ticket.object', {
#             'object': obj
#         })
