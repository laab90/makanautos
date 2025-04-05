from odoo import models, fields, api
from datetime import datetime
from datetime import date
from openerp.exceptions import ValidationError
from odoo.exceptions import ValidationError
import dateutil.relativedelta
import base64
import xlsxwriter

class invoice_sale_wizard(models.TransientModel):
    _name = 'invoice.sale.wizard.rq'

    date_ini = fields.Date(string='Fecha Inicial', required=True, default=(datetime.today() - dateutil.relativedelta.relativedelta(months=1)))
    date_fin = fields.Date(string='Fecha Final', required=True, default=datetime.today())

    company = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env['res.company']._company_default_get('account.invoice'))

    invoice_sale_ids = fields.Text(string='Factura cliente')

    journal_ids = fields.Many2many('account.journal', required=True, domain=[('type', '=', 'sale')], default=lambda self: self.env['account.journal'].search([('type', '=', 'sale')]))

    def export_invoice_sale_excel(self):
        diario_ids = []
        for x in self.journal_ids:
            diario_ids.append(x.id)
        ventas = self.env['account.move'].search( ['|', ('type', '=', 'out_invoice'), ('type', '=', 'out_refund'), '|', ('state', '=', 'posted'), ('state', '=', 'cancel'), ('invoice_date', '>=', self.date_ini), ('invoice_date', '<=', self.date_fin)] )

        cad_ventas = ''
        if len(ventas) > 0:
            cad_ventas += str(ventas[0].id)
            for x in range(1, len(ventas)):
                if ventas[x].journal_id.id in diario_ids:
                    cad_ventas += ',' + str(ventas[x].id)
        else:
            raise ValidationError('Error, no hay facturas disponibles')

        self.invoice_sale_ids = cad_ventas
        return self.env.ref('account_invoice_report_excel_rq.sale_rq_xlsx').report_action(self)


class invoice_purchase_wizard(models.TransientModel):
    _name = 'invoice.purchase.wizard.rq'

    date_ini = fields.Date(string='Fecha Inicial', required=True, default=(datetime.today() - dateutil.relativedelta.relativedelta(months=1)))
    date_fin = fields.Date(string='Fecha Final', required=True, default=datetime.today())

    company_current = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env['res.company']._company_default_get('account.invoice'))

    invoice_purchase_ids = fields.Text(string='Factura Proveedor')

    journal_ids = fields.Many2many('account.journal', required=True, domain=[('type', '=', 'purchase')], default=lambda self: self.env['account.journal'].search([('type', '=', 'purchase')]))

    def export_invoice_purchase_excel(self):
        diario_ids = []
        for x in self.journal_ids:
            diario_ids.append(x.id)
        compras = self.env['account.move'].search( ['|', ('type', '=', 'in_invoice'), ('type', '=', 'in_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', self.date_ini), ('invoice_date', '<=', self.date_fin)] )

        cad_compras = ''
        if len(compras) > 0:
            cad_compras += str(compras[0].id)
            for x in range(1, len(compras)):
                if compras[x].journal_id.id in diario_ids:
                    cad_compras += ',' + str(compras[x].id)
        else:
            raise ValidationError('Error, no hay facturas disponibles')

        self.invoice_purchase_ids = cad_compras
        return self.env.ref('account_invoice_report_excel_rq.purchase_rq_xlsx').report_action(self)
