from odoo import fields, models, api, _
from odoo.addons.cheques_banco import numero_a_texto


class AccountPayment(models.Model):
    _inherit = "account.payment"

    effective_date = fields.Date('Effective Date')
    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)

    def get_amount_in_word(self):
        #return self.currency_id.amount_to_text(self.amount)
        return str(numero_a_texto.Numero_a_Texto(self.amount))
