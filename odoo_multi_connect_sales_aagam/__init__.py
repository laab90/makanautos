# -*- coding: utf-8 -*-
from . import models
from . import wizard
from . import controllers
from . import tools

def pre_init_check(cr):
	from odoo.service import common
	from odoo.exceptions import Warning
	version_info = common.exp_version()
	server_serie =version_info.get('server_serie')
	if server_serie!='15.0':raise Warning('Module support Odoo series 15.0 found {}.'.format(server_serie))
	return True
