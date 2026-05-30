# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DocumentDirectory(models.Model):
    _name = 'document.directory'
    _description = 'Document Directory'
    _parent_name = 'parent_directory_id'
    _order = 'name'
    _rec_name = 'full_name'
    
    name = fields.Char(string='Directory Name', required=True)
    full_name = fields.Char(
        'Full Path', 
        compute='_compute_full_name', 
        recursive=True, 
        store=True
    )
    sequence = fields.Integer('Sequence', default=10)
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        index=True, 
        default=lambda self: self.env.company
    )
    parent_directory_id = fields.Many2one(
        'document.directory',
        string='Parent Directory', 
        ondelete="cascade", 
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    child_directory_ids = fields.One2many(
        'document.directory',
        'parent_directory_id', 
        string="Sub Directories"
    )
    file_ids = fields.One2many(
        'ir.attachment', 
        'directory_id', 
        string="Files"
    )
    linked_model_id = fields.Many2one('ir.model', string='Linked Model')
    file_count = fields.Integer(compute="_compute_file_count")
    
    def name_get(self):
        if not self.env.context.get('hierarchical_naming', True):
            return [(record.id, record.name) for record in self]
        return super(DocumentDirectory, self).name_get()

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    @api.depends('name', 'parent_directory_id.full_name')
    def _compute_full_name(self):
        for directory in self:
            if directory.parent_directory_id:
                directory.full_name = '%s / %s' % (
                    directory.parent_directory_id.full_name, 
                    directory.name
                )
            else:
                directory.full_name = directory.name
    
    @api.constrains('parent_directory_id')
    def _check_parent_directory_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive directories.'))

    @api.depends()
    def _compute_file_count(self):
        read_group_result = self.env['ir.attachment']._read_group(
            [('directory_id', 'in', self.ids)],
            ['directory_id'],
            ['__count']
        )
        
        file_count_mapping = {
            directory.id: count 
            for directory, count in read_group_result
        }
        
        for record in self:
            record.file_count = file_count_mapping.get(record.id, 0)
       
    @api.constrains('linked_model_id')
    def _check_linked_model(self):
        self.ensure_one()
        existing_directory = self.env['document.directory'].sudo().search([
            ('linked_model_id.model', '=', self.linked_model_id.model)
        ])
        if len(existing_directory) > 1:
            raise ValidationError(_(
                'A directory for this model already exists!'
            ))
            
    def action_view_files(self):
        domain = [('directory_id', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'views': [(False, 'list'), (False, 'form')],
            'view_mode': 'tree,form',
            'context': "{'default_directory_id': %s}" % self.id
        }

    @api.model_create_multi
    def create(self, vals_list):
        result = super(DocumentDirectory, self).create(vals_list)
        all_files = self.env['ir.attachment'].sudo().search([])

        for rec, vals in zip(result, vals_list):
            model_id = vals.get('linked_model_id', False)
            if model_id:
                linked_model = self.env['ir.model'].sudo().search([
                    ('id', '=', model_id)
                ], limit=1)
                
                if linked_model:
                    for file_record in all_files:
                        if file_record.res_model == linked_model.model:
                            file_record.sudo().write({'directory_id': rec.id})
        return result
