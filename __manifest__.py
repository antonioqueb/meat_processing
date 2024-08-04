{
    "name": "Despiece",
    "version": "1.0",
    "summary": "Gestión de Órdenes de Procesamiento de Carne",
    "description": """
        El módulo 'Despiece' está diseñado para gestionar órdenes de procesamiento de carne de manera eficiente. Este módulo permite la creación, el seguimiento y la finalización de órdenes de despiece, asegurando un control riguroso sobre cada etapa del proceso. Ideal para empresas que buscan optimizar su inventario y operaciones de manufactura en el ámbito cárnico.
    """,
    "category": "Inventory",
    "author": "Alphaqueb Consulting S.A.S.",
    "website": "https://gestpro.cloud",
    "license": "LGPL-3",
    "depends": ["base", "stock", "product", "mrp", "web"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/meat_processing_views.xml",
        "views/meat_processing_menu.xml"
    ],
    "installable": True,
    "auto_install": False,
    "assets": {
        "web.assets_frontend": [
            "meat_processing/static/src/css/*.css",
            "meat_processing/static/src/js/*.js"
        ]
    },
    "images": ["static/description/icon.png"]
}
