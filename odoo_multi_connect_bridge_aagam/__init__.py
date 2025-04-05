# -*- coding: utf-8 -*-

from . import models,wizard
def pre_init_check(cr):
    try:
        from woocommerce import API
    except ImportError:
        raise Warning('Please Install Woocommerce Python Api (command: pip install woocommerce)')
    return True
