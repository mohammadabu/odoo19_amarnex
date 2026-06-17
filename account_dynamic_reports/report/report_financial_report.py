# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class FinancialReportPdf(models.AbstractModel):
    _name = 'report.account_dynamic_reports.ins_report_financial'
    _description = 'Financial Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wiz_id = self.env["ins.financial.report"].browse(docids)
        data.update({'wiz_id': wiz_id,
                     'rep': self,
                     'get_filters': self._get_filters,
                     'get_main_lines': self._get_main_lines,
                     })
        return data

    def _get_filters(self, wiz_id):
        '''
        :param wiz_id: object of wizard
        :return:
        '''
        filters = wiz_id.prepare_values_for_component()
        return filters

    def _get_main_lines(self, wiz_id):
        main_lines = wiz_id.get_report_values()
        return main_lines
