# -*- encoding: UTF-8 -*-
##############################################################################
#
# Copyright (C) 2018-Today J2L Tech GT
# (<https://j2ltechgt.odoo.com>)
#
##############################################################################

from odoo import fields, api, models, tools
from odoo.exceptions import UserError
from datetime import datetime

import logging

_logger = logging.getLogger( __name__ )



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    procesado_prod = fields.Boolean(string='Procesado para Producción', default=False)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    silverpos_mrp = fields.Integer(string='SilverPOS MRP', default=0)
    silverpos_processed = fields.Boolean(string='Processed by SilverPOS', default=False)

   
class SaleOrder(models.Model):
    _inherit = "sale.order"

    #*******************************************************************************************
    # Variables creadas para la DB PRUEBAS20132023
    # num_doc = fields.Char(string='Número de Documento')
    # amount_tip = fields.Float(string='Importe por proina')
    # discount_total = fields.Float(string='Total descuentos')
    # amount_tip = fields.Float(string='Total descuentos')
    #*******************************************************************************************


    silverpos_id = fields.Integer('IdSilverPos', required=False, )
    silverpos_uuid = fields.Char('UUID')
    silverpos_serie_fel = fields.Char('Serie')
    silverpos_numero_fel = fields.Char('Numero')
    silverpos_user_id = fields.Many2one('res.users', 'Usuario SilverPos', required=False, copy=False)
    silverpos_order_date = fields.Date('Fecha', compute="_compute_order_date")
    journal_id = fields.Many2one('account.journal', 'Diario', related="analytic_account_id.journal_id")
    is_anulado_silverpos = fields.Float('Anulado Silverpos')
    silverpos_entrega = fields.Integer(string='SilverPOS Entrega', default=0)
    silverpos_produccion_hecha = fields.Integer(string='Produccion hecha', default=0)


    @api.model
    def crear_stock_picking_y_actualizar_ordenes(self):
        MrpProduction = self.env['mrp.production']
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        Bom = self.env['mrp.bom']

        # Buscar órdenes de venta que necesitan procesamiento
        ordenes = self.search([
            ('silverpos_id', '>', 0),
            ('silverpos_entrega', '=', 0),
            ('state', '=', 'sale'),
            ('picking_ids', '=', False),
        ])

        # Salir si no hay órdenes para procesar
        if not ordenes:
            return False

        # Diccionarios para acumular información
        mrp_directorio = {}
        stock_directorio = {}

        for orden in ordenes:

            location_src_id = orden.warehouse_id.lot_stock_id.id
            bodega_tipo_movimiento_manufacturing = orden.warehouse_id.manu_type_id.id
            bodega_antesDeProduccion = orden.warehouse_id.pbm_type_id.id
            bodega_despuesDeProducir = orden.warehouse_id.sam_type_id.id


            for linea in orden.order_line:
                producto = linea.product_id
                cantidad = linea.product_uom_qty

                # Buscar BOM de tipo 'normal'
                bom_normal = Bom.search([
                    '|',
                    ('product_tmpl_id', '=', producto.product_tmpl_id.id),
                    ('product_id', '=', producto.id),
                    ('type', '=', 'normal')
                ], limit=1)

                # Acumular cantidades para las órdenes de fabricación
                if bom_normal:
                    clave_producto = (producto.product_tmpl_id.id, producto.id)
                    if clave_producto not in mrp_directorio:
                        mrp_directorio[clave_producto] = {'cantidad': cantidad, 'orden': orden}
                    else:
                        mrp_directorio[clave_producto]['cantidad'] += cantidad

                # Se asume que todos los productos se deben enviar, independientemente de si son fabricados o no
                if producto.id not in stock_directorio:
                    stock_directorio[producto.id] = cantidad
                else:
                    stock_directorio[producto.id] += cantidad

        all_mos_processed = True
        # Procesar el directorio de MRP para crear órdenes de fabricación
        for (product_tmpl_id, product_id), datos in mrp_directorio.items():
            cantidad = datos['cantidad']
            orden = datos['orden']
            producto = self.env['product.product'].browse(product_id)
            bom = Bom.search([('product_tmpl_id', '=', product_tmpl_id), ('type', '=', 'normal')], limit=1)

            if bom:
                mo_vals = {
                    'product_id': product_id,
                    'product_qty': cantidad,
                    'bom_id': bom.id,
                    'product_uom_id': producto.uom_id.id, 
                    'origin': orden.name,
                    'state': 'draft',
                    'silverpos_mrp': 1,
                    'picking_type_id': bodega_tipo_movimiento_manufacturing,
                    # 'location_src_id': bodega_antesDeProduccion,
                    # 'location_dest_id': bodega_despuesDeProducir,
                    #'location_src_id': bodega_antesDeProduccion,
                    #'location_dest_id': location_src_id,
                    # 'location_src_id': 3,
                    # 'location_dest_id': 3,
                    # 'picking_type_id': 37,
                }
            manufacturing_order = MrpProduction.create(mo_vals)
            manufacturing_order._onchange_workorder_ids()
            manufacturing_order._onchange_product_id()
            # Modificado
            manufacturing_order._onchange_product_qty() 
            manufacturing_order._onchange_picking_type() 
            # Fin modificado
            manufacturing_order._onchange_move_raw()
            manufacturing_order._onchange_move_finished_product() 
            manufacturing_order._onchange_move_finished()
            manufacturing_order.action_confirm()

            # Si la orden está confirmada, actualizar quantity_done y qty_producing
            if manufacturing_order.state == 'confirmed':
                for move in manufacturing_order.move_raw_ids: 
                    move.quantity_done = move.product_uom_qty
                for move in manufacturing_order.move_finished_ids:
                    move.quantity_done = move.product_uom_qty
                manufacturing_order.qty_producing = manufacturing_order.product_qty

                # Marcar la orden como hecha
                manufacturing_order.button_mark_done()

                if manufacturing_order.state == 'done':
                    manufacturing_order.silverpos_processed = True
                else:
                    all_mos_processed = False

        # Crear una orden de entrega consolidada para productos almacenable y fabricados
        picking_vals = {
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        }
        picking = StockPicking.create(picking_vals)

        # Crear movimientos de stock para la orden de entrega
        for producto_id, total_cantidad in stock_directorio.items():
            StockMove.create({
                'name': self.env['product.product'].browse(producto_id).display_name,
                'product_id': producto_id,
                'product_uom_qty': total_cantidad,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'picking_id': picking.id,
                'product_uom': self.env['product.product'].browse(producto_id).uom_id.id,
            })

        # No confirmamos ni asignamos la orden de entrega aquí
        picking.state = 'draft'

        #if all_mos_processed:
            #picking.action_confirm()
            #picking.action_set_quantities_to_reservation()
            #picking.button_validate()

        # Actualizar órdenes de venta para marcarlas como procesadas
        ordenes.write({'silverpos_entrega': 1})
        return True
   




    

    

    

     

    @api.depends('date_order')
    def _compute_order_date(self):
        for rec in self:
            date = False
            if rec.date_order:
                date = rec.date_order.date()
            rec.update({
                'silverpos_order_date': date,
            })

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        for rec in self:
            res.update({
                'silverpos_uuid': rec.silverpos_uuid,
                'silverpos_serie_fel': rec.silverpos_serie_fel,
                'silverpos_numero_fel': rec.silverpos_numero_fel,
                'invoice_user_id': rec.silverpos_user_id.id or rec.user_id.id,
                'invoice_date': datetime.strptime(str(rec.date_order), "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d'),
            })
            if rec.journal_id:
                res.update({
                    'journal_id': rec.journal_id.id or False,
                })
        return res
    
    @api.model
    def _action_confirm_orders(self):
        count = 0
        item = 0
        so_obj = self.env['sale.order']
        #company_ids = self.env.company.ids
        #if not company_ids:
        company_ids = self.env['res.company'].sudo().search([]).ids
        orders_ids = self.env['sale.order'].sudo().search([('silverpos_id', '!=', 0), ('state', '=', 'draft'), ('company_id', 'in', company_ids)])
        for order in orders_ids:
            try:
                item += 1
                #if order.state == 'draft':
                order.sudo().action_confirm()
                count += 1
                so_obj += order
                if count == 20:
                    self.env.cr.commit()
                    log = ("----------------Item %s OrderIds: %s-%s -> Transacciones Liberadas----------------" %(item, order.id, order.name))
                    _logger.info(log)
                    so_obj = self.env['sale.order']
                    count = 0
                #order.env.cr.commit()
                #_logger.info(("SO Confirmada con Exito..! -> %s" %(order.name)))
                log = ("----------------Item %s OrderId: %s-%s -> Confirmada exitosamente----------------" %(item, order.id, order.name))
                _logger.info(log)
            except Exception as e:
                error = ("%s %s -> %s" %(order.id, order.name, e))
                _logger.info(error)
                #order.env.cr.rollback()
                pass
        
        # Tu lógica personalizada
        for order in orders_ids:
            order.picking_ids.unlink()

        if so_obj and len(so_obj.ids) > 0:
            self.env.cr.commit()

        # Llamar al método crear_stock_picking_y_actualizar_ordenes
        self.crear_stock_picking_y_actualizar_ordenes() 

        return True 


    @api.model
    def _action_invoiced_orders(self):
        #company_ids = self.env.company.ids
        #if not company_ids:
        company_ids = self.env['res.company'].sudo().search([]).ids
        orders_ids = self.env['sale.order'].sudo().search([('silverpos_id', '!=', 0), ('state', '=', 'sale'), ('invoice_status', '=', 'to invoice'), ('company_id', 'in', company_ids)])
        for order in orders_ids:
            try:
                if order.state == 'sale':
                    order.sudo()._create_invoices()
                    order.env.cr.commit()
            except Exception as e:
                error = ("%s %s -> %s" %(order.id, order.name, e))
                _logger.info(error)
                order.env.cr.rollback()
                pass


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    @api.model
    def _action_post_payment_silverpos(self, records=100):
        #company_ids = self.env.user.company_ids.ids
        #if not company_ids:
        company_ids = self.env['res.company'].sudo().search([]).ids
        payments_ids = self.env['account.payment'].search([('sale_id', '!=', False), ('state', '=', 'draft'), ('company_id', 'in', company_ids)], limit=records)
        for payment in payments_ids:
            try:
                if payment.state == 'draft':
                    payment.action_post()
                    if payment.sale_id and payment.sale_id.invoice_ids:
                        domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
                        #payment.write({
                        #    'invoice_ids': payment.sale_id.invoice_ids.ids if payment.sale_id.invoice_ids else False,
                        #})
                        payment_lines = payment.line_ids.filtered_domain(domain)
                        invoice_lines = payment.sale_id.invoice_ids.line_ids.filtered_domain(domain)
                        for account in payment_lines.account_id:
                            (payment_lines + invoice_lines).filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
                    #payment.post()
                    payment.env.cr.commit()
                    log = ("----------------PaymentId: %s-%s -> Asentado exitosamente----------------" %(payment.id, payment.name))
                    _logger.info(log)
            except Exception as e:
                error = ("PaymentId: %s -> Error: %s" %(payment.id, e))
                _logger.info(error)
                payment.env.cr.rollback()
                pass
AccountPayment()



# class StockMove(models.Model):
#     _inherit = "stock.move"

#     def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
#         self.ensure_one()
#         AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

#         move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
#         if move_lines:
#             date = False
#             if self.sale_line_id.order_id.silverpos_order_date:
#                 date = self.sale_line_id.order_id.silverpos_order_date
#             else:
#                 date = self._context.get('force_period_date', fields.Date.context_today(self))
#             new_account_move = AccountMove.sudo().create({
#                 'journal_id': journal_id,
#                 'line_ids': move_lines,
#                 'date': date,
#                 'ref': description,
#                 'stock_move_id': self.id,
#                 'stock_valuation_layer_ids': [(6, None, [svl_id])],
#                 'type': 'entry',
#             })
#             new_account_move.post()
# StockMove()