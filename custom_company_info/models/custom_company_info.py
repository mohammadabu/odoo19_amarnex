from odoo import models, fields, api,exceptions
class Custom_Company_Info(models.Model):
    _inherit = 'res.company'
    company_terms = fields.Html()
    company_footer = fields.Binary()
    right_footer_logo = fields.Binary()
    large_logo = fields.Binary() 