
{
    "name": "Punto de Venta - Cambiar Pagos",
    "version": "1.0",
    "summary": "Permitir al usuario cambiar los pagos de los pedidos,"
    "siempre que la sesión no esté cerrada.",
    "category": "Point Of Sale",
    "author": "",
    "license": "AGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/view_pos_payment_change_wizard.xml",
        "views/view_pos_config.xml",
        "views/view_pos_order.xml",
    ],
    "installable": True,
}
