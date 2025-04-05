# -*- encoding: UTF-8 -*-
##############################################################################
#	
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    'name': 'Gestion de Cheques GT',
    'summary': """Impresion de Cheques""",
    'version': '12.0.1.0.',
    'description': """Permite imprimir cheques. Campo Benefeciario en Cheques. Campo 
Tipo de Cheque""",
    'author': 'J2L',
    'maintainer': '',
    'website': 'https://www.j2l.com',
    'category': 'account',
    'depends': ['account', 'payment'],
    'license': 'AGPL-3',
    'data': [
            'views/account_voucher_view_beneficiario.xml',
            'reports/check_print.xml',
            'reports/check_print_av.xml',
            'reports/check_print_bi.xml',
            'reports/check_print_gyt.xml',
            'reports/account_pdf_menu.xml',
             ],
    'demo': [],
    'sequence': 1,
    'installable': True,
    'auto_install': False,
    'application': True,

}
