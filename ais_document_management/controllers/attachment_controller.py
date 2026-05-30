# -*- coding: utf-8 -*-

import json
import base64
import logging
import werkzeug.urls

from odoo import http
from odoo.http import request
from odoo.tools import html_escape

_logger = logging.getLogger(__name__)


class DocumentAttachmentController(http.Controller):
    """Controller for public attachment access via security token"""
    
    @http.route(
        '/document/download/token/<string:security_token>', 
        type='http', 
        auth="public",  # Changed to public for better compatibility
        methods=['GET']
    )
    def download_attachment_by_token(self, security_token, **kwargs):
        """
        Public route to download attachments using security token
        
        :param security_token: Unique token for attachment access
        :return: HTTP response with file content or error
        """
        try:
            ir_attachment_env = request.env['ir.attachment']
            attachment = ir_attachment_env.sudo().search([
                ('security_token', '=', security_token)
            ], limit=1)
            
            if not attachment:
                _logger.warning(
                    f"Attachment download failed: Invalid token {security_token}"
                )
                error = {
                    'code': 404,
                    'message': "Unable to locate the attachments",
                }
                return request.make_response(
                    html_escape(json.dumps(error)),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            if not attachment.datas:
                _logger.error(
                    f"Attachment {attachment.id} has no content"
                )
                error = {
                    'code': 404,
                    'message': "Document content is not available",
                }
                return request.make_response(
                    html_escape(json.dumps(error)),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            content = base64.b64decode(attachment.datas)
            
            filename = attachment.name or 'document'
            disposition = 'attachment; filename=%s' % werkzeug.urls.url_quote(filename)
            
            _logger.info(
                f"Attachment {attachment.id} ({attachment.name}) downloaded via token"
            )
            
            return request.make_response(
                content,
                headers=[
                    ('Content-Length', len(content)),
                    ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                    ('Content-Disposition', disposition)
                ]
            )
            
        except Exception as e:
            _logger.exception(
                f"Error downloading attachment with token {security_token}: {str(e)}"
            )
            error = {
                'code': 500,
                'message': "Error - Odoo Server Error",
            }
            return request.make_response(
                html_escape(json.dumps(error)),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
