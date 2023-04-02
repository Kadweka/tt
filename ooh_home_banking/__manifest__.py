{
    'name': "Ooh Home Banking",
    'summary': """This module for home banking""",
    'version': '15.0.1.0.0',
    'description': """This module will add a record to store student details""",
    'author': '@The-Kadweka',
    'category': 'Tools',
    'depends': ['base','contacts','account','sale'],
    'license': 'AGPL-3',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/bank_view.xml',
        'views/configuration.xml',
        'wizard/register_payment_inherit.xml',
        'wizard/transaction_wizard_view.xml',
        'data/data.xml'
        ],
    'demo': [],
    'assets': {
    'web.assets_backend': [
        'ooh_home_banking/static/src/scss/styles.css',
    ],
 },
    'installable': True,
    'auto_install': False,
}