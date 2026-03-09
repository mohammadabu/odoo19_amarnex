# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _name = "document.document"
    _description = 'Document'
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence,id'
    _order = 'parent_id,sequence,id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    parent_path = fields.Char(index=True)
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=0)
    color = fields.Integer()
    name = fields.Char('Name', required=True)
    full_name = fields.Char('Full Name', compute='_compute_full_name')
    description = fields.Char('Description')
    content = fields.Html('Content')
    parent_id = fields.Many2one('document.document', "Parent", ondelete="cascade", index=True)
    parent_full_name = fields.Char("Path", related='parent_id.full_name')
    child_ids = fields.One2many('document.document', 'parent_id', string='Child')
    child_count = fields.Integer(compute='_compute_child_count', string='Child Count')

    _uniq_name = models.Constraint(
        'unique(parent_id, name)',
        'Name already exists!',
    )

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(_('Parent already recursive!'))

    def _compute_child_count(self):
        relative_field = self._fields.get("child_ids")
        comodel_name = relative_field.comodel_name
        inverse_name = relative_field.inverse_name
        count_list = self.env[comodel_name]._read_group([(inverse_name, 'in', self.ids)], [inverse_name], ['%s:sum' % inverse_name])
        mapped_data = {record.id: count for record, count in count_list}
        for record in self:
            record.child_count = mapped_data.get(record.id, 0)

    def name_get(self):
        if self.env.context.get('display_full_name', False):
            pass
        else:
            return super(Document, self).name_get()
        def get_names(record):
            res = []
            while record:
                res.append(record.name or '')
                record = record.parent_id
            return res
        return [(record.id, " / ".join(reversed(get_names(record)))) for record in self]

    def _compute_full_name(self):
        res_dict = dict(self.with_context({'display_full_name': True}).name_get())
        for record in self:
            record.full_name = res_dict.get(record.id, "")

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for rec, vals in zip(self, vals_list):
                vals['name'] = _("%s (copy)", rec.name)
        return vals_list

    def action(self):
        self.ensure_one()
        context = self.env.context
        action_id = context.get('module_action_id')
        if action_id:
            action_dict = self.env.ref(action_id).read([
                "type", "res_model", "view_mode", "domain"
            ])[0]
            action_dict["name"] = self.name
        return action_dict
