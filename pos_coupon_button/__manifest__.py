{
    'name': 'Mi Módulo POS',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Módulo para agregar un botón en el POS',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale.assets': [
            'mi_pos_modulo/static/src/js/pos_button.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
