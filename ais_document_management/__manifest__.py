# -*- coding: utf-8 -*-
#################################################################################
# Author      : AVERIANS (<https://www.averians.com/>)
# Copyright(c): 2017-Present AVERIANS.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.averians.com/>
#################################################################################

{
    "name": "Document Management System | Document Management | Documents | Attachment Documents",
    "summary": """
        This module offers a simple yet powerful way to manage documents, including features like directories (folders), 
        labels(tags), exports, numbering, version control, and access control via security groups.
        """,
    "version": "19.1",
    "description": """
        This module offers a simple yet powerful way to manage documents, including features like directories (folders), 
        labels(tags), exports, numbering, version control, and access control via security groups.
    """,    
    "author": "AVERIANS",
    "maintainer": "AVERIANS",
    "license" :  "Other proprietary",
    "website": "https://www.averians.com",
    "images": ["images/ais_document_management.png"],
    "category": "Extra Tools",
    "depends": [
        "base", "mail", "web"
    ],
    "data": [
        "security/security_rules.xml",
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "data/email_template_data.xml",
        "wizards/attachment_share_wizard_views.xml",
        "wizards/attachment_export_wizard_views.xml",
        "views/document_directory_views.xml",
        "views/document_label_views.xml",
        "views/attachment_enhanced_views.xml",
        "views/partner_enhanced_views.xml",
        "views/menu_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ais_document_management/static/src/js/attachment_preview.js",
            "ais_document_management/static/src/js/attachment_share_button.js",
            "ais_document_management/static/src/xml/attachment_preview.xml",
            "ais_document_management/static/src/css/attachment_styles.css",
        ],
    },
    "installable": True,
    "application": True,
    "price"                 :  11,
    "currency"              :  "EUR",
    "pre_init_hook"         :  "pre_init_check",
}