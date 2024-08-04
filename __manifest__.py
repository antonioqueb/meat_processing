{
    'name': 'Meat Processing',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Manage Meat Processing Orders',
    'description': """
        Module for managing meat processing orders including order creation, 
        processing, and finalization.
    """,
    'depends': ['base', 'stock', 'product', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/meat_processing_views.xml',
        'views/meat_processing_menu.xml',
        'views/meat_processing_assets.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
