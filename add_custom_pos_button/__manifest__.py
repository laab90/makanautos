{
    'name': 'POS Canje de Puntos',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'Agregar botón de canje de puntos en POS',
    'description': 'Permite seleccionar un programa de cupones relacionado con puntos y generar un cupón.',
    'author': 'Tu Nombre',
    'depends': ['point_of_sale', 'coupon'],
    'data': [
        'views/custom_pos_templates.xml',  # Define la carga de activos
    ],
    'qweb': [
        'static/src/js/custom_button.js',  # Define el archivo JS
        'views/custom_pos_button.xml',     # Define el QWeb (interfaz del botón)
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
