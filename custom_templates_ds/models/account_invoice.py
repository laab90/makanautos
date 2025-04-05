# -*- coding: utf-8 -*-

import random

import datetime
import uuid

from odoo import fields, models, api
from odoo.exceptions import UserError, Warning
from odoo.addons.cheques_banco import numero_a_texto

import requests
import json
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
import base64
from odoo.tools.translate import _

import os  


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def _manual_taxes(self):
        for data in self:
            data_dict = {
                'importe_extento': 0,
                'importe_exonerado': 0,
                'isv_15': 0,
                'isv_18': 0,
                'gravado_15': 0,
                'gravado_18': 0,
                'cesc': 0,
                'iva_retenido': 0,
                'iva_13': 0,
            }
            json_taxes = json.loads(data.tax_totals_json)
            for linea in json_taxes['groups_by_subtotal']['Base imponible']:
                if linea['tax_group_name'] == 'ISV 15%':
                    data_dict['isv_15'] = linea['tax_group_amount']
                    data_dict['gravado_15'] = linea['tax_group_amount']
                if linea['tax_group_name'] == 'ISV 18%':
                    data_dict['isv_18'] = linea['tax_group_amount']
                    data_dict['gravado_18'] = linea['tax_group_amount']
                if linea['tax_group_name'] == '5% Contribución Especial CESC':
                    data_dict['cesc'] = linea['tax_group_amount']
                if linea['tax_group_name'] == 'IVA retenido':
                    data_dict['iva_retenido'] = linea['tax_group_amount']
                if linea['tax_group_name'] == 'IVA 13%':
                    data_dict['iva_13'] = linea['tax_group_amount']

            data.importe_extento = data_dict['importe_extento']
            data.importe_exonerado = data_dict['importe_exonerado']
            data.isv_15 = data_dict['isv_15']
            data.isv_18 = data_dict['isv_18']
            data.gravado_15 = ((data_dict['gravado_15'] * 100)/15) 
            data.gravado_18 = ((data_dict['gravado_18'] * 100)/18)
            data.amount_cesc = data_dict['cesc']
            data.amount_iva_retenido = data_dict['iva_retenido']
            data.iva_13 = data_dict['iva_13']

    def _manual_amount(self):
        for data in self:
            for line in data.invoice_line_ids:
                if not len(line.tax_ids):
                    data.importe_exonerado += line.price_subtotal
                else:
                    data.importe_exonerado += 0

    def _manual_amount_gravado(self):
        for data in self:
            data.gravado_15 = 0
            if len(data.invoice_line_ids):
                for line in data.invoice_line_ids:
                    if len(line.tax_ids):
                        for tax_line in line.tax_ids:
                            if tax_line.name == 'ISV por Pagar':
                                data.gravado_15 += line.price_subtotal


    def _subtotal_sin_iva(self):
        for data in self:
            data.subtotal_sin_iva = 0
            for line in data.invoice_line_ids:
                data.subtotal_sin_iva += line.complete_subtotal

    #Fields Honduras
    orden_compra_exenta = fields.Char('No. de Orden de compra exenta', required=False)
    numero_reg_exoneracion = fields.Char('No. de Consta. de Reg. de Exonerdado', required=False)
    numero_sag = fields.Char('No. Registro SAG', required=False)
    ncf_number = fields.Char('NCF', required=False)
    amount_cesc = fields.Monetary('CESC', required=False, default=0.00, compute="_manual_taxes")
    amount_iva_retenido = fields.Monetary('(-)IVA retenido', required=False, default=0.00, compute="_manual_taxes")
    amount_iva_percibido = fields.Monetary('(+)IVA percibido', required=False, default=0.00)
    amount_subtotal = fields.Monetary('Subtotal', compute="_amount_subtotal")
    importe_extento = fields.Monetary(compute="_manual_taxes")
    importe_exonerado = fields.Monetary(compute="_manual_amount")
    isv_15 = fields.Monetary(compute="_manual_taxes")
    isv_18 = fields.Monetary(compute="_manual_taxes")
    gravado_15 = fields.Monetary(compute="_manual_taxes")
    gravado_18 = fields.Monetary(compute="_manual_taxes")
    iva_13 = fields.Monetary('iva 13%', required=False, default=0.00, compute="_manual_taxes")
    subtotal_sin_iva = fields.Monetary( required=False, default=0.00, compute="_subtotal_sin_iva")

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'amount_cesc',
        'amount_iva_retenido',
        'amount_iva_percibido')
    def _amount_subtotal(self):
        res = super(AccountInvoice, self)._compute_amount()
        for move in self:
            move.amount_subtotal = move.amount_untaxed + move.amount_tax
        return res

    def format_date(self, date):
        return date.strftime("%d/%m/%Y")

AccountInvoice()


class ResPartner(models.Model):
    _inherit = "res.partner"
    giro_number = fields.Char('Giro', required=False)
    registro_number = fields.Char('Registro', required=False)

ResPartner()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    @api.depends(
        'debit',
        'credit',
    )
    def _complete_subtotal(self):
        for data in self:
            data.complete_subtotal = 0
            data.complete_unit_price = 0
            amount = 0
            for tax in data.tax_ids:
                if(tax.name != 'IVA retenido'):
                    amount += tax.amount * (data.price_subtotal/100)
                    data.complete_subtotal = amount + data.price_subtotal
                    if data.quantity:
                        data.complete_unit_price = data.complete_subtotal / data.quantity

    def _complete_subtotal_con_iva(self):
        for data in self:
            data.complete_subtotal_con_iva = 0
            data.complete_unit_price_con_iva = 0
            amount = 0
            for tax in data.tax_ids:
                amount += tax.amount * (data.price_subtotal/100)
                data.complete_subtotal_con_iva = amount + data.price_subtotal
                if data.quantity:
                    data.complete_unit_price_con_iva = data.complete_subtotal_con_iva / data.quantity

    complete_subtotal = fields.Monetary(compute="_complete_subtotal")
    complete_unit_price = fields.Monetary(compute="_complete_subtotal")

    complete_subtotal_con_iva = fields.Monetary(compute="_complete_subtotal_con_iva")
    complete_unit_price_con_iva = fields.Monetary(compute="_complete_subtotal_con_iva")

    #precio sin impuestos
    price_unit_without_taxes = fields.Monetary('Precio Unitario sin Impuestos', compute="_compute_price_unit_without_taxes")
    price_unit_with_taxes = fields.Monetary('Precio Unitario con Impuestos', compute="_compute_price_unit_without_taxes")
    price_total_with_taxes = fields.Monetary('Subtotal con Impuestos', compute="_compute_price_unit_without_taxes")

    @api.depends('price_unit', 'tax_ids')
    def _compute_price_unit_without_taxes(self):
        for line in self:
            price_unit = 0.00
            amount_tax = 0.00
            taxes = {}
            if line.tax_ids:
                taxes = line.tax_ids.compute_all(line.price_unit, line.company_id.currency_id, 1.00, line.product_id, line.partner_id)
                for tax in taxes.get('taxes', []):
                    if tax.get('id', False):
                        tax_obj = self.env['account.tax'].browse([tax.get('id', False)])
                        if tax_obj.amount > 0.00:
                            amount_tax += tax.get('amount', 0.00)
            line.update({
                'price_unit_without_taxes': taxes.get('total_excluded', 0.00) or 0.00,
                'price_unit_with_taxes': (taxes.get('total_excluded', 0.00) + amount_tax) or 0.00,
                'price_total_with_taxes': (line.quantity * (taxes.get('total_excluded', 0.00) + amount_tax)) or 0.00,
            })