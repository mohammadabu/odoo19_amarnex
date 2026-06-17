# -*- coding: utf-8 -*-
{
    'name' : 'All in one Dynamic Financial Reports v19',
    'version' : '19.11',
    'summary': "General Ledger Trial Balance Ageing Balance Sheet Profit and Loss Cash Flow Dynamic Analytic Reproting",
    'sequence': 15,
    'description': """
                    Odoo 19 Full Accounting, Odoo 18 All in one Accounting, PDF Reports, XLSX Reports,
                    Dynamic View, Drill down, Clickable, Pdf and Xlsx package, Odoo 19 Accounting,
                    Full Account Reports, Complete Accounting Reports, Financial Report for Odoo 19,
                    Financial Reports, Excel reports, Financial Reports in Excel, Ageing Report,
                    General Ledger, Partner Ledger, Trial Balance, Balance Sheet, Profit and Loss, Analytic,
                    Financial Report Kit, Cash Flow Statements, Cash Flow Report, Cash flow, Dynamic reports,
                    Dynamic accounting, Dynamic financial, Community, CE, Analytic Reporting, Owl, Journal, Drill down
                    """,
    'category': 'Accounting/Accounting',
    "price": 150,
    'author': 'Pycus',
    'maintainer': 'Pycus Technologies',
    'website': '',
    'images': ['static/description/GL.gif'],
    'depends': ['account', 'web'],
    'data': [
             'security/ir.model.access.csv',
             'data/data_account_account_type.xml',
             'data/data_financial_report.xml',

             'views/views.xml',
             'views/res_company_view.xml',

             'views/general_ledger_view.xml',
             'views/partner_ledger_view.xml',
             'views/trial_balance_view.xml',
             'views/partner_ageing_view.xml',
             'views/financial_report_view.xml',
             'views/analytic_report_view.xml',

             'wizard/general_ledger_view.xml',
             'wizard/partner_ledger_view.xml',
             'wizard/trial_balance_view.xml',
             'wizard/partner_ageing_view.xml',
             'wizard/financial_report_view.xml',
             'wizard/analytic_report.xml'
             ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'account_dynamic_reports/static/src/components/pycus_filters/*.js',
            'account_dynamic_reports/static/src/components/pycus_filters/*.xml',
            'account_dynamic_reports/static/src/components/pycus_filters/*.scss',
            'account_dynamic_reports/static/src/components/*/*.xml',
            'account_dynamic_reports/static/src/components/*/*.js',
            'account_dynamic_reports/static/src/components/*/*.xml',
            'account_dynamic_reports/static/src/components/*/*.scss',
            #'web/static/lib/select2/select2.css',
            #'web/static/lib/select2/select2.js'
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
