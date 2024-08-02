# meat_processing/__manifest__.py
{
    'name': 'Meat Processing',
    'version': '1.0',
    'summary': 'Module for processing and deboning beef and chicken carcasses',
    'sequence': -100,
    'description': """Manage the processing and deboning of beef and chicken carcasses.""",
    'category': 'Manufacturing',
    'author': 'Your Name',
    'website': 'http://www.yourwebsite.com',
    'depends': ['base', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/meat_processing_menu.xml',
        'views/meat_processing_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
