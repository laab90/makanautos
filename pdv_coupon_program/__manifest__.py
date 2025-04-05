{
    'name': 'PdV - Programas Promocionales',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Modulo puente entre pos.config y coupon.program',
    'description': """
        Este módulo corrige algunas actitudes cuando ambos módulos están instalados.
    """,
    'author': '',
    'depends': ['point_of_sale', 'sale_coupon'],
    'data': [
        'views/coupon_program_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}