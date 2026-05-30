# -*- coding: utf-8 -*-

import uuid
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError
from collections import defaultdict


class AttachmentEnhanced(models.Model):
    _name = 'ir.attachment'
    _inherit = ['ir.attachment', 'mail.thread']
    
    directory_id = fields.Many2one(
        'document.directory', 
        string='Directory'
    )
    label_ids = fields.Many2many(
        'document.label', 
        'attachment_label_rel',
        'attachment_id', 
        'label_id', 
        string='Labels'
    )
    color_index = fields.Integer('Color Index', default=0)
    revision_number = fields.Integer('Revision', default=0, readonly=True)
    reference_code = fields.Char(
        'Reference Code', 
        default=lambda self: _('New'), 
        copy=False, 
        readonly=True, 
        tracking=True
    )
    security_token = fields.Char('Security Token', readonly=True)
    responsible_user_id = fields.Many2one(
        'res.users', 
        default=lambda self: self.env.user.id, 
        string="Responsible User",
        track_visibility='onchange'
    )
    contact_id = fields.Many2one(
        'res.partner', 
        string="Related Contact", 
        tracking=True
    )

    def _generate_security_token(self):
        """Generate unique security token for attachment access"""
        if not self.security_token:
            self.sudo().write({'security_token': str(uuid.uuid4())})
        return self.security_token
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = vals.get('res_model', False)
            file_name = vals.get('name', False)
            record_id = vals.get('res_id', False)

            # Auto-assign directory based on model
            linked_directory = self.env['document.directory'].sudo().search([
                ('linked_model_id.model', '=', model_name)
            ], limit=1)
            
            if linked_directory:
                vals['directory_id'] = linked_directory.id

            if file_name and model_name and record_id:
                # Search for existing attachments with same name, model, and record
                existing_files = self.search([
                        ('name', '=', file_name), 
                        ('res_model', '=', model_name), 
                        ('res_id', '=', record_id)
                ], order="revision_number desc", limit=1)
                
                if existing_files:
                    # Increment version from the latest file
                    vals['revision_number'] = existing_files[0].revision_number + 1
                else:
                    # First version of this file
                    vals['revision_number'] = 1
            else:
                # No file name or not attached to a record, default to 0
                vals['revision_number'] = 0

            # Generate reference code
            ref_code = self.env['ir.sequence'].next_by_code(
                'attachment.reference.code'
            )
            if ref_code:
                vals['reference_code'] = ref_code

        return super(AttachmentEnhanced, self).create(vals_list)
    
    def _get_email_template(self):
        """Find the email template for sending attachments"""
        template_id = False
        if not template_id:
            template_id = self.env['ir.model.data']._xmlid_to_res_id(
                'ais_document_management.email_template_file_send', 
                raise_if_not_found=False
            )
        return template_id
    
    def action_send_by_email(self):
        """Open email compose wizard with attachment"""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        template_id = self._get_email_template()
        current_lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        
        if template.lang:
            current_lang = template._render_lang(self.ids)[self.id]
        
        try:
            compose_form_id = ir_model_data._xmlid_lookup(
                'mail.email_compose_message_wizard_form'
            )[1]
        except ValueError:
            compose_form_id = False

        context = {
            'default_model': 'ir.attachment',
            'active_model': 'ir.attachment',
            'active_id': self.ids[0],
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True,
            'custom_layout': "mail.mail_notification_light",
            'default_attachment_ids': [(6, 0, [self.id])]
        }

        return {
            'name': _('Send Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': context,
        }
    
    def _read_group_allowed_fields(self):
        """Define allowed fields for read_group operations"""
        return [
            'directory_id', 'type', 'company_id', 'res_id', 
            'create_date', 'create_uid', 'name', 'mimetype', 
            'id', 'url', 'res_field', 'res_model'
        ]
    
    @api.model
    def check(self, mode, values=None):
        """Enhanced access control for attachments"""
        if self.env.is_superuser():
            return True
            
        # Require internal user access
        if not (self.env.is_admin() or self.env.user._is_internal()) \
            or self.env.user.has_group('base.group_portal'):
            raise AccessError(_(
                "Sorry, you are not allowed to access this document."
            ))
            
        # Collect records to check by model
        model_records = defaultdict(set)
        
        if self:
            self.env['ir.attachment'].flush_model([
                'res_model', 'res_id', 'create_uid', 
                'public', 'res_field'
            ])
            self._cr.execute(
                'SELECT res_model, res_id, create_uid, public, res_field '
                'FROM ir_attachment WHERE id IN %s', 
                [tuple(self.ids)]
            )
            
            for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
                if public and mode == 'read':
                    continue
                    
                if not self.env.is_system():
                    if not res_id and create_uid != self.env.uid:
                        raise AccessError(_(
                            "Sorry, you are not allowed to access this document."
                        ))
                    if res_field:
                        field = self.env[res_model]._fields[res_field]
                        if field.groups:
                            if not self.env.user.user_has_groups(field.groups):
                                raise AccessError(_(
                                    "Sorry, you are not allowed to access this document."
                                ))
                                
                if not (res_model and res_id):
                    continue
                model_records[res_model].add(res_id)
                
        if values and values.get('res_model') and values.get('res_id'):
            model_records[values['res_model']].add(values['res_id'])

        # Check access rights on related records
        for res_model, res_ids in model_records.items():
            if res_model not in self.env:
                continue
                
            if res_model == 'res.users' and len(res_ids) == 1 \
                and self.env.uid == list(res_ids)[0]:
                continue
                
            records = self.env[res_model].browse(res_ids).exists()
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)
