# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning
import odoo.addons.l10n_gt_fel_g4s.a_letras as a_letras
from datetime import datetime
from lxml import etree
import base64
import logging
import zeep

import random

import logging

_logger = logging.getLogger( __name__ )

class AccountMove(models.Model):
    _inherit = "account.move"

    firma_fel = fields.Char('Firma FEL', copy=False)
    serie_fel = fields.Char('Serie FEL', copy=False)
    numero_fel = fields.Char('Numero FEL', copy=False)
    factura_original_id = fields.Many2one('account.move', string="Factura original FEL",
                                          domain="[('invoice_date', '!=', False)]")
    consignatario_fel = fields.Many2one('res.partner', string="Consignatario o Destinatario FEL")
    comprador_fel = fields.Many2one('res.partner', string="Comprador FEL")
    exportador_fel = fields.Many2one('res.partner', string="Exportador FEL")
    incoterm_fel = fields.Char(string="Incoterm FEL")
    frase_exento_fel = fields.Integer('Fase Exento FEL')
    motivo_fel = fields.Char(string='Motivo FEL')
    frase_ids = fields.Many2many('satdte.frases', 'inv_frases_rel', 'inv_id', 'frases_id', 'Frases')
    documento_xml_fel = fields.Binary('Documento xml FEL', copy=False)
    documento_xml_fel_name = fields.Char('Nombre doc xml FEL', default='documento_xml_fel.xml', size=32)
    resultado_xml_fel = fields.Binary('Resultado xml FEL', copy=False)
    resultado_xml_fel_name = fields.Char('Resultado doc xml FEL', default='resultado_xml_fel.xml', size=32)
    certificador_fel = fields.Char('Certificador FEL', copy=False)
    pdf_fel = fields.Binary('PDF FEL', copy=False)
    pdf_fel_name = fields.Char('Nombre PDF FEL', default='pdf_fel.pdf')
    tipo_gasto = fields.Selection([("mixto", "Mixto"), ("compra", "Compra/Bien"), ("servicio", "Servicio"),
                                   ("importacion", "Importación/Exportación"), ("combustible", "Combustible")],
                                  string="Tipo de Gasto", default="mixto")
    is_fel = fields.Boolean('FEL', related="journal_id.generar_fel")
    xml_request = fields.Text(string='XML Request', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_response = fields.Text(string='XML Response', readonly=True, states={'draft': [('readonly', False)]},
                               copy=False)
    xml_response_cancel = fields.Text(string='XML Response ', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    fel_date = fields.Char('Fecha Certificacion')
    no_acceso = fields.Char('No. Acceso')
    active_contingencia = fields.Boolean('Activar Contigencia', default=True, copy=False)

    @api.onchange('company_id')
    def onchange_frases(self):
        if self.company_id and self.company_id.frase_ids:
            self.frase_ids = self.company_id.frase_ids.ids

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft)
        for factura in self:
            if factura.reversed_entry_id:
                factura.factura_original_id = factura.reversed_entry_id
            if factura.requiere_certificacion():
                if factura.error_pre_validacion():
                    return
                dte_dict = factura.generate_dte_dict()
                xml = False
                if factura.move_type in ('out_invoice', 'out_refund'):
                    if factura.journal_id.tipo_documento_fel == 'FACT':
                        xml = factura.GenerateXML_FACT(data=dte_dict)
                    if factura.journal_id.tipo_documento_fel == 'NCRE':
                        xml = factura.GenerateXML_NCRE(data=dte_dict)
                #raise UserError(('%s') %(xml))
                #dte = factura.dte_documento()
                #xmls = etree.tostring(dte, pretty_print=True, xml_declaration=True, encoding="UTF-8")
                factura.xml_request = xml
                logging.warn(xml)
                if factura.journal_id.active_contingencia == True:
                    factura.write({
                        'active_contingencia': True,
                    })
                else:
                    xmls_base64 = base64.b64encode(xml)
                    wsdl = 'https://certificador.feel.com.gt/api/v2/servicios/externos/login'
                    if factura.company_id.pruebas_fel:
                        wsdl = 'https://pruebasfel.g4sdocumenta.com/webservicefront/factwsfront.asmx?wsdl'
                    client = zeep.Client(wsdl=wsdl)
                    resultado = client.service.RequestTransaction(factura.company_id.requestor_fel, "SYSTEM_REQUEST", "GT",
                                                                factura.company_id.vat, factura.company_id.requestor_fel,
                                                                factura.company_id.usuario_fel, "POST_DOCUMENT_SAT",
                                                                xmls_base64, factura.journal_id.code + str(factura.id))
                    logging.warn(str(resultado))
                    if resultado['Response']['Result']:
                        xml_resultado = base64.b64decode(resultado['ResponseData']['ResponseData1'])
                        logging.warn(xml_resultado)
                        dte_resultado = etree.XML(xml_resultado)
                        data_dte_resultado = etree.tostring(dte_resultado, pretty_print=True, xml_declaration=True, encoding='utf-8')
                        factura.xml_response = data_dte_resultado
                        numero_autorizacion = dte_resultado.xpath("//*[local-name() = 'NumeroAutorizacion']")[0]
                        factura.firma_fel = numero_autorizacion.text
                        factura.serie_fel = numero_autorizacion.get("Serie")
                        factura.numero_fel = numero_autorizacion.get("Numero")
                        factura.documento_xml_fel = base64.encodebytes(xml)
                        factura.resultado_xml_fel = base64.encodebytes(data_dte_resultado)
                        factura.certificador_fel = 'g4s'
                        resultado = client.service.RequestTransaction(factura.company_id.requestor_fel, "GET_DOCUMENT",
                                                                    "GT", factura.company_id.vat,
                                                                    factura.company_id.requestor_fel,
                                                                    factura.company_id.usuario_fel,
                                                                    numero_autorizacion.text, "", "PDF")
                        logging.warn(str(resultado))
                        factura.pdf_fel = resultado['ResponseData']['ResponseData3']
                        factura.obtener_pdf()
                    else:
                        factura.error_certificador(resultado['Response']['Description'])

        return res

    def button_cancel(self):
        result = super(AccountMove, self).button_cancel()
        for factura in self:
            if factura.requiere_certificacion() and factura.firma_fel:
                dte = factura.dte_anulacion()
                xmls = etree.tostring(dte, xml_declaration=True, encoding="UTF-8")
                logging.warn(xmls)
                xmls_base64 = base64.b64encode(xmls)
                wsdl = 'https://certificador.feel.com.gt/api/v2/servicios/externos/login'
                if factura.company_id.pruebas_fel:
                    wsdl = 'https://pruebasfel.g4sdocumenta.com/webservicefront/factwsfront.asmx?wsdl'
                client = zeep.Client(wsdl=wsdl)

                resultado = client.service.RequestTransaction(factura.company_id.requestor_fel, "SYSTEM_REQUEST", "GT",
                                                              factura.company_id.vat, factura.company_id.requestor_fel,
                                                              factura.company_id.usuario_fel, "VOID_DOCUMENT",
                                                              xmls_base64, "XML")
                logging.warn(str(resultado))
                if resultado['Response']['Result']:
                    xml_resultado = base64.b64decode(resultado['ResponseData']['ResponseData1'])
                    dte_resultado = etree.XML(xml_resultado)
                    data_dte_resultado = etree.tostring(dte_resultado, pretty_print=True, xml_declaration=True,
                                                        encoding='utf-8')
                    factura.xml_response_cancel = data_dte_resultado
                if not resultado['Response']['Result']:
                    raise UserError(resultado['Response']['Description'])
        return result

    def obtener_pdf(self):
        for factura in self:
            wsdl = 'https://certificador.feel.com.gt/api/v2/servicios/externos/login'
            if factura.company_id.pruebas_fel:
                wsdl = 'https://pruebasfel.g4sdocumenta.com/webservicefront/factwsfront.asmx?wsdl'
            client = zeep.Client(wsdl=wsdl)
            resultado = client.service.RequestTransaction(factura.company_id.requestor_fel, "GET_DOCUMENT", "GT",
                                                          factura.company_id.vat, factura.company_id.requestor_fel,
                                                          factura.company_id.usuario_fel, factura.firma_fel, "", "PDF")
            logging.warn(str(resultado))
            factura.pdf_fel = resultado['ResponseData']['ResponseData3']

    def num_a_letras(self, amount):
        return a_letras.num_a_letras(amount, completo=True)

    def error_certificador(self, error):
        for factura in self:
            if factura.journal_id.error_en_historial_fel:
                factura.message_post(
                    body='<p>No se publicó la factura por error del certificador FEL:</p> <p><strong>' + error + '</strong></p>')
            else:
                raise UserError('No se publicó la factura por error del certificador FEL: ' + error)

    def requiere_certificacion(self):
        for factura in self:
            return factura.is_invoice() and factura.journal_id.generar_fel and factura.amount_total != 0

    def error_pre_validacion(self):
        for factura in self:
            if factura.firma_fel:
                factura.error_certificador("La factura ya fue validada, por lo que no puede ser validada nuevamnte")
                return True

            return False

    def descuento_lineas(self):
        self.ensure_one()
        factura = self

        precio_total_descuento = 0
        precio_total_positivo = 0

        # Guardar las descripciones, por que las modificaciones de los precios
        # y descuentos las reinician :(
        descr = {}
        for linea in factura.invoice_line_ids:
            descr[linea.id] = linea.name
        line_discount = {}
        amount_total = sum([(x.price_unit * x.quantity) for x in factura.invoice_line_ids.filtered(lambda l: l.price_total > 0.00)])
        for linea in factura.invoice_line_ids:
            if linea.price_total > 0:
                precio_total_positivo += linea.price_unit * linea.quantity
                line_discount[linea.id] = ((linea.price_total) / (amount_total if amount_total > 0.00 else 1.00))
            if linea.price_total < 0:
                precio_total_descuento += abs(linea.price_total)
                factura.write({'invoice_line_ids': [[1, linea.id, {'price_unit': 0}]]})

        if precio_total_descuento > 0 and line_discount:
            _logger.info('****************line_discount********************')
            _logger.info(line_discount)
            for linea in factura.invoice_line_ids:
                if linea.price_total > 0.00:
                    line_dist = line_discount[linea.id] if line_discount and linea.id in line_discount else 1.00
                    descuento = round((precio_total_descuento * line_dist), 6)
                    name = linea.name
                    factura.write({'invoice_line_ids': [[1, linea.id, {'fix_discount': descuento}]]})

            for linea in factura.invoice_line_ids:
                linea.name = descr[linea.id]

    def dte_documento(self):
        self.ensure_one()
        factura = self
        fel_dateformat = "%Y-%m-%dT%H:%M:%S"
        attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")

        NSMAP = {
            "ds": "http://www.w3.org/2000/09/xmldsig#",
            "dte": "http://www.sat.gob.gt/dte/fel/0.2.0",
        }

        NSMAP_REF = {
            "cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0",
        }

        NSMAP_ABONO = {
            "cfc": "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0",
        }

        NSMAP_EXP = {
            "cex": "http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0",
        }

        NSMAP_FE = {
            "cfe": "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0",
        }

        DTE_NS = "{http://www.sat.gob.gt/dte/fel/0.2.0}"
        DS_NS = "{http://www.w3.org/2000/09/xmldsig#}"
        CNO_NS = "{http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0}"
        CFE_NS = "{http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0}"
        CEX_NS = "{http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0}"
        CFC_NS = "{http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0}"

        GTDocumento = etree.Element(DTE_NS + "GTDocumento", {}, Version="0.1", nsmap=NSMAP)
        SAT = etree.SubElement(GTDocumento, DTE_NS + "SAT", ClaseDocumento="dte")
        DTE = etree.SubElement(SAT, DTE_NS + "DTE", ID="DatosCertificados")
        DatosEmision = etree.SubElement(DTE, DTE_NS + "DatosEmision", ID="DatosEmision")

        tipo_documento_fel = factura.journal_id.tipo_documento_fel
        tipo_interno_factura = factura.type if 'type' in factura.fields_get() else factura.move_type
        if tipo_documento_fel in ['FACT', 'FACM'] and tipo_interno_factura == 'out_refund':
            tipo_documento_fel = 'NCRE'

        moneda = "GTQ"
        if factura.currency_id.id != factura.company_id.currency_id.id:
            moneda = "USD"

        fecha = factura.invoice_date.strftime('%Y-%m-%d') if factura.invoice_date else fields.Date.context_today(self).strftime('%Y-%m-%d')
        hora = "00:00:00-06:00"
        fel_date = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.now())
        fecha_hora = str(fel_date.strftime(fel_dateformat))
        factura.fel_date = fecha_hora
        no_acceso = str(factura.id + 100000000)
        factura.no_acceso = no_acceso
        DatosGenerales = etree.SubElement(DatosEmision, DTE_NS + "DatosGenerales", CodigoMoneda=moneda,
                                          FechaHoraEmision=fecha_hora, Tipo=tipo_documento_fel,
                                          NumeroAcceso=no_acceso)
        if factura.tipo_gasto == 'importacion':
            DatosGenerales.attrib['Exp'] = "SI"

        Emisor = etree.SubElement(DatosEmision, DTE_NS + "Emisor",
                                  AfiliacionIVA=factura.company_id.afiliacion_iva_fel or "GEN",
                                  CodigoEstablecimiento=str(factura.journal_id.codigo_establecimiento),
                                  CorreoEmisor=factura.company_id.email or '',
                                  NITEmisor=factura.company_id.vat.replace('-', ''),
                                  NombreComercial=factura.journal_id.direccion.name,
                                  NombreEmisor=factura.company_id.name)
        DireccionEmisor = etree.SubElement(Emisor, DTE_NS + "DireccionEmisor")
        Direccion = etree.SubElement(DireccionEmisor, DTE_NS + "Direccion")
        Direccion.text = factura.journal_id.direccion.street or 'Ciudad'
        CodigoPostal = etree.SubElement(DireccionEmisor, DTE_NS + "CodigoPostal")
        CodigoPostal.text = factura.journal_id.direccion.zip or '01001'
        Municipio = etree.SubElement(DireccionEmisor, DTE_NS + "Municipio")
        Municipio.text = factura.journal_id.direccion.city or 'Guatemala'
        Departamento = etree.SubElement(DireccionEmisor, DTE_NS + "Departamento")
        Departamento.text = factura.journal_id.direccion.state_id.name if factura.journal_id.direccion.state_id else ''
        Pais = etree.SubElement(DireccionEmisor, DTE_NS + "Pais")
        Pais.text = factura.journal_id.direccion.country_id.code or 'GT'

        nit_receptor = 'CF'
        if factura.partner_id.vat:
            nit_receptor = factura.partner_id.vat.replace('-', '')
        if tipo_documento_fel == "FESP" and factura.partner_id.cui:
            nit_receptor = factura.partner_id.cui
        Receptor = etree.SubElement(DatosEmision, DTE_NS + "Receptor", IDReceptor=nit_receptor,
                                    NombreReceptor=factura.partner_id.name if not factura.partner_id.parent_id else factura.partner_id.parent_id.name)
        if factura.partner_id.email:
            Receptor.attrib['CorreoReceptor'] = factura.partner_id.email
        if tipo_documento_fel == "FESP" and factura.partner_id.cui:
            Receptor.attrib['TipoEspecial'] = "CUI"

        DireccionReceptor = etree.SubElement(Receptor, DTE_NS + "DireccionReceptor")
        Direccion = etree.SubElement(DireccionReceptor, DTE_NS + "Direccion")
        Direccion.text = str(factura.partner_id.street if factura.partner_id.street else "-") + " " + str(
            factura.partner_id.street2 if factura.partner_id.street2 else "-")
        CodigoPostal = etree.SubElement(DireccionReceptor, DTE_NS + "CodigoPostal")
        CodigoPostal.text = factura.partner_id.zip or '01001'
        Municipio = etree.SubElement(DireccionReceptor, DTE_NS + "Municipio")
        Municipio.text = factura.partner_id.city or 'Guatemala'
        Departamento = etree.SubElement(DireccionReceptor, DTE_NS + "Departamento")
        Departamento.text = factura.partner_id.state_id.name if factura.partner_id.state_id else ''
        Pais = etree.SubElement(DireccionReceptor, DTE_NS + "Pais")
        Pais.text = factura.partner_id.country_id.code or 'GT'

        if tipo_documento_fel not in ['NDEB', 'RECI', 'NABN', 'FESP']:
            frases = etree.SubElement(DatosEmision, DTE_NS + 'Frases')
            for phrase in factura.frase_ids:
                frase = etree.SubElement(frases, DTE_NS + 'Frase')
                frase.set('CodigoEscenario', str(phrase.codigo_escenario))
                frase.set('TipoFrase', str(phrase.tipo_frase))

        Items = etree.SubElement(DatosEmision, DTE_NS + "Items")

        linea_num = 0
        gran_subtotal = 0
        gran_total = 0
        gran_total_impuestos = 0
        cantidad_impuestos = 0
        self.descuento_lineas()
        total_impuestos = 0.00
        for linea in factura.invoice_line_ids:

            if linea.price_total == 0:
                continue

            linea_num += 1

            tipo_producto = "B"
            if linea.product_id.type == 'service':
                tipo_producto = "S"
            #precio_unitario = round((linea.price_unit * (100 - linea.discount) / 100), 6)
            #precio_sin_descuento = round(linea.price_unit, 6)
            #descuento = precio_sin_descuento * linea.quantity - precio_unitario * linea.quantity
            #precio_unitario_base = linea.price_subtotal / linea.quantity
            #total_linea = precio_unitario * linea.quantity
            #total_linea_base = precio_unitario_base * linea.quantity
            #total_impuestos = total_linea - total_linea_base
            #cantidad_impuestos += len(linea.tax_ids)
            quantity = linea.quantity
            price_unit = linea.price_unit
            discount_unit = (linea.price_unit * (linea.discount / 100))
            discount = (discount_unit * linea.quantity) if linea.discount and linea.discount > 0.00 else linea.fix_discount
            subtotal_taxes = linea.tax_ids.compute_all(price_unit, factura.currency_id, linea.quantity, linea.product_id, factura.partner_id)
            subtotal_without_discount = subtotal_taxes.get('total_included', 0.00) - discount
            subtotal_without_discount_taxes = linea.tax_ids.compute_all(subtotal_without_discount, factura.currency_id, 1.00, linea.product_id, factura.partner_id, fel=True)
            #discount = 
            #if linea.fix_discount and linea.fix_discount > 0.00:
            #    descuento = linea.fix_discount
            #Line taxes
            iva_amount = 0.00
            for tax in subtotal_without_discount_taxes.get('taxes', []):
                tax_name = tax.get('name', '')
                if tax_name and 'IVA' in tax_name.upper():
                    iva_amount += tax.get('amount', 0.00)

            Item = etree.SubElement(Items, DTE_NS + "Item", BienOServicio=tipo_producto, NumeroLinea=str(linea_num))
            Cantidad = etree.SubElement(Item, DTE_NS + "Cantidad")
            Cantidad.text = str(quantity)
            UnidadMedida = etree.SubElement(Item, DTE_NS + "UnidadMedida")
            UnidadMedida.text = linea.product_uom_id.name[0:3] if linea.product_uom_id else 'UNI'
            Descripcion = etree.SubElement(Item, DTE_NS + "Descripcion")
            Descripcion.text = linea.name
            PrecioUnitario = etree.SubElement(Item, DTE_NS + "PrecioUnitario")
            PrecioUnitario.text = '{:.6f}'.format(price_unit)
            Precio = etree.SubElement(Item, DTE_NS + "Precio")
            Precio.text = '{:.6f}'.format(subtotal_taxes.get('total_included', 0.00))
            Descuento = etree.SubElement(Item, DTE_NS + "Descuento")
            Descuento.text = '{:.6f}'.format(discount)
            if tipo_documento_fel not in ['NABN']:
                Impuestos = etree.SubElement(Item, DTE_NS + "Impuestos")
                Impuesto = etree.SubElement(Impuestos, DTE_NS + "Impuesto")
                NombreCorto = etree.SubElement(Impuesto, DTE_NS + "NombreCorto")
                NombreCorto.text = "IVA"
                CodigoUnidadGravable = etree.SubElement(Impuesto, DTE_NS + "CodigoUnidadGravable")
                CodigoUnidadGravable.text = "1"
                if factura.currency_id.is_zero(iva_amount):
                    CodigoUnidadGravable.text = "2"
                MontoGravable = etree.SubElement(Impuesto, DTE_NS + "MontoGravable")
                MontoGravable.text = '{:.6f}'.format(subtotal_without_discount_taxes.get('total_excluded', 0.00))
                MontoImpuesto = etree.SubElement(Impuesto, DTE_NS + "MontoImpuesto")
                MontoImpuesto.text = '{:.6f}'.format(iva_amount)
            Total = etree.SubElement(Item, DTE_NS + "Total")
            Total.text = '{:.3f}'.format(subtotal_without_discount_taxes.get('total_included', 0.00))

            gran_total += factura.currency_id.round(subtotal_without_discount_taxes.get('total_included', 0.00))
            gran_subtotal += factura.currency_id.round(subtotal_without_discount_taxes.get('total_excluded', 0.00))
            gran_total_impuestos += factura.currency_id.round(iva_amount)

        Totales = etree.SubElement(DatosEmision, DTE_NS + "Totales")
        if tipo_documento_fel not in ['NABN']:
            TotalImpuestos = etree.SubElement(Totales, DTE_NS + "TotalImpuestos")
            TotalImpuesto = etree.SubElement(TotalImpuestos, DTE_NS + "TotalImpuesto", NombreCorto="IVA",
                                             TotalMontoImpuesto='{:.3f}'.format(
                                                 factura.currency_id.round(gran_total_impuestos)))
        GranTotal = etree.SubElement(Totales, DTE_NS + "GranTotal")
        GranTotal.text = '{:.3f}'.format(factura.currency_id.round(gran_total))

        if DatosEmision.find("{http://www.sat.gob.gt/dte/fel/0.2.0}Frases") and factura.currency_id.is_zero(
                gran_total_impuestos) and (factura.company_id.afiliacion_iva_fel or 'GEN') == 'GEN':
            Frase = etree.SubElement(DatosEmision.find("{http://www.sat.gob.gt/dte/fel/0.2.0}Frases"), DTE_NS + "Frase",
                                     CodigoEscenario=str(factura.frase_exento_fel) if factura.frase_exento_fel else "1",
                                     TipoFrase="4")

        # if factura.company_id.adenda_fel:
        # Adenda = etree.SubElement(SAT, DTE_NS+"Adenda")
        # exec(factura.company_id.adenda_fel, {'etree': etree, 'Adenda': Adenda, 'factura': factura})

        # En todos estos casos, es necesario enviar complementos
        if tipo_documento_fel in ['NDEB', 'NCRE'] or tipo_documento_fel in ['FCAM'] or (tipo_documento_fel in ['FACT',
                                                                                                               'FCAM'] and factura.tipo_gasto == 'importacion') or tipo_documento_fel in [
            'FESP']:
            Complementos = etree.SubElement(DatosEmision, DTE_NS + "Complementos")

            if tipo_documento_fel in ['NDEB', 'NCRE']:
                Complemento = etree.SubElement(Complementos, DTE_NS + "Complemento", IDComplemento="ReferenciasNota",
                                               NombreComplemento="Nota de Credito" if tipo_documento_fel == 'NCRE' else "Nota de Debito",
                                               URIComplemento="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0")
                if factura.factura_original_id:
                    if factura.factura_original_id.numero_fel:
                        ReferenciasNota = etree.SubElement(Complemento, CNO_NS + "ReferenciasNota",
                                                           FechaEmisionDocumentoOrigen=str(
                                                               factura.factura_original_id.invoice_date),
                                                           MotivoAjuste=factura.motivo_fel or 'Nota de Credito',
                                                           NumeroAutorizacionDocumentoOrigen=factura.factura_original_id.firma_fel,
                                                           NumeroDocumentoOrigen=factura.factura_original_id.numero_fel,
                                                           SerieDocumentoOrigen=factura.factura_original_id.serie_fel,
                                                           Version="0.0", nsmap=NSMAP_REF)
                    else:
                        ReferenciasNota = etree.SubElement(Complemento, CNO_NS + "ReferenciasNota",
                                                           RegimenAntiguo="Antiguo", FechaEmisionDocumentoOrigen=str(
                                factura.factura_original_id.invoice_date), MotivoAjuste=factura.motivo_fel or '-',
                                                           NumeroAutorizacionDocumentoOrigen=factura.factura_original_id.firma_fel,
                                                           NumeroDocumentoOrigen=factura.factura_original_id.ref.split("-")[
                                                               1],
                                                           SerieDocumentoOrigen=factura.factura_original_id.ref.split("-")[
                                                               0], Version="0.0", nsmap=NSMAP_REF)

            if tipo_documento_fel in ['FCAM']:
                Complemento = etree.SubElement(Complementos, DTE_NS + "Complemento", IDComplemento="FCAM",
                                               NombreComplemento="AbonosFacturaCambiaria",
                                               URIComplemento="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0")
                AbonosFacturaCambiaria = etree.SubElement(Complemento, CFC_NS + "AbonosFacturaCambiaria", Version="1",
                                                          nsmap=NSMAP_ABONO)
                Abono = etree.SubElement(AbonosFacturaCambiaria, CFC_NS + "Abono")
                NumeroAbono = etree.SubElement(Abono, CFC_NS + "NumeroAbono")
                NumeroAbono.text = "1"
                FechaVencimiento = etree.SubElement(Abono, CFC_NS + "FechaVencimiento")
                FechaVencimiento.text = str(factura.invoice_date_due)
                MontoAbono = etree.SubElement(Abono, CFC_NS + "MontoAbono")
                MontoAbono.text = '{:.3f}'.format(gran_total)

            if tipo_documento_fel in ['FACT', 'FCAM'] and factura.tipo_gasto == 'importacion':
                Complemento = etree.SubElement(Complementos, DTE_NS + "Complemento", IDComplemento="text",
                                               NombreComplemento="text",
                                               URIComplemento="http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0")
                Exportacion = etree.SubElement(Complemento, CEX_NS + "Exportacion", Version="1", nsmap=NSMAP_EXP)
                NombreConsignatarioODestinatario = etree.SubElement(Exportacion,
                                                                    CEX_NS + "NombreConsignatarioODestinatario")
                NombreConsignatarioODestinatario.text = factura.consignatario_fel.name if factura.consignatario_fel else "-"
                DireccionConsignatarioODestinatario = etree.SubElement(Exportacion,
                                                                       CEX_NS + "DireccionConsignatarioODestinatario")
                DireccionConsignatarioODestinatario.text = factura.consignatario_fel.street or "-" if factura.consignatario_fel else "-"
                CodigoConsignatarioODestinatario = etree.SubElement(Exportacion,
                                                                    CEX_NS + "CodigoConsignatarioODestinatario")
                CodigoConsignatarioODestinatario.text = factura.consignatario_fel.ref or "-" if factura.consignatario_fel else "-"
                NombreComprador = etree.SubElement(Exportacion, CEX_NS + "NombreComprador")
                NombreComprador.text = factura.comprador_fel.name if factura.comprador_fel else "-"
                DireccionComprador = etree.SubElement(Exportacion, CEX_NS + "DireccionComprador")
                DireccionComprador.text = factura.comprador_fel.street or "-" if factura.comprador_fel else "-"
                CodigoComprador = etree.SubElement(Exportacion, CEX_NS + "CodigoComprador")
                CodigoComprador.text = factura.comprador_fel.ref or "-" if factura.comprador_fel else "-"
                INCOTERM = etree.SubElement(Exportacion, CEX_NS + "INCOTERM")
                INCOTERM.text = factura.incoterm_fel or "-"
                NombreExportador = etree.SubElement(Exportacion, CEX_NS + "NombreExportador")
                NombreExportador.text = factura.exportador_fel.name if factura.exportador_fel else "-"
                CodigoExportador = etree.SubElement(Exportacion, CEX_NS + "CodigoExportador")
                CodigoExportador.text = factura.exportador_fel.ref or "-" if factura.exportador_fel else "-"

            if tipo_documento_fel in ['FESP']:
                total_isr = abs(factura.amount_tax)

                total_iva_retencion = 0
                for impuesto in factura.amount_by_group:
                    if impuesto[1] > 0:
                        total_iva_retencion += impuesto[1]

                Complemento = etree.SubElement(Complementos, DTE_NS + "Complemento", IDComplemento="FacturaEspecial",
                                               NombreComplemento="FacturaEspecial",
                                               URIComplemento="http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0")
                RetencionesFacturaEspecial = etree.SubElement(Complemento, CFE_NS + "RetencionesFacturaEspecial",
                                                              Version="1", nsmap=NSMAP_FE)
                RetencionISR = etree.SubElement(RetencionesFacturaEspecial, CFE_NS + "RetencionISR")
                RetencionISR.text = str(total_isr)
                RetencionIVA = etree.SubElement(RetencionesFacturaEspecial, CFE_NS + "RetencionIVA")
                RetencionIVA.text = str(total_iva_retencion)
                TotalMenosRetenciones = etree.SubElement(RetencionesFacturaEspecial, CFE_NS + "TotalMenosRetenciones")
                TotalMenosRetenciones.text = str(factura.amount_total)

        return GTDocumento

    def dte_anulacion(self):
        self.ensure_one()
        factura = self

        NSMAP = {
            "ds": "http://www.w3.org/2000/09/xmldsig#",
            "dte": "http://www.sat.gob.gt/dte/fel/0.1.0",
        }

        DTE_NS = "{http://www.sat.gob.gt/dte/fel/0.1.0}"
        DS_NS = "{http://www.w3.org/2000/09/xmldsig#}"

        tipo_documento_fel = factura.journal_id.tipo_documento_fel
        tipo_interno_factura = factura.type if 'type' in factura.fields_get() else factura.move_type
        if tipo_documento_fel in ['FACT', 'FACM'] and tipo_interno_factura == 'out_refund':
            tipo_documento_fel = 'NCRE'

        nit_receptor = 'CF'
        if factura.partner_id.vat:
            nit_receptor = factura.partner_id.vat.replace('-', '')
        if tipo_documento_fel == "FESP" and factura.partner_id.cui:
            nit_receptor = factura.partner_id.cui

        fecha = fields.Date.from_string(factura.invoice_date).strftime('%Y-%m-%d')
        hora = "00:00:00-06:00"
        fecha_hora = fecha + 'T' + hora

        fecha_hoy_hora = fields.Date.context_today(factura).strftime('%Y-%m-%dT%H:%M:%S')

        GTAnulacionDocumento = etree.Element(DTE_NS + "GTAnulacionDocumento", {}, Version="0.1", nsmap=NSMAP)
        SAT = etree.SubElement(GTAnulacionDocumento, DTE_NS + "SAT")
        AnulacionDTE = etree.SubElement(SAT, DTE_NS + "AnulacionDTE", ID="DatosCertificados")
        DatosGenerales = etree.SubElement(AnulacionDTE, DTE_NS + "DatosGenerales", ID="DatosAnulacion",
                                          NumeroDocumentoAAnular=factura.firma_fel,
                                          NITEmisor=factura.company_id.vat.replace("-", ""), IDReceptor=nit_receptor,
                                          FechaEmisionDocumentoAnular=fecha_hora, FechaHoraAnulacion=fecha_hoy_hora,
                                          MotivoAnulacion=factura.motivo_fel or '-')

        return GTAnulacionDocumento

    @api.model
    def create(self, vals):
        if 'frase_ids' not in vals:
            vals.update({
                'frase_ids': self.env.user.company_id.frase_ids.ids if self.env.user.company_id.frase_ids else False,
            })
        res = super(AccountMove, self).create(vals)
        return res

    #Method to generate xml
    def generate_dte_dict(self):
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
            currency = inv.company_id.fel_currency_id if inv.company_id and inv.company_id.fel_currency_id else inv.currency_id
            access_number = str(random.randint(100000000, 999999999))
            while True:
                access_count = self.env['account.move'].search_count([('no_acceso', '=', access_number)])
                if access_count > 0:
                    access_number = str(random.randint(100000000, 999999999))
                else:
                    break
            dte['access_number'] = access_number
            date_dte = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.now())
            dte['date_dte'] = date_dte.strftime(megaprint_dateformat)
            inv.fel_date = date_dte.strftime(megaprint_dateformat)
            dte['tipo'] = inv.journal_id.tipo_documento_fel
            if self.frase_ids:
                for frase in self.frase_ids:
                    frases_lines.append([frase.codigo_escenario, frase.tipo_frase])
            else:
                frases_lines = [[1, 1]]
            #Datos emisor
            dte['frases'] = frases_lines
            dte['moneda'] = inv.currency_id.name or 'GTQ'
            dte['establecimiento'] = str(inv.journal_id.codigo_establecimiento)
            dte['regimeniva']  = inv.company_id.afiliacion_iva_fel
            dte['correoemisor'] = inv.company_id.email
            dte['nitemisor'] = inv.company_id.vat.upper() if inv.company_id.vat else 'CF'
            dte['nombrecomercial'] = inv.journal_id.direccion.name
            dte['nombreemisor'] = inv.company_id.name
            dte['calleemisor'] = inv.company_id.street  if inv.company_id.street  else ''
            dte['municipioemisor'] = inv.company_id.city or '.'
            dte['departamentoemisor'] = inv.company_id.state_id.name or '.'
            dte['postalemisor'] = inv.company_id.zip or '502'
            dte['paisemisor'] = inv.company_id.country_id.code or 'GT'
            #Datos Receptor
            dte['correoreceptor'] = inv.partner_id.email or ''
            dte['nitreceptor'] = inv.validate_nit(nit=inv.partner_id.vat)
            dte['nombrereceptor'] = inv.partner_id.name
            dte['callereceptor'] = inv.partner_id.street if inv.partner_id.street else 'CIUDAD'
            dte['municipiorecptor'] = inv.partner_id.city or '.'
            dte['departamentoreceptor'] = inv.partner_id.state_id.name or '.'
            dte['postalreceptor'] = inv.partner_id.zip or '502'
            dte['paisreceptor'] = inv.partner_id.country_id.code or 'GT'
            #Nota de Credito complementos
            if inv.move_type in ['out_refund', 'in_refund'] and inv.journal_id.tipo_documento_fel == 'NCRE':  # Credit Note
                complement['auth_number_doc_origin'] = inv.factura_original_id.firma_fel or '.'
                complement['origin_date'] = str(inv.factura_original_id.invoice_date) if inv.factura_original_id.invoice_date else '.'
                complement['reference'] = inv.ref or "NOTA DE CREDITO"
                complement['doc_numero_origin'] = inv.factura_original_id.numero_fel or '.'
                complement['doc_serie_origin'] = inv.factura_original_id.serie_fel or '.'
                #complement_data.append(complement)
                dte['complementos'] = complement
                dte['tipo'] = 'NCRE'
            amount_total = 0.00
            #Items de la factura
            discount_lines = inv.invoice_line_ids.filtered(lambda x: x.price_total < 0.00)
            if discount_lines and len(discount_lines.ids) > 0:
                inv.descuento_lineas()
            for line in inv.invoice_line_ids.filtered(lambda x: x.price_total > 0.00):
                #Variables x item
                item = {}
                tax_line = {}
                details_taxes = []
                details_total_taxes = []
                subtotal_taxes = 0.00
                item_no += 1
                price_unit = 0.00
                discount_unit = 0.00
                discount_total = 0.00
                taxes_unit = {}
                taxes = {}
                if line.fix_discount > 0.00:
                    _logger.info('*******************if line.fix_discount > 0.00:***************************')
                    price_unit = round(line.price_unit, 6)
                    discount_unit = line.fix_discount
                    taxes_unit = line.tax_ids.compute_all((price_unit - discount_unit), currency, 1.00, line.product_id, inv.partner_id)
                    taxes = line.tax_ids.compute_all(((line.quantity * price_unit) - discount_unit), currency, 1.00, line.product_id, inv.partner_id)
                    discount_total = line.fix_discount
                    _logger.info('***********taxes1***************')
                    _logger.info(taxes)
                elif line.discount > 0.00:
                    _logger.info('*******************if line.discount > 0.00:***************************')
                    price_unit = round(line.price_unit, 6)
                    discount_unit = (line.price_unit * (line.discount / 100))
                    taxes_unit = line.tax_ids.compute_all((price_unit - discount_unit), currency, 1.00, line.product_id, inv.partner_id)
                    taxes = line.tax_ids.compute_all((price_unit - discount_unit), currency, line.quantity, line.product_id, inv.partner_id)
                    discount_total = (discount_unit * line.quantity)
                else:
                    price_unit = round(line.price_unit, 6)
                    discount_unit = 0.00
                    taxes_unit = line.tax_ids.compute_all((price_unit - discount_unit), currency, 1.00, line.product_id, inv.partner_id)
                    taxes = line.tax_ids.compute_all(((line.quantity * price_unit) - discount_unit), currency, 1.00, line.product_id, inv.partner_id)
                    discount_total = line.fix_discount
                #Taxes calculted
                amount_total += taxes.get('total_included', 0.00)
                item['grabable'] = "{:.6f}".format(round(taxes.get('total_included', 0.00), 6))
                item['subtotal'] = "{:.6f}".format(round((line.quantity * line.price_unit), 6))
                item['subtotal_line'] = "{:.6f}".format(round(taxes.get('total_included', 0.00), 6))
                item['descuento'] = "{:.6f}".format(round(discount_total, 6))
                item['cantidad'] = "{:.6f}".format(round(line.quantity, 6))
                item['descripcion'] = str(line.name)
                item['preciounitario'] = "{:.6f}".format(round(line.price_unit, 6))
                item['uom'] = 'UNI'
                item['line'] = str(item_no)
                item['exento'] = '2' if (not line.tax_ids) else '1'
                item['tipoitem'] = 'S' if line.product_id.type == 'service' else 'B'
                _logger.info('***********taxes2***************')
                _logger.info(taxes.get('taxes', []))
                for tax in taxes.get('taxes', []):
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
            _logger.info('************details**************')
            _logger.info(details)
            dte['itemimpuestos'] = str(details_total_taxes)
            dte['totalimpuestos'] = "{:.6f}".format(round(total_taxes, 6))
            dte['total'] = "{:.6f}".format(round(amount_total, 6))
        return dte


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
        else:
            res_nit = 'CF'
        return res_nit


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    fix_discount = fields.Float('Monto Descuento')

AccountMoveLine()