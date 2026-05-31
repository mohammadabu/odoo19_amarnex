{
    'name': 'Enterprise Backend Theme',
    'version': '19.0.1.0.6',
    'category': 'Themes/Backend',
    'summary': 'Enterprise-style Backend Theme for Odoo Community - White Navbar, App Icons, Login Page',
    'author': 'Smart System for Information Technology',
    'maintainer': 'Smart System for Information Technology',
    'support': 'info@smartsystem.sa',
    'website': 'https://smartsystem.sa',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'account'],
    'data': [
        'data/menu_rename.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ss_enterprise_theme/static/src/css/backend_theme.css',
            'ss_enterprise_theme/static/src/js/home_menu_icons.js',
        ],
        'web.assets_frontend': [
            'ss_enterprise_theme/static/src/css/login_theme.css',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
