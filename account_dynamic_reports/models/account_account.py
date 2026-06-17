# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def get_cashflow_domain(self):
        cash_flow_id = self.env.ref('account_dynamic_reports.ins_account_financial_report_cashflow0')
        if cash_flow_id:
            return [('parent_id.id', '=', cash_flow_id.id)]

    cash_flow_category = fields.Many2one('ins.account.financial.report', string="Cash Flow type", domain=get_cashflow_domain)

    @api.onchange('cash_flow_category')
    def onchange_cash_flow_category(self):
        # Add account to cash flow record to account_ids
        if self._origin and self._origin.id:
            self.cash_flow_category.write({'account_ids': [(4, self._origin.id)]})
            # self.env.ref(
            #     'account_dynamic_reports.ins_account_financial_report_cashflow0').write(
            #     {'account_ids': [(4, self._origin.id)]})
        # Remove account from previous category
        # In case of changing/ removing category
        if self._origin.cash_flow_category:
            self._origin.cash_flow_category.write({'account_ids': [(3, self._origin.id)]})
            # self.env.ref(
            #     'account_dynamic_reports.ins_account_financial_report_cashflow0').write(
            #     {'account_ids': [(3, self._origin.id)]})
