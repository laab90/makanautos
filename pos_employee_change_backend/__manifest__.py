{
    'name': 'POS Employee Change Backend',
    'version': '15.0.1.0.0',
    'summary': 'Allows changing the cashier (employee) in pos.order from the backend.',
    'author': 'Your Name',
    'depends': ['point_of_sale', 'hr'],
    'data': [
        'views/pos_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
