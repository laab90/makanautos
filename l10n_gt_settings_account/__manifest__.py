# -*- coding: utf-8 -*-
{
    'name': "Configuración Contable Guatemala",
    'summary': """Módulo que añade el segmento de Contabilidad a la localización de Guatemala""",
    'description': """1. Añade el segmento de Contabilidad a la localización de Guatemala""",
    'author': "J2l Tech GT",
    'website': "https://j2ltechgt.com",
    'support': 'soporte@j2ltechgt.com',
    'category': 'Technical Settings',
    'version': '0.1',
    'license': "AGPL-3",
    'depends': ['l10n_gt_settings'],
    'data': [
        'security/groups.xml',
        'views/res_config_settings.xml',
        ],
    'application': True,
    'sequence': 1,
}
