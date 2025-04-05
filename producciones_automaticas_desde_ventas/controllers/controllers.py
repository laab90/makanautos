# -*- coding: utf-8 -*-
# from odoo import http


# class ProduccionesAutomaticasDesdeVentas(http.Controller):
#     @http.route('/producciones_automaticas_desde_ventas/producciones_automaticas_desde_ventas', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/producciones_automaticas_desde_ventas/producciones_automaticas_desde_ventas/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('producciones_automaticas_desde_ventas.listing', {
#             'root': '/producciones_automaticas_desde_ventas/producciones_automaticas_desde_ventas',
#             'objects': http.request.env['producciones_automaticas_desde_ventas.producciones_automaticas_desde_ventas'].search([]),
#         })

#     @http.route('/producciones_automaticas_desde_ventas/producciones_automaticas_desde_ventas/objects/<model("producciones_automaticas_desde_ventas.producciones_automaticas_desde_ventas"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('producciones_automaticas_desde_ventas.object', {
#             'object': obj
#         })
