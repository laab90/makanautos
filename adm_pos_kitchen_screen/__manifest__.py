{
    'name': "Pos Kitchen Screen",
    'version': "15.0.3",
    'category': "Tools",
    'summary': """
        Point of sale Kitchen Screen | Pos Restaurant Screen | POS Bar Screen | POS Kitchen Screen
        | Point of sale bar screen | Point of sale restaurant screen | vista de cocina en punto de venta | cocina en POS
    """,
    'author': "Javier Fernández",
    'website': "https://asdelmarketing.com",
    'license': 'OPL-1',
    'price': 25.99,
    'currency': 'EUR',
    'data': [
        'views/kitchen_menu_view.xml',
        'views/product_views.xml',
        'views/user_views.xml'
    ],
    'demo': [],
    'images': [
        'static/description/thumbnail.gif',
    ],
    'depends': [
        'web',
        'point_of_sale',
        'pos_restaurant'
    ],
    "assets": {
        "web.assets_backend": [
            "adm_pos_kitchen_screen/static/src/js/kitchen.js",
            "adm_pos_kitchen_screen/static/src/css/custom.css",
        ],
        'web.assets_qweb': [
            "adm_pos_kitchen_screen/static/src/xml/kitchen.xml",
            #"adm_pos_kitchen_screen/static/src/xml/kitchen_screen_in_pos.xml",
        ],
    },
   


    'installable': True,
}