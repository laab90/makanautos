# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    #Sale/Purhcase Journals 
    gt_sale_journal_tr_ids = fields.Many2many('account.journal', related="company_id.gt_sale_journal_tr_ids", string="Sale Journals", readonly=False)
    gt_purchase_journal_tr_ids = fields.Many2many('account.journal', related="company_id.gt_purchase_journal_tr_ids", string="Purchase Journals", readonly=False)

    #Sales/Purchase Journals
    gt_iva_sale_tax_tr_ids = fields.Many2many('account.tax', related="company_id.gt_iva_sale_tax_tr_ids", string="IVA for Sale Taxes", readonly=False)
    gt_iva_purchase_tax_tr_ids = fields.Many2many('account.tax', related="company_id.gt_iva_purchase_tax_tr_ids", string="IVA for Purchase Taxes", readonly=False)
    gt_idp_tax_tr_ids = fields.Many2many('account.tax', related="company_id.gt_idp_tax_tr_ids", string="IDP for Combustible Taxes", readonly=False)
    gt_other_sale_tax_tr_ids = fields.Many2many('account.tax', related="company_id.gt_other_sale_tax_tr_ids", string="Other Sale Taxes", readonly=False)
    gt_other_purchase_tax_tr_ids = fields.Many2many('account.tax', related="company_id.gt_other_purchase_tax_tr_ids", string="Other Purchase Taxes", readonly=False)

    #fields Transaction Type
    gt_product_trans_tr_id = fields.Many2many('account.move.type.tr', related="company_id.gt_product_trans_tr_id", string="Bienes", readonly=False)
    gt_service_trans_tr_id = fields.Many2many('account.move.type.tr', related="company_id.gt_service_trans_tr_id", string="Servicios", readonly=False)
    gt_import_trans_tr_id = fields.Many2many('account.move.type.tr', related="company_id.gt_import_trans_tr_id", string="Importaciones", readonly=False)
    gt_combustible_trans_tr_id = fields.Many2many('account.move.type.tr', related="company_id.gt_combustible_trans_tr_id", string="Combustibles", readonly=False)
    gt_pqc_trans_tr_id = fields.Many2many('account.move.type.tr', related="company_id.gt_pqc_trans_tr_id", string="Peq. Contribuyentes", readonly=False)

ResConfigSettings()