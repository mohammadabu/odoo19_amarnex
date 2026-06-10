import json
import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, api,exceptions

class CustomCompany(models.Model):
    _inherit = 'res.company'

    signature = fields.Image(string='Signature', attachment=True)
