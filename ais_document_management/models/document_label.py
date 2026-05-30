# -*- coding: utf-8 -*-

from random import randint
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DocumentLabelGroup(models.Model):
    _name = "document.label.group"
    _description = "Label Group"
    _order = "sequence, name"

    directory_id = fields.Many2one('document.directory', ondelete="cascade")
    name = fields.Char(required=True)
    label_ids = fields.One2many('document.label', 'label_group_id')
    description = fields.Char(
        help="Hover text description", 
        string="Description"
    )
    sequence = fields.Integer('Sequence', default=10)

    _sql_constraints = [
        (
            'name_unique', 
            'unique (directory_id, name)', 
            "Label group already exists in this directory"
        ),
    ]


class DocumentLabel(models.Model):
    _name = "document.label"
    _description = "Document Label"
    _order = "sequence, name"

    def _get_default_color_index(self):
        return randint(1, 11)

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    color_index = fields.Integer(
        string='Color Index', 
        default=_get_default_color_index
    )
    directory_id = fields.Many2one(
        'document.directory', 
        string='Directory'
    )
    label_group_id = fields.Many2one(
        'document.label.group', 
        ondelete='cascade', 
        required=True
    )

    _sql_constraints = [
        (
            'label_group_name_unique', 
            'unique (label_group_id, name)', 
            "Label already exists for this group"
        ),
    ]
    
    def name_get(self):
        result_list = []
        for record in self:
            result_list.append((
                record.id, 
                "%s > %s" % (record.label_group_id.name, record.name)
            ))
        return result_list
