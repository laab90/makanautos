{
    'name': 'Separate Transit Transfers',
    'version': '1.0',
    'summary': 'Ensure each transfer to transit locations is independent',
    'description': """
        This module modifies the transfer process in Odoo Inventory to ensure that 
        each transfer to a transit location is handled independently, without grouping 
        with other pending transfers.
    """,
    'author': 'Your Name',
    'depends': ['stock'],
    'data': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
