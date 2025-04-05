# -*- coding: utf-8 -*-

import random

import datetime
import uuid

from odoo import fields, models, api
from odoo.exceptions import UserError, Warning
from odoo.addons.account_invoice_fel_corposistemas import numero_a_texto

import requests
import json
#from xml.etree.ElementTree import Element, SubElement, Comment, tostring, fromstring
#from xml.dom import minidom
import xmltodict
import pprint
#import json
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
import base64
from odoo.tools.translate import _

import os  


import logging

_logger = logging.getLogger( __name__ )

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    uuid_fel = fields.Char(string='No. Factura', readonly=True, default=0, copy=False,
                           states={'draft': [('readonly', False)]}, help='UUID returned by certifier')  # No. Invoice
    fel_serie = fields.Char(string='Serie', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                            help='Raw Serial number return by GFACE or FEL provider')  # Fel Series
    fel_no = fields.Char(string='Numero.', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                         help='Raw Serial number return by GFACE or FEL provider')
    fel_date = fields.Char(string='Fecha DTE.', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                         help='Raw date return by GFACE or FEL provider')
    fel_received_sat = fields.Char(string='Acuse Recibo SAT', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    uuid = fields.Char(string='UUID', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                       help='UUID given to the certifier to register the document')
    no_acceso = fields.Char(string='Numero de Acceso', readonly=True, states={'draft': [('readonly', False)]},
                            copy=False, help='Electronic singnature given sent to FEL')  # Access Number
    frase_ids = fields.Many2many('satdte.frases', 'inv_frases_rel', 'inv_id', 'frases_id', 'Frases', default=lambda self: self.env.company.frase_ids)

    factura_cambiaria = fields.Boolean('Factura Cambiaria', related='journal_id.factura_cambiaria', readonly=True)
    number_of_payments = fields.Integer('Cantidad De Abonos', default=1, copy=False, help='Number Of Payments')
    frecuencia_de_vencimiento = fields.Integer('Frecuencia De Vencimiento', copy=False, help='Due date frequency (calendar days)')
    megaprint_payment_lines = fields.One2many('megaprint.payment.line', 'invoice_id', 'Payment Info', copy=False)
    xml_request = fields.Text(string='XML Request', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_response = fields.Text(string='XML Response', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_notes = fields.Text('XML Children')
    uuid_refund = fields.Char('UUID a rectificar', related="reversed_entry_id.uuid")
    txt_filename = fields.Char('Archivo', required=False, readonly=True, copy=False)
    file = fields.Binary('Archivo', required=False, readonly=True, copy=False)
    txt_filename_xml = fields.Char('Archivo XML', required=False, readonly=True, copy=False)
    file_xml = fields.Binary('Archivo XML', required=False, readonly=True, copy=False)
    invoice_refund_id = fields.Many2one('account.move', 'Invoice Refund', required=False, readonly=False)
    #FEL Cancel
    be_cancel = fields.Boolean('DTE Anulado', default=False)
    fel_codes_cancel = fields.Char(string='Codigos SAT', readonly=True, copy=False)
    fel_cancel_sat = fields.Char(string='Acuse Anulacion SAT', readonly=True, copy=False)
    txt_filename_cancel = fields.Char('Archivo XML Anulacion', required=False, readonly=True, copy=False)
    file_cancel = fields.Binary('Archivo XML Anulacion', required=False, readonly=True, copy=False)
    is_fel = fields.Boolean('FEL', related="journal_id.is_fel")
    is_export = fields.Boolean('Exportacion', required=False)
    is_exento = fields.Boolean('Exento', required=False)
    country_name = fields.Char(related="company_id.country_id.name")
    #customer_name = fields.Char()



    def calculate_payment_info(self):
        for inv in self:
            if inv.journal_id.factura_cambiaria and inv.number_of_payments and inv.frecuencia_de_vencimiento and inv.invoice_date:
                inv.megaprint_payment_lines.unlink()  # Delete Old Payment Lines
                amount = inv.amount_total / inv.number_of_payments
                new_date = None
                for i in range(inv.number_of_payments):
                    if not new_date:
                        new_date = datetime.datetime.strptime(str(inv.invoice_date), '%Y-%m-%d').date() + datetime.timedelta(days=inv.frecuencia_de_vencimiento)
                    else:
                        new_date = new_date + datetime.timedelta(days=inv.frecuencia_de_vencimiento)
                    self.env['megaprint.payment.line'].create({
                        'invoice_id': inv.id,
                        'serial_no': i + 1,
                        'amount': amount,
                        'due_date': new_date.strftime('%Y-%m-%d')
                    })
    
    def generate_xml(self):
        megaprint_dateformat = "%Y-%m-%dT%H:%M:%S"
        item_no = 0
        dte = {}
        adenda = []
        complement_data = []
        complement = {}
        details = []
        details_taxes = []
        details_total_taxes = []
        frases_lines = []
        total_taxes = 0.00
        for inv in self:
            access_number = str(random.randint(100000000, 999999999))
            while True:
                access_count = self.env['account.move'].search_count([('no_acceso', '=', access_number)])
                if access_count > 0:
                    access_number = str(random.randint(100000000, 999999999))
                else:
                    break
            dte['access_number'] = access_number
            date_dte = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.datetime.now())
            dte['date_dte'] = date_dte.strftime(megaprint_dateformat)
            inv.fel_date = date_dte.strftime(megaprint_dateformat)
            #Adenda DTE
            #if not inv.is_export:
            #    #if inv.name:
            #    #    adenda.append({'REFERENCIA_INTERNA': self.name})
            #    #adenda.append({'FECHA_REFERENCIA': date_dte.strftime(megaprint_dateformat)})
            num_to_str = numero_a_texto.Numero_a_Texto(inv.amount_total)
            adenda.append({'TotalEnLetras': num_to_str})
            adenda.append({'textoadicional': inv.name})
            dte['adenda'] = adenda
            #Tipo Documento DTE
            if inv.move_type in ['out_invoice', 'in_invoice']:
                if inv.journal_id.factura_cambiaria == True:
                    dte['tipo'] = 'FCAM'
                else:
                    dte['tipo'] = 'FACT'
            #Frases del DTE
            #if not frases_lines:
            #    frases_lines = [[1, 1]]
            #if self.is_export:
            #    dte['export'] = 'SI'
            if self.frase_ids:
                for frase in self.frase_ids:
                    frases_lines.append([frase.codigo_escenario, frase.tipo_frase])
            else:
                frases_lines = [[1, 1]]
            #Datos emisor
            dte['frases'] = frases_lines
            dte['moneda'] = inv.currency_id.name or 'GTQ'
            dte['establecimiento'] = inv.journal_id.codigo_est
            dte['regimeniva']  = inv.company_id.regimen_iva
            dte['correoemisor'] = inv.company_id.email
            dte['nitemisor'] = inv.company_id.vat.upper() if inv.company_id.vat else 'CF'
            dte['nombrecomercial'] = inv.company_id.nombre_comercial
            dte['nombreemisor'] = inv.company_id.name
            dte['calleemisor'] = inv.company_id.street  if inv.company_id.street  else ''
            dte['municipioemisor'] = inv.company_id.city or '.'
            dte['departamentoemisor'] = inv.company_id.state_id.name or '.'
            dte['postalemisor'] = inv.company_id.zip or '502'
            dte['paisemisor'] = inv.company_id.country_id.code or 'GT'
            #Datos Receptor
            customer_address = inv.partner_id.street
            if inv.partner_id and inv.partner_id.street2:
                customer_address += inv.partner_id.street2
            dte['correoreceptor'] = inv.partner_id.email or ''
            dte['nitreceptor'] = inv.partner_id.vat.upper() if inv.partner_id.vat else 'CF'
            dte['nombrereceptor'] = inv.partner_id.name
            dte['callereceptor'] = customer_address if customer_address else 'CIUDAD'
            dte['municipiorecptor'] = inv.partner_id.city or '.'
            dte['departamentoreceptor'] = inv.partner_id.state_id.name or '.'
            dte['postalreceptor'] = inv.partner_id.zip or '502'
            dte['paisreceptor'] = inv.partner_id.country_id.code or 'GT'
            #Nota de Credito complementos
            if inv.move_type in ['out_refund', 'in_refund']:  # Credit Note
                complement['auth_number_doc_origin'] = inv.uuid_refund
                complement['origin_date'] = str(inv.reversed_entry_id.invoice_date)
                complement['reference'] = inv.ref or ""
                complement['doc_numero_origin'] = inv.reversed_entry_id.fel_no
                complement['doc_serie_origin'] = inv.reversed_entry_id.fel_serie
                #complement_data.append(complement)
                dte['complementos'] = complement
                dte['tipo'] = 'NCRE'
            #Complemento exportaciones exentas
            if inv.is_export:
                dte['export'] = 'SI'
                complement['nombre_consignatario'] =  inv.partner_id.name
                complement['direccion_consignatario'] =  customer_address
                complement['incoterm'] =  inv.invoice_incoterm_id.code or ''
                complement['export_code'] =  inv.company_id.export_code or ''
                dte['complementos'] = complement
            #Items de la factura
            for line in inv.invoice_line_ids:
                #Variables x item
                item = {}
                tax_line = {}
                details_taxes = []
                details_total_taxes = []
                subtotal_taxes = 0.00
                item_no += 1
                price_unit = round(line.price_unit, 6)
                discount_unit = (line.price_unit * (line.discount / 100))
                taxes_unit = line.tax_ids.compute_all((price_unit - discount_unit), inv.currency_id, 1.00, line.product_id, inv.partner_id)
                taxes = line.tax_ids.compute_all((price_unit - discount_unit), inv.currency_id, line.quantity, line.product_id, inv.partner_id)
                print(taxes)
                #difference = 0.00
                #grabable_subtotal = round(taxes.get('total_included', 0.00), 2)
                #grabable_unidad = round(taxes_unit.get('total_included', 0.00),2)
                #difference = (line.quantity)

                #Taxes calculted
                item['grabable'] = "{:.6f}".format(round(taxes.get('total_included', 0.00), 6))
                item['subtotal'] = "{:.6f}".format(round(taxes.get('total_included', 0.00), 6))
                item['descuento'] = "{:.6f}".format(round((discount_unit * line.quantity), 6))
                item['cantidad'] = "{:.6f}".format(round(line.quantity, 6))
                item['descripcion'] = str(line.name)
                item['preciounitario'] = "{:.6f}".format(round(taxes_unit.get('total_included', 0.00), 6))
                item['uom'] = 'UNI'
                item['line'] = str(item_no)
                item['exento'] = '2' if (not line.tax_ids or inv.is_exento) or inv.is_export else '1'
                #if inv.is_exento:
                #    item['exento'] = '2'
                item['tipoitem'] = 'S' if line.product_id.type == 'service' else 'B'
                #if taxes.get('taxes', False):
                for tax in taxes.get('taxes', False):
                    tax_name = ""
                    subtotal_taxes += round(tax.get('amount', 0.00), 6)
                    total_taxes += subtotal_taxes
                    if tax.get('name', '')[0:3] == "IVA":
                        tax_name = 'IVA'
                    else:
                        tax_name = tax.get('name', '')
                    tax_line = {
                        'base': "{:.6f}".format(round(tax.get('base', 0.00), 6)),
                        'tax': "{:.6f}".format(round(tax.get('amount', 0.00), 6)),
                        'tax_name': tax_name,
                        'quantity': "{:.6f}".format(round(line.quantity, 6)),
                    }
                    details_taxes.append(tax_line)
                    details_total_taxes.append(tax_line)
                    item['itemsimpuestos'] = details_taxes
                    item['subtotalimpuestos'] = "{:.6f}".format(round(subtotal_taxes, 6))
                details.append(item)
            dte['items'] = details
            dte['itemimpuestos'] = str(details_total_taxes)
            dte['totalimpuestos'] = "{:.6f}".format(round(total_taxes, 6))
            dte['total'] = "{:.6f}".format(round(inv.amount_total, 6))
        return dte

    def action_post(self):
        xml = False
        res = super(AccountInvoice, self).action_post()
        for rec in self:
            if rec.journal_id.is_fel == True:
                result = self.generate_xml()
                _logger.info(result)
                if rec.move_type in ['out_invoice', 'in_invoice']:
                    xml = self.GenerateXML_FACT(result)
                    _logger.info(xml.decode('utf-8'))
                    
                elif rec.move_type in ['out_refund', 'in_refund']:
                    xml = self.GenerateXML_NCRE(result)
                    _logger.info(xml.decode('utf-8'))
                xml_res = self.generate_xml_dte(xml_dte=xml, transaction="SYSTEM_REQUEST", type="POST_DOCUMENT_SAT")
                response = self.post_dte(str(xml_res.decode('utf-8')))
                self.update_invoice(xml_dte=xml_res.decode('utf-8'), response=response)
                self.action_get_pdf()
                #xml_pdf_req = self.generate_xml_dte(xml_dte=False, transaction="GET_DOCUMENT", type=rec.uuid)
                #response2 = self.post_dte(str(xml_pdf_req.decode('utf-8')))
                #self.update_invoice(xml_dte=xml_res.decode('utf-8'), response=response2)
        return res

    def action_get_pdf(self):
        for rec in self:
            xml_pdf_req = self.generate_xml_dte(xml_dte=False, transaction="GET_DOCUMENT", type=rec.uuid)
            response = self.post_dte(str(xml_pdf_req.decode('utf-8')))
            if response and response.status_code == 200:
                json_res = self.get_xml_dict(xml_reponse=response.content.decode("utf-8"))
                rec.write({
                    'txt_filename': json_res.get('txt_filename', ''),
                    'file': base64.decodebytes(base64.b64encode(str(json_res.get('file', '')).encode('utf-8'))),
                })

    def action_fel_pdf(self):
        for rec in self:
            xml_pdf_req = self.generate_xml_dte(xml_dte=False, transaction="GET_DOCUMENT", type=rec.uuid)
            response = self.post_dte(str(xml_pdf_req.decode('utf-8')))
            #self.update_invoice(xml_dte=xml_res.decode('utf-8'), response=response2)
            if response and response.status_code == 200:
                json_res = self.get_xml_dict(xml_reponse=response.content.decode("utf-8"))
                rec.write({
                    'txt_filename': json_res.get('txt_filename', ''),
                    'file': base64.decodebytes(base64.b64encode(str(json_res.get('file', '')).encode('utf-8'))),
                })
            return {
                'type': 'ir.actions.act_url',
                'name': 'Factura Electroncia',
                'url':"/web/content/?model=" + "account.move" +"&id=" + str(rec.id) + "&filename_field=file_name&field=file&download=true&filename=" + str(rec.txt_filename),
                'target': 'self',
            }

    def update_invoice(self, xml_dte=False, response=False):
        if response and response.status_code == 200:
            _logger.info("********************status_code == 200**************************")
            _logger.info(response.content.decode("utf-8"))
            json_res = self.get_xml_dict(xml_reponse=response.content.decode("utf-8"))
            self.write({
                'xml_request': xml_dte,
                'xml_response': response.content.decode("utf-8"),
                'fel_serie': json_res.get('fel_serie', ''),
                'fel_no': json_res.get('fel_no', ''),
                'uuid': json_res.get('fel_uuid', ''),
                #'fel_date': json_res.get('fel_date', ''),
                #'fel_received_sat': json_res.get('AcuseReciboSAT', ''),
                #'txt_filename': "%s.pdf" %(json_res.get('Autorizacion', '')),
                #'file': base64.decodebytes(base64.b64encode(str(json_res.get('ResponseDATA3', '')).encode('utf-8'))),
                'txt_filename_xml':  json_res.get('txt_filename_xml', ''),
                'file_xml': base64.decodebytes(base64.b64encode(str(json_res.get('file_xml', '')).encode('utf-8'))),
            })

    
    def post_dte(self, xml_dte):
        if xml_dte:
            if not self.company_id.url_request:
                raise UserError(('Para la compañia %s no hay url de firmado configurado.!') %(self.company_id.name))
            post_url = self.company_id.url_request
            nit = self.company_id.vat
            headers = {
                'Content-Type': 'text/xml'
            }
            response = {}
            try:
                response  = requests.post(post_url, data=str(xml_dte), headers=headers, stream=True, verify=False)
            except Exception as e:
                raise Warning(('%s') %(e))
            finally:
                return response

    def generate_xml_dte(self, xml_dte=False, transaction=False, type=False):
        xml_str = ""
        for rec in self:
            if not rec.company_id.url_request:
                raise UserError(('Para la compañia %s no hay url de firmado configurado.!') %(rec.company_id.name))
            if not rec.company_id.vat:
                raise UserError(('Para la compañia %s no hay numero de NIT asignado.!') %(self.company_id.name))
            if not xml_dte and type == 'POST_DOCUMENT_SAT':
                raise UserError(('No se puede certificar con un XML DTE vacio.!'))
            #xml_b64 = base64.b64encode(xml_dte)
            try:
                SoapRequest = Element('soap:Envelope')
                SoapRequest.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
                SoapRequest.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
                SoapRequest.set('xmlns:soap', 'http://schemas.xmlsoap.org/soap/envelope/')
                SoapBody = SubElement(SoapRequest, 'soap:Body')
                SoapTrans = SubElement(SoapBody, 'RequestTransaction')
                SoapTrans.set('xmlns', 'http://www.fact.com.mx/schema/ws')
                SoapRequestor = SubElement(SoapTrans, 'Requestor')
                SoapRequestor.text = str(rec.company_id.request_id)
                SoapType = SubElement(SoapTrans, 'Transaction')
                #SoapType.text = "SYSTEM_REQUEST"
                SoapType.text = transaction
                SoapCountry = SubElement(SoapTrans, 'Country')
                SoapCountry.text = "GT"
                SoapEntity = SubElement(SoapTrans, 'Entity')
                SoapEntity.text = str(rec.company_id.vat)
                SoapUser = SubElement(SoapTrans, 'User')
                SoapUser.text = str(rec.company_id.request_id)
                SoapUserName = SubElement(SoapTrans, 'UserName')
                SoapUserName.text = "ADMINISTRADOR"
                #Data in XML
                SoapData1 = SubElement(SoapTrans, 'Data1')
                SoapData2 = SubElement(SoapTrans, 'Data2')
                SoapData3 = SubElement(SoapTrans, 'Data3')
                #SoapData1.text = "POST_DOCUMENT_SAT" if cancel == False else "VOID_DOCUMENT"
                if type == 'POST_DOCUMENT_SAT':
                    SoapData1.text = type
                    SoapData2.text = base64.b64encode(xml_dte).decode('utf-8')
                    SoapData3.text = str(rec.id)
                if type == 'VOID_DOCUMENT':
                    SoapData1.text = type
                    SoapData2.text = base64.b64encode(xml_dte).decode('utf-8')
                    SoapData3.text = ""
                if transaction == 'GET_DOCUMENT':
                    SoapData1.text = type
                    SoapData2.text = ""
                    SoapData3.text = "PDF"
                #End Data in XML
                rough_string = ET.tostring(SoapRequest)
                reparsed = minidom.parseString(rough_string)
                xml_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
            except Exception as e:
                raise UserError(('%s') %(e))
            finally:
                return xml_str

    def get_xml_dict(self, xml_reponse):
        dict_res = {}
        if xml_reponse:
            xml = ET.fromstring(xml_reponse)
            dict_res = xmltodict.parse(xml_reponse)
            _logger.info("********************XML to DICT**************************")
            _logger.info(dict_res)
            json_data = json.dumps(dict_res)
            json_str = json.loads(json_data)
            _logger.info(json_str)
            SoapRes = json_str['soap:Envelope']['soap:Body']['RequestTransactionResponse']['RequestTransactionResult']
            _logger.info(SoapRes)
            #Get Request a Respose SOAP Service
            SoapResponse = SoapRes.get('Response', False)
            SoapRequest = SoapRes.get('Request', False)
            _logger.info(SoapResponse)
            _logger.info(SoapRequest)
            SoarResult = SoapResponse.get('Result')
            if SoapResponse and SoarResult == "false":
                _logger.info("********************Result = False**************************")
                _logger.info(SoarResult)
                raise UserError(("Codigo: %s - Error: %s  %s") %(SoapResponse.get('Code', False), SoapResponse.get('LastResult', False), SoapResponse.get('Description', False)))
            SoapIndent = SoapResponse.get('Identifier')
            SoapData = SoapRes.get('ResponseData', False)
            dict_res.update({
                'fel_serie': SoapIndent.get('Batch', False),
                'fel_no': SoapIndent.get('Serial', False),
                'fel_uuid': SoapIndent.get('DocumentGUID', False),
                'fel_date': SoapResponse.get('TimeStamp', False),
                'txt_filename': (("%s.pdf") %(SoapIndent.get('DocumentGUID', False))),
                'file': SoapData.get('ResponseData3', False),
                'txt_filename_xml': (("%s.xml") %(SoapIndent.get('SuggestedFileName', False))),
                'file_xml': SoapData.get('ResponseData1', False),
            })
        return dict_res

    def generate_xml_cancel(self):
        megaprint_dateformat = "%Y-%m-%dT%H:%M:%S"
        xml_str = ""
        for rec in self:
            try:
                GTAnulacionDocumento = Element('dte:GTAnulacionDocumento')
                GTAnulacionDocumento.set('xmlns:dte', 'http://www.w3.org/2000/09/xmldsig#')
                GTAnulacionDocumento.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
                GTAnulacionDocumento.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.1.0')
                GTAnulacionDocumento.set('xsi:schemaLocation', 'http://www.sat.gob.gt/dte/fel/0.1.0 GT_AnulacionDocumento-0.1.0.xsd')
                GTAnulacionDocumento.set('Version', '0.1')
                sat = SubElement(GTAnulacionDocumento, 'dte:SAT')
                AnulacionDTE = SubElement(sat, 'dte:AnulacionDTE')
                AnulacionDTE.set('ID', 'DatosCertificados')
                DatosGenerales = SubElement(AnulacionDTE, 'dte:DatosGenerales')
                DatosGenerales.set('ID', 'DatosAnulacion')
                DatosGenerales.set('NumeroDocumentoAAnular', str(rec.uuid))
                DatosGenerales.set('NITEmisor', str(rec.company_id.vat))
                DatosGenerales.set('IDReceptor', str(rec.partner_id.vat.upper() if rec.partner_id.vat else 'CF'))
                DatosGenerales.set('FechaEmisionDocumentoAnular', str(rec.fel_date))
                #DatosGenerales.set('FechaHoraAnulacion', str(rec.fel_date))
                date_fel = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.datetime.now())
                DatosGenerales.set('FechaHoraAnulacion', str(date_fel.strftime(megaprint_dateformat)))
                DatosGenerales.set('MotivoAnulacion', str(rec.narration))
                #Datos del certificador
                #DatoCertificador = SubElement(AnulacionDTE, 'dte:Certificacion')
                #NitCertificador = SubElement(DatoCertificador, 'dte:NITCertificador')
                #NitCertificador.text = '10815165-4'
                #NombreCertificador = SubElement(DatoCertificador, 'dte:NombreCertificador')
                #NombreCertificador.text = 'CORPOSISTEMAS, SOCIEDAD ANONIMA'
                #FechaHora = SubElement(DatoCertificador, 'dte:FechaHoraCertificacion')
                #date_dte = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.datetime.now())
                #FechaHora.text = str(date_dte.strftime(megaprint_dateformat))
                #To XML to String
                rough_string = ET.tostring(GTAnulacionDocumento)
                reparsed = minidom.parseString(rough_string)
                xml_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
            except Exception as e:
                raise UserError(('%s') %(e))
            finally:
                return xml_str
    
    def action_cancel_fel(self):
        view = self.env.ref('account_invoice_fel_corposistemas.wizard_cancel_fel')
        new_id = self.env['wizard.fel.cancel']
        for rec in self:
            vals = {
                'invoice_id': rec.id or False,
            }
            view_id = new_id.create(vals)
            return {
                'name': _("Anulacion FEL"),
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': view_id.id,
                'view_type': 'form',
                'res_model': 'wizard.fel.cancel',
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    def post_cancel_dte(self, xml_dte):
        if xml_dte:
            if not self.company_id.url_request:
                raise UserError(('Para la compañia %s no hay url de firmado configurado.!') %(self.company_id.name))
            post_url = self.company_id.url_request
            nit = self.company_id.vat
            headers = {
                'Content-Type': 'text/xml'
            }
            response = {}
            try:
                _logger.info("******************AVOID_DOCUMENT******************")
                _logger.info(xml_dte)
                response  = requests.post(post_url, data=str(xml_dte), headers=headers, stream=True, verify=False)
                _logger.info(response.content)
                json_res = self.get_xml_dict(xml_reponse=response.content.decode("utf-8"))
                _logger.info(json_res)
            except Exception as e:
                raise Warning(('%s') %(e))
            if response and response.status_code == 200:
                #json_res = json.loads(response.content.decode("utf-8"))
                self.write({
                    'be_cancel': True,
                    #'fel_codes_cancel': json_res.get('CodigosSAT', ''),
                    #'fel_cancel_sat': json_res.get('AcuseReciboSAT', ''),
                    'txt_filename_cancel': json_res.get('txt_filename_xml', ''),
                    'file_cancel': base64.decodebytes(base64.b64encode(str(json_res.get('file_xml', '')).encode('utf-8'))),
                })


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
