from odoo import api, models, fields
from odoo.addons.account_invoice_megaprint import numero_a_texto

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    text_amount = fields.Char(string="Montant en lettre", required=False, compute="amount_to_words")

    @api.depends('amount_total')
    def amount_to_words(self):
        for data in self:
            data.text_amount = str(numero_a_texto.Numero_a_Texto(data.amount_total))

