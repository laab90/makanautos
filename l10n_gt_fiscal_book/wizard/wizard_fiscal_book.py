# -*- coding: utf-8 -*-
import time
from datetime import datetime
from dateutil import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import time
import xlwt
import base64
from io import BytesIO


class WizardVentasCompras(models.TransientModel):
    _name = 'wizard.fiscal.book'
    _description = "Wizard Fiscal Book"

    def _revisar_diario(self):
        return self.env.context('active_id', None)

    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
    journal_ids = fields.Many2many('account.journal', 'book_journal_rel', 'wizard_id', 'journal_id', 'Journals', required=True)
    tax_id = fields.Many2one('account.tax.group', 'Taxes', required=True,default= lambda self: self.env['account.tax.group'].search([], limit=1).id)
    base_id = fields.Many2one('account.tax.group', 'Tax Base', required=True, default=lambda self: self.env['account.tax.group'].search([], limit=1).id)
    date_from = fields.Date('Date From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date To', required=True, default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    type_book = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase')], string="Fiscal Type", required=True, default="sale", readoly=True)
    type_report = fields.Selection([
        ('pdf', 'PDF'),
        ('xls', 'XLS')],string="Report Type", required=True, default="pdf")
    
    #Binary Fields
    file_name = fields.Char('Filename', size=32)
    file = fields.Binary('File', filters='.xls')

    @api.onchange('company_id')
    def _onchange_company(self):
        if self.company_id: 
            if self.type_book and self.type_book == 'sale' :
                self.journal_ids = self.company_id.gt_sale_journal_tr_ids.ids if self.company_id.gt_sale_journal_tr_ids else False
            if self.type_book and self.type_book == 'purchase':
                self.journal_ids = self.company_id.gt_purchase_journal_tr_ids.ids if self.company_id.gt_purchase_journal_tr_ids else False

    @api.onchange('type_book')
    def _onchange_domain_journal_ids(self):
        """Force domain for the 'journal_id' field"""
        #self.journal_ids = [(6, 0, [])]
        domain = [('type', 'in', ['sale', 'sale_refund'])]
        if self.type_book == 'purchase':
            domain = [('type', 'in', ['purchase', 'purchase_refund'])]
        return {'domain': {'journal_ids': domain}}

    def print_report_sale(self):
        self.ensure_one()
        domain = [
                ('invoice_date', '>=', self.date_from),
                ('invoice_date', '<=', self.date_to),
                ('company_id', '=', self.company_id.id),
                ('journal_id', 'in', self.journal_ids.ids),
                ('state', '=', ('posted', 'cancel')),
                ('move_type', 'in', ('out_invoice', 'out_refund'))]
        values = self.generate_sale_values(domain=domain)
        datas = {
            'values': values,
            'company_name': self.company_id.partner_id.name,
            'company_street': self.company_id.street,
            'company_nit': self.company_id.vat,
            'dates': (("Del %s Al %s") %(self.date_from.strftime("%d/%m/%Y"), self.date_to.strftime("%d/%m/%Y")))
        }
        return self.env.ref('l10n_gt_fiscal_book.report_sale_fiscal_book').report_action(self, data=datas)

    def print_report_purchase(self):
        self.ensure_one()
        domain = [
                ('invoice_date', '>=', self.date_from),
                ('invoice_date', '<=', self.date_to),
                ('company_id', '=', self.company_id.id),
                ('journal_id', 'in', self.journal_ids.ids),
                ('state', '=', ('posted', 'cancel')),
                ('move_type', 'in', ('in_invoice', 'in_refund'))]
        values = self.generate_purchase_values(domain=domain)
        datas = {
            'values': values,
            'company_name': self.company_id.partner_id.name,
            'company_street': self.company_id.street,
            'company_nit': self.company_id.vat,
            'dates': (("Del %s Al %s") %(self.date_from.strftime("%d/%m/%Y"), self.date_to.strftime("%d/%m/%Y")))
        }
        return self.env.ref('l10n_gt_fiscal_book.report_purchase_fiscal_book').report_action(self, data=datas)

    def generate_sale_values(self, domain=None):
        res = []
        if domain:
            invoice_ids = self.env['account.move'].search(domain, order="invoice_date asc")
            for inv in invoice_ids:
                amount_bienes_grabable = 0.00
                amount_bienes_exento = 0.00
                amount_servicios_grabable = 0.00
                amount_servicios_exento = 0.00
                amount_iva = 0.00
                amount_total = 0.00
                for l in inv.invoice_line_ids:
                    price_unit = l.price_unit if inv.state != 'cancel' else 0.00
                    #Valido que la moneda de la compañia es diferente a la del documento para aplicar currency rate
                    if inv.company_id.currency_id != inv.currency_id:
                        price_unit = inv.currency_id._convert(price_unit, inv.company_id.currency_id, inv.company_id, inv.invoice_date)
                    #Ajusto el precio para descontar el descuento por linea
                    price_unit = price_unit * (1-(l.discount or 0.0)/100.0)
                    #Si el documento es una NC lo hago negativo porque descuentan del libro de ventas
                    if inv.move_type == 'out_refund':
                        price_unit = (price_unit * - 1)
                    #Determino los valores de base imponible e impuestos
                    taxes = l.tax_ids.compute_all(price_unit, inv.company_id.currency_id, l.quantity, l.product_id, inv.partner_id)
                    if l.product_id and l.product_id.type == 'service':
                        #Si tiene impuestos en la linea es un monto grabable
                        if l.tax_ids:
                            amount_servicios_grabable += taxes.get('total_excluded', 0.00)
                            for tax in taxes['taxes']:
                                #aux_iva += tax['amount']
                                if tax.get('id', False) in inv.company_id.gt_iva_sale_tax_tr_ids.ids:
                                    amount_iva += tax.get('amount', 0.00)
                        else:
                            amount_servicios_exento += taxes.get('total_excluded', 0.00)
                    if l.product_id and l.product_id.type in ('product', 'consu'):
                        if l.tax_ids:
                            amount_bienes_grabable += taxes.get('total_excluded', 0.00)
                            for tax in taxes['taxes']:
                                #aux_iva += tax['amount']
                                if tax.get('id', False) in inv.company_id.gt_iva_sale_tax_tr_ids.ids:
                                    amount_iva += tax.get('amount', 0.00)
                        else:
                            amount_bienes_exento += taxes.get('total_excluded', 0.00)
                #sumo todas la varibales (grabables y exentas) y el impuesto (IVA)
                amount_total = sum([amount_bienes_grabable, amount_bienes_exento, amount_servicios_grabable, amount_servicios_exento, amount_iva])
                line = {
                    'invoice_date': inv.invoice_date.strftime("%d/%m/%Y"),
                    'type': "FC",
                    'trans': inv.gt_move_type_tr_id.name,
                    'serie': inv.fel_serie,
                    'number': inv.fel_no,
                    'customer_vat': inv.partner_id.vat or "CF",
                    'customer': inv.partner_id.name,
                    'amount_bienes_grabables': inv.currency_id.round(amount_bienes_grabable) or 0.00,
                    'amount_bienes_exentos': inv.currency_id.round(amount_bienes_exento) or 0.00,
                    'amount_servicios_grabables': inv.currency_id.round(amount_servicios_grabable) or 0.00,
                    'amount_servicios_exentos': inv.currency_id.round(amount_servicios_exento) or 0.00,
                    'amount_iva': inv.currency_id.round(amount_iva) or 0.00,
                    'amount_total': inv.currency_id.round(amount_total) or 0.00,
                }
                res.append(line)
        return res

    def print_purchase_excel(self):
        for rec in self:
            domain = [
                ('invoice_date', '>=', rec.date_from),
                ('invoice_date', '<=', rec.date_to),
                ('company_id', '=', rec.company_id.id),
                ('journal_id', 'in', rec.journal_ids.ids),
                ('state', '=', ('posted', 'cancel')),
                ('move_type', 'in', ('in_invoice', 'in_refund'))]
            values = self.generate_purchase_values(domain=domain)
            if not rec.journal_ids:
                raise UserError(("No hay ningun diario seleccionado..!"))
            book = xlwt.Workbook()
            sheet = book.add_sheet('Libro de Ventas')
            titulos_principales_style = xlwt.easyxf('borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; align: horiz center; font:bold on;')
            titulos_texto_style = xlwt.easyxf('align: horiz left;')
            titulos_numero_style = xlwt.easyxf('align: horiz right;')
            subtitle_strong_style = xlwt.easyxf('align: horiz left; font: bold on;')
            subtitle_style = xlwt.easyxf('align: horiz left; font: bold on;')
            company_tittle_style = xlwt.easyxf('align: horiz left; font:bold on;')
            company_subtittle_style = xlwt.easyxf('align: horiz left;')
            sums_style = xlwt.easyxf('borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; align: horiz right; font:bold on;')

            sheet.write_merge(0, 0, 0, 6, rec.company_id.name, style=company_tittle_style)
            sheet.write_merge(1, 1, 0, 1, "Dirección:", style=company_tittle_style)
            sheet.write_merge(1, 1, 2, 4, rec.company_id.street, style=company_subtittle_style)
            sheet.write_merge(2, 2, 0, 1, "NIT:", style=company_tittle_style)
            sheet.write_merge(2, 2, 2, 4, rec.company_id.vat, style=company_subtittle_style)
            sheet.write_merge(3, 3, 0, 6, "REGISTRO DE COMPRAS Y SERVICIOS", style=company_tittle_style)
            sheet.write_merge(4, 4, 0, 1, "Período:", style=company_tittle_style)
            sheet.write_merge(4, 4, 2, 4, (("Del %s al %s") %(rec.date_from.strftime("%d/%m/%Y"), rec.date_to.strftime("%d/%m/%Y"))), style=company_subtittle_style)
            sheet.write_merge(5, 5, 0, 6, "(Valores en Quetzales)", style=company_tittle_style)
            y = 7
            sheet.write_merge(y, y, 6, 10, 'Precio Neto', style=titulos_principales_style)
            #sheet.write_merge(y, y, 9, 10, 'BASE EXENTA', style=titulos_principales_style)
            y += 1
            sheet.col(0).width = 3000
            sheet.write(y, 0, 'Fecha', style=titulos_principales_style)
            sheet.col(1).width = 3000
            sheet.write(y, 1, 'Tipo', style=titulos_principales_style)
            sheet.col(2).width = 3000
            sheet.write(y, 2, 'Serie', style=titulos_principales_style)
            sheet.col(3).width = 3000
            sheet.write(y, 3, 'Número', style=titulos_principales_style)
            #sheet.col(4).width = 3000
            #sheet.write(y, 4, 'TRAN', style=titulos_principales_style)
            sheet.col(4).width = 3000
            sheet.write(y, 4, 'NIT O CEDULA', style=titulos_principales_style)
            sheet.col(5).width = 10000
            sheet.write(y, 5, 'Nombre', style=titulos_principales_style)
            sheet.col(6).width = 3000
            sheet.write(y, 6, 'Bienes', style=titulos_principales_style)
            sheet.col(7).width = 3000
            sheet.write(y, 7, 'Servicios', style=titulos_principales_style)
            sheet.col(8).width = 3000
            sheet.write(y, 8, 'Importación', style=titulos_principales_style)
            sheet.col(9).width = 3000
            sheet.write(y, 9, 'Combustibles', style=titulos_principales_style)
            sheet.col(10).width = 3000
            sheet.write(y, 10, 'Peq. Contribuyente', style=titulos_principales_style)
            sheet.col(11).width = 3000
            sheet.write(y, 11, 'IVA', style=titulos_principales_style)
            sheet.col(12).width = 3000
            sheet.write(y, 12, 'Total', style=titulos_principales_style)
            init_rows = y
            for linea in values:
                y += 1
                sheet.write(y, 0, linea.get('invoice_date', False), style=titulos_texto_style)
                sheet.write(y, 1, linea.get('type', False), style=titulos_texto_style)
                sheet.write(y, 2, linea.get('serie', False), style=titulos_texto_style)
                sheet.write(y, 3, linea.get('number', False), style=titulos_texto_style)
                sheet.write(y, 4, linea.get('customer_vat', False), style=titulos_texto_style)
                sheet.write(y, 5, linea.get('customer', False), style=titulos_texto_style)
                sheet.write(y, 6, linea.get('amount_bienes', False), style=titulos_texto_style)
                sheet.write(y, 7, linea.get('amount_servicios', 0.00), style=titulos_numero_style)
                sheet.write(y, 8, linea.get('amount_import', 0.00), style=titulos_numero_style)
                sheet.write(y, 9, linea.get('amount_combustible', 0.00), style=titulos_numero_style)
                sheet.write(y, 10, linea.get('amount_pqc', 0.00), style=titulos_numero_style)
                sheet.write(y, 11, linea.get('amount_iva', 0.00), style=titulos_numero_style)
                sheet.write(y, 12, linea.get('amount_total', 0.00), style=titulos_numero_style)
            y += 1
            #Sum on numeric cell
            sheet.write_merge(y, y, 0, 6, "*TOTALES*", style=sums_style)
            sheet.write(y, 7, xlwt.Formula((("sum(H%s:H%s)") %(init_rows, y))) , style=sums_style)
            sheet.write(y, 8, xlwt.Formula((("sum(I%s:I%s)") %(init_rows, y))), style=sums_style)
            sheet.write(y, 9, xlwt.Formula((("sum(J%s:J%s)") %(init_rows, y))), style=sums_style)
            sheet.write(y, 10, xlwt.Formula((("sum(K%s:K%s)") %(init_rows, y))), style=sums_style)
            sheet.write(y, 11, xlwt.Formula((("sum(L%s:L%s)") %(init_rows, y))), style=sums_style)
            sheet.write(y, 12, xlwt.Formula((("sum(M%s:M%s)") %(init_rows, y))), style=sums_style)
            fp = BytesIO()
            book.save(fp)
            fp.seek(0)
            report_data_file = base64.encodestring(fp.read())
            fp.close()
            self.write({'file': report_data_file})
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=wizard.fiscal.book&field=file&download=true&id=%s&filename=libro_compras.xls' % (rec.id),
                'target': 'new',
            }

    def print_sale_excel(self):
        for rec in self:
            domain = [
                ('invoice_date', '>=', rec.date_from),
                ('invoice_date', '<=', rec.date_to),
                ('company_id', '=', rec.company_id.id),
                ('journal_id', 'in', rec.journal_ids.ids),
                ('state', '=', ('posted', 'cancel')),
                ('move_type', 'in', ('out_invoice', 'out_refund'))]
            values = self.generate_sale_values(domain=domain)
            if not rec.journal_ids:
                raise UserError(("No hay ningun diario seleccionado..!"))
            book = xlwt.Workbook()
            sheet = book.add_sheet('Libro de Ventas')
            titulos_principales_style = xlwt.easyxf('borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; align: horiz center; font:bold on;')
            titulos_texto_style = xlwt.easyxf('align: horiz left;')
            titulos_numero_style = xlwt.easyxf('align: horiz right;')
            subtitle_strong_style = xlwt.easyxf('align: horiz left; font: bold on;')
            subtitle_style = xlwt.easyxf('align: horiz left; font: bold on;')
            company_tittle_style = xlwt.easyxf('align: horiz left; font:bold on;')
            company_subtittle_style = xlwt.easyxf('align: horiz left;')
            sums_style = xlwt.easyxf('borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; align: horiz right; font:bold on;')

            sheet.write_merge(0, 0, 0, 6, rec.company_id.name, style=company_tittle_style)
            sheet.write_merge(1, 1, 0, 1, "Dirección:", style=company_tittle_style)
            sheet.write_merge(1, 1, 2, 4, rec.company_id.street, style=company_subtittle_style)
            sheet.write_merge(2, 2, 0, 1, "NIT:", style=company_tittle_style)
            sheet.write_merge(2, 2, 2, 4, rec.company_id.vat, style=company_subtittle_style)
            sheet.write_merge(3, 3, 0, 6, "LIBRO DE VENTAS Y SERVICIOS PRESTADOS", style=company_tittle_style)
            sheet.write_merge(4, 4, 0, 1, "Período:", style=company_tittle_style)
            sheet.write_merge(4, 4, 2, 4, (("Del %s al %s") %(rec.date_from.strftime("%d/%m/%Y"), rec.date_to.strftime("%d/%m/%Y"))), style=company_subtittle_style)
            sheet.write_merge(5, 5, 0, 6, "(Valores en Quetzales)", style=company_tittle_style)
            y = 7
            sheet.write_merge(y, y, 7, 8, 'BASE GRAVADA', style=titulos_principales_style)
            sheet.write_merge(y, y, 9, 10, 'BASE EXENTA', style=titulos_principales_style)
            y += 1
            sheet.col(0).width = 3000
            sheet.write(y, 0, 'Fecha', style=titulos_principales_style)
            sheet.col(1).width = 3000
            sheet.write(y, 1, 'Tipo', style=titulos_principales_style)
            sheet.col(2).width = 3000
            sheet.write(y, 2, 'Serie', style=titulos_principales_style)
            sheet.col(3).width = 3000
            sheet.write(y, 3, 'Número', style=titulos_principales_style)
            sheet.col(4).width = 3000
            sheet.write(y, 4, 'TRAN', style=titulos_principales_style)
            sheet.col(5).width = 3000
            sheet.write(y, 5, 'NIT', style=titulos_principales_style)
            sheet.col(6).width = 10000
            sheet.write(y, 6, 'Nombre', style=titulos_principales_style)
            sheet.col(7).width = 3000
            sheet.write(y, 7, 'Bienes', style=titulos_principales_style)
            sheet.col(8).width = 3000
            sheet.write(y, 8, 'Servicios', style=titulos_principales_style)
            sheet.col(9).width = 3000
            sheet.write(y, 9, 'Bienes', style=titulos_principales_style)
            sheet.col(10).width = 3000
            sheet.write(y, 10, 'Servicios', style=titulos_principales_style)
            sheet.col(11).width = 3000
            sheet.write(y, 11, 'IVA', style=titulos_principales_style)
            sheet.col(12).width = 3000
            sheet.write(y, 12, 'Total', style=titulos_principales_style)
            init_rows = y
            for linea in values:
                y += 1
                sheet.write(y, 0, linea.get('invoice_date', False), style=titulos_texto_style)
                sheet.write(y, 1, linea.get('type', False), style=titulos_texto_style)
                sheet.write(y, 2, linea.get('serie', False), style=titulos_texto_style)
                sheet.write(y, 3, linea.get('number', False), style=titulos_texto_style)
                sheet.write(y, 4, linea.get('trans', False), style=titulos_texto_style)
                sheet.write(y, 5, linea.get('customer_vat', False), style=titulos_texto_style)
                sheet.write(y, 6, linea.get('customer', False), style=titulos_texto_style)
                sheet.write(y, 7, linea.get('amount_bienes_grabables', 0.00), style=titulos_numero_style)
                sheet.write(y, 8, linea.get('amount_servicios_grabables', 0.00), style=titulos_numero_style)
                sheet.write(y, 9, linea.get('amount_bienes_exentos', 0.00), style=titulos_numero_style)
                sheet.write(y, 10, linea.get('amount_servicios_exentos', 0.00), style=titulos_numero_style)
                sheet.write(y, 11, linea.get('amount_iva', 0.00), style=titulos_numero_style)
                sheet.write(y, 12, linea.get('amount_total', 0.00), style=titulos_numero_style)
            y += 1
            #Sum on numeric cell
            sheet.write_merge(y, y, 0, 6, "*TOTALES*", style=sums_style)
            sheet.write(y, 7, xlwt.Formula((("sum(H%s:H%s)") %(init_rows, y))) , style=sums_style)
            sheet.write(y, 8, xlwt.Formula((("sum(I%s:I%s)") %(init_rows, y))), style=sums_style)
            sheet.write(y, 9, xlwt.Formula((("sum(J%s:J%s)") %(init_rows, y))), style=sums_style)
            sheet.write(y, 10, xlwt.Formula((("sum(K%s:K%s)") %(init_rows, y))), style=sums_style)
            sheet.write(y, 11, xlwt.Formula((("sum(L%s:L%s)") %(init_rows, y))), style=sums_style)
            sheet.write(y, 12, xlwt.Formula((("sum(M%s:M%s)") %(init_rows, y))), style=sums_style)
            fp = BytesIO()
            book.save(fp)
            fp.seek(0)
            report_data_file = base64.encodestring(fp.read())
            fp.close()
            self.write({'file': report_data_file})
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=wizard.fiscal.book&field=file&download=true&id=%s&filename=libro_ventas.xls' % (rec.id),
                'target': 'new',
            }

    def generate_purchase_values(self, domain=None):
        res = []
        if domain:
            invoice_ids = self.env['account.move'].search(domain, order="invoice_date asc")
            for inv in invoice_ids:
                amount_bienes = 0.00
                amount_combustible = 0.00
                amount_import = 0.00
                amount_pqc = 0.00
                amount_servicios = 0.00
                amount_iva = 0.00
                amount_total = 0.00
                tax_ids = self.env['account.tax'].search(['|', ('tax_group_id', '=', self.tax_id.id), ('tax_group_id', '=', self.tax_id.id), ('type_tax_use', '=', 'purchase')]).mapped('id')
                for l in inv.invoice_line_ids:
                    price_unit = l.price_unit if inv.state != 'cancel' else 0.00
                    #Valido que la moneda de la compañia es diferente a la del documento para aplicar currency rate
                    if inv.company_id.currency_id != inv.currency_id:
                        price_unit = inv.currency_id._convert(price_unit, inv.company_id.currency_id, inv.company_id, inv.invoice_date)
                    #Ajusto el precio para descontar el descuento por linea
                    price_unit = price_unit * (1-(l.discount or 0.0)/100.0)
                    #Si el documento es una NC lo hago negativo porque descuentan del libro de ventas
                    if inv.move_type == 'in_refund':
                        price_unit = (price_unit * - 1)
                    #Determino los valores de base imponible e impuestos
                    taxes = l.tax_ids.compute_all(price_unit, inv.company_id.currency_id, l.quantity, l.product_id, inv.partner_id)
                    if l.product_id and l.product_id.type == 'service':
                        #Si tiene impuestos en la linea es un monto grabable
                        #Validacion si el tipo de movimiento es para los tipos Bienes en la configuracion
                        if inv.gt_move_type_tr_id.id in inv.company_id.gt_service_trans_tr_id.ids:
                            if l.tax_ids:
                                amount_servicios += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                            else:
                                amount_servicios += taxes.get('total_excluded', 0.00)
                        elif inv.gt_move_type_tr_id.id in inv.company_id.gt_import_trans_tr_id.ids:
                            if l.tax_ids:
                                amount_import += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                            else:
                                amount_import += taxes.get('total_excluded', 0.00)
                        #Validacion si la transaccion pertenes a Peq. Contribuyentes
                        elif inv.gt_move_type_tr_id.id in inv.company_id.gt_pqc_trans_tr_id.ids:
                            if l.tax_ids:
                                amount_pqc += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                            else:
                                amount_pqc += taxes.get('total_excluded', 0.00)
                        #de lo contrario se va como servicio
                        else:
                            if l.tax_ids:
                                amount_servicios += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                            else:
                                amount_servicios += taxes.get('total_excluded', 0.00)
                    if l.product_id and l.product_id.type in ('product', 'consu'):
                        #Validacion si el tipo de movimiento es para los tipos Bienes en la configuracion
                        if inv.gt_move_type_tr_id.id in inv.company_id.gt_product_trans_tr_id.ids:
                            if l.tax_ids:
                                amount_bienes += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                            else:
                                amount_bienes += taxes.get('total_excluded', 0.00)
                        #Validacion si la transaccion pertenece a los combustibles
                        elif inv.gt_move_type_tr_id.id in inv.company_id.gt_combustible_trans_tr_id.ids:
                            if l.tax_ids:
                                amount_combustible += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    #if tax.get('id') not in inv.company_id.gt_combustible_trans_tr_id.ids:
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                                    #else:
                                    #    if tax.get('amount', 0.00) > 0.00:
                                    #        amount_combustible += tax.get('amount', 0.00)
                            else:
                                amount_combustible += taxes.get('total_excluded', 0.00)
                        #Validacion si la transaccion pertenes a importaciones
                        elif inv.gt_move_type_tr_id.id in inv.company_id.gt_import_trans_tr_id.ids:
                            if l.tax_ids:
                                amount_import += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                            else:
                                amount_import += taxes.get('total_excluded', 0.00)
                        #Validacion si la transaccion pertenes a Peq. Contribuyentes
                        elif inv.gt_move_type_tr_id.id in inv.company_id.gt_pqc_trans_tr_id.ids:
                            if l.tax_ids:
                                amount_pqc += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                            else:
                                amount_pqc += taxes.get('total_excluded', 0.00)
                        #De lo contrario se va como bienes en general
                        else:
                            if l.tax_ids:
                                amount_bienes += taxes.get('total_excluded', 0.00)
                                for tax in taxes['taxes']:
                                    #aux_iva += tax['amount']
                                    if tax.get('id', False) in inv.company_id.gt_iva_purchase_tax_tr_ids.ids:
                                        amount_iva += tax.get('amount', 0.00)
                            else:
                                amount_bienes += taxes.get('total_excluded', 0.00)
                #sumo todas la varibales (grabables y exentas) y el impuesto (IVA)
                amount_total = sum([amount_bienes, amount_servicios, amount_import, amount_combustible, amount_pqc, amount_iva])
                line = {
                    'invoice_date': inv.invoice_date.strftime("%d/%m/%Y"),
                    'type': "FC",
                    'trans': inv.gt_move_type_tr_id.name,
                    'serie': inv.gt_dte_serie_tr,
                    'number': inv.gt_dte_number_tr,
                    'customer_vat': inv.partner_id.vat or "CF",
                    'customer': inv.partner_id.name,
                    'amount_bienes': inv.currency_id.round(amount_bienes) or 0.00,
                    'amount_servicios': inv.currency_id.round(amount_servicios) or 0.00,
                    'amount_import': inv.currency_id.round(amount_import) or 0.00,
                    'amount_pqc': inv.currency_id.round(amount_pqc) or 0.00,
                    'amount_combustible': inv.currency_id.round(amount_combustible) or 0.00,
                    'amount_iva': inv.currency_id.round(amount_iva) or 0.00,
                    'amount_total': inv.currency_id.round(amount_total) or 0.00,
                }
                res.append(line)
        return res
