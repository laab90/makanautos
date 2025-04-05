from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    _PAYMENT_CHANGE_POLICY_SELECTION = [
        ("refund", "Reembolso y reventa"),
        ("update", "Actualizar pagos"),
    ]

    payment_change_policy = fields.Selection(
        selection=_PAYMENT_CHANGE_POLICY_SELECTION,
        default="refund",
        required=True,
        help="Política de cambio de pago cuando los usuarios desean cambiar las líneas de"
        "pago de un pedido de TPV determinado.\n"
        "* 'Reembolso y reventa': Odoo reembolsará el pedido de posición actual para"
        "cancelarlo y creará un nuevo pedido de TPV con las líneas de pago "
        "correctas.\n"
        "* 'Actualizar pagos': Odoo cambiará las líneas de pago.\n\n"
        "Nota: En algunos países, la opción 'Actualizar pagos' no está permitida por "
        "ley, ya que el historial de pedidos no debe modificarse.",
    )

    @api.constrains("payment_change_policy")
    def _check_payment_change_policy(self):
        # Check if certification module is installed
        # and if yes, if 'update payments' option is allowed
        module_states = (
            self.env["ir.module.module"]
            .sudo()
            .search([("name", "=", "l10n_fr_pos_cert")])
            .mapped("state")
        )
        if "installed" not in module_states:
            return
        for config in self.filtered(lambda x: x.payment_change_policy == "update"):
            if config.company_id._is_accounting_unalterable():
                raise ValidationError(
                    _(
                        "No se pueden usar las opciones de 'Actualizar pagos' para empresas que"
                        "tienen contabilidad inalterable."
                    )
                )
