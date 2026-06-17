# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class InsReportTrialBalance(models.AbstractModel):
    _name = 'report.account_dynamic_reports.trial_balance'

    @api.model
    def _get_report_values(self, docids, data=None):
        wiz_id = self.env["ins.trial.balance"].browse(docids)
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
        main_lines = wiz_id.prepare_main_lines()
        return main_lines
