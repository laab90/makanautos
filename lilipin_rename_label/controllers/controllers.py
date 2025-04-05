# -*- coding: utf-8 -*-
# from odoo import http


# class LilipinRenameLabel(http.Controller):
#     @http.route('/lilipin_rename_label/lilipin_rename_label', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lilipin_rename_label/lilipin_rename_label/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('lilipin_rename_label.listing', {
#             'root': '/lilipin_rename_label/lilipin_rename_label',
#             'objects': http.request.env['lilipin_rename_label.lilipin_rename_label'].search([]),
#         })

#     @http.route('/lilipin_rename_label/lilipin_rename_label/objects/<model("lilipin_rename_label.lilipin_rename_label"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lilipin_rename_label.object', {
#             'object': obj
#         })
