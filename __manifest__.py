{
    'name': 'Meat Processing',
    'version': '1.0',
    'summary': 'Manage Meat Processing Orders',
    'description': """
        Module for managing meat processing orders including order creation, 
        processing, and finalization.
    """,
    'category': 'Inventory',
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'license': 'LGPL-3',  # Asegúrate de incluir la clave license
    'depends': ['base', 'stock', 'product', 'mrp', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/meat_processing_views.xml',
        'views/meat_processing_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'assets': {
        'web.assets_frontend': [
            'meat_processing/static/src/css/*.css',
            'meat_processing/static/src/js/*.js',
        ],
    },
}
