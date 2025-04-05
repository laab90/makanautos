from odoo import fields, models


class PosPaymentChangeWizardOldLine(models.TransientModel):
    _name = "pos.payment.change.wizard.old.line"
    _description = "Asistente de cambio de pago de una línea antigua del PdV"

    wizard_id = fields.Many2one(
        string="Asistente",
        comodel_name="pos.payment.change.wizard",
        required=True,
        ondelete="cascade",
    )

    old_payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="Método de Pago",
        required=True,
        readonly=True,
    )

    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        store=True,
        related="old_payment_method_id.company_id.currency_id",
        string="Moneda de la compañía",
        readonly=True,
        help="Campo de utilidad para expresar la cantidad de la moneda",
    )

    amount = fields.Monetary(
        string="Importe",
        required=True,
        readonly=True,
        default=0.0,
        currency_field="company_currency_id",
    )
