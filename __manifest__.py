{
    'name': 'Despiece',
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
        'views/meat_processing_menu.xml',
        'views/meat_processing_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'meat_processing/static/src/css/meat_processing_styles.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'maintainer': 'Alphaqueb Consulting S.A.S',
    'license': 'LGPL-3'
}
