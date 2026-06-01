from odoo import fields, models,api


# Inheriting view and adding Gantt view to View.
class KsGanttView(models.Model):
    _inherit = "ir.ui.view"

    type = fields.Selection(selection_add=[('ks_gantt', "Gantt")], ondelete={'ks_gantt': 'cascade'})

    def _postprocess_access_rights(self, tree):
        if self._context.get('view_type', False) == 'form':
            return super(KsGanttView, self)._postprocess_access_rights(tree)

        else:

            for node in tree.xpath('//*[@groups]'):
                if not self.env.user.has_group(node.attrib.pop('groups')):
                    node.getparent().remove(node)
                elif node.tag == 't' and not node.attrib:
                    for child in reversed(node):
                        node.addnext(child)
                    node.getparent().remove(node)
            base_model = tree.get('model_access_rights')
            for node in tree.xpath('//*[@model_access_rights]'):
                model = self.env[node.attrib.pop('model_access_rights')]
                if node.tag == 'field':
                    can_create = model.has_access('create')
                    can_write = model.has_access('write')
                    node.set('can_create', 'true' if can_create else 'false')
                    node.set('can_write', 'true' if can_write else 'false')
                else:
                    is_base_model = base_model == model._name
                    for action, operation in (('create', 'create'), ('delete', 'unlink'), ('edit', 'write')):
                        if (not node.get(action) and
                                not model.has_access(operation) or
                                not self._context.get(action, True) and is_base_model):
                            node.set(action, 'false')
                    if node.tag == 'ks_gantt':
                        group_by_name = node.get('default_group_by')
                        group_by_field = model._fields.get(group_by_name)
                        if group_by_field and group_by_field.type == 'many2one':
                            group_by_model = model.env[group_by_field.comodel_name]
                            for action, operation in (('group_create', 'create'), ('group_delete', 'unlink'),
                                                      ('group_edit', 'write')):
                                if (not node.get(action) and
                                        not group_by_model.has_access(operation) or
                                        not self._context.get(action, True) and is_base_model):
                                    node.set(action, 'false')
            return super(KsGanttView, self)._postprocess_access_rights(tree)

    def _get_view_info(self):
        return {'ks_gantt': {'icon': 'fa fa-tasks'}} | super()._get_view_info()

class KsBase(models.AbstractModel):
    _inherit = "base"
    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        self = self.with_context(view_type=view_type)
        result = super(KsBase, self).get_view(view_id=view_id, view_type=view_type, **options)
        return result
