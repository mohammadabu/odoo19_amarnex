# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AttachmentShareWizard(models.TransientModel):
    _name = 'attachment.share.wizard'
    _description = 'Share Attachment Wizard'

    file_name = fields.Char('File Name')
    share_url = fields.Char('Share URL', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(AttachmentShareWizard, self).default_get(fields)
        
        context = self.env.context or {}
        active_id = context.get('active_id')
        
        link = ''
        
        file_record = self.env['ir.attachment'].search([
            ('id', '=', active_id)
        ], limit=1)

        if not file_record:
            res['file_name'] = ''
            res['share_url'] = ''
            return res

        file_record.sudo()._generate_security_token()
        
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url'
        )
        share_endpoint = "%s/document/download/token/" % base_url
        
        if file_record.type == 'binary' and file_record.security_token:
            link = share_endpoint + str(file_record.security_token)
        elif file_record.type == 'url':
            link = file_record.url

        res['file_name'] = file_record.name
        res['share_url'] = link
        return res
