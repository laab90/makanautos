from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PosPaymentChangeWizard(models.TransientModel):
    _name = "pos.payment.change.wizard"
    _description = "Asistente de cambio de pago del TPV"

    # Column Section
    order_id = fields.Many2one(comodel_name="pos.order", string="Pedido", readonly=True)

    old_line_ids = fields.One2many(
        comodel_name="pos.payment.change.wizard.old.line",
        inverse_name="wizard_id",
        string="Viejas líneas de pago",
        readonly=True,
    )

    new_line_ids = fields.One2many(
        comodel_name="pos.payment.change.wizard.new.line",
        inverse_name="wizard_id",
        string="Nuevas líneas de pago",
    )

    amount_total = fields.Float(string="Total", readonly=True)

    # View Section
    @api.model
    def default_get(self, fields):
        PosOrder = self.env["pos.order"]
        res = super().default_get(fields)
        order = PosOrder.browse(self._context.get("active_id"))
        old_lines_vals = []
        for payment in order.payment_ids:
            old_lines_vals.append(
                (
                    0,
                    0,
                    {
                        "old_payment_method_id": payment.payment_method_id.id,
                        "amount": payment.amount,
                    },
                )
            )
        res.update(
            {
                "order_id": order.id,
                "amount_total": order.amount_total,
                "old_line_ids": old_lines_vals,
            }
        )
        return res

    # View section
    def button_change_payment(self):
        self.ensure_one()
        order = self.order_id

        # Check if the total is correct
        total = sum(self.mapped("new_line_ids.amount"))
        if (
            float_compare(
                total,
                self.amount_total,
                precision_rounding=self.order_id.currency_id.rounding,
            )
            != 0
        ):
            raise UserError(
                _(
                    "Diferencias entre los dos valores para el pedido POS"
                    " Orden '%(name)s':\n\n"
                    " * Total de todos los nuevos pagos %(total)s;\n"
                    " * Total del Pedido TPV %(amount_total)s;\n\n"
                    "Por favor, cambie los pagos.",
                    name=order.name,
                    total=total,
                    amount_total=order.amount_total,
                )
            )

        # Change payment
        new_payments = [
            {
                "pos_order_id": order.id,
                "payment_method_id": line.new_payment_method_id.id,
                "amount": line.amount,
                "payment_date": fields.Date.context_today(self),
            }
            for line in self.new_line_ids
        ]

        orders = order.change_payment(new_payments)

        if len(orders) == 1:
            # if policy is 'update', only close the pop up
            action = {"type": "ir.actions.act_window_close"}
        else:
            # otherwise (refund policy), displays the 3 orders
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "point_of_sale.action_pos_pos_form"
            )
            action["domain"] = [("id", "in", orders.ids)]

        return action
