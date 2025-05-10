{
    'name': 'Gestion Hospitalière',
    'version': '18.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Module de gestion hospitalière',
    'description': """
        Module de gestion hospitalière avec les fonctionnalités suivantes:
        - Gestion des patients
        - Consultations par spécialité
        - Hospitalisations
        - Gestion des chambres
        - Statistiques
        - Impression d'états
    """,
    'author': 'NOUMABEU MOUTACDIER JORDAN',
    'website': 'https://www.votresite.com',
    'depends': ['base', 'mail', 'report_xlsx'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/patient_views.xml',
        'views/consultation_views.xml',
        'views/specialite_views.xml',
        'views/chambre_views.xml',
        'views/hospitalisation_views.xml',
        'views/medecin_views.xml',
        'views/menu_views.xml',
        'demo/medecin_demo.xml',
        'demo/patient_demo.xml',
        'demo/medecin_demo1.xml',
        'demo/patient_demo1.xml',
        # 'report/patient_report.xml',
        # 'report/consultation_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'gestion_hospital/static/src/js/hospital_dashboard.js',
            # 'gestion_hospital/static/src/css/hospital_style.css',
        ],
    },
    'demo': [],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
} 