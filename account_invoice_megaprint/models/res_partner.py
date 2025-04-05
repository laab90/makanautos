# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.http import request
import requests
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, fromstring

import re
class ResPartner(models.Model):
    _inherit = 'res.partner'


    cui_pasaporte = fields.Char('CUI/Pasaporte')
    is_extranjero = fields.Boolean('Es extrajero')
    tipo_especial = fields.Boolean('Tipo Especial')
    #tipo de documento
    type_document = fields.Selection([
        ('CUI', 'Con DPI'),
        ('EXT', 'Con Pasaporte'),
        ('NIT', 'Con NIT')], string="Documento", default="NIT")

    @api.onchange('cui_pasaporte', 'vat')
    def on_change_id_partner(self):
        if not self.name:
            self.name = 'CF'

    def button_get_data_nit(self):
        print('get clientes')
        if self.vat not in ['', 'CF', 'EXT', 'EXPORT', False, None]:
            self.name, self.street = self.get_datos_cliente(self.vat)

    def button_get_datos_CUI(self):
        for rec in self:
            if rec.cui_pasaporte not in ['', 'CF', 'EXT', 'EXPORT', False, None]:
                rec.name = rec.get_nombre_cliente_cui(rec.cui_pasaporte)

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

    def get_nombre(self, xml_str):
        var = ""
        tree = fromstring(xml_str)
        for child in tree:
            if child.tag == 'nombre':
                var = child.text
        return var

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

    def post_dte(self, xml_request, type):
        if xml_request and type:
            response = False
            #Validaciones de contenido
            if not self.create_uid.company_id.token_access:
                raise UserError(('La empresa %s no tiene token de autorizacion generado') %(self.create_uid.company_id.name))
            if not self.create_uid.company_id.url_request_signature:

                raise UserError(('No hay URL para firma de DTE en la compañia %s') %(self.create_uid.company_id.name))
            if not self.create_uid.company_id.url_request:
                raise UserError(('No hay URL para registro de DTE en la compañia %s') % (self.create_uid.company_id.name))


            if type == 'datos_cliente':
                post_url = self.create_uid.company_id.url_customer
            elif type == 'datos_cliente_cui':
                post_url = self.create_uid.company_id.url_customer_cui
            headers = {
                "Content-type": "application/xml",
                "Authorization": "Bearer " + str(self.create_uid.company_id.token_access)
            }
            try:
                response = requests.post(post_url, data=xml_request, headers=headers, stream=True, verify=False)
                return response
            except Exception as e:

                raise UserError(('%s') %(e))

    def get_datos_cliente(self, nit_cliente=False):
        NombreCliente = ""
        DireccionCliente = ""
        if nit_cliente:
            XmlRequest = self.dte_request(type_request='RetornaDatosClienteRequest')
            if XmlRequest:
                res = self.post_dte(xml_request=XmlRequest, type='datos_cliente')
                self.xml_validation(res.content.decode('utf-8'))
                NombreCliente = self.get_nombre(res.content.decode('utf-8'))
                DireccionCliente = self.get_direccion(res.content.decode('utf-8'))
        return NombreCliente, DireccionCliente

    def get_nombre_cliente_cui(self, cui):
        Nombre_Cliente = ''
        if cui:
            XmlRequest = self.dte_request(type_request='retornaDatosClienteCui')
            if XmlRequest:
                if XmlRequest:
                    res = self.post_dte(xml_request=XmlRequest, type='datos_cliente_cui')
                    self.xml_validation(res.content.decode('utf-8'))
                    Nombre_Cliente = self.get_nombre(res.content.decode('utf-8'))
        return Nombre_Cliente

    def dte_request(self, type_request):
        xml_str = ''
        if type_request == 'RetornaDatosClienteRequest':
            RetornaCliente = Element('RetornaDatosClienteRequest')
            nit_node = SubElement(RetornaCliente, 'nit')
            nit_node.text = str(self.vat)
            xml_str = tostring(RetornaCliente)

        elif type_request == 'retornaDatosClienteCui':
            RetornaCliente = Element('RetornaDatosClienteRequestCUI')
            nit_node = SubElement(RetornaCliente, 'CUI')
            nit_node.text = str(self.cui_pasaporte)
            xml_str = tostring(RetornaCliente)

        return xml_str


    @api.constrains('cui_pasaporte', 'is_extranjero')
    def validate_cui_pasaporte(self):
        for rec in self:
            if rec.cui_pasaporte:
                if not (re.match("^[0-9]{4}\\s?[0-9]{5}\\s?[0-9]{4}$", rec.cui_pasaporte)) and not rec.is_extranjero:
                    raise UserError('El CUI no es valido para un cliente nacional')
