# -*- coding: utf-8 -*-

{
    'name': 'Pos Reward Extends',
    'version': '15.1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Kalim',
    'summary': "This module allows you get specific cheapest product on rewards." ,
    'description': """

=======================

This module allows you get specific cheapest product on rewards
Add New option On specific products, applies cheapest product on Promotion
Discount compute specific cheapest product from added order lines 

""",
    'depends': [
        'point_of_sale',
        'pos_coupon',
    ],
    'data': [
        'views/coupon_program_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_reward_extends/static/src/js/pos.js',
        ],
    },
    'installable': True,
    'website': '',
    'auto_install': False,
}
