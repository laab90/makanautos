from odoo import models
import io
import base64
from datetime import datetime
from decimal import Decimal


class InvoiceSaleXlsx(models.AbstractModel):
    _name = 'report.account_invoice_report_excel_rq.sale_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            sheet = workbook.add_worksheet('Facturas Ventas')

            # FORMATOS
            bold = workbook.add_format({'bold': True})
            bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
            bold_center_color = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': 'orange'})

            no_bold = workbook.add_format({'bold': False})
            no_bold_center = workbook.add_format({'bold': False, 'align': 'center', 'valign': 'vcenter'})
            no_bold_color = workbook.add_format({'bold': False, 'bg_color': 'orange'})

            # desde AQUI LOGO y TITULO
            logo = io.BytesIO(base64.b64decode(obj.company.logo_web))
            sheet.insert_image(0, 0, "image.png", {'image_data': logo})
            sheet.write(0, 4, 'LIBRO DE VENTAS', bold)
            # ENCABEZADO
            sheet.write(4, 0, 'NOMBRE O RAZON SOCIAL:', bold)
            sheet.write(4, 3, obj.company.name, no_bold)
            sheet.write(5, 0, 'DIRECCION CASA MATRIZ:', bold)
            sheet.write(5, 3, obj.company.street, no_bold)
            sheet.write(6, 0, 'SUCURSAL:', bold)
            sheet.write(6, 3, '', no_bold)
            sheet.write(7, 0, 'RTN:', bold)
            sheet.write(7, 3, obj.company.vat, no_bold)


            # TAMAÑOS
            sheet.set_column('D:D', 15)
            sheet.set_column('F:F', 25)
            sheet.set_column('G:G', 12)
            sheet.set_column('H:H', 45)
            sheet.set_column('I:I', 26)
            sheet.set_column('J:J', 30)
            sheet.set_column('K:K', 18)
            sheet.set_column('L:L', 40)
            sheet.set_column('M:M', 30)
            sheet.set_column('N:N', 30)
            sheet.set_column('O:O', 30)
            sheet.set_column('P:P', 30)
            sheet.set_column('Q:Q', 16)
            sheet.set_column('R:R', 16)
            sheet.set_column('S:S', 50)
            sheet.set_column('T:T', 10)
            # TITULO TABLA
            sheet.merge_range('A11:C11', 'FECHA', bold_center)
            sheet.write(11, 0, 'DIA', bold_center)
            sheet.write(11, 1, 'MES', bold_center)
            sheet.write(11, 2, 'AÑO', bold_center)
            sheet.merge_range('D11:D12', 'PREFIJO', bold_center)
            sheet.merge_range('E11:E12', 'N°\nDOCUMENTO', bold_center)
            sheet.merge_range('F11:F12', 'CAI', bold_center_color)
            sheet.merge_range('G11:G12', 'TIPO\nDOCUMENTO', bold_center)
            sheet.merge_range('H11:H12', 'OC\nExenta', bold_center)
            sheet.merge_range('I11:I12', 'No. Constancia\nRegistro Exonerados', bold_center)
            sheet.merge_range('J11:J12', 'No. Reg.\nSAG', bold_center)
            sheet.merge_range('K11:K12', 'VENTA BRUTA\nSIN IMPUESTOS', bold_center_color)

            sheet.merge_range('L11:L12', 'DESCUENTOS', bold_center_color)
            sheet.merge_range('M11:M12', 'VENTA NETA SIN IMPUESTOS', bold_center_color)
            sheet.merge_range('N11:N12', 'IMPORTE EXENTO', bold_center_color)
            sheet.merge_range('O11:O12', 'IMPORTE EXONERADO', bold_center_color)
            sheet.merge_range('P11:P12', 'IMPORTE GRAVADO 15%', bold_center_color)
            sheet.merge_range('Q11:Q12', 'IMPORTE GRAVADO 18%', bold_center_color)
            sheet.merge_range('R11:R12', 'IMPUESTO 15%', bold_center_color)
            sheet.merge_range('S11:S12', 'IMPUESTO 18%', bold_center_color)
            sheet.merge_range('T11:T12', 'I.V.A. DEBITO FISCAL (SUMA IMPUESTO 15 Y 18%)', bold_center_color)
            sheet.merge_range('U11:U12', 'PROPINA', bold_center_color)
            sheet.merge_range('V11:V12', 'TOTAL', bold_center_color)

            # sheet.write(0, 0,  obj.company_current.logo, bold)
            # for i in range(10):
            #     sheet.write(4, i, 'sale', bold)

            # ---------------------------------------------------------------------------------------------------
            # ---------------------------------------------------------------------------------------------------
            # ---------------------------------------------------------------------------------------------------
            # Facturas de cliente (ventas)
            id_fac = obj.invoice_sale_ids.split(',')
            for x in range(len(id_fac)):
                id_fac[x] = int(id_fac[x])
            ventas = self.env['account.move'].search( [('id', 'in', id_fac)],  order="invoice_date asc" )

            # SUMAS DE COLUMNAS
            suma_venta_bruta_sin_impuesto_9 = 0
            suma_discount_total = 0
            suma_venta_neta_sin_impuesto_11 = 0
            suma_importe_exento_12 = 0
            suma_importe_grabado_15_14 = 0
            suma_importe_grabado_18_15 = 0
            suma_impuesto_15_16 = 0
            suma_impuesto_18_17 = 0
            suma_suma_impuestos_18 = 0
            suma_propina_19 = 0
            suma_total_20 = 0

            ini_row = 12
            for x in range(len(ventas)):
                # date
                sheet.write(ini_row + x, 0, str(ventas[x].invoice_date.day), no_bold)
                sheet.write(ini_row + x, 1, str(ventas[x].invoice_date.month), no_bold)
                sheet.write(ini_row + x, 2, str(ventas[x].invoice_date.year), no_bold)

                # name - prefijo y numero
                name_split = ventas[x].name.strip().split('/')
                # sheet.write(ini_row + x, 3, str(int(name_split[-1])), no_bold)

                # num_doc - Numero de documento
                sheet.write(ini_row + x, 3, ventas[x].journal_id.prefix, no_bold_color)
                sheet.write(ini_row + x, 4, ventas[x].num_doc, no_bold)
                sheet.write(ini_row + x, 5, ventas[x].journal_id.cai, no_bold_color)

                # factura de cliente F si es rectificativa NC
                if ventas[x].type == 'out_invoice':
                    sheet.write(ini_row + x, 6, 'F', no_bold)
                elif ventas[x].type == 'out_refund':
                    sheet.write(ini_row + x, 6, 'NC', no_bold)

                # 3 libres
                venta_bruta_sin_impuesto_9 = 0
                descuento_10 = 0
                venta_neta_sin_impuesto_11 = 0 # fuera del for se calcula para eviaar la multiplicacion
                importe_exento_12 = 0
                importe_grabado_15_14 = 0
                importe_grabado_18_15 = 0
                impuesto_15_16 = 0      # fuera
                impuesto_18_17 = 0      # fuera
                suma_impuestos_18 = 0      # fuera
                propina_19 = ventas[x].amount_tip            # no hay nada todavia
                discount_total = 0    # Descuento
                total_20 = 0            # no hay nada todavia
                for y in ventas[x].invoice_line_ids:
                    temp_venta = y.quantity * y.price_unit
                    if y.product_id.id != ventas[x].company_id.product_tip_id.id:
                        venta_bruta_sin_impuesto_9 += temp_venta
                    temp_descuento = (temp_venta * y.discount) / 100
                    # descuento_10 += temp_descuento
                    #if y.product_id.id == y.company_id.product_tip_id.id:
                    #    propina_19 += y.price_subtotal
                    # temp_descuento = y.price_subtotal - y.product_discount
                    discount_total += y.product_discount
                    tax_amount = 0.00
                    #calculo de impuestos
                    taxes = y.tax_ids.compute_all(y.price_unit, y.company_id.currency_id, y.quantity, y.product_id, y.partner_id)
                    for tax in taxes.get('taxes', []):
                        tax_amount += tax.get('amount', 0.00)
                    if tax_amount == 0.00:
                        importe_exento_12 += temp_venta - temp_descuento
                    if len(y.tax_ids) == 0:
                        importe_exento_12 += temp_venta - temp_descuento
                    else:
                        if y.tax_ids[0].name.find('15') != -1:
                            importe_grabado_15_14 += temp_venta - temp_descuento
                        elif y.tax_ids[0].name.find('18') != -1:
                            importe_grabado_18_15 += temp_venta - temp_descuento

                    # print('')
                    # input('click')
                
                venta_neta_sin_impuesto_11 = venta_bruta_sin_impuesto_9 - discount_total
                impuesto_15_16 = importe_grabado_15_14 * 0.15
                impuesto_18_17 = importe_grabado_18_15 * 0.18
                suma_impuestos_18 = impuesto_15_16 + impuesto_18_17
                total_20 = venta_neta_sin_impuesto_11 + suma_impuestos_18 + propina_19

                sheet.write(ini_row + x, 10, round(Decimal(venta_bruta_sin_impuesto_9), 2), no_bold)
                sheet.write(ini_row + x, 11, round(Decimal(discount_total), 2), no_bold)
                sheet.write(ini_row + x, 12, round(Decimal(venta_neta_sin_impuesto_11), 2), no_bold)
                sheet.write(ini_row + x, 13, round(Decimal(importe_exento_12), 2), no_bold)
                #sheet.write(ini_row + x, 12, 0.00, no_bold)
                sheet.write(ini_row + x, 15, round(Decimal(importe_grabado_15_14), 2), no_bold)
                sheet.write(ini_row + x, 16, round(Decimal(importe_grabado_18_15), 2), no_bold)
                sheet.write(ini_row + x, 17, round(Decimal(impuesto_15_16), 2), no_bold)
                sheet.write(ini_row + x, 18, round(Decimal(impuesto_18_17), 2), no_bold)
                sheet.write(ini_row + x, 19, round(Decimal(suma_impuestos_18), 2), no_bold)
                sheet.write(ini_row + x, 20, round(Decimal(propina_19), 2), no_bold)
                sheet.write(ini_row + x, 21, round(Decimal(total_20), 2), no_bold)

                # SUMAS DE LAS COLUMNAS ARRIBA ES DE LAS FILAS
                suma_venta_bruta_sin_impuesto_9 += venta_bruta_sin_impuesto_9
                suma_discount_total += discount_total
                suma_venta_neta_sin_impuesto_11 += venta_neta_sin_impuesto_11
                suma_importe_exento_12 += importe_exento_12
                suma_importe_grabado_15_14 += importe_grabado_15_14
                suma_importe_grabado_18_15 += importe_grabado_18_15
                suma_impuesto_15_16 += impuesto_15_16
                suma_impuesto_18_17 += impuesto_18_17
                suma_suma_impuestos_18 += suma_impuestos_18
                suma_propina_19 += propina_19
                suma_total_20 += total_20


            # IMPRIMIENDO TOTALES de COLUMNAS
            row_total = ini_row + len(ventas)

            sheet.write(row_total, 10, round(Decimal(suma_venta_bruta_sin_impuesto_9), 2), bold)
            sheet.write(row_total, 11, round(Decimal(suma_discount_total), 2), bold)
            sheet.write(row_total, 12, round(Decimal(suma_venta_neta_sin_impuesto_11), 2), bold)
            sheet.write(row_total, 13, round(Decimal(suma_importe_exento_12), 2), bold)
            sheet.write(row_total, 15, round(Decimal(suma_importe_grabado_15_14), 2), bold)
            sheet.write(row_total, 16, round(Decimal(suma_importe_grabado_18_15), 2), bold)
            sheet.write(row_total, 17, round(Decimal(suma_impuesto_15_16), 2), bold)
            sheet.write(row_total, 18, round(Decimal(suma_impuesto_18_17), 2), bold)
            sheet.write(row_total, 19, round(Decimal(suma_suma_impuestos_18), 2), bold)
            # sheet.write(row_total, 19, suma_venta_bruta_sin_impuesto_9, no_bold)
            sheet.write(row_total, 21, round(Decimal(suma_total_20), 2), bold)

            # input('termino?')


class InvoicePurchaseXlsx(models.AbstractModel):
    _name = 'report.account_invoice_report_excel_rq.purchase_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            sheet = workbook.add_worksheet('Facturas Compras')

            # FORMATOS
            bold = workbook.add_format({'bold': True})
            bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
            bold_center_color = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': 'orange'})
            no_bold = workbook.add_format({'bold': False})
            no_bold_center = workbook.add_format({'bold': False, 'align': 'center', 'valign': 'vcenter'})

            # desde AQUI LOGO y TITULO
            logo = io.BytesIO(base64.b64decode(obj.company_current.logo_web))
            sheet.insert_image(0, 0, "image.png", {'image_data': logo})
            sheet.write(0, 4, 'LIBRO DE COMPRAS', bold)

            # ENCABEZADO
            sheet.write(4, 0, 'NOMBRE O RAZON SOCIAL:', bold)
            sheet.write(4, 3, obj.company_current.name, no_bold)
            sheet.write(5, 0, 'DIRECCION CASA MATRIZ:', bold)
            sheet.write(5, 3, obj.company_current.street, no_bold)
            sheet.write(6, 0, 'SUCURSAL:', bold)
            sheet.write(6, 3, '', no_bold)
            sheet.write(7, 0, 'RTN:', bold)
            sheet.write(7, 3, obj.company_current.vat, no_bold)

            date_ini = str(obj.date_ini.day) + '-' + str(obj.date_ini.month) + '-' + str(obj.date_ini.year)
            date_fin = str(obj.date_fin.day) + '-' + str(obj.date_fin.month) + '-' + str(obj.date_fin.year)
            sheet.write(8, 0, 'FECHA INICIO:', bold)
            sheet.write(8, 3, date_ini, no_bold)
            sheet.write(9, 0, 'FECHA FIN:', bold)
            sheet.write(9, 3, date_fin, no_bold)

            # TAMAÑOS
            sheet.set_column('A:A', 24)
            sheet.set_column('B:B', 24)
            sheet.set_column('C:C', 16)
            sheet.set_column('D:D', 50)
            sheet.set_column('E:E', 26)
            sheet.set_column('F:F', 38)
            sheet.set_column('G:G', 26)
            sheet.set_column('H:H', 26)
            sheet.set_column('I:I', 30)
            sheet.set_column('J:J', 30)
            sheet.set_column('K:K', 16)
            sheet.set_column('L:L', 16)
            sheet.set_column('M:M', 26)
            sheet.set_column('N:N', 26)
            # TITULO TABLA
            sheet.merge_range('A12:A13', 'FECHA DE OPERACIÓN', bold_center_color)
            sheet.merge_range('B12:B13', 'FECHA DEL DOCUMENTO', bold_center_color)
            sheet.merge_range('C12:C13', 'RTN', bold_center_color)
            sheet.merge_range('D12:D13', 'PROVEEDOR', bold_center_color)
            sheet.merge_range('E12:E13', 'NÚMERO DE FACTURA', bold_center_color)
            sheet.merge_range('F12:F13', 'CUENTA ANALÍTICA', bold_center_color)
            sheet.merge_range('G12:G13', 'IMPORTE SIN IMPUESTOS', bold_center_color)
            sheet.merge_range('H12:H13', 'IMPORTE EXENTO', bold_center_color)
            sheet.merge_range('I12:I13', 'IMPORTE GRAVADO 15%', bold_center_color)
            sheet.merge_range('J12:J13', 'IMPORTE GRAVADO 18%', bold_center_color)
            sheet.merge_range('K12:K13', 'IMPUESTO 15%', bold_center_color)
            sheet.merge_range('L12:L13', 'IMPUESTO 18%', bold_center_color)
            sheet.merge_range('M12:M13', 'TOTAL IMPUESTOS', bold_center_color)
            sheet.merge_range('N12:N13', 'TOTAL IMPORTE', bold_center_color)

            # ---------------------------------------------------------------------------------------------------
            # ---------------------------------------------------------------------------------------------------
            # ---------------------------------------------------------------------------------------------------
            # Facturas de proveedor (compras)
            id_fac = obj.invoice_purchase_ids.split(',')
            for x in range(len(id_fac)):
                id_fac[x] = int(id_fac[x])
            compras = self.env['account.move'].search( [('id', 'in', id_fac)], order="invoice_date asc")


            suma_importe_sin_impuestos_5 = 0
            suma_importe_exento_6 = 0
            suma_importe_grabado_15_7 = 0
            suma_importe_grabado_18_8 = 0
            suma_impuesto_15_9 = 0
            suma_impuesto_18_10 = 0
            suma_suma_impuestos_11 = 0
            suma_total_12 = 0

            ini_row = 13
            for x in range(len(compras)):
                # fechas
                sheet.write(ini_row + x, 0, str(compras[x].date.strftime('%d-%m-%Y')), no_bold)
                sheet.write(ini_row + x, 1, str(compras[x].invoice_date.strftime('%d-%m-%Y')), no_bold)

                # proveedor
                partner_vat = compras[x].partner_id.vat
                partner_name = compras[x].partner_id.name
                # print(compras[x].partner_id.vat)
                # print(compras[x].partner_id.name)
                # print(compras[x].name)
                sheet.write(ini_row + x, 2, partner_vat, no_bold)
                sheet.write(ini_row + x, 3, partner_name, no_bold)
                # input('jaja')

                # # fac
                # fac_name = compras[x].name
                # sheet.write(ini_row + x, 4, fac_name, no_bold)

                # num factura 
                num_factura = compras[x].num_factura
                sheet.write(ini_row + x, 4, num_factura, no_bold)

                # analytic account
                analytic_account = compras[x].invoice_line_ids[0].analytic_account_id.name
                sheet.write(ini_row + x, 5, analytic_account, no_bold)

                importe_sin_impuestos_5 = 0
                importe_exento_6 = 0
                importe_grabado_15_7 = 0
                importe_grabado_18_8 = 0
                impuesto_15_9 = 0
                impuesto_18_10 = 0
                suma_impuestos_11 = 0
                total_12 = 0

                for y in compras[x].invoice_line_ids:
                    temp_compra = y.quantity * y.price_unit
                    temp_descuento = (temp_compra * y.discount) / 100
                    importe_sin_impuestos_5 += temp_compra - temp_descuento
                    tax_amount = 0.00
                    #calculo de impuestos
                    taxes = y.tax_ids.compute_all(y.price_unit, y.company_id.currency_id, y.quantity, y.product_id, y.partner_id)
                    for tax in taxes.get('taxes', []):
                        tax_amount += tax.get('amount', 0.00)
                    if tax_amount == 0.00:
                        importe_exento_6 += temp_compra - temp_descuento
                    if len(y.tax_ids) == 0:
                        importe_exento_6 += temp_compra - temp_descuento
                    else:
                        if y.tax_ids[0].name.find('15') != -1:
                            importe_grabado_15_7 += temp_compra - temp_descuento
                        elif y.tax_ids[0].name.find('18') != -1:
                            importe_grabado_18_8 += temp_compra - temp_descuento

                impuesto_15_9 = importe_grabado_15_7 * 0.15
                impuesto_18_10 = importe_grabado_18_8 * 0.18
                suma_impuestos_11 = impuesto_15_9 + impuesto_18_10
                total_12 = importe_sin_impuestos_5 + suma_impuestos_11 

                sheet.write(ini_row + x, 6, round(Decimal(compras[x].amount_untaxed_without_tip), 2), no_bold)
                sheet.write(ini_row + x, 7, round(Decimal(importe_exento_6), 2), no_bold)
                sheet.write(ini_row + x, 8, round(Decimal(importe_grabado_15_7), 2), no_bold)
                sheet.write(ini_row + x, 9, round(Decimal(importe_grabado_18_8), 2), no_bold)
                sheet.write(ini_row + x, 10, round(Decimal(impuesto_15_9), 2), no_bold)
                sheet.write(ini_row + x, 11, round(Decimal(impuesto_18_10), 2), no_bold)
                sheet.write(ini_row + x, 12, round(Decimal(suma_impuestos_11), 2), no_bold)
                sheet.write(ini_row + x, 13, round(Decimal(total_12), 2), no_bold)

                # SUMAS DE LAS COLUMNAS ARRIBA ES DE LAS FILAS
                suma_importe_sin_impuestos_5 += importe_sin_impuestos_5
                suma_importe_exento_6 += importe_exento_6
                suma_importe_grabado_15_7 += importe_grabado_15_7
                suma_importe_grabado_18_8 += importe_grabado_18_8
                suma_impuesto_15_9 += impuesto_15_9
                suma_impuesto_18_10 += impuesto_18_10
                suma_suma_impuestos_11 += suma_impuestos_11
                suma_total_12 += total_12


            # IMPRIMIENDO TOTALES de COLUMNAS
            row_total = ini_row + len(compras)

            sheet.write(row_total, 6, round(Decimal(suma_importe_sin_impuestos_5), 2), bold)
            sheet.write(row_total, 7, round(Decimal(suma_importe_exento_6), 2), bold)
            sheet.write(row_total, 8, round(Decimal(suma_importe_grabado_15_7), 2), bold)
            sheet.write(row_total, 9, round(Decimal(suma_importe_grabado_18_8), 2), bold)
            sheet.write(row_total, 10, round(Decimal(suma_impuesto_15_9), 2), bold)
            sheet.write(row_total, 11, round(Decimal(suma_impuesto_18_10), 2), bold)
            sheet.write(row_total, 12, round(Decimal(suma_suma_impuestos_11), 2), bold)
            sheet.write(row_total, 13, round(Decimal(suma_total_12), 2), bold)
            # sheet.write(row_total, 19, suma_venta_bruta_sin_impuesto_9, no_bold)
            # input('terminado?')
