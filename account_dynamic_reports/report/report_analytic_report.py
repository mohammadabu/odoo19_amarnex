# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class InsReportAnalyticReport(models.AbstractModel):
    _name = 'report.account_dynamic_reports.analytic_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wiz_id = self.env["ins.analytic.report"].browse(docids)
        data.update({'wiz_id': wiz_id,
                     'rep': self,
                     'get_filters': self._get_filters,
                     'get_main_lines': self._get_main_lines,
                     'get_sub_lines': self._get_sub_lines
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
        main_lines = wiz_id.prepare_main_lines()
        return main_lines

    def _get_sub_lines(self, wiz_id, id_list, account_id):
        sub_lines = wiz_id.prepare_detailed_lines(id_list, account_id)
        return sub_lines


