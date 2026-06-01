from odoo import api, fields, models, _


class ksProject(models.Model):
    _inherit = "project.project"

    allow_subtasks = fields.Boolean(string="Allow Sub-tasks", readonly=True)
