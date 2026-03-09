import json
import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, api,exceptions
class Custom_Invoice(models.Model):
    _inherit = 'account.move'
    flag = fields.Char()


    # def _check_balanced(self):
    #     return True
    invoice_payments_widget = fields.Binary()