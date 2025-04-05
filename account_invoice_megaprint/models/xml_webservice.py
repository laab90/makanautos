# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement

from odoo import models



class AccountInvoice(models.Model):
    _inherit = "account.move"

    def GenerateXML_FCAM(self, _moneda, _fechayhora, _numeroacceso, _tipo, _afiIVA, _estabCode, _mailEmi, _NITEmisor, _NombreComercial, _NombreEmisor,
                         _calleEmisor, _postalEmisor, _muniEmisor, _deptoEmisor, _paisEmisor, _mailRec, _IDReceptor, _NombreReceptor, _calleRecept,
                         _postalRecept, _muniRecept, _deptoRecept, _paisRecept, _frases, _items, _iva, _total, _uuId, Complemento_Data, AdendaSummaryData):

        fe = Element('dte:GTDocumento')
        fe.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.2.0')
        # fe.set('xmlns:cfc', 'http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0')
        fe.set('xmlns:xd', 'http://www.w3.org/2000/09/xmldsig#')
        fe.set('Version', '0.1')

        sat = SubElement(fe, 'dte:SAT')
        sat.set('ClaseDocumento', 'dte')

        DTE = SubElement(sat, 'dte:DTE')

        DTE.set('ID', 'DatosCertificados')
        # minimo = SubElement(documento, 'minimo')

        DatosEmision = SubElement(DTE, 'dte:DatosEmision')
        DatosEmision.set('ID', 'DatosEmision')

        DatosGenerales = SubElement(DatosEmision, 'dte:DatosGenerales')
        DatosGenerales.set('CodigoMoneda', _moneda)
        DatosGenerales.set('FechaHoraEmision', _fechayhora)
        DatosGenerales.set('NumeroAcceso', _numeroacceso)
        DatosGenerales.set('Tipo', _tipo)

        # Emisor
        Emisor = SubElement(DatosEmision, 'dte:Emisor')
        Emisor.set('AfiliacionIVA', _afiIVA)
        Emisor.set('CodigoEstablecimiento', _estabCode)
        Emisor.set('CorreoEmisor', _mailEmi)
        Emisor.set('NITEmisor', _NITEmisor)
        Emisor.set('NombreComercial', _NombreComercial)
        Emisor.set('NombreEmisor', _NombreEmisor)

        DireccionEmisor = SubElement(Emisor, 'dte:DireccionEmisor')

        calleEmisor = SubElement(DireccionEmisor, 'dte:Direccion')
        calleEmisor.text = str(_calleEmisor)

        postalEmisor = SubElement(DireccionEmisor, 'dte:CodigoPostal')
        postalEmisor.text = str(_postalEmisor)

        municipioEmisor = SubElement(DireccionEmisor, 'dte:Municipio')
        municipioEmisor.text = str(_muniEmisor)

        departamentoEmisor = SubElement(DireccionEmisor, 'dte:Departamento')
        departamentoEmisor.text = str(_deptoEmisor)

        paisEmisor = SubElement(DireccionEmisor, 'dte:Pais')
        paisEmisor.text = str(_paisEmisor)

        # RECEPTOR
        Receptor = SubElement(DatosEmision, 'dte:Receptor')
        Receptor.set('CorreoReceptor', _mailRec)
        Receptor.set('IDReceptor', _IDReceptor)
        Receptor.set('NombreReceptor', _NombreReceptor)
        if self.partner_id.type_document == 'CUI':
            Receptor.set('TipoEspecial', 'CUI')
        elif self.partner_id.type_document == 'EXT':
            Receptor.set('TipoEspecial', 'EXT')
        else: 
            pass

        DireccionReceptor = SubElement(Receptor, 'dte:DireccionReceptor')

        calleRecept = SubElement(DireccionReceptor, 'dte:Direccion')
        calleRecept.text = str(_calleRecept)

        postalRecept = SubElement(DireccionReceptor, 'dte:CodigoPostal')
        postalRecept.text = str(_postalRecept)

        municipioRecept = SubElement(DireccionReceptor, 'dte:Municipio')
        municipioRecept.text = str(_muniRecept)

        departamentoRecept = SubElement(DireccionReceptor, 'dte:Departamento')
        departamentoRecept.text = str(_deptoRecept)

        paisRecept = SubElement(DireccionReceptor, 'dte:Pais')
        paisRecept.text = str(_paisRecept)

        # FRASES
        frases = SubElement(DatosEmision, 'dte:Frases')
        for phrase in _frases:
            frase = SubElement(frases, 'dte:Frase')
            frase.set('CodigoEscenario', str(phrase[0]))
            frase.set('TipoFrase', str(phrase[1]))

        # ITEMS
        items = SubElement(DatosEmision, 'dte:Items')
        for prod in _items:
            item = SubElement(items, 'dte:Item')
            item.set('BienOServicio', str(prod[0]))
            item.set('NumeroLinea', str(prod[1]))
            cantidad = SubElement(item, 'dte:Cantidad')
            cantidad.text = str(prod[2])
            uom = SubElement(item, 'dte:UnidadMedida')
            uom.text = str(prod[3])
            descripcion = SubElement(item, 'dte:Descripcion')
            descripcion.text = str(prod[4])
            precio_unitario = SubElement(item, 'dte:PrecioUnitario')
            precio_unitario.text = str(prod[5])
            precio = SubElement(item, 'dte:Precio')
            precio.text = str(prod[6])
            descuento = SubElement(item, 'dte:Descuento')
            descuento.text = str(prod[7])
            impuestos = SubElement(item, 'dte:Impuestos')
            impuesto = SubElement(impuestos, 'dte:Impuesto')
            nombre_corto = SubElement(impuesto, 'dte:NombreCorto')
            nombre_corto.text = "IVA"
            codigo_tax = SubElement(impuesto, 'dte:CodigoUnidadGravable')
            codigo_tax.text = "1"
            taxable = SubElement(impuesto, 'dte:MontoGravable')
            taxable.text = str(prod[8])
            tax_amount = SubElement(impuesto, 'dte:MontoImpuesto')
            tax_amount.text = str(prod[10])
            total_line = SubElement(item, 'dte:Total')
            total_line.text = str(prod[11])

        # TOTALES
        totales = SubElement(DatosEmision, 'dte:Totales')
        listaImpuestos = SubElement(totales, 'dte:TotalImpuestos')
        totalImpuesto = SubElement(listaImpuestos, 'dte:TotalImpuesto')
        totalImpuesto.set('NombreCorto', 'IVA')
        totalImpuesto.set('TotalMontoImpuesto', str(_iva))

        granTotal = SubElement(totales, 'dte:GranTotal')
        granTotal.text = str(_total)

        # Adenda
        if AdendaSummaryData:
            Adenda = SubElement(sat, 'dte:Adenda')
            AdendaDetail = SubElement(Adenda, 'dte:AdendaDetail')
            AdendaDetail.set('ID', 'AdendaSummary')
            AdendaSummary = SubElement(AdendaDetail, 'dte:AdendaSummary')
            count = 1
            for adsum in AdendaSummaryData:
                val = SubElement(AdendaSummary, 'dte:Valor' + str(count))
                val.text = adsum
                count += 1

        Complementos = SubElement(DatosEmision, 'dte:Complementos')
        Complemento = SubElement(Complementos, 'dte:Complemento')
        Complemento.set('IDComplemento', 'Text')
        Complemento.set('NombreComplemento', 'Text')
        Complemento.set('URIComplemento', 'Text')

        AbonosFacturaCambiaria = SubElement(Complemento, 'cfc:AbonosFacturaCambiaria')
        # AbonosFacturaCambiaria.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.1.0')
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

        rough_string = ET.tostring(fe)
        reparsed = minidom.parseString(rough_string)
        pretty_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
        #self.xml_request = pretty_str
        return pretty_str

    def GenerateXML_FACT(self, _moneda, _fechayhora, _numeroacceso, _tipo, _afiIVA, _estabCode, _mailEmi, _NITEmisor, _NombreComercial, _NombreEmisor,
                         _calleEmisor, _postalEmisor, _muniEmisor, _deptoEmisor, _paisEmisor, _mailRec, _IDReceptor, _NombreReceptor, _calleRecept,
                         _postalRecept, _muniRecept, _deptoRecept, _paisRecept, _frases, _items, _iva, _total, _uuId, AdendaSummaryData):

        fe = Element('dte:GTDocumento')
        fe.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.2.0')
        fe.set('xmlns:xd', 'http://www.w3.org/2000/09/xmldsig#')
        fe.set('Version', '0.1')

        sat = SubElement(fe, 'dte:SAT')
        sat.set('ClaseDocumento', 'dte')

        DTE = SubElement(sat, 'dte:DTE')
        DTE.set('ID', 'DatosCertificados')

        DatosEmision = SubElement(DTE, 'dte:DatosEmision')
        DatosEmision.set('ID', 'DatosEmision')

        DatosGenerales = SubElement(DatosEmision, 'dte:DatosGenerales')
        DatosGenerales.set('CodigoMoneda', _moneda)
        DatosGenerales.set('FechaHoraEmision', _fechayhora)
        DatosGenerales.set('NumeroAcceso', _numeroacceso)
        DatosGenerales.set('Tipo', _tipo)

        # EMISOR
        Emisor = SubElement(DatosEmision, 'dte:Emisor')
        Emisor.set('AfiliacionIVA', _afiIVA)
        Emisor.set('CodigoEstablecimiento', _estabCode)
        Emisor.set('CorreoEmisor', _mailEmi)
        Emisor.set('NITEmisor', _NITEmisor)
        Emisor.set('NombreComercial', _NombreComercial)
        Emisor.set('NombreEmisor', _NombreEmisor)

        DireccionEmisor = SubElement(Emisor, 'dte:DireccionEmisor')

        calleEmisor = SubElement(DireccionEmisor, 'dte:Direccion')
        calleEmisor.text = str(_calleEmisor)

        postalEmisor = SubElement(DireccionEmisor, 'dte:CodigoPostal')
        postalEmisor.text = str(_postalEmisor)

        municipioEmisor = SubElement(DireccionEmisor, 'dte:Municipio')
        municipioEmisor.text = str(_muniEmisor)

        departamentoEmisor = SubElement(DireccionEmisor, 'dte:Departamento')
        departamentoEmisor.text = str(_deptoEmisor)

        paisEmisor = SubElement(DireccionEmisor, 'dte:Pais')
        paisEmisor.text = str(_paisEmisor)

        # RECEPTOR
        Receptor = SubElement(DatosEmision, 'dte:Receptor')
        Receptor.set('CorreoReceptor', _mailRec)
        Receptor.set('IDReceptor', _IDReceptor)
        Receptor.set('NombreReceptor', _NombreReceptor)
        if self.partner_id.type_document == 'CUI':
            Receptor.set('TipoEspecial', 'CUI')
        elif self.partner_id.type_document == 'EXT':
            Receptor.set('TipoEspecial', 'EXT')
        else: 
            pass

        DireccionReceptor = SubElement(Receptor, 'dte:DireccionReceptor')

        calleRecept = SubElement(DireccionReceptor, 'dte:Direccion')
        calleRecept.text = str(_calleRecept)

        postalRecept = SubElement(DireccionReceptor, 'dte:CodigoPostal')
        postalRecept.text = str(_postalRecept)

        municipioRecept = SubElement(DireccionReceptor, 'dte:Municipio')
        municipioRecept.text = str(_muniRecept)

        departamentoRecept = SubElement(DireccionReceptor, 'dte:Departamento')
        departamentoRecept.text = str(_deptoRecept)

        paisRecept = SubElement(DireccionReceptor, 'dte:Pais')
        paisRecept.text = str(_paisRecept)

        # FRASES
        frases = SubElement(DatosEmision, 'dte:Frases')
        for phrase in _frases:
            frase = SubElement(frases, 'dte:Frase')
            frase.set('CodigoEscenario', str(phrase[0]))
            frase.set('TipoFrase', str(phrase[1]))

        # ITEMS
        items = SubElement(DatosEmision, 'dte:Items')
        for prod in _items:
            item = SubElement(items, 'dte:Item')
            item.set('BienOServicio', str(prod[0]))
            item.set('NumeroLinea', str(prod[1]))
            cantidad = SubElement(item, 'dte:Cantidad')
            cantidad.text = str(prod[2])
            uom = SubElement(item, 'dte:UnidadMedida')
            uom.text = str(prod[3])
            descripcion = SubElement(item, 'dte:Descripcion')
            descripcion.text = str(prod[4])
            precio_unitario = SubElement(item, 'dte:PrecioUnitario')
            precio_unitario.text = str(prod[5])
            precio = SubElement(item, 'dte:Precio')
            precio.text = str(prod[6])
            descuento = SubElement(item, 'dte:Descuento')
            descuento.text = str(prod[7])
            impuestos = SubElement(item, 'dte:Impuestos')
            impuesto = SubElement(impuestos, 'dte:Impuesto')
            nombre_corto = SubElement(impuesto, 'dte:NombreCorto')
            nombre_corto.text = "IVA"
            codigo_tax = SubElement(impuesto, 'dte:CodigoUnidadGravable')
            codigo_tax.text = "1"
            taxable = SubElement(impuesto, 'dte:MontoGravable')
            taxable.text = str(prod[8])
            tax_amount = SubElement(impuesto, 'dte:MontoImpuesto')
            tax_amount.text = str(prod[10])
            total_line = SubElement(item, 'dte:Total')
            total_line.text = str(prod[11])

        # TOTALES
        totales = SubElement(DatosEmision, 'dte:Totales')
        listaImpuestos = SubElement(totales, 'dte:TotalImpuestos')
        totalImpuesto = SubElement(listaImpuestos, 'dte:TotalImpuesto')
        totalImpuesto.set('NombreCorto', 'IVA')
        totalImpuesto.set('TotalMontoImpuesto', str(_iva))

        granTotal = SubElement(totales, 'dte:GranTotal')
        granTotal.text = str(_total)

        # Adenda
        if AdendaSummaryData:
            Adenda = SubElement(sat, 'dte:Adenda')
            AdendaDetail = SubElement(Adenda, 'dte:AdendaDetail')
            AdendaDetail.set('ID', 'AdendaSummary')
            AdendaSummary = SubElement(AdendaDetail, 'dte:AdendaSummary')
            count = 1
            for adsum in AdendaSummaryData:
                val = SubElement(AdendaSummary, 'dte:Valor' + str(count))
                val.text = adsum
                count += 1

        rough_string = ET.tostring(fe, encoding='utf-8', method='xml')
        reparsed = minidom.parseString(rough_string)
        pretty_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
        return pretty_str

    def GenerateXML_NCRE(self, _moneda, _fechayhora, _numeroacceso, _tipo, _afiIVA, _estabCode, _mailEmi, _NITEmisor, _NombreComercial, _NombreEmisor,
                         _calleEmisor, _postalEmisor, _muniEmisor, _deptoEmisor, _paisEmisor, _mailRec, _IDReceptor, _NombreReceptor, _calleRecept,
                         _postalRecept, _muniRecept, _deptoRecept, _paisRecept, _frases, _items, _iva, _total, _uuId, Complemento_Data, AdendaSummaryData):

        fe = Element('dte:GTDocumento')
        fe.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.2.0')
        fe.set('xmlns:xd', 'http://www.w3.org/2000/09/xmldsig#')
        #fe.set('xmlns:n1', 'http://www.altova.com/samplexml/other-namespace')
        #fe.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        fe.set('Version', '0.1')

        #fe.set('xmlns:xd', 'http://www.w3.org/2000/09/xmldsig#')
        #fe.set('xmlns:cfc', 'http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0')
        #fe.set('xmlns:cex', 'http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0')
        #fe.set('xmlns:cfe', 'http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0')
        #fe.set('xmlns:cno', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0')

        sat = SubElement(fe, 'dte:SAT')
        sat.set('ClaseDocumento', 'dte')

        DTE = SubElement(sat, 'dte:DTE')
        DTE.set('ID', 'DatosCertificados')

        DatosEmision = SubElement(DTE, 'dte:DatosEmision')
        DatosEmision.set('ID', 'DatosEmision')

        DatosGenerales = SubElement(DatosEmision, 'dte:DatosGenerales')
        DatosGenerales.set('CodigoMoneda', _moneda)
        DatosGenerales.set('FechaHoraEmision', _fechayhora)
        DatosGenerales.set('NumeroAcceso', _numeroacceso)
        DatosGenerales.set('Tipo', _tipo)

        # Emisor
        Emisor = SubElement(DatosEmision, 'dte:Emisor')
        Emisor.set('AfiliacionIVA', _afiIVA)
        Emisor.set('CodigoEstablecimiento', _estabCode)
        # Emisor.set('AfiliacionIVA',_estabCode)
        Emisor.set('CorreoEmisor', _mailEmi)
        Emisor.set('NITEmisor', _NITEmisor)
        Emisor.set('NombreComercial', _NombreComercial)
        Emisor.set('NombreEmisor', _NombreEmisor)

        DireccionEmisor = SubElement(Emisor, 'dte:DireccionEmisor')

        calleEmisor = SubElement(DireccionEmisor, 'dte:Direccion')
        calleEmisor.text = str(_calleEmisor)

        postalEmisor = SubElement(DireccionEmisor, 'dte:CodigoPostal')
        postalEmisor.text = str(_postalEmisor)

        municipioEmisor = SubElement(DireccionEmisor, 'dte:Municipio')
        municipioEmisor.text = str(_muniEmisor)

        departamentoEmisor = SubElement(DireccionEmisor, 'dte:Departamento')
        departamentoEmisor.text = str(_deptoEmisor)

        paisEmisor = SubElement(DireccionEmisor, 'dte:Pais')
        paisEmisor.text = str(_paisEmisor)

        # RECEPTOR
        Receptor = SubElement(DatosEmision, 'dte:Receptor')
        Receptor.set('CorreoReceptor', _mailRec)
        Receptor.set('IDReceptor', _IDReceptor)
        Receptor.set('NombreReceptor', _NombreReceptor)
        if self.partner_id.type_document == 'CUI':
            Receptor.set('TipoEspecial', 'CUI')
        elif self.partner_id.type_document == 'EXT':
            Receptor.set('TipoEspecial', 'EXT')
        else: 
            pass

        DireccionReceptor = SubElement(Receptor, 'dte:DireccionReceptor')

        calleRecept = SubElement(DireccionReceptor, 'dte:Direccion')
        calleRecept.text = str(_calleRecept)

        postalRecept = SubElement(DireccionReceptor, 'dte:CodigoPostal')
        postalRecept.text = str(_postalRecept)

        municipioRecept = SubElement(DireccionReceptor, 'dte:Municipio')
        municipioRecept.text = str(_muniRecept)

        departamentoRecept = SubElement(DireccionReceptor, 'dte:Departamento')
        departamentoRecept.text = str(_deptoRecept)

        paisRecept = SubElement(DireccionReceptor, 'dte:Pais')
        paisRecept.text = str(_paisRecept)

        # FRASES
        frases = SubElement(DatosEmision, 'dte:Frases')
        for phrase in _frases:
            frase = SubElement(frases, 'dte:Frase')
            frase.set('CodigoEscenario', str(phrase[0]))
            frase.set('TipoFrase', str(phrase[1]))

        # ITEMS
        items = SubElement(DatosEmision, 'dte:Items')
        for prod in _items:
            item = SubElement(items, 'dte:Item')
            item.set('BienOServicio', str(prod[0]))
            item.set('NumeroLinea', str(prod[1]))
            cantidad = SubElement(item, 'dte:Cantidad')
            cantidad.text = str(prod[2])
            uom = SubElement(item, 'dte:UnidadMedida')
            uom.text = str(prod[3])
            descripcion = SubElement(item, 'dte:Descripcion')
            descripcion.text = str(prod[4])
            precio_unitario = SubElement(item, 'dte:PrecioUnitario')
            precio_unitario.text = str(prod[5])
            precio = SubElement(item, 'dte:Precio')
            precio.text = str(prod[6])
            descuento = SubElement(item, 'dte:Descuento')
            descuento.text = str(prod[7])
            impuestos = SubElement(item, 'dte:Impuestos')
            impuesto = SubElement(impuestos, 'dte:Impuesto')
            nombre_corto = SubElement(impuesto, 'dte:NombreCorto')
            nombre_corto.text = "IVA"
            codigo_tax = SubElement(impuesto, 'dte:CodigoUnidadGravable')
            codigo_tax.text = "1"
            taxable = SubElement(impuesto, 'dte:MontoGravable')
            taxable.text = str(prod[8])
            tax_amount = SubElement(impuesto, 'dte:MontoImpuesto')
            tax_amount.text = str(prod[10])
            total_line = SubElement(item, 'dte:Total')
            total_line.text = str(prod[11])

        # TOTALES
        totales = SubElement(DatosEmision, 'dte:Totales')
        listaImpuestos = SubElement(totales, 'dte:TotalImpuestos')
        totalImpuesto = SubElement(listaImpuestos, 'dte:TotalImpuesto')
        totalImpuesto.set('NombreCorto', 'IVA')
        totalImpuesto.set('TotalMontoImpuesto', str(_iva))

        granTotal = SubElement(totales, 'dte:GranTotal')
        granTotal.text = str(_total)

        # Adenda
        if AdendaSummaryData:
            Adenda = SubElement(sat, 'dte:Adenda')
            AdendaDetail = SubElement(Adenda, 'dte:AdendaDetail')
            AdendaDetail.set('ID', 'AdendaSummary')
            AdendaSummary = SubElement(AdendaDetail, 'dte:AdendaSummary')
            count = 1
            for adsum in AdendaSummaryData:
                val = SubElement(AdendaSummary, 'dte:Valor' + str(count))
                val.text = adsum
                count += 1

        Complementos = SubElement(DatosEmision, 'dte:Complementos')
        Complemento = SubElement(Complementos, 'dte:Complemento')
        Complemento.set('IDComplemento', '1')
        Complemento.set('NombreComplemento', 'NOTA CREDITO')
        Complemento.set('URIComplemento', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0')

        ReferenciasNota = SubElement(Complemento, 'cno:ReferenciasNota')
        ReferenciasNota.set('xmlns:cno', 'http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0')
        ReferenciasNota.set('FechaEmisionDocumentoOrigen', Complemento_Data['origin_date'])
        ReferenciasNota.set('NumeroDocumentoOrigen', self.invoice_refund_id.fel_no)
        ReferenciasNota.set('SerieDocumentoOrigen', self.invoice_refund_id.fel_serie)
        # ReferenciasNota.set('MotivoAjuste', 'devolucion')
        ReferenciasNota.set('MotivoAjuste', 'Nota de credito')
        ReferenciasNota.set('NumeroAutorizacionDocumentoOrigen', Complemento_Data['auth_number_doc_origin'])
        ReferenciasNota.set('Version', '0.1')

        rough_string = ET.tostring(fe, encoding='utf-8', method='xml')
        reparsed = minidom.parseString(rough_string)
        pretty_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
        #self.xml_request = pretty_str
        return pretty_str

    def GenerateXML_FPEQ(self, _moneda, _fechayhora, _numeroacceso, _tipo, _afiIVA, _estabCode, _mailEmi, _NITEmisor, _NombreComercial, _NombreEmisor,
                         _calleEmisor, _postalEmisor, _muniEmisor, _deptoEmisor, _paisEmisor, _mailRec, _IDReceptor, _NombreReceptor, _calleRecept,
                         _postalRecept, _muniRecept, _deptoRecept, _paisRecept, _frases, _items, _iva, _total, _uuId, AdendaSummaryData):

        fe = Element('dte:GTDocumento')
        fe.set('xmlns:dte', 'http://www.sat.gob.gt/dte/fel/0.2.0')
        fe.set('xmlns:xd', 'http://www.w3.org/2000/09/xmldsig#')
        fe.set('Version', '0.1')

        sat = SubElement(fe, 'dte:SAT')
        sat.set('ClaseDocumento', 'dte')

        DTE = SubElement(sat, 'dte:DTE')
        DTE.set('ID', 'DatosCertificados')

        DatosEmision = SubElement(DTE, 'dte:DatosEmision')
        DatosEmision.set('ID', 'DatosEmision')

        DatosGenerales = SubElement(DatosEmision, 'dte:DatosGenerales')
        DatosGenerales.set('CodigoMoneda', _moneda)
        DatosGenerales.set('FechaHoraEmision', _fechayhora)
        DatosGenerales.set('NumeroAcceso', _numeroacceso)
        DatosGenerales.set('Tipo', _tipo)

        # EMISOR
        Emisor = SubElement(DatosEmision, 'dte:Emisor')
        Emisor.set('AfiliacionIVA', _afiIVA)
        Emisor.set('CodigoEstablecimiento', _estabCode)
        Emisor.set('CorreoEmisor', _mailEmi)
        Emisor.set('NITEmisor', _NITEmisor)
        Emisor.set('NombreComercial', _NombreComercial)
        Emisor.set('NombreEmisor', _NombreEmisor)

        DireccionEmisor = SubElement(Emisor, 'dte:DireccionEmisor')

        calleEmisor = SubElement(DireccionEmisor, 'dte:Direccion')
        calleEmisor.text = str(_calleEmisor)

        postalEmisor = SubElement(DireccionEmisor, 'dte:CodigoPostal')
        postalEmisor.text = str(_postalEmisor)

        municipioEmisor = SubElement(DireccionEmisor, 'dte:Municipio')
        municipioEmisor.text = str(_muniEmisor)

        departamentoEmisor = SubElement(DireccionEmisor, 'dte:Departamento')
        departamentoEmisor.text = str(_deptoEmisor)

        paisEmisor = SubElement(DireccionEmisor, 'dte:Pais')
        paisEmisor.text = str(_paisEmisor)

        # RECEPTOR
        Receptor = SubElement(DatosEmision, 'dte:Receptor')
        Receptor.set('CorreoReceptor', _mailRec)
        Receptor.set('IDReceptor', _IDReceptor)
        Receptor.set('NombreReceptor', _NombreReceptor)
        if self.partner_id.type_document == 'CUI':
            Receptor.set('TipoEspecial', 'CUI')
        elif self.partner_id.type_document == 'EXT':
            Receptor.set('TipoEspecial', 'EXT')
        else: 
            pass

        DireccionReceptor = SubElement(Receptor, 'dte:DireccionReceptor')

        calleRecept = SubElement(DireccionReceptor, 'dte:Direccion')
        calleRecept.text = str(_calleRecept)

        postalRecept = SubElement(DireccionReceptor, 'dte:CodigoPostal')
        postalRecept.text = str(_postalRecept)

        municipioRecept = SubElement(DireccionReceptor, 'dte:Municipio')
        municipioRecept.text = str(_muniRecept)

        departamentoRecept = SubElement(DireccionReceptor, 'dte:Departamento')
        departamentoRecept.text = str(_deptoRecept)

        paisRecept = SubElement(DireccionReceptor, 'dte:Pais')
        paisRecept.text = str(_paisRecept)

        # FRASES
        frases = SubElement(DatosEmision, 'dte:Frases')
        for phrase in _frases:
            frase = SubElement(frases, 'dte:Frase')
            frase.set('CodigoEscenario', str(phrase[0]))
            frase.set('TipoFrase', str(phrase[1]))

        # ITEMS
        items = SubElement(DatosEmision, 'dte:Items')
        for prod in _items:
            item = SubElement(items, 'dte:Item')
            item.set('BienOServicio', str(prod[0]))
            item.set('NumeroLinea', str(prod[1]))
            cantidad = SubElement(item, 'dte:Cantidad')
            cantidad.text = str(prod[2])
            uom = SubElement(item, 'dte:UnidadMedida')
            uom.text = str(prod[3])
            descripcion = SubElement(item, 'dte:Descripcion')
            descripcion.text = str(prod[4])
            precio_unitario = SubElement(item, 'dte:PrecioUnitario')
            precio_unitario.text = str(prod[5])
            precio = SubElement(item, 'dte:Precio')
            precio.text = str(prod[6])
            descuento = SubElement(item, 'dte:Descuento')
            descuento.text = str(prod[7])
            #impuestos = SubElement(item, 'dte:Impuestos')
            #impuesto = SubElement(impuestos, 'dte:Impuesto')
            #nombre_corto = SubElement(impuesto, 'dte:NombreCorto')
            #nombre_corto.text = "IVA"
            #codigo_tax = SubElement(impuesto, 'dte:CodigoUnidadGravable')
            #codigo_tax.text = "1"
            #taxable = SubElement(impuesto, 'dte:MontoGravable')
            #taxable.text = str(prod[8])
            #tax_amount = SubElement(impuesto, 'dte:MontoImpuesto')
            #tax_amount.text = str(prod[10])
            total_line = SubElement(item, 'dte:Total')
            total_line.text = str(prod[11])

        # TOTALES
        totales = SubElement(DatosEmision, 'dte:Totales')
        #listaImpuestos = SubElement(totales, 'dte:TotalImpuestos')
        #totalImpuesto = SubElement(listaImpuestos, 'dte:TotalImpuesto')
        #totalImpuesto.set('NombreCorto', 'IVA')
        #totalImpuesto.set('TotalMontoImpuesto', str(_iva))

        granTotal = SubElement(totales, 'dte:GranTotal')
        granTotal.text = str(_total)

        # Adenda
        if AdendaSummaryData:
            Adenda = SubElement(sat, 'dte:Adenda')
            AdendaDetail = SubElement(Adenda, 'dte:AdendaDetail')
            AdendaDetail.set('ID', 'AdendaSummary')
            AdendaSummary = SubElement(AdendaDetail, 'dte:AdendaSummary')
            count = 1
            for adsum in AdendaSummaryData:
                val = SubElement(AdendaSummary, 'dte:Valor' + str(count))
                val.text = adsum
                count += 1

        rough_string = ET.tostring(fe, encoding='utf-8', method='xml')
        reparsed = minidom.parseString(rough_string)
        pretty_str = reparsed.toprettyxml(indent="  ", encoding="utf-8")
        return pretty_str


AccountInvoice()