# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement

from odoo import models

from odoo.exceptions import UserError, Warning


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def GenerateXML_FACT(self, data={}):

        fe = Element('dte:GTDocumento')
        fe.set('xmlns:cex', 'http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0')
        fe.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        fe.set('xmlns:cfe', 'http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0')
        fe.set('xmlns:ds', 'http://www.w3.org/2000/09/xmldsig#')
        fe.set('xmlns:cfc', 'http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0')
        fe.set('xmlns:cno', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0')
        fe.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.2.0')
        fe.set('Version', '0.1')

        sat = SubElement(fe, 'dte:SAT')
        sat.set('ClaseDocumento', 'dte')

        DTE = SubElement(sat, 'dte:DTE')
        DTE.set('ID', 'DatosCertificados')

        DatosEmision = SubElement(DTE, 'dte:DatosEmision')
        DatosEmision.set('ID', 'DatosEmision')

        DatosGenerales = SubElement(DatosEmision, 'dte:DatosGenerales')
        DatosGenerales.set('CodigoMoneda', data.get('moneda', False))
        DatosGenerales.set('FechaHoraEmision',data.get('date_dte', False))
        DatosGenerales.set('Tipo', data.get('tipo', False))
        if data.get('export', False):
            DatosGenerales.set('Exp', data.get('export', False))

        # EMISOR
        Emisor = SubElement(DatosEmision, 'dte:Emisor')
        Emisor.set('AfiliacionIVA', data.get('regimeniva', False))
        Emisor.set('CodigoEstablecimiento', data.get('establecimiento', False))
        Emisor.set('NITEmisor', data.get('nitemisor', False))
        Emisor.set('NombreComercial', data.get('nombrecomercial', False))
        Emisor.set('NombreEmisor', data.get('nombreemisor', False))

        DireccionEmisor = SubElement(Emisor, 'dte:DireccionEmisor')

        calleEmisor = SubElement(DireccionEmisor, 'dte:Direccion')
        calleEmisor.text = data.get('calleemisor', False)

        postalEmisor = SubElement(DireccionEmisor, 'dte:CodigoPostal')
        postalEmisor.text = data.get('postalemisor', False)

        municipioEmisor = SubElement(DireccionEmisor, 'dte:Municipio')
        municipioEmisor.text = data.get('municipioemisor', False)

        departamentoEmisor = SubElement(DireccionEmisor, 'dte:Departamento')
        departamentoEmisor.text = data.get('departamentoemisor', False)

        paisEmisor = SubElement(DireccionEmisor, 'dte:Pais')
        paisEmisor.text = data.get('paisemisor', False)

        # RECEPTOR
        Receptor = SubElement(DatosEmision, 'dte:Receptor')
        Receptor.set('IDReceptor', data.get('nitreceptor', False))
        Receptor.set('NombreReceptor', data.get('nombrereceptor', False))
        if self.partner_id.type_document == 'CUI':
            Receptor.set('TipoEspecial', 'CUI')
        elif self.partner_id.type_document == 'EXT':
            Receptor.set('TipoEspecial', 'EXT')
        else:
            pass

        DireccionReceptor = SubElement(Receptor, 'dte:DireccionReceptor')

        calleRecept = SubElement(DireccionReceptor, 'dte:Direccion')
        calleRecept.text = data.get('callereceptor', False)

        postalRecept = SubElement(DireccionReceptor, 'dte:CodigoPostal')
        postalRecept.text = data.get('postalreceptor', False)

        municipioRecept = SubElement(DireccionReceptor, 'dte:Municipio')
        municipioRecept.text = data.get('municipiorecptor', False)

        departamentoRecept = SubElement(DireccionReceptor, 'dte:Departamento')
        departamentoRecept.text = data.get('departamentoreceptor', False)

        paisRecept = SubElement(DireccionReceptor, 'dte:Pais')
        paisRecept.text = data.get('paisreceptor', False)

        # FRASES
        frases = SubElement(DatosEmision, 'dte:Frases')
        for phrase in data.get('frases', []):
            frase = SubElement(frases, 'dte:Frase')
            frase.set('CodigoEscenario', str(phrase[0]))
            frase.set('TipoFrase', str(phrase[1]))

        # ITEMS
        items = SubElement(DatosEmision, 'dte:Items')
        #raise UserError(('%s') %(data.get('items', [])))
        for line in data.get('items', []):
            item = SubElement(items, 'dte:Item')
            item.set('BienOServicio', line.get('tipoitem', False))
            item.set('NumeroLinea', line.get('line', False))
            cantidad = SubElement(item, 'dte:Cantidad')
            cantidad.text = line.get('cantidad', False)
            uom = SubElement(item, 'dte:UnidadMedida')
            uom.text = line.get('uom', False)
            descripcion = SubElement(item, 'dte:Descripcion')
            description = str(line['descripcion'])
            descripcion.text = description
            precio_unitario = SubElement(item, 'dte:PrecioUnitario')
            precio_unitario.text = line.get('preciounitario', False)
            precio = SubElement(item, 'dte:Precio')
            precio.text = line.get('subtotal', False)
            descuento = SubElement(item, 'dte:Descuento')
            descuento.text = line.get('descuento', False)
            impuestos = SubElement(item, 'dte:Impuestos')
            impuesto = SubElement(impuestos, 'dte:Impuesto')
            for tax in line.get('itemsimpuestos', []):
                nombre_corto = SubElement(impuesto, 'dte:NombreCorto')
                nombre_corto.text = tax.get('tax_name', False)
                codigo_tax = SubElement(impuesto, 'dte:CodigoUnidadGravable')
                codigo_tax.text = line.get('exento', False)
                taxable = SubElement(impuesto, 'dte:MontoGravable')
                taxable.text = tax.get('base', False)
                tax_amount = SubElement(impuesto, 'dte:MontoImpuesto')
                tax_amount.text = tax.get('tax', False)
            total_line = SubElement(item, 'dte:Total')
            total_line.text = line.get('subtotal', False)

        # TOTALES
        totales = SubElement(DatosEmision, 'dte:Totales')
        listaImpuestos = SubElement(totales, 'dte:TotalImpuestos')
        totalImpuesto = SubElement(listaImpuestos, 'dte:TotalImpuesto')
        totalImpuesto.set('NombreCorto', 'IVA')
        totalImpuesto.set('TotalMontoImpuesto', data.get('totalimpuestos', False))

        granTotal = SubElement(totales, 'dte:GranTotal')
        granTotal.text = data.get('total', False)
        
        #FCAM
        fcam = self.journal_id.factura_cambiaria
        Complemento_Data = data.get('complementos', {})
        if (fcam or data.get('adenda', False)) or Complemento_Data:
            Complementos = SubElement(DatosEmision, 'dte:Complementos')
            #Complemento = SubElement(Complementos, 'dte:Complemento')
            if fcam:
                #Complemento_Data = data.get('complementos', {})
                #Complementos = SubElement(DatosEmision, 'dte:Complementos')
                Complemento = SubElement(Complementos, 'dte:Complemento')
                Complemento.set('IDComplemento', 'Text')
                Complemento.set('NombreComplemento', 'Text')
                #ABONOS DE FCAM
                Complemento.set('URIComplemento', 'Text')
                AbonosFacturaCambiaria = SubElement(Complemento, 'cfc:AbonosFacturaCambiaria')
                AbonosFacturaCambiaria.set('xmlns:cfc', 'http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0')
                AbonosFacturaCambiaria.set('Version', '1')
                
                for line in self.megaprint_payment_lines:
                    Abono = SubElement(AbonosFacturaCambiaria, 'cfc:Abono')
                    NumeroAbono = SubElement(Abono, 'cfc:NumeroAbono')
                    NumeroAbono.text = str(line.serial_no or 0)
                    FechaVencimiento = SubElement(Abono, 'cfc:FechaVencimiento')
                    FechaVencimiento.text = str(line.due_date or 0)
                    MontoAbono = SubElement(Abono, 'cfc:MontoAbono')
                    MontoAbono.text = str(line.amount or 0)
            #Complementos Exportacion
            if data.get('export', False):
                #Complemento_Data = data.get('complementos', {})
                #Complementos = SubElement(DatosEmision, 'dte:Complementos')
                Complemento = SubElement(Complementos, 'dte:Complemento')
                Complemento.set('NombreComplemento', 'Exp')
                Complemento.set('URIComplemento', 'EXW')

                Exportacion = SubElement(Complemento, 'cex:Exportacion')
                Exportacion.set('xmlns:cex', 'http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0')
                Exportacion.set('Version', '1')
                Exportacion.set('xsi:schemaLocation', 'http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0 GT_Complemento_Exportaciones-0.1.0.xsd')
                #Complemento Nombre/Direccion Consignatario
                NombreConsignatario = SubElement(Exportacion, 'cex:NombreConsignatarioODestinatario')
                NombreConsignatario.text = Complemento_Data.get('nombre_consignatario', False)
                DireccionConsignatario = SubElement(Exportacion, 'cex:DireccionConsignatarioODestinatario')
                DireccionConsignatario.text = Complemento_Data.get('direccion_consignatario', False)
                #Complemento Nombre/DireccionComprador
                NombreComprador = SubElement(Exportacion, 'cex:NombreComprador')
                NombreComprador.text = Complemento_Data.get('nombre_consignatario', False)
                DireccionComprador = SubElement(Exportacion, 'cex:DireccionComprador')
                DireccionComprador.text = Complemento_Data.get('direccion_consignatario', False)
                #Complemento Inconterm
                Incoterm = SubElement(Exportacion, 'cex:INCOTERM')
                Incoterm.text = Complemento_Data.get('incoterm', False)
                #Complemento Codigo Exportador
                NombreExportador = SubElement(Exportacion, 'cex:NombreExportador')
                NombreExportador.text = data.get('nombrecomercial', False)
                CodigoExportador = SubElement(Exportacion, 'cex:CodigoExportador')
                CodigoExportador.text = Complemento_Data.get('export_code', False)
        # Adenda
        if data.get('adenda', False):
            Adenda = SubElement(sat, 'dte:Adenda')
            AdendaDetail = SubElement(Adenda, 'Adicionales')
            AdendaDetail.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            AdendaDetail.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
            AdendaDetail.set('xmlns', 'Schema-totalletras')
            #AdendaSummary = SubElement(AdendaDetail, 'dtecomm:InformacionAdicional')
            #AdendaSummary.set('Version', '7.1234654163')
            for item in data.get('adenda', []):
                for key, value in item.items():
                    val = SubElement(AdendaDetail, key)
                    val.text = str(value)

        rough_string = ET.tostring(fe, encoding='utf-8', method='xml')
        reparsed = minidom.parseString(rough_string)
        pretty_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
        return pretty_str

    def GenerateXML_NCRE(self, data={}):

        fe = Element('dte:GTDocumento')
        fe.set('xmlns:ds', 'http://www.w3.org/2000/09/xmldsig#')
        fe.set('xmlns:cfc', 'http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0')
        fe.set('xmlns:cno', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0')
        fe.set('xmlns:cex', 'http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0')
        fe.set('xmlns:cfe', 'http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0')
        fe.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        fe.set('xmlns:cca', 'http://www.sat.gob.gt/face2/CobroXCuentaAjena/0.1.0')
        fe.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.2.0')
        fe.set('Version', '0.1')
        
        sat = SubElement(fe, 'dte:SAT')
        sat.set('ClaseDocumento', 'dte')

        DTE = SubElement(sat, 'dte:DTE')
        DTE.set('ID', 'DatosCertificados')

        DatosEmision = SubElement(DTE, 'dte:DatosEmision')
        DatosEmision.set('ID', 'DatosEmision')

        DatosGenerales = SubElement(DatosEmision, 'dte:DatosGenerales')
        DatosGenerales.set('CodigoMoneda', data.get('moneda', False))
        DatosGenerales.set('FechaHoraEmision', data.get('date_dte', False))
        DatosGenerales.set('Tipo', data.get('tipo', False))

        # Emisor
        Emisor = SubElement(DatosEmision, 'dte:Emisor')
        Emisor.set('AfiliacionIVA', data.get('regimeniva', False))
        Emisor.set('CodigoEstablecimiento', data.get('establecimiento', False))
        Emisor.set('NITEmisor', data.get('nitemisor', False))
        Emisor.set('NombreComercial', data.get('nombrecomercial', False))
        Emisor.set('NombreEmisor', data.get('nombreemisor', False))

        DireccionEmisor = SubElement(Emisor, 'dte:DireccionEmisor')

        calleEmisor = SubElement(DireccionEmisor, 'dte:Direccion')
        calleEmisor.text = data.get('calleemisor', False)

        postalEmisor = SubElement(DireccionEmisor, 'dte:CodigoPostal')
        postalEmisor.text = data.get('postalemisor', False)

        municipioEmisor = SubElement(DireccionEmisor, 'dte:Municipio')
        municipioEmisor.text = data.get('municipioemisor', False)

        departamentoEmisor = SubElement(DireccionEmisor, 'dte:Departamento')
        departamentoEmisor.text = data.get('departamentoemisor', False)

        paisEmisor = SubElement(DireccionEmisor, 'dte:Pais')
        paisEmisor.text = data.get('paisemisor', False)

        # RECEPTOR
        Receptor = SubElement(DatosEmision, 'dte:Receptor')
        Receptor.set('CorreoReceptor', data.get('correoreceptor', False))
        Receptor.set('IDReceptor', data.get('nitreceptor', False))
        Receptor.set('NombreReceptor', data.get('nombrereceptor', False))

        DireccionReceptor = SubElement(Receptor, 'dte:DireccionReceptor')

        calleRecept = SubElement(DireccionReceptor, 'dte:Direccion')
        calleRecept.text = data.get('callereceptor', False)

        postalRecept = SubElement(DireccionReceptor, 'dte:CodigoPostal')
        postalRecept.text = data.get('postalreceptor', False)

        municipioRecept = SubElement(DireccionReceptor, 'dte:Municipio')
        municipioRecept.text = data.get('municipiorecptor', False)

        departamentoRecept = SubElement(DireccionReceptor, 'dte:Departamento')
        departamentoRecept.text = data.get('departamentoreceptor', False)

        paisRecept = SubElement(DireccionReceptor, 'dte:Pais')
        paisRecept.text = data.get('paisreceptor', False)

        # FRASES
        #frases = SubElement(DatosEmision, 'dte:Frases')
        #for phrase in _frases:
        #    frase = SubElement(frases, 'dte:Frase')
        #    frase.set('CodigoEscenario', str(phrase[0]))
        #    frase.set('TipoFrase', str(phrase[1]))

        # ITEMS
        items = SubElement(DatosEmision, 'dte:Items')
        #raise UserError(('%s') %(data.get('items', [])))
        for line in data.get('items', []):
            item = SubElement(items, 'dte:Item')
            item.set('BienOServicio', line.get('tipoitem', False))
            item.set('NumeroLinea', line.get('line', False))
            cantidad = SubElement(item, 'dte:Cantidad')
            cantidad.text = line.get('cantidad', False)
            uom = SubElement(item, 'dte:UnidadMedida')
            uom.text = line.get('uom', False)
            descripcion = SubElement(item, 'dte:Descripcion')
            descripcion.text = line.get('descripcion', False)
            precio_unitario = SubElement(item, 'dte:PrecioUnitario')
            precio_unitario.text = line.get('preciounitario', False)
            precio = SubElement(item, 'dte:Precio')
            precio.text = line.get('subtotal', False)
            descuento = SubElement(item, 'dte:Descuento')
            descuento.text = line.get('descuento', False)
            impuestos = SubElement(item, 'dte:Impuestos')
            impuesto = SubElement(impuestos, 'dte:Impuesto')
            for tax in line.get('itemsimpuestos', []):
                nombre_corto = SubElement(impuesto, 'dte:NombreCorto')
                nombre_corto.text = tax.get('tax_name', False)
                codigo_tax = SubElement(impuesto, 'dte:CodigoUnidadGravable')
                codigo_tax.text = "1"
                taxable = SubElement(impuesto, 'dte:MontoGravable')
                taxable.text = tax.get('base', False)
                tax_amount = SubElement(impuesto, 'dte:MontoImpuesto')
                tax_amount.text = tax.get('tax', False)
            total_line = SubElement(item, 'dte:Total')
            total_line.text = line.get('subtotal', False)

        # TOTALES
        totales = SubElement(DatosEmision, 'dte:Totales')
        listaImpuestos = SubElement(totales, 'dte:TotalImpuestos')
        totalImpuesto = SubElement(listaImpuestos, 'dte:TotalImpuesto')
        totalImpuesto.set('NombreCorto', 'IVA')
        totalImpuesto.set('TotalMontoImpuesto', data.get('totalimpuestos', False))

        granTotal = SubElement(totales, 'dte:GranTotal')
        granTotal.text = data.get('total', False)

        # Adenda
        if data.get('adenda', False):
            Adenda = SubElement(sat, 'dte:Adenda')
            AdendaDetail = SubElement(Adenda, 'Adicionales')
            AdendaDetail.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            AdendaDetail.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
            AdendaDetail.set('xmlns', 'Schema-totalletras')
            for item in data.get('adenda', []):
                for key, value in item.items():
                    val = SubElement(AdendaDetail, key)
                    val.text = str(value)

        #Complementos NCRE
        Complemento_Data = data.get('complementos', {})
        Complementos = SubElement(DatosEmision, 'dte:Complementos')
        Complemento = SubElement(Complementos, 'dte:Complemento')
        Complemento.set('IDComplemento', 'ReferenciasNota')
        Complemento.set('NombreComplemento', 'ReferenciasNota')
        Complemento.set('URIComplemento', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0')
        #Complemento.set('xmlns:dteref', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0')
        #Complemento.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        #Complemento.set('xsi:schemaLocation', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0 GT_Complemento_Referencia_Nota-0.1.0.xsde')

        ReferenciasNota = SubElement(Complemento, 'cno:ReferenciasNota')
        ReferenciasNota.set('xmlns:cno', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0')
        ReferenciasNota.set('FechaEmisionDocumentoOrigen', Complemento_Data['origin_date'])
        ReferenciasNota.set('MotivoAjuste', Complemento_Data['reference'])
        ReferenciasNota.set('NumeroAutorizacionDocumentoOrigen', Complemento_Data['auth_number_doc_origin'])
        ReferenciasNota.set('NumeroDocumentoOrigen', Complemento_Data['doc_numero_origin'])
        ReferenciasNota.set('SerieDocumentoOrigen', Complemento_Data['doc_serie_origin'])
        ReferenciasNota.set('Version', '0.1')

        rough_string = ET.tostring(fe, encoding='utf-8', method='xml')
        reparsed = minidom.parseString(rough_string)
        pretty_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
        #self.xml_request = pretty_str
        return pretty_str


AccountInvoice()