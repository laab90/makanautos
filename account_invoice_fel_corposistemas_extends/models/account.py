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


    customer_vat = fields.Char('Customer Vat')
    customer_name = fields.Char('Customer Name')


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
            customer_vat = inv.partner_id.vat.upper() if inv.partner_id.vat else 'CF'
            customer_name = inv.partner_id.name
            if inv.customer_vat and inv.customer_name:
                customer_vat = inv.customer_vat
                customer_name = inv.customer_name
            dte['correoreceptor'] = inv.partner_id.email or ''
            dte['nitreceptor'] = customer_vat
            dte['nombrereceptor'] = customer_name
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

    def generate_xml_cancel(self):
        megaprint_dateformat = "%Y-%m-%dT%H:%M:%S"
        xml_str = ""
        for rec in self:
            try:
                customer_vat = rec.partner_id.vat.upper() if rec.partner_id.vat else 'CF'
                if rec.customer_vat:
                    customer_vat = rec.customer_vat
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
                DatosGenerales.set('IDReceptor', str(customer_vat))
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