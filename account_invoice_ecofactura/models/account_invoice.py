# -*- coding: utf-8 -*-

import random

import datetime
import uuid

from odoo import fields, models, api, _
from suds.client import Client
import xml.etree.ElementTree as ET
from odoo.exceptions import UserError, ValidationError
import base64


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    uuid_fel = fields.Char(string='No. Factura', readonly=True, default=0, copy=False,
                            states={'draft': [('readonly', False)]}, help='UUID returned by certifier')  # No. Invoice
    fel_serie = fields.Char(string='Serie Fel', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                            help='Raw Serial number return by GFACE or FEL provider')  # Fel Series
    fel_no = fields.Char(string='Fel No.', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                        help='Raw Serial number return by GFACE or FEL provider')
    uuid = fields.Char(string='UUID', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                        help='UUID given to the certifier to register the document')
    no_acceso = fields.Char(string='Numero de Acceso', readonly=True, states={'draft': [('readonly', False)]},
                            copy=False, help='Electronic singnature given sent to FEL')  # Access Number
    frase_ids = fields.Many2many('satdte.frases', 'inv_frases_rel', 'inv_id', 'frases_id', 'Frases')
    frase_id = fields.Many2one('satdte.frases')
    factura_cambiaria = fields.Boolean('Factura Cambiaria', related='journal_id.factura_cambiaria', readonly=True)
    number_of_payments = fields.Integer('Cantidad De Abonos', default=1, copy=False, help='Number Of Payments')
    frecuencia_de_vencimiento = fields.Integer('Frecuencia De Vencimiento', copy=False, help='Due date frequency (calendar days)')
    megaprint_payment_lines = fields.One2many('megaprint.payment.line', 'invoice_id', 'Payment Info', copy=False)
    xml_request = fields.Text(string='XML Request', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_response = fields.Text(string='XML Response', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_notes = fields.Text('XML Children')
    uuid_refund = fields.Char('UUID a rectificar')
    txt_filename = fields.Char('Archivo', required=False, readonly=True)
    file = fields.Binary('Archivo', required=False, readonly=True)
    fecha_emision = fields.Text('Fecha de Emision', required=False, readonly=True)
    fecha_certificacion = fields.Text('Fecha de Certificacion', required=False, readonly=True)
    numero_autorizacion = fields.Text('Numero de Autorizacion', required=False, readonly=True)
    serie = fields.Text('Serie', required=False, readonly=True)
    numero = fields.Text('Numero', required=False, readonly=True)
    razon_anulacion = fields.Text('Razon de anulacion')
    invoice_refund_id = fields.Many2one('account.move', 'Invoice Refund', required=False, readonly=False)

    def init_fields(self):
        self.ExtendModel()
    
    def calculate_payment_info(self):
        for inv in self:
            if inv.journal_id.factura_cambiaria and inv.number_of_payments and inv.frecuencia_de_vencimiento and inv.date_invoice:
                inv.megaprint_payment_lines.unlink()  # Delete Old Payment Lines
                amount = inv.amount_total / inv.number_of_payments
                new_date = None
                for i in range(inv.number_of_payments):
                    if not new_date:
                        new_date = datetime.datetime.strptime(str(inv.date_invoice), '%Y-%m-%d').date() + datetime.timedelta(days=inv.frecuencia_de_vencimiento)
                    else:
                        new_date = new_date + datetime.timedelta(days=inv.frecuencia_de_vencimiento)
                    self.env['megaprint.payment.line'].create({
                        'invoice_id': inv.id,
                        'serial_no': i + 1,
                        'amount': amount,
                        'due_date': new_date.strftime('%Y-%m-%d')
                    })

    def set_response_data(self):
        dte_atributos = ET.fromstring(self.xml_response).attrib
        self.fecha_emision = dte_atributos['FechaEmision']
        self.fecha_certificacion = dte_atributos['FechaCertificacion']
        self.numero_autorizacion = dte_atributos['NumeroAutorizacion']
        self.serie = dte_atributos['Serie']
        self.numero = dte_atributos['Numero']

    def set_pdf(self):
        response_xml = ET.fromstring(self.xml_response)
        for child in response_xml:
            if child.tag == 'Pdf':
                self.file = base64.encodestring(base64.standard_b64decode(child.text))                   

    def validar_errores_en_response(self):
        errores = ""
        response_xml = ET.fromstring(self.xml_response)
        for child in response_xml:
            if child.tag == 'Error':
                if not child.attrib['Codigo'] == '2001':
                    errores += child.text + "\n"
        return errores


    def generate_xml(self):
        uuid_txt = uuid.uuid4()
        self.uuid = uuid_txt
        res_xml = ""
        if self.journal_id.is_fel:
            if self.type == 'out_refund' and self.journal_id.is_nota_abono == True:
                res_xml = self.GenerateXML_NABN()
            else:
                res_xml = self.GenerateXML_FACT()
            self.xml_request = res_xml
            ws = Client(self.journal_id.url_webservice)
            response = ws.service.Execute(
                self.journal_id.no_cliente,
                self.journal_id.usuario_ecofactura,
                self.journal_id.password_ecofactura,
                self.journal_id.nit_emisor, res_xml
            )

            self.xml_response = response
            errores = self.validar_errores_en_response()

            if not len(errores) > 1:
                self.set_pdf()
                self.set_response_data()
            else:
                raise UserError(('%s') % (errores))

    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        if self.type in ('out_invoice', 'out_refund') and self.journal_id.is_fel == True:
            self.generate_xml()
        if self.name:
            self.txt_filename = self.name + '.pdf'
        return res

    def action_invoice_cancel(self):
        if self.razon_anulacion and self.journal_id.is_fel:
            res = super(AccountInvoice, self).action_invoice_cancel()
            self.cancel_fel_document()
            return res
        elif not self.journal_id.is_fel:
            res = super(AccountInvoice, self).action_invoice_cancel()
            return  res
        else:
            raise UserError(('%s') % ('No existe una razon de anulación'))

    def cancel_fel_document(self):
        ws = Client(self.journal_id.url_webservice_anulacion)
        response = ws.service.Execute(
            self.journal_id.no_cliente,
            self.journal_id.usuario_ecofactura,
            self.journal_id.password_ecofactura,
            self.journal_id.nit_emisor,
            self.numero_autorizacion,
            self.razon_anulacion
        )
        self.xml_response = response
        errores = self.validar_errores_en_response()

        if not len(errores) > 1:
            self.set_pdf()
        else:
            raise UserError(('%s') % (errores))


AccountInvoice()

class MegaprintPaymentLine(models.Model):
    _name = 'megaprint.payment.line'
    _description = 'Megaprint Payment Line'
    _order = 'serial_no'

    invoice_id = fields.Many2one('account.move', 'Inovice')
    serial_no = fields.Integer('#No', readonly=True)
    amount = fields.Float('Monto', readonly=True, help='Amount')
    due_date = fields.Date('Vencimiento', readonly=True, help='Due Date')

MegaprintPaymentLine()

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        res.update({
            'invoice_refund_id': move.id or False,
        })
        return res

AccountMoveReversal()

