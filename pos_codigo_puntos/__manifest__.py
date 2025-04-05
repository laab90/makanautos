# __manifest__.py
{
    'name': 'POS Código Puntos',
    'version': '1.0',
    'summary': 'Botón para mostrar códigos de programas de puntos en el POS',
    'description': 'Agrega un botón en el POS que permite ver y copiar códigos de cupones de programas que contienen "puntos" en el nombre.',
    'author': 'Tu Nombre',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_codigo_puntos_assets.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_codigo_puntos/static/src/js/pos_codigo_puntos_button.js',
        ],
    },
    'installable': True,
    'application': False,
}
