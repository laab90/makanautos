from odoo import api, fields, models


class PosPaymentChangeWizardLine(models.TransientModel):
    _name = "pos.payment.change.wizard.new.line"
    _description = "Asistente de cambio de pago de una nueva línea del PdV"

    wizard_id = fields.Many2one(
        string="Asistente",
        comodel_name="pos.payment.change.wizard",
        required=True,
        ondelete="cascade",
    )

    new_payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="Método de Pago",
        required=True,
        domain=lambda s: s._domain_new_payment_method_id(),
    )

    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        store=True,
        related="new_payment_method_id.company_id.currency_id",
        string="Moneda de la compañía",
        readonly=True,
        help="Campo de utilidad para expresar la cantidad de la moneda",
    )

    amount = fields.Monetary(
        string="Importe",
        required=True,
        default=0.0,
        currency_field="company_currency_id",
    )

    @api.model
    def _domain_new_payment_method_id(self):
        PosOrder = self.env["pos.order"]
        order = PosOrder.browse(self.env.context.get("active_id"))
        return [("id", "in", order.mapped("session_id.payment_method_ids").ids)]

    # View Section
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if "new_line_ids" not in self._context:
            return res
        balance = self._context.get("amount_total", 0.0)
        for line in self.wizard_id.old_line_ids:
            balance -= line.get("amount")
        res.update({"amount": balance})
        return res
