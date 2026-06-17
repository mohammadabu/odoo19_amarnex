# -*- coding: utf-8 -*-

import odoo
from odoo import http
from odoo.http import request
from odoo.api import Environment
from odoo import SUPERUSER_ID
import datetime
import json
import logging
# from openpyxl.pivot import record
from datetime import datetime

# from docutils.languages import fa
_logger = logging.getLogger(__name__)
from odoo.http import content_disposition
from odoo.http import serialize_exception as _serialize_exception
from odoo.tools.translate import _
import base64


class Binary(http.Controller):
    """Common controller to download file"""

    @http.route('/web/binary/download_document', type='http', auth="public")
    def download_document(self, model, field, id, filename=None, **kw):
        env = Environment(request.cr, SUPERUSER_ID, {})
        res = env[str(model)].search([('id', '=', int(id))]).sudo().read()[0]
        filecontent = base64.b64decode(res.get(field) or '')
        if not filename:
            filename = '%s_%s' % (model.replace('.', '_'), id)
        if not filecontent:
            return request.not_found()
        return request.make_response(filecontent,
                                     [('Content-Type', 'application/octet-stream'),
                                      ('Content-Disposition', content_disposition(filename))])
