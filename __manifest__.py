{
    'name': 'Meat Processing',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Manage Meat Processing Orders',
    'description': """
        Module for managing meat processing orders including order creation, 
        processing, and finalization.
    """,
    'depends': ['base', 'stock', 'product', 'mrp', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/meat_processing_views.xml',
        'views/meat_processing_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'meat_processing/static/src/css/meat_processing_styles.css',
            'meat_processing/static/src/css/kanban_color.css',
            'meat_processing/static/src/js/kanban_color.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
