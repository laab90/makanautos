# -*- coding: utf-8 -*-

from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"


    #Sale/Purhcase Journals 
    gt_sale_journal_tr_ids = fields.Many2many('account.journal', 'rel_sale_journal_company', 'sale_journal_id', 'company_id', string="Sale Journals")
    gt_purchase_journal_tr_ids = fields.Many2many('account.journal', 'rel_purchase_journal_company', 'purchase_journal_id', 'company_id', string="Purchase Journals")

    #Sales/Purchase Journals
    gt_iva_sale_tax_tr_ids = fields.Many2many('account.tax', 'rel_sale_tax_company', 'sale_tax_id', 'company_id', string="IVA for Sale Taxes")
    gt_iva_purchase_tax_tr_ids = fields.Many2many('account.tax', 'rel_purchase_tax_company', 'purchase_tax_id', 'company_id', string="IVA for Purchase Taxes")
    gt_idp_tax_tr_ids = fields.Many2many('account.tax', 'rel_idp_tax_company', 'idp_tax_id', 'company_id', string="IDP for Combustible Taxes")
    gt_other_sale_tax_tr_ids = fields.Many2many('account.tax', 'rel_other_sale_tax_company', 'other_sale_tax_id', 'company_id', string="Other Sale Taxes")
    gt_other_purchase_tax_tr_ids = fields.Many2many('account.tax', 'rel_other_pur_tax_company', 'other_pur_tax_id', 'company_id', string="Other Purchase Taxes")

    #fields Transaction Type
    gt_product_trans_tr_id = fields.Many2many('account.move.type.tr', 'rel_product_trans_company', 'product_trans_id', 'company_id', string="Transacciones de Bienes")
    gt_service_trans_tr_id = fields.Many2many('account.move.type.tr', 'rel_service_trans_company', 'service_trans_id', 'company_id', string="Transacciones de Servicios")
    gt_import_trans_tr_id = fields.Many2many('account.move.type.tr', 'rel_import_trans_company', 'import_trans_id', 'company_id', string="Transacciones de Importaciones")
    gt_combustible_trans_tr_id = fields.Many2many('account.move.type.tr', 'rel_combustible_trans_company', 'combustible_trans_id', 'company_id', string="Transacciones de Combustibles")
    gt_pqc_trans_tr_id = fields.Many2many('account.move.type.tr', 'rel_pqc_trans_company', 'pqc_trans_id', 'company_id', string="Transacciones de Peq.Contribuyentes")

ResCompany()