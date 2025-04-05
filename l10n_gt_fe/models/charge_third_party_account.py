from odoo import _, api, fields, models

class ChargeThirdPartyAccount(models.Model):
    _name = 'charge.third.party.account'
    _description = 'Charge Third Party Account'
    
    vat = fields.Char(string='NIT Tercero', required=True) 
    number = fields.Char(string='N. Doc.', required=True) 
    date = fields.Date(string='Fecha Doc.', required=True)
    name = fields.Char(string='Descripcion', required=True) 
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_untaxes = fields.Monetary(string='Base Imponible', required=True) 
    amount_dai = fields.Monetary(string='DAI', required=True,) 
    amount_taxes = fields.Monetary(string='IVA', required=True, compute="_compute_all") 
    other_amount = fields.Monetary(string='Otros', required=True,) 
    amount_total = fields.Monetary(string='Total', required=True, compute="_compute_all")
    move_id = fields.Many2one('account.move', string='Invoice')
    
    @api.depends("amount_untaxes", "amount_dai", "other_amount")
    def _compute_all(self):
        for record in self:
            record.amount_taxes = record.amount_untaxes * 0.12
            record.amount_total = record.amount_dai + record.amount_taxes + record.other_amount
     
