# -*- coding: utf-8 -*-

import base64
import logging
import requests
import json
from xml.etree import ElementTree as ET

from datetime import datetime, date, timedelta
from dateutil.parser import parse
#from lxml import ET
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement
_logger = logging.getLogger(__name__)


TYPE_FE = [
    ('FACT', 'Factura'),
    ('FESP', 'Factura Especial'),
    ('FCAM', 'Factura Cambiaria'),
    ('NDEB', 'Nota de Débito'),
    ('NCRE', 'Nota de Crédito'),
    ('NABN', 'Nota de Abono'),
    ('FAEX', 'Factura Exportación'),
    ('OTRO', 'Otro')
]


class AccountMove(models.Model):
    _inherit = 'account.move'


    @api.model
    def default_get(self, default_fields):
        # OVERRIDE
        values = super(AccountMove, self).default_get(default_fields)
        values['fe_type'] = 'NCRE' if values.get('move_type', False) == 'out_refund' else 'FACT'
        return values

    partner_type = fields.Selection([
        ('NIT', 'NIT'),
        ('CUI', 'DPI'), 
        ('EXT','Pasaporte')], string="Tipo de Documento", readonly=True, related='partner_id.partner_type')
    arch_xml = fields.Text(string="XML Architecture", help='XML Architecture', copy=False, readonly=True)
    sent_arch_xml = fields.Text(string="XML Architecture Sent", help='XML Architecture ', copy=False, readonly=True)
    partner_vat = fields.Char('VAT', compute="get_partner_vat", store=True)
    process_status = fields.Selection([('ok', 'success'), ('fail', 'Failed'), ('process', 'Process'), ('cancel', 'Cancel')], copy=False)
    fe_type = fields.Selection(TYPE_FE, string='Tipo', related="journal_id.fe_type", readonly=True)
    fe_phrase_ids = fields.Many2many('account.fe.phrase', string='Frases', default=lambda s: s.env.company.fe_phrase_ids)
    #fe_customer_reference = fields.Char(string='Customer Reference')
    fe_exhangerate = fields.Char(string='Tasa de Cambio', size=6, default=1.00)
    fe_uuid = fields.Char(string='UUID', readonly=True, copy=False)
    fe_serie = fields.Char(string='Serie', readonly=True, copy=False)
    fe_number = fields.Char(string='Number', readonly=True, copy=False)
    fe_certification_date = fields.Datetime(string="Certification Date", readonly=True, copy=False)
    complement_ids = fields.One2many('account.move.complement', 'move_id', string='Complements' )
    third_party_account_ids = fields.One2many('charge.third.party.account', 'move_id', string='Third Party Accounts')
    fe_count_payment = fields.Integer(string='No. Pagos', default=1)
    fe_payment_frequency = fields.Integer(string='Frecuencia Pagos', default=1)
    fe_payment_line_ids = fields.One2many('account.move.payment', 'move_id', string='Payment Lines')
    fe_errors = fields.Text('Errors', readonly=True)
    fe_use_new_vat = fields.Boolean(string='Facturar a Diferente NIT', help='Marque si la factura se emite a diferente NIT', copy=False)
    fe_new_vat_id = fields.Many2one('res.partner', string='Cliente', help='Ingrese NIT del cliente', copy=False)
    #fe_new_cust = fields.Char(string='Cliente', help='Ingrese nombre del cliente', copy=False)
    #fe_new_street = fields.Char(string='Direccion', help='Ingrese Direccion', copy=False)

    fe_xml_file = fields.Binary(string='Download XML', copy=False)
    fe_pdf_file = fields.Binary(string='Download PDF', copy=False)

    rel_establishment_user = fields.Many2one('res.company.establishment', string='Establecimiento Usuario', related="invoice_user_id.fe_establishment_id")
    
    @api.depends('partner_id')
    def get_partner_vat(self):
        for record in self:
            if record.fe_use_new_vat == False:
                record.update( {'partner_vat': record.partner_id.vat} )
            else:
                record.update( {'partner_vat': record.fe_new_vat_id.vat} )

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self:
            if rec.move_type in ['out_invoice', 'out_refund']:
                if not rec.invoice_date:
                    rec.invoice_date = date.today()

                if rec.invoice_date < ( date.today() - timedelta(days=5) ) and rec.journal_id.active_fel == True:
                    raise UserError(_('Error. Date cannot exceed 5 days'))
            #if rec.journal_id and rec.journal_id.active_fel == True:
            rec.send_invoice()
        return res

    @api.onchange('journal_id', 'fe_type')
    def _onchange_complements(self):
        if self.fe_type == 'FESP' and not self.complement_ids:
            self.update({
                'complement_ids': [(0, 0, {'complement': 'IVA'}), (0, 0, {'complement': 'ISR'})]
            })

    def compute_fe_payment_line(self):
        date = False
        if self.fe_type == 'FCAM':
            if not self.fe_count_payment and not self.fe_payment_frequency:
                return
            if not self.amount_total:
                raise UserError(_('Error. Empty invoice'))
            date = self.invoice_date or fields.Date.today()
            lines = []
            self.fe_payment_line_ids.unlink()
            for count in range(self.fe_count_payment):
                date = date + timedelta(days=self.fe_payment_frequency)
                lines.append( (0, 0, {
                                        'sequence': count+1, 
                                        'date': date, 
                                        'amount': self.amount_total / self.fe_count_payment
                                    }) )
            self.update({'fe_payment_line_ids': lines})

    def _xml(self):
        origin_faex = False
        f = BytesIO()
        invd = self.invoice_date or date.today()

        fe = Element('dte:GTDocumento')
        fe.set('xmlns:ds', 'http://www.w3.org/2000/09/xmldsig#')
        fe.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.2.0')
        fe.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        fe.set('Version', '0.1')

        SAT = SubElement(fe, 'dte:SAT')
        SAT.set('ClaseDocumento', 'dte')

        DTE = ET.SubElement(SAT, 'dte:DTE')
        DTE.set('ID', 'DatosCertificados')

        Adenda = SubElement(SAT, 'dte:Adenda')
        #ET.SubElement(Adenda, 'Valor1').text=self.name
        #ET.SubElement(Adenda, 'Valor2').text=self.partner_id.patient_id
        #ET.SubElement(Adenda, 'Valor3').text=self.company_id.phone
        #ET.SubElement(Adenda, 'CorrelativoInterno').text = self.name
        #ET.SubElement(Adenda, 'OrdenVenta').text = self.invoice_origin or 'N/A'
        #ET.SubElement(Adenda, 'Vendedor').text = self.user_id.name
        #ET.SubElement(Adenda, 'Tipodecambio').text = self.fe_exhangerate


        if self.fe_type == 'FCAM':
            ET.SubElement(Adenda, 'auto-generated_for_wildcard')
        elif self.fe_type == 'NABN':
            ET.SubElement(Adenda,
                          'tipopago').text = self.reversed_entry_id.invoice_payment_term_id.name.upper() if self.reversed_entry_id.invoice_payment_term_id else 'CONTADO'
            ET.SubElement(Adenda, 'factura_referencia').text = self.reversed_entry_id.name
        if self.fe_use_new_vat == False:
            ET.SubElement(Adenda, 'cliente').text = self.partner_id.vat.replace("-", "")
        else:
        	ET.SubElement(Adenda, 'cliente').text = self.fe_new_vat_id.vat.replace("-","")
        DatosEmision = ET.SubElement(DTE, 'dte:DatosEmision', {'ID': "DatosEmision"})
        DatosGenerales = {
            'CodigoMoneda': self.currency_id.name,
            'FechaHoraEmision': datetime(invd.year, invd.month, invd.day, 0, 0, 1).isoformat(),
            'Tipo': self.fe_type
        }
        if DatosGenerales['Tipo'] == 'FAEX':
            DatosGenerales.update({'Tipo': 'FACT', 'Exp': 'SI'})
        elif self.reversed_entry_id and self.fe_type == 'NCRE':
            if self.reversed_entry_id.fe_type == 'FAEX':
                DatosGenerales.update({'Tipo': 'NCRE', 'Exp': 'SI'})
                origin_faex = True
        ET.SubElement(DatosEmision, 'dte:DatosGenerales', DatosGenerales)
        Emisor = ET.SubElement(DatosEmision, 'dte:Emisor')
        Emisor.set('AfiliacionIVA', 'GEN')
        Emisor.set('CodigoEstablecimiento', str(self.journal_id.fe_establishment_id.fe_code if self.journal_id.fe_establishment_id else "1"))
        Emisor.set('CorreoEmisor', self.company_id.email)
        Emisor.set('NITEmisor', self.company_id.vat)
        Emisor.set('NombreComercial', self.journal_id.fe_establishment_id.fe_tradename)
        Emisor.set('NombreEmisor', self.company_id.name)

        DireccionEmisor = ET.SubElement(Emisor, 'dte:DireccionEmisor')
        ET.SubElement(DireccionEmisor, 'dte:Direccion').text = '%s' % (
        self.journal_id.fe_establishment_id.fe_tradename_street or self.company_id.street and self.company_id.street2 or '')
        ET.SubElement(DireccionEmisor, 'dte:CodigoPostal').text = self.company_id.zip or '0'
        ET.SubElement(DireccionEmisor, 'dte:Municipio').text = self.journal_id.fe_establishment_id.fe_tradename_city or self.company_id.city or ''
        ET.SubElement(DireccionEmisor, 'dte:Departamento').text = self.journal_id.fe_establishment_id.fe_tradename_state_id.name or self.company_id.state_id.name or ''
        ET.SubElement(DireccionEmisor, 'dte:Pais').text = self.company_id.country_id.code or ''

        if self.reversed_entry_id and self.fe_type == 'NCRE' and self.reversed_entry_id.fe_use_new_vat == True:
            datosEmisor = {'CorreoReceptor': self.reversed_entry_id.partner_id.email or self.company_id.fe_other_email,
                           'IDReceptor': self.reversed_entry_id.fe_new_vat_id.vat,
                           'NombreReceptor': self.reversed_entry_id.fe_new_vat_id.name
                           }        
        elif self.fe_use_new_vat == False:
            datosEmisor = {'CorreoReceptor': self.partner_id.email or self.company_id.fe_other_email,
                           'IDReceptor': self.partner_id.vat,
                           'NombreReceptor': self.partner_id.name
                           } 
        else:                   
            datosEmisor = {'CorreoReceptor': self.partner_id.email or self.company_id.fe_other_email,
                           'IDReceptor': self.fe_new_vat_id.vat,
                           'NombreReceptor': self.fe_new_vat_id.name
                           }

        if self.fe_type == 'FESP':
            datosEmisor['TipoEspecial'] = 'CUI'
        if self.partner_id.partner_type == 'CUI':
            datosEmisor['TipoEspecial'] = 'CUI'
        if self.partner_id.partner_type == 'EXT':
            datosEmisor['TipoEspecial'] = 'EXT'
        Receptor = ET.SubElement(DatosEmision, 'dte:Receptor', datosEmisor)
        DireccionReceptor = ET.SubElement(Receptor, 'dte:DireccionReceptor')
        direccion = '%s %s' % (self.partner_id.street, self.partner_id.street2 or '.')
        if not self.partner_id.street and not self.partner_id.street2:
            direccion = 'CIUDAD'
        if self.fe_use_new_vat == False:
            ET.SubElement(DireccionReceptor, 'dte:Direccion').text = direccion
            ET.SubElement(DireccionReceptor, 'dte:CodigoPostal').text = self.company_id.zip or '1'
            ET.SubElement(DireccionReceptor, 'dte:Municipio').text = self.partner_id.city or ''
            ET.SubElement(DireccionReceptor, 'dte:Departamento').text = self.partner_id.state_id.name or ''
            ET.SubElement(DireccionReceptor, 'dte:Pais').text = self.partner_id.country_id.code or self.env.ref(
                'base.gt').code
        else:
            ET.SubElement(DireccionReceptor, 'dte:Direccion').text = self.fe_new_vat_id.street or 'CIUDAD'
            ET.SubElement(DireccionReceptor, 'dte:CodigoPostal').text = self.company_id.zip or '1'
            ET.SubElement(DireccionReceptor, 'dte:Municipio').text = self.fe_new_vat_id.city or ''
            ET.SubElement(DireccionReceptor, 'dte:Departamento').text = self.fe_new_vat_id.state_id.name or ''
            ET.SubElement(DireccionReceptor, 'dte:Pais').text = self.fe_new_vat_id.country_id.code or self.env.ref(
                'base.gt').code        	

        if self.fe_phrase_ids:
            Frases = ET.SubElement(DatosEmision, 'dte:Frases')
            for phrase in self.fe_phrase_ids:
                ET.SubElement(Frases, 'dte:Frase', {'CodigoEscenario': phrase.code, 'TipoFrase': phrase.type})

        Items = ET.SubElement(DatosEmision, 'dte:Items')
        count = 1
        for line in self.invoice_line_ids:

            if line.product_id:
                description = "%s | %s" % (line.product_id.name,line.product_id.default_code)
            elif not line.product_id:
                description = "%s" % (line.name)

            Item = ET.SubElement(Items, 'dte:Item',
                                 {'BienOServicio': 'B' if line.product_id.type in ('consu', 'product') else 'S',
                                  'NumeroLinea': str(count)})
            ET.SubElement(Item, 'dte:Cantidad').text = str(line.quantity)
            ET.SubElement(Item, 'dte:UnidadMedida').text = line.product_uom_id.name.upper()[
                                                           0:3] if line.product_uom_id else 'UND'
            ET.SubElement(Item, 'dte:Descripcion').text = description
            ET.SubElement(Item, 'dte:PrecioUnitario').text = str("{:.3f}".format(line.price_unit))
            ET.SubElement(Item, 'dte:Precio').text = str("{:.3f}".format((line.price_unit * line.quantity)))
            ET.SubElement(Item, 'dte:Descuento').text = str("{:.3f}".format(line.price_discount))
            if self.fe_type not in ['NABN', 'FESP']:
                Impuestos = ET.SubElement(Item, 'dte:Impuestos')
                for tax in line.tax_ids:
                    Impuesto = ET.SubElement(Impuestos, 'dte:Impuesto')
                    ET.SubElement(Impuesto, 'dte:NombreCorto').text = tax.description
                    if not origin_faex:
                        ET.SubElement(Impuesto, 'dte:CodigoUnidadGravable').text = "2" if self.fe_type == 'FAEX' else "1"
                    elif origin_faex:
                        ET.SubElement(Impuesto, 'dte:CodigoUnidadGravable').text = "2"
                    #ET.SubElement(Impuesto, 'dte:MontoGravable').text = str(round(line.price_subtotal, 3))
                    ET.SubElement(Impuesto, 'dte:MontoGravable').text = str("{:.3f}".format(line.price_subtotal))
                    #ET.SubElement(Impuesto, 'dte:MontoImpuesto').text = str(round(line.price_tax, 3))
                    ET.SubElement(Impuesto, 'dte:MontoImpuesto').text = str("{:.3f}".format(line.price_tax))
                    #ET.SubElement(Item, 'dte:Total').text = str(round(line.price_total, 3))
                    ET.SubElement(Item, 'dte:Total').text = str("{:.3f}".format(line.price_total))
            elif self.fe_type == 'FESP':
                Impuestos = ET.SubElement(Item, 'dte:Impuestos')
                for tax in line.tax_ids.filtered(lambda t: not t.tax_group_id.withhold):
                    if tax.description != 'RetencionISR' and tax.description != 'RetencionIVA':
                        taxes_res = tax.compute_all(
                            line.price_unit,
                            quantity=line.quantity,
                            currency=line.currency_id,
                            product=line.product_id,
                            partner=line.partner_id,
                            is_refund=line.move_id.move_type in ('out_refund', 'in_refund'),
                        )

                        price_total = taxes_res["total_included"]
                        price_subtotal = taxes_res["total_excluded"]
                        price_tax = price_total - price_subtotal
                        Impuesto = ET.SubElement(Impuestos, 'dte:Impuesto')
                        ET.SubElement(Impuesto, 'dte:NombreCorto').text = tax.description
                        if not origin_faex:
                            ET.SubElement(Impuesto, 'dte:CodigoUnidadGravable').text = "2" if self.fe_type == 'FAEX' else "1"
                        elif origin_faex:
                            ET.SubElement(Impuesto, 'dte:CodigoUnidadGravable').text = "2"
                        ET.SubElement(Impuesto, 'dte:MontoGravable').text = str(round(price_subtotal, 2))
                        ET.SubElement(Impuesto, 'dte:MontoImpuesto').text = str(round(price_tax, 2))
                        ET.SubElement(Item, 'dte:Total').text = str(round(price_total, 2))
            elif self.fe_type == 'NABN':
                ET.SubElement(Item, 'dte:Total').text = str(round(line.price_total, 2))
            count += 1
        Totales = ET.SubElement(DatosEmision, 'dte:Totales')
        if self.fe_type != 'NABN':
            if self.fe_type == 'FESP':
                TotalImpuestos = ET.SubElement(Totales, 'dte:TotalImpuestos')
                dict_taxes = json.loads(self.tax_totals_json)
                groups_by_subtotal = dict_taxes.get("groups_by_subtotal", {})
                for group_tax in groups_by_subtotal.values():
                    for tax in group_tax:
                        if tax['tax_group_name'] != 'RetencionISR' and tax['tax_group_name'] != 'RetencionIVA':
                            if not self.env["account.tax.group"]._apply_withholding(tax['tax_group_id']):
                                ET.SubElement(
                                    TotalImpuestos,
                                    'dte:TotalImpuesto',
                                    {
                                        'NombreCorto': tax["tax_group_name"],
                                        'TotalMontoImpuesto': str(round(tax["tax_group_amount"], 3))
                                    }
                                )
            else:
                TotalImpuestos = ET.SubElement(Totales, 'dte:TotalImpuestos')
                dict_taxes = json.loads(self.tax_totals_json)
                groups_by_subtotal = dict_taxes.get("groups_by_subtotal", {})
                for group_tax in groups_by_subtotal.values():
                    for tax in group_tax:
                        if not self.env["account.tax.group"]._apply_withholding(tax['tax_group_id']):
                            ET.SubElement(
                                TotalImpuestos,
                                'dte:TotalImpuesto',
                                {
                                    'NombreCorto': tax["tax_group_name"],
                                    'TotalMontoImpuesto': str(round(tax["tax_group_amount"], 3))
                                }
                            )
        if self.fe_type == 'FESP':
            withhold_amount = sum(self.complement_ids.mapped("amount"))
            ET.SubElement(Totales, 'dte:GranTotal').text = str(round(self.amount_total + withhold_amount, 2))
        else:
            ET.SubElement(Totales, 'dte:GranTotal').text = str(round(self.amount_total, 2))
        if self.third_party_account_ids:
            Complementos = ET.SubElement(DatosEmision, 'dte:Complementos')
            Complemento = ET.SubElement(Complementos, 'dte:Complemento', {"IDComplemento": "CobroXCuentaAjena",
                                                                          "NombreComplemento": "CobroXCuentaAjena",
                                                                          "URIComplemento": "http://www.sat.gob.gt/face2/CobroXCuentaAjena/0.1.0"
                                                                          })
            CobroXCuentaAjena = ET.SubElement(Complemento, 'cca:CobroXCuentaAjena', {
                "xmlns:cca": "http://www.sat.gob.gt/face2/CobroXCuentaAjena/0.1.0",
                "Version": "1",
                "xsi:schemaLocation": "http://www.sat.gob.gt/face2/CobroXCuentaAjena/0.1.0 schema.xsd"})
            for account in self.third_party_account_ids:
                ItemCuentaAjena = ET.SubElement(CobroXCuentaAjena, 'cca:ItemCuentaAjena')
                ET.SubElement(ItemCuentaAjena, 'cca:NITtercero').text = account.vat
                ET.SubElement(ItemCuentaAjena, 'cca:NumeroDocumento').text = account.number
                ET.SubElement(ItemCuentaAjena, 'cca:FechaDocumento').text = account.date.strftime('%Y-%m-%d')
                ET.SubElement(ItemCuentaAjena, 'cca:Descripcion').text = account.name
                ET.SubElement(ItemCuentaAjena, 'cca:BaseImponible').text = str(round(account.amount_untaxes, 2))
                ET.SubElement(ItemCuentaAjena, 'cca:MontoCobroDAI').text = str(round(account.amount_dai, 2))
                ET.SubElement(ItemCuentaAjena, 'cca:MontoCobroIVA').text = str(round(account.amount_taxes, 2))
                ET.SubElement(ItemCuentaAjena, 'cca:MontoCobroOtros').text = str(round(account.other_amount, 2))
                ET.SubElement(ItemCuentaAjena, 'cca:MontoCobroTotal').text = str(round(account.amount_total, 2))
        if self.fe_type in ('FESP', 'NDEB', 'NCRE', 'FCAM', 'FAEX'):
            Complementos = ET.SubElement(DatosEmision, 'dte:Complementos')
            if self.fe_type in ('NDEB', 'NCRE'):
                Complemento = ET.SubElement(Complementos, 'dte:Complemento', {"IDComplemento": "ReferenciasNota",
                                                                              "NombreComplemento": "Nota de Credito" if self.fe_type == 'NCRE' else "Nota de Debito",
                                                                              "URIComplemento": "text"
                                                                              })
                ET.SubElement(Complemento, "cno:ReferenciasNota",
                              {"xmlns:cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0",
                               "FechaEmisionDocumentoOrigen": self.reversed_entry_id.invoice_date.strftime('%Y-%m-%d'),
                               # year-month-day,
                               "MotivoAjuste": self.ref or '%s: %s' % (
                               self.reversed_entry_id.name, self.reversed_entry_id.fe_uuid),
                               "NumeroAutorizacionDocumentoOrigen": self.reversed_entry_id.fe_uuid,
                               "NumeroDocumentoOrigen": self.reversed_entry_id.name,
                               "SerieDocumentoOrigen": self.reversed_entry_id.fe_serie,
                               "Version": "0.0"
                               })
            elif self.fe_type == 'FESP':
                Complemento = ET.SubElement(Complementos, 'dte:Complemento', {"IDComplemento": "1",
                                                                              "NombreComplemento": "RETENCION",
                                                                              "URIComplemento": "TEXT"
                                                                              })
                RetencionesFacturaEspecial = ET.SubElement(Complemento, "cfe:RetencionesFacturaEspecial", {
                    "xmlns:cfe": "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0",
                    "Version": "1",
                    "xsi:schemaLocation": "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0"
                })
                for line in self.complement_ids.sorted(lambda r: r.complement):
                    if line.complement == 'ISR':
                        ET.SubElement(RetencionesFacturaEspecial, "cfe:RetencionISR").text = str(round(line.amount, 2))
                    if line.complement == 'IVA':
                        ET.SubElement(RetencionesFacturaEspecial, "cfe:RetencionIVA").text = str(round(line.amount, 2))
                ET.SubElement(RetencionesFacturaEspecial, "cfe:TotalMenosRetenciones").text = str(
                    round(self.amount_total, 2))
            elif self.fe_type == 'FCAM':
                if not self.fe_payment_line_ids:
                    self.compute_fe_payment_line()
                Complemento = ET.SubElement(Complementos, 'dte:Complemento', {"IDComplemento": "Cambiaria",
                                                                              "NombreComplemento": "Cambiaria",
                                                                              "URIComplemento": "http://www.sat.gob.gt/fel/cambiaria.xsd"
                                                                              })
                AbonosFacturaCambiaria = ET.SubElement(Complemento, "cfc:AbonosFacturaCambiaria", {
                    "xmlns:cfc": "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0",
                    "Version": "1",
                    "xsi:schemaLocation": "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0"
                    })
                if not self.fe_payment_line_ids:
                    raise UserError(_('Error. Enter payments for exchange bill'))
                for line in self.fe_payment_line_ids:
                    Abono = ET.SubElement(AbonosFacturaCambiaria, 'cfc:Abono')
                    ET.SubElement(Abono, 'cfc:NumeroAbono').text = str(line.sequence)
                    ET.SubElement(Abono, 'cfc:FechaVencimiento').text = line.date.strftime('%Y-%m-%d')
                    ET.SubElement(Abono, 'cfc:MontoAbono').text = str(round(line.amount, 2))
            elif self.fe_type == 'FAEX':
                Complemento = ET.SubElement(Complementos, "dte:Complemento")
                Complemento.set('IDComplemento', 'text')
                Complemento.set('NombreComplemento', 'Complemento_Exportacion')
                Complemento.set('URIComplemento', 'uri_complemento')
                Exportacion = ET.SubElement(Complemento, "cex:Exportacion")
                Exportacion.set('xmlns:cex', 'http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0')
                Exportacion.set('Version', '1')
                Exportacion.set('xsi:schemaLocation', 'http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0 C:\\Users\\Nadir\\Desktop\\SAT_FEL_FINAL_V1\\Esquemas\\GT_Complemento_Exportaciones-0.1.0.xsd')


                ET.SubElement(Exportacion, "cex:NombreConsignatarioODestinatario").text = self.partner_id.name.upper()
                ET.SubElement(Exportacion, "cex:DireccionConsignatarioODestinatario").text = '%s %s %s %s %s' % (
                self.partner_id.street, self.partner_id.street2 or '', self.partner_id.city or '',
                self.partner_id.state_id.name or '', self.partner_id.country_id.name)
                ET.SubElement(Exportacion, "cex:CodigoConsignatarioODestinatario").text = self.partner_id.vat.replace(
                    "-", "")
                ET.SubElement(Exportacion, "cex:NombreComprador").text = self.partner_id.name.upper()
                ET.SubElement(Exportacion, "cex:CodigoComprador").text = self.partner_id.vat.replace("-", "")
                ET.SubElement(Exportacion, "cex:OtraReferencia").text = "EXPORTACION"
                ET.SubElement(Exportacion, "cex:INCOTERM").text = "FOB"
                ET.SubElement(Exportacion,
                              "cex:NombreExportador").text = self.journal_id.fe_establishment_id.fe_tradename
                ET.SubElement(Exportacion,
                              "cex:CodigoExportador").text = self.journal_id.fe_establishment_id.export_code

        # ******************* ALTERNATIVA? ***************
        # rough_string = ET.tostring(fe, encoding='UTF-8', method='xml')
        # reparsed = minidom.parseString(rough_string)
        # pretty_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
        # return pretty_str
        # ******************* ALTERNATIVA? ***************


        final = ET.ElementTree(fe)
        final.write(f, encoding='UTF-8', xml_declaration=True)
        return f.getvalue()


    def _sign_invoice(self, cancel=False, xml_cancel=False):
        headers = {'Content-Type': 'application/json'}
        URL = self.env['ir.config_parameter'].sudo().get_param('url.sign.webservice.fe')
        payloads = self.company_id._get_sign_token()
        payloads.update({
            "codigo": str(self.journal_id.fe_establishment_id.fe_code) if self.journal_id.fe_establishment_id else "0",
            "archivo": xml_cancel if cancel else self.arch_xml,
            "es_anulacion": "S" if cancel else "N"
        })
        response = requests.post(url=URL, json=payloads, headers=headers)
        data = response.json()
        print(data)
        # if not data['resultado']:
        #     values.update( {'arch_xml': '', 'process_status': 'fail'})
        # else:
        #     values.update( {'arch_xml': data['archivo'], 'process_status': 'process'})
        return data['archivo']#self.write( values )

    def send_invoice(self):
        if self.journal_id and not self.journal_id.active_fel:
            return
        URL = self.env['ir.config_parameter'].sudo().get_param('url.webservice.fe')
        xml = self._xml()
        _logger.info('*************Infile-XML***************************')
        _logger.info(base64.b64encode( xml ))
        self.write({ 'arch_xml': base64.b64encode( xml ),
                    'sent_arch_xml': xml,
                    'process_status': 'process',
                    'fe_errors': ''
                  })
        headers = self.company_id._get_headers()
        signed_invoice = self._sign_invoice()
        #return self.write({ 'arch_xml': base64.b64decode(signed_invoice) })
        _logger.info( 'signed' )
        headers['identificador'] = self.name
        payloads = {
            "nit_emisor": self.company_id.vat.replace("-", ""),
            "correo_copia": self.partner_id.email or self.company_id.fe_other_email,
            "xml_dte": signed_invoice
            }
        _logger.info('********************JSON Requests*************************')
        _logger.info(payloads)
        response = requests.post(url=URL, json=payloads, headers=headers )
        _logger.info("MUESTRAAAA RESPONSEEEEEEE DEL CERTIFICACIÓN")
        _logger.info(response.json())
        data = response.json()
        if data['resultado']:
            certification_date = parse( data['fecha'] )
            xml = base64.b64decode( data['xml_certificado'] )
            self.write( {
                            'fe_uuid': data['uuid'],
                            'fe_xml_file': data['xml_certificado'],
                            'arch_xml': xml, 
                            'process_status': 'ok',
                            'fe_serie': data['serie'],
                            'fe_number': data['numero'],
                            'fe_certification_date': certification_date.strftime('%Y-%m-%d %H:%M:%S')
                        } )
        else:
            error_msg = ''
            count = 0
            _logger.info("MUESTRAAAA DATAAAAAAAA DEL CERTIFICACIÓN")
            _logger.info(data)
            for error in data['descripcion_errores']:
                count+=1
                _logger.info("MUESTRAAAA ERRORRRES DEL CERTIFICACIÓN")
                _logger.info(error)
                error_msg += '%s. %s \n'%(count, error['mensaje_error'])
            self.write( {'fe_errors': error_msg,'process_status': 'fail'} )
            raise UserError(_('%s') %(error_msg))
        return 
        

    def cancel_dte(self):
        URL = self.env['ir.config_parameter'].sudo().get_param('url.webservice.cancel.fe')
        f = BytesIO()
        invd = self.invoice_date or date.today()
        dtnow= datetime.now()
        root = ET.Element('dte:GTAnulacionDocumento', {
                            'xmlns:ds':"http://www.w3.org/2000/09/xmldsig#",  
                            'xmlns:dte':"http://www.sat.gob.gt/dte/fel/0.1.0",
                            'xmlns:n1':"http://www.altova.com/samplexml/other-namespace",
                            'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance",
                            'Version':"0.1",
                            'xsi:schemaLocation':"http://www.sat.gob.gt/dte/fel/0.1.0"
                            })
        SAT = ET.SubElement(root, 'dte:SAT')
        AnulacionDTE = ET.SubElement(SAT, 'dte:AnulacionDTE', {'ID' : "DatosCertificados"})
        ET.SubElement(AnulacionDTE, 'dte:DatosGenerales', {'FechaEmisionDocumentoAnular': datetime(invd.year, invd.month, invd.day, 0, 0, 1).isoformat(), #"2020-03-04T00:00:00-06:00"
                                                            'FechaHoraAnulacion': datetime(dtnow.year, dtnow.month, dtnow.day, dtnow.hour, dtnow.minute, 1).isoformat(), #"2020-04-21T00:00:00-06:00" 
                                                            'ID':"DatosAnulacion",
                                                            "IDReceptor": self.fe_new_vat_id.vat.replace("-", "") if self.fe_use_new_vat == True else self.partner_id.vat.replace("-", ""),
                                                            "MotivoAnulacion":"Anulación" ,
                                                            "NITEmisor": self.company_id.vat.replace("-", "") ,
                                                            "NumeroDocumentoAAnular": self.fe_uuid
                                                        })

        fe = ET.ElementTree(root)
        fe.write(f, encoding='utf-8', xml_declaration=True)
        canceled = base64.b64encode( f.getvalue() ).decode('utf-8')
        signed = self._sign_invoice(cancel=True, xml_cancel=canceled  )
        
        headers = self.company_id._get_headers()
        payloads = {
            "nit_emisor": self.company_id.vat.replace("-", ""),
            "correo_copia": self.partner_id.email,
            "xml_dte": signed
            }
        response = requests.post(url=URL, json=payloads, headers=headers )
        data =  response.json() 

        if data['resultado']:
            xml = base64.b64decode( data['xml_certificado'] )
            self.write( {  
                            'arch_xml': xml, 
                            'fe_xml_file': data['xml_certificado'],
                            'process_status': 'cancel'} )
            self.get_pdf()
        return self.button_cancel()

         
    def button_cancel(self):
        #for record in self:                
        #    if record.state!='draft' and record.journal_id.fe_type != 'OTRO' and record.move_type in ['out_invoice', 'out_refund'] and record.process_status != 'cancel' and record.journal_id.active_fel == True:
        #        raise UserError(_('Error. You must send the cancellation to the certifier'))
        return super(AccountMove, self).button_cancel()


    def get_pdf(self):
        URL = 'https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid=%s'%self.fe_uuid
        fe_file = requests.get(URL)
        self.fe_pdf_file = base64.b64encode( fe_file.content )

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    price_tax = fields.Monetary(string='Subtotal', store=True, readonly=True)
    price_discount = fields.Monetary(string='Price Discount', store=True, readonly=True)
    #guide = fields.Char(string='Guide', size=12)

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.
        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' ,'price_tax' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * price_unit_wo_discount

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
            res['price_tax'] = sum( t.get('amount', 0.0) for t in taxes_res['taxes'] )
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if discount:
            res['price_discount'] = (quantity * price_unit) * (discount / 100.0)
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

class AccountFePhrase(models.Model):
    _name = 'account.fe.phrase'
    _description = 'Account Fe Phrase'
    
    name = fields.Char(string='Name', required=1)
    description = fields.Char(string='Description')
    type = fields.Char(string='Type', required=1)
    code = fields.Char(string='Code', required=1)


class AccountMoveComplement(models.Model):
    _name = 'account.move.complement'
    _description = 'Account Move Complement'


    amount = fields.Monetary(string='Amount', compute="_compute_complement")
    complement = fields.Selection( [('IVA', 'RETENCIÓN IVA'), ('ISR', 'RETENCIÓN ISR') ], string='Complement')
    base = fields.Monetary(string='Base Amount', compute="_compute_complement")
    move_id = fields.Many2one('account.move', string='Invoice')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda s: s.env.company.currency_id)


    @api.depends('move_id.invoice_line_ids', 'complement')
    def _compute_complement(self):
        for record in self:
            base = sum( record.move_id.invoice_line_ids.mapped('price_subtotal') )
            #base = price_total / 1.12
            if record.complement == 'IVA':
                amount = base * 0.12
            else:
                #if base < 30000:
                amount = base * 0.05
                #else:
                #    amount = (30000 * 0.05) + (base - 30000) * 0.07 
            record.update( {    'base': base,
                                'amount': amount
                        }  )
        return


class AccountMovePayment(models.Model):
    _name = 'account.move.payment'
    _description = 'Account Move Payment'
    _rec_name = 'move_id'
    _order = 'sequence,date'

    sequence = fields.Integer(string='Sequence')
    date = fields.Date(string='Date')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda s: s.env.company.currency_id)
    amount = fields.Monetary(string='Amount')
    move_id = fields.Many2one('account.move', string='Invoice')
