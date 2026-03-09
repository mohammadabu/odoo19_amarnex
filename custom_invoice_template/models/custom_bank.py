import json
import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, api,exceptions
class Custom_Bank(models.Model):
    _inherit = 'res.partner.bank'
    beneficiary_ar = fields.Char(string="Beneficiary Name (ARABIC)")
    iban = fields.Char()
    
    account_name = fields.Char(required=True)


    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id,rec.account_name))
        return result    