# -*- coding: utf-8 -*-

import random

import datetime
import uuid
from odoo import fields, models, api
from odoo.exceptions import UserError, Warning

import base64
from odoo.tools.translate import _
import requests
import json
from ast import literal_eval

#XML libraries
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, fromstring
from xml.dom import minidom
from odoo.addons.account_invoice_megaprint import numero_a_texto
from odoo.addons.account_invoice_megaprint import cdata

import logging
_logger = logging.getLogger(__name__)

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
    frase_ids = fields.Many2many('satdte.frases', 'inv_frases_rel', 'inv_id', 'frases_id', 'Frases')

    factura_cambiaria = fields.Boolean('Factura Cambiaria', related='journal_id.factura_cambiaria', readonly=True)
    number_of_payments = fields.Integer('Cantidad De Abonos', default=1, copy=False, help='Number Of Payments')
    frecuencia_de_vencimiento = fields.Integer('Frecuencia De Vencimiento', copy=False, help='Due date frequency (calendar days)')
    megaprint_payment_lines = fields.One2many('megaprint.payment.line', 'invoice_id', 'Payment Info', copy=False)
    xml_request = fields.Text(string='XML Request', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_response = fields.Text(string='XML Response', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_response_cancel = fields.Text(string='XML Response', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_notes = fields.Text('XML Children')
    uuid_refund = fields.Char('UUID a rectificar', related="invoice_refund_id.uuid")
    txt_filename = fields.Char('Archivo', required=False, readonly=True, copy=False)
    file = fields.Binary('Archivo', required=False, readonly=True, copy=False)
    txt_filename_xml = fields.Char('Archivo XML', required=False, readonly=True, copy=False)
    file_xml = fields.Binary('Archivo XML', required=False, readonly=True, copy=False)
    invoice_refund_id = fields.Many2one('account.move', 'Invoice Refund', required=False, readonly=False)
    is_fel = fields.Boolean('FEL', related="journal_id.is_fel")
    be_cancel = fields.Boolean('DTE Anulado', default=False)
    partner_vat = fields.Char('Nit', readonly=False, related='partner_id.vat')
    numero_origen = fields.Char('Número de documento de Origen', related="invoice_refund_id.fel_no")
    serie_origen = fields.Char('Serie documento de origen', related="invoice_refund_id.fel_serie")

    notes = fields.Char()
    active_contingencia = fields.Boolean('Activar Contigencia', required=False, default=False)
    xml_request_contingencia = fields.Text(string='XML Request Contigencia', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    customer_name = fields.Char('Cliente')
    customer_addres = fields.Char('Direccion')

    @api.onchange('company_id')
    def onchange_frases(self):
        if self.company_id and self.company_id.frase_ids:
            self.frase_ids = self.company_id.frase_ids.ids

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
    
    #Certificacion documentos en contigencia
    def action_certificate_dte(self):
        for inv in self:
            try:
                if not inv.xml_request_contingencia and not inv.active_contingencia == False:
                    continue
                xml_request = inv.dte_request(xml_string=str(inv.xml_request_contingencia), type_request='FirmaDocumentoRequest')
                xml_sing = inv.get_signature(xml_request.decode('utf-8'))
                xml_signed = inv.dte_request(xml_string=xml_sing, type_request='RegistraDocumentoXMLRequest')
                inv.register_dte(xml_signed.decode('utf-8'))
                _logger.info("***************DTE EN CONTIGENCIA -CERTIFICACION-***************")
                _logger.info(inv.xml_request)
                if inv.uuid:
                    inv.write({
                        'active_contingencia': False,
                    })
                log = ("----------------Factura %s Certificada----------------" %(inv.name))
                _logger.info(log)
                inv.env.cr.commit()
            except Exception as e:
                error = ("%s" %(e))
                _logger.info(error)
                raise UserError(('%s') %(error))
        return True

    #Funcion para certificar DTE en contigencia
    @api.model
    def _cron_certificate_dte(self):
        invoice_ids = self.env['account.move'].search([
            ('active_contingencia', '=', True), 
            ('state', 'not in', ('draft', 'cancel')),
            ('move_type', 'in', ('out_invoice', 'out_refund'))])
        for inv in invoice_ids:
            try:
                if not inv.xml_request_contingencia and not inv.active_contingencia == False:
                    continue
                xml_request = inv.dte_request(xml_string=str(inv.xml_request_contingencia), type_request='FirmaDocumentoRequest')
                xml_sing = inv.get_signature(xml_request.decode('utf-8'))
                xml_signed = inv.dte_request(xml_string=xml_sing, type_request='RegistraDocumentoXMLRequest')
                inv.register_dte(xml_signed.decode('utf-8'))
                _logger.info("***************DTE EN CONTIGENCIA -CERTIFICACION-***************")
                _logger.info(inv.xml_request)
                if inv.uuid:
                    inv.write({
                        'active_contingencia': False,
                    })
                log = ("----------------Factura %s Certificada----------------" %(inv.name))
                _logger.info(log)
                inv.env.cr.commit()
            except Exception as e:
                error = ("%s" %(e))
                _logger.info(error)
                pass


    def action_post(self):
        res = super(AccountInvoice, self).action_post()
        self.customer_name = self.partner_id.name
        self.customer_addres = self.partner_id.street
        if self.move_type in ('out_invoice', 'out_refund') and self.journal_id.is_fel == True:
            if self.journal_id.active_contingencia == True:
                xml = self.generate_xml()
                _logger.info("***************DTE EN CONTIGENCIA***************")
                _logger.info(xml.decode('utf-8'))
                self.write({
                    'active_contingencia': True,
                    'xml_request_contingencia': xml.decode('utf-8'),
                })
            else:
                xml = self.generate_xml()
                _logger.info("***************DTE***************")
                _logger.info(xml.decode('utf-8'))
                xml_request = self.dte_request(xml_string=xml.decode('utf-8'), type_request='FirmaDocumentoRequest')
                xml_sing = self.get_signature(xml_request.decode('utf-8'))
                xml_signed = self.dte_request(xml_string=xml_sing, type_request='RegistraDocumentoXMLRequest')
                self.register_dte(xml_signed.decode('utf-8'))
        return res

    def validate_nit(self, nit=None):
        res = False
        res_nit = False
        if nit:
            res_nit = nit.upper()
            if ' ' in res_nit:
                res_nit = res_nit.replace(' ', '')
            if '-' in res_nit:
                res_nit = res_nit.replace('-', '')
            if '/' in res_nit:
                res_nit = res_nit.replace('/', '')
        return res_nit

    def generate_xml(self):
        res_xml = False
        megaprint_dateformat = "%Y-%m-%dT%H:%M:%S"
        no_lin = 1
        AdendaSummary = []
        Complemento_Data = {}
        _items = []
        total_impuesto = 0

        gran_total = 0

        # Generate 9 digit random number as a Access Number
        no_acceso = str(random.randint(100000000, 999999999))
        while True:
            acceso = self.env['account.move'].search_count([('no_acceso', '=', no_acceso)])
            if acceso > 0:
                no_acceso = str(random.randint(100000000, 999999999))
            else:
                break
        #Se agrego el no_acceso al formulario para manejar la contigencia
        self.no_acceso = no_acceso

        # Current time For the tag FechaHoraEmision
        fecha = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.datetime.now())
        if fecha:
            fecha_str = str(fecha.strftime(megaprint_dateformat))
            self.fel_date = fecha_str
        
        if self.name:
            numero = self.name.split('/')
            if numero:
                AdendaSummary.append(numero[0]) #valor1
                AdendaSummary.append(numero[2]) #valor2
        AdendaSummary.append(str(numero_a_texto.Numero_a_Texto(self.amount_total))) #valor3
        AdendaSummary.append(str(self.amount_total)) #valor4
        AdendaSummary.append(str(self.invoice_date_due)) #valor5
        AdendaSummary.append(str(self.invoice_origin)) #valor6
        for inv_line in self.invoice_line_ids:
            if inv_line.display_type == 'line_section':
                continue
            detail = []
            if inv_line.product_id.type == 'service':
                bien_servicio = 'S'
            else:
                bien_servicio = 'B'

            total_price = round((inv_line.price_unit * inv_line.quantity), 2)
            discount = round((total_price * ((inv_line.discount or 0.0) / 100.0)), 2)
            # grabable = total_price - discount
            grabable = round(((total_price - discount) / 1.12), 2)
            MontoImp = round((total_price - discount - grabable), 2)
            total_impuesto += MontoImp
            total = grabable + MontoImp
            gran_total += total
            descripcion_not = inv_line.name
            #AdendaSummary.append(inv_line.name)

            if str(inv_line.product_uom_id.name):
                uom = "UNI"
            else:
                uom = inv_line.product_uom_id.name
                uom = uom.encode('utf-8')

            for tax in inv_line.tax_ids:
                if tax.name[0:3] == "IVA":
                    iva_grabable = str(grabable)
                    iva_qty = str(inv_line.quantity)
                    iva = str(total_price - grabable)
                    #if inv_line.price_tax:
                    #    iva = str(inv_line.price_tax)
                    # iva = '''<dte:Impuestos><dte:Impuesto><dte:NombreCorto>IVA</dte:NombreCorto><dte:CodigoUnidadGravable>1</dte:CodigoUnidadGravable><dte:MontoGravable>'''+grabable+'''</dte:MontoGravable><dte:CantidadUnidadesGravables>'''+str(inv_line.quantity)+'''</dte:CantidadUnidadesGravables><dte:MontoImpuesto>'''+str(inv_line.price_tax)+'''</dte:MontoImpuesto></dte:Impuesto></dte:Impuestos>'''

            detail.append(bien_servicio)  # Product Type
            detail.append(no_lin)  # Line number
            no_lin += 1
            detail.append(round(inv_line.quantity, 2))  # Product Quantity
            detail.append(uom)  # Unit Of Measure
            detail.append(descripcion_not)  # Product description
            detail.append(round(inv_line.price_unit, 2))  # Price of the product
            detail.append(round(total_price, 2))  # Total Price
            detail.append(round(discount, 2))  # Product Discount
            # IVA info
            detail.append(round(grabable, 2))
            detail.append(round(inv_line.quantity, 2))  # Product Quantity
            detail.append(round(MontoImp, 2))
            detail.append(round(total, 2))
            _items.append(detail)

        total_impuesto = round(total_impuesto, 2)
        gran_total = round(gran_total, 2)

        codeEstab = self.journal_id.codigo_est or ''  # Company Establishment Code
        afIVA = self.company_id.regimen_iva or 'GEN'  # Company Associated VAT regime OR 'GEN'(Default)
        correoEmisor = self.company_id.email or ''  # Company Email
        nitEmisor = self.company_id.vat or ''  # Compant vat No
        nombreComercial = self.journal_id.company_name_display if self.journal_id.use_street and self.journal_id.company_name_display else self.company_id.nombre_comercial  # Company Tradename
        nombreRec = ""
        calleRec = ""
        departamentoRec = ""
        postalRec = ""
        paisRec = ""
        municipioRec = ""
        DatosCliente = False
        nombreEmisor = self.company_id.name or ''  # Company Name
        # Company Address Details
        if self.journal_id.use_street:
            calleEmisor = self.journal_id.establecimiento_street
        else:
            if self.company_id.street:
                calleEmisor = self.company_id.street
            else:
                calleEmisor = "Ciudad"
            if self.company_id.street2:
                calleEmisor = calleEmisor + ' ' + self.company_id.street2 or ''
        if self.company_id.city:
            municipioEmisor = self.company_id.city
        else:
            municipioEmisor = '.'
        if self.company_id.state_id:
            departamentoEmisor = self.company_id.state_id.name or ''
        else:
            departamentoEmisor = "."
        if self.company_id.zip:
            postalEmisor = self.company_id.zip
        else:
            postalEmisor = "502"
        if self.company_id.country_id.code:
            paisEmisor = self.company_id.country_id.code or ''
        else:
            paisEmisor = "GT"
        # Partner Details
        #if not self.partner_id.vat or self.partner_id.var != "CF":
        #DatosCliente = self.get_datos_cliente(nitEmisor, self.partner_id.vat)
        if self.partner_id.email:
            correoRec = self.partner_id.email
        else:
            correoRec = ""
        nit = self.validate_nit(nit=self.partner_id.vat)
        if nit:
            vatRec = nit
        elif nit == 'EXPORT':
            vatRec = "EXPORT"
        elif nit == "CF":
            vatRec = "CF"
        else:
            vatRec = "CF"
        if self.partner_id.type_document=='CUI':
            if not nit:
                raise UserError('Para realizar facturas de tipo especial se requiere llenar el campo CUI/Pasaporte')
        elif vatRec == "CF" and self.company_id.limit_with_cf < gran_total:
            raise UserError('Para facturas mayores a 2500.00 se requiere llenar el campo CUI/Pasaporte o un NIT que no sea CF')

        #if vatRec not in ['CF', 'EXPORT']:
        #    DatosCliente = self.get_datos_cliente((self.partner_vat if self.partner_vat else self.partner_id.vat))
        #    if DatosCliente:
        #        nombreRec = DatosCliente[0] if DatosCliente[0] else "Consumidor Final"
        #        calleRec = DatosCliente[1] if DatosCliente[1] else "CF"
        #        postalRec = self.partner_id.zip if self.partner_id.zip else "502"
        #        paisRec = self.partner_id.country_id.code if self.partner_id.country_id.code else "GT"
        #        municipioRec = self.partner_id.city if self.partner_id.city else ""
        #else:
        if self.partner_id.name:   
            nombreRec = self.partner_id.name or "Consumidor Final"
        if self.partner_id.street:
            calleRec = self.partner_id.street
        else:
            calleRec = "Ciudad"
        if self.partner_id.street2:
            calleRec = calleRec + ' ' + self.partner_id.street2
        if self.partner_id.city:
            municipioRec = self.partner_id.city
        else:
            municipioRec = "."
        if self.partner_id.state_id:
            departamentoRec = self.partner_id.state_id.name
        else:
            departamentoRec = "."
        if self.partner_id.zip:
            postalRec = self.partner_id.zip
        else:
            postalRec = "502"
        if self.partner_id.country_id:
            paisRec = self.partner_id.country_id.code
        else:
            paisRec = "GT"

        fases_lines = []  # Frase Information
        for frase in self.frase_ids:
            fases_lines.append([frase.codigo_escenario, frase.tipo_frase])
        if not fases_lines:
            fases_lines = [[1, 1]]

        # currency = self.currency_id.name
        currency = 'GTQ'

        uuid_txt = uuid.uuid4()
        self.uuid = uuid_txt

        Complemento_Data['origin_date'] = str(self.invoice_refund_id.invoice_date)
        Complemento_Data['auth_number_doc_origin'] = str(self.uuid)

        if self.move_type in ['out_invoice', 'in_invoice']:
            #raise UserError('Entro a genera el XML')
            if self.journal_id.factura_cambiaria:  # Cambiaria Invoice
                res_xml = self.GenerateXML_FCAM(currency, fecha_str, no_acceso, "FCAM", afIVA, codeEstab, correoEmisor, nitEmisor, nombreComercial,
                                      nombreEmisor, calleEmisor, postalEmisor, municipioEmisor, departamentoEmisor, paisEmisor, correoRec,
                                      vatRec, nombreRec, calleRec, postalRec, municipioRec, departamentoRec, paisRec, fases_lines,
                                      _items, total_impuesto, gran_total, uuid_txt, Complemento_Data, AdendaSummary)
                #self.send_appfirma(res_xml)
                #self.xml_request = res_xml
            else:  # Normal Invoice
                res_xml = self.GenerateXML_FACT(currency, fecha_str, no_acceso, "FACT", afIVA, codeEstab, correoEmisor, nitEmisor, nombreComercial,
                                      nombreEmisor, calleEmisor, postalEmisor, municipioEmisor, departamentoEmisor, paisEmisor, correoRec,
                                      vatRec, nombreRec, calleRec, postalRec, municipioRec, departamentoRec, paisRec, fases_lines,
                                      _items, total_impuesto, gran_total, uuid_txt, AdendaSummary)
                #raise UserError(('%s')%(res_xml))
                #self.send_appfirma(res_xml)
                #self.xml_request = res_xml

        if self.move_type in ['out_refund', 'in_refund']:  # Credit Note
            #uuid_txt = self.uuid_refund
            #self.uuid = uuid_txt
            Complemento_Data['auth_number_doc_origin'] = str(self.uuid_refund)
            res_xml = self.GenerateXML_NCRE(currency, fecha_str, no_acceso, "NCRE", afIVA, codeEstab, correoEmisor, nitEmisor, nombreComercial,
                                  nombreEmisor, calleEmisor, postalEmisor, municipioEmisor, departamentoEmisor, paisEmisor, correoRec,
                                  vatRec, nombreRec, calleRec, postalRec, municipioRec, departamentoRec, paisRec, fases_lines,
                                  _items, total_impuesto, gran_total, uuid_txt, Complemento_Data, AdendaSummary)
            #self.send_appfirma(res_xml)
            #self.xml_request = res_xml
        # return super(AccountInvoice, self).action_invoice_open()
        return res_xml

    def dte_request(self, xml_string=False, type_request=False, uuid_res=False, nit=False):
        xml = ""
        uuid_txt = uuid.uuid4()
        if xml_string:
            try:
                if type_request == 'FirmaDocumentoRequest':
                    FirmaDocument = Element('FirmaDocumentoRequest')
                    xml_dte = SubElement(FirmaDocument, 'xml_dte')
                    xml_dte.append(cdata.CDATA(xml_string))
                    xml = tostring(FirmaDocument)
                elif type_request == 'RegistraDocumentoXMLRequest':
                    RegistraDocumento = Element('RegistraDocumentoXMLRequest')
                    RegistraDocumento.set('id', str(uuid_txt).upper())
                    xml_dte = SubElement(RegistraDocumento, 'xml_dte')
                    xml_dte.append(cdata.CDATA(xml_string))
                    xml = tostring(RegistraDocumento)
                elif type_request == 'AnulaDocumentoXMLRequest':
                    AnulaDocumentoXMLRequest = Element('AnulaDocumentoXMLRequest')
                    AnulaDocumentoXMLRequest.set('id', str(uuid_txt).upper())
                    xml_dte = SubElement(AnulaDocumentoXMLRequest, 'xml_dte')
                    xml_dte.append(cdata.CDATA(xml_string))
                    xml = tostring(AnulaDocumentoXMLRequest)
                elif type_request == 'RetornaPDFRequest':
                    RetornaPDFRequest = Element('RetornaPDFRequest')
                    uuid_tag = SubElement(RetornaPDFRequest, 'uuid')
                    uuid_tag.text = str(uuid_res)
                    xml = tostring(RetornaPDFRequest)
                elif type_request == 'RetornaDatosClienteRequest':
                    RetornaCliente = Element('RetornaDatosClienteRequest')
                    nit_node = SubElement(RetornaCliente, 'nit')
                    nit_node.text = str(nit)
                    xml = tostring(RetornaCliente)
                elif type_request == 'retornaDatosClienteCui':
                    RetornaCliente = Element('RetornaDatosClienteRequestCUI')
                    nit_node = SubElement(RetornaCliente, 'CUI')
                    nit_node.text = str(nit)
                    xml = tostring(RetornaCliente)
            except Exception as e:
                raise UserError(("%s") %(e))
            finally:
                return xml

    def register_dte(self, xml_signed):
        if xml_signed:
            xml = fromstring(xml_signed)
            xml_res = tostring(xml)
            response  = self.post_dte(xml_res.decode('utf-8'), 'register_dte')
            if response and response.status_code == 200:
                self.xml_validation(response.content.decode('utf-8'))
                res_dict = self.get_xml_dict(response.content.decode('utf-8'))
                fel_dict = self.get_number_fel(res_dict['uuid'])
                pdf_xml = self.dte_request(xml_res, 'RetornaPDFRequest', res_dict['uuid'])
                pdf_response  = self.post_dte(pdf_xml.decode('utf-8'), 'pdf_dte')
                pdf_dict = self.get_pdf_dict(pdf_response.content.decode('utf-8'))
                self.write({
                    'xml_response': response.content.decode('utf-8'),
                    'uuid': res_dict['uuid'],
                    'fel_serie': fel_dict['serie'],
                    'fel_no': fel_dict['numero'],
                    'txt_filename': "%s.pdf" %(res_dict['uuid']),
                    'file': base64.decodebytes(base64.b64encode(str(pdf_dict.get('pdf', '')).encode('utf-8'))),
                })
            else:
                self.xml_validation(response.content.decode('utf-8'))
        return True
    
    def get_signature(self, xml_request):
        xml_signed = ""
        if xml_request:
            response  = self.post_dte(xml_request, 'sign_dte')
            if response and response.status_code == 200:
                self.xml_validation(response.content.decode('utf-8'))
                res_dict = self.get_xml_dict(response.content.decode('utf-8'))
                xml_signed = res_dict['xml_dte']
                self.write({
                    'xml_request': res_dict['xml_dte'],
                    'uuid': res_dict['uuid'],
                })
            else:
                self.xml_validation(response.content.decode('utf-8'))
        return xml_signed
    
    def post_dte(self, xml_request, type):
        """
            Types:
                * sign_dte : this type send a xml to sign at FirmaDocumentoRequest
                * register_dte : This type send a xm to sign a RegistraDocumentoXMLRequest
                * cancel_dte : This type send a xml to cancel
                * pdf_dte : This type return the binary pdf
                * customer_data : This tyep return the data of customer on invoice
        """
        if xml_request and type:
            response = False
            #Validaciones de contenido
            if not self.company_id.token_access:
                raise UserError(('La empresa %s no tiene token de autorizacion generado') %(self.company_id.name))
            if not self.company_id.url_request_signature:
                raise UserError(('No hay URL para firma de DTE en la compañia %s') %(self.company_id.name))
            if not self.company_id.url_request:
                raise UserError(('No hay URL para registro de DTE en la compañia %s') %(self.company_id.name))
            if not self.company_id.url_cancel:
                raise UserError(('No hay URL para anulacion de DTE en la compañia %s') %(self.company_id.name))
            if not self.company_id.url_pdf:
                raise UserError(('No hay URL para retorno de PDF para el DTE en la compañia %s') %(self.company_id.name))
            #Get url to send the xml
            if type == 'sign_dte':
                post_url = self.journal_id.company_id.url_request_signature
            elif type == 'register_dte':
                post_url = self.journal_id.company_id.url_request
            elif type == 'cancel_dte':
                post_url = self.journal_id.company_id.url_cancel
            elif type == 'pdf_dte':
                post_url = self.journal_id.company_id.url_pdf
            elif type == 'datos_cliente':
                post_url = self.journal_id.company_id.url_customer
            headers = {
                "Content-type": "application/xml",
                "Authorization": "Bearer " + str(self.company_id.token_access)
            }
            try:
                response  = requests.post(post_url, data=xml_request, headers=headers, stream=True, verify=False)
                return response
            except Exception as e:
                raise UserError(('%s') %(e))
            #finally:
            #    return response

    def get_xml_dict(self, xml_reponse):
        dict_res = {}
        if xml_reponse:
            xml = fromstring(xml_reponse)
            for child in xml:
                #print(child.text)
                if child.tag ==  'xml_dte':
                    dict_res.update({'xml_dte': child.text})
                elif child.tag == 'uuid':
                    dict_res.update({'uuid': child.text})
        return dict_res

    def get_pdf_dict(self, xml_reponse):
        dict_res = {}
        if xml_reponse:
            xml = fromstring(xml_reponse)
            for child in xml:
                if child.tag == 'pdf':
                    dict_res.update({'pdf': child.text})
        return dict_res
    
    def xml_validation(self, xml_str):
        lst_errores = ""
        lst_tags = ""
        if xml_str:
            tree = fromstring(xml_str)
            for child in tree:
                if child.tag == 'tipo_respuesta':
                    if child.text != '0':
                        for subchild in tree:
                            if subchild.tag == 'listado_errores':
                                for error in subchild:
                                    for suberror in error:
                                       lst_errores += "%s %s \n" %(suberror.tag, suberror.text)
                                raise UserError(('%s') %(lst_errores))
            return True

    def get_number_fel(self, uuid):
        if uuid:
            hexa = '0x'
            uuid_res = uuid.split('-')
            serie = uuid_res[0]
            number = literal_eval(hexa + uuid_res[1] + uuid_res[2])
            return {
                'serie': serie,
                'numero': number,
            }

    def generate_xml_cancel(self):
        megaprint_dateformat = "%Y-%m-%dT%H:%M:%S"
        xml_str = ""
        for rec in self:
            try:
                GTAnulacionDocumento = Element('ns:GTAnulacionDocumento')
                GTAnulacionDocumento.set('xmlns:ds', 'http://www.w3.org/2000/09/xmldsig#')
                GTAnulacionDocumento.set('xmlns:ns', 'http://www.sat.gob.gt/dte/fel/0.1.0')
                GTAnulacionDocumento.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
                GTAnulacionDocumento.set('Version', '0.1')
                sat = SubElement(GTAnulacionDocumento, 'ns:SAT')
                AnulacionDTE = SubElement(sat, 'ns:AnulacionDTE')
                AnulacionDTE.set('ID', 'DatosCertificados')
                DatosGenerales = SubElement(AnulacionDTE, 'ns:DatosGenerales')
                DatosGenerales.set('ID', 'DatosAnulacion')
                DatosGenerales.set('NumeroDocumentoAAnular', str(rec.uuid))
                DatosGenerales.set('NITEmisor', str(rec.company_id.vat))
                DatosGenerales.set('IDReceptor', str(rec.partner_id.vat))
                DatosGenerales.set('FechaEmisionDocumentoAnular', str(rec.fel_date))
                date_fel = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.datetime.now())
                DatosGenerales.set('FechaHoraAnulacion', str(date_fel.strftime(megaprint_dateformat)))
                DatosGenerales.set('MotivoAnulacion', str(rec.narration))
                #To XML to String
                xml_str = tostring(GTAnulacionDocumento)
                return xml_str
            except Exception as e:
                raise UserError(('%s') %(e))

    def action_cancel_fel(self):
        view = self.env.ref('account_invoice_megaprint.wizard_cancel_fel')
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

    def post_cancel_dte(self):
        xml = self.generate_xml_cancel()
        xml_request = self.dte_request(xml_string=xml.decode('utf-8'), type_request='FirmaDocumentoRequest')
        response  = self.post_dte(xml_request, 'sign_dte')
        if response and response.status_code == 200:
            self.xml_validation(response.content.decode('utf-8'))
            res_dict = self.get_xml_dict(response.content.decode('utf-8'))
            xml_sign = res_dict['xml_dte']
            xml_signed = self.dte_request(xml_string=xml_sign, type_request='AnulaDocumentoXMLRequest')
            response_2  = self.post_dte(xml_signed.decode('utf-8'), 'cancel_dte')
            if response_2 and response_2.status_code == 200:
                self.xml_validation(response_2.content.decode('utf-8'))
                self.write({
                    'xml_response_cancel': response_2.content.decode('utf-8'),
                })
            else:
                raise UserError(('(%s) -%s') %(response_2.status_code, response_2.content.decode('utf-8')))
        else:
            raise UserError(('(%s) -%s') %(response.status_code, response.content.decode('utf-8')))
        return True

    def get_datos_cliente(self, nit_cliente=False):
        NombreCliente = ""
        DireccionCliente = ""
        if nit_cliente:
            XmlRequest = self.dte_request(xml_string=True, type_request='RetornaDatosClienteRequest', uuid_res=False, nit=nit_cliente)
            if XmlRequest:
                res = self.post_dte(xml_request=XmlRequest, type='datos_cliente')
                self.xml_validation(res.content.decode('utf-8'))
                NombreCliente = self.get_nombre(res.content.decode('utf-8'))
                DireccionCliente = self.get_direccion(res.content.decode('utf-8'))
        return NombreCliente, DireccionCliente
    
    def get_direccion(self, xml_str):
        var = ""
        if xml_str:
            tree = fromstring(xml_str)
            for child in tree:
                if child.tag == 'direcciones':
                    for subchild in child:
                        if subchild.tag == 'direccion':
                            var = subchild.text
        return var

    def get_nombre(self, xml_str):
        var = ""
        tree = fromstring(xml_str)
        for child in tree:
            if child.tag == 'nombre':
                var = child.text
        return var
    
    def get_nombre_cliente_cui(self, cui):
        Nombre_Cliente = ''
        if cui:
            XmlRequest = self.dte_request(xml_string=True, type_request='retornaDatosClienteCui', uuid_res=False, nit=cui)
            if XmlRequest:
                if XmlRequest:
                    res = self.post_dte(xml_request=XmlRequest, type='datos_cliente_cui')
                    Nombre_Cliente = self.get_nombre(res.content.decode('utf-8'))
        return Nombre_Cliente

    @api.model
    def create(self, vals):
        if 'frase_ids' not in vals:
            vals.update({
                'frase_ids': self.env.company.frase_ids.ids if self.env.company.frase_ids else False,
            })
        res = super(AccountInvoice, self).create(vals)
        return res

    def action_print_fel(self):
        rec = self
        return {
            'type': 'ir.actions.act_url',
            'name': 'Factura Electroncia',
            'url':"/web/content/?model=" + "account.move" +"&id=" + str(rec.id) + "&filename_field=file_name&field=file&download=true&filename=" + str(rec.txt_filename),
            'target': 'self',
        }
    
    @api.onchange('partner_vat')
    def onchange_nit(self):
        if self.partner_vat:
            nit = self.partner_vat
            if '-' in nit:
                self.partner_vat = nit.replace('-', '')
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

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.onchange('vat')
    def onchange_nit(self):
        if self.vat:
            nit = self.vat
            if '-' in nit:
                self.vat = nit.replace('-', '')
ResPartner()