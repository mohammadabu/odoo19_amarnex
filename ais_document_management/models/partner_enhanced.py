# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools, _


class PartnerEnhanced(models.Model):
    _inherit = "res.partner"
    
    def _compute_document_count(self):
        """Compute total documents related to partner"""
        for record in self:
            partner_files = self.env['ir.attachment'].sudo().search([
                '|',
                ('contact_id', 'in', self.ids), 
                '&',
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', self.id)
            ])
            record.document_count = len(partner_files)
    
    document_count = fields.Integer(
        compute='_compute_document_count', 
        string='Document Count'
    )
    
    def action_open_documents(self):
        """Open documents related to this partner"""
        self.ensure_one()
        partner_files = self.env['ir.attachment'].sudo().search([
            '|',
            ('contact_id', 'in', self.ids), 
            '&',
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.id)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Documents'),
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', partner_files.ids)],
        }
