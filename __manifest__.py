{
    'name': 'Procesamiento de Carne',
    'version': '1.0',
    'summary': 'Módulo para procesar y despiezar canales de res y pollo',
    'sequence': -100,
    'description': """Gestiona el procesamiento y despiece de canales de res y pollo.""",
    'category': 'Manufacturing',
    'author': 'Alphaqueb Consulting S.A.S',
    'website': 'http://www.tuwebsite.com',
    'depends': ['base', 'mrp', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/meat_processing_views.xml',  # Ensure this is loaded first
        'views/meat_processing_menu.xml',  # Then load the menu
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
