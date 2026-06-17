# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import re

from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import json
import io
from odoo.tools import date_utils
import base64

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

DATE_DICT = {
    '%m/%d/%Y' : 'mm/dd/yyyy',
    '%Y/%m/%d' : 'yyyy/mm/dd',
    '%m/%d/%y' : 'mm/dd/yy',
    '%d/%m/%Y' : 'dd/mm/yyyy',
    '%d/%m/%y' : 'dd/mm/yy',
    '%d-%m-%Y' : 'dd-mm-yyyy',
    '%d-%m-%y' : 'dd-mm-yy',
    '%m-%d-%Y' : 'mm-dd-yyyy',
    '%m-%d-%y' : 'mm-dd-yy',
    '%Y-%m-%d' : 'yyyy-mm-dd',
    '%f/%e/%Y' : 'm/d/yyyy',
    '%f/%e/%y' : 'm/d/yy',
    '%e/%f/%Y' : 'd/m/yyyy',
    '%e/%f/%y' : 'd/m/yy',
    '%f-%e-%Y' : 'm-d-yyyy',
    '%f-%e-%y' : 'm-d-yy',
    '%e-%f-%Y' : 'd-m-yyyy',
    '%e-%f-%y' : 'd-m-yy'
}


class InsFinancialReport(models.TransientModel):
    _name = "ins.financial.report"
    _description = "Financial Reports"

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.journal_ids = self.env['account.journal'].search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].search([])

    @api.onchange('date_range', 'financial_year')
    def onchange_date_range(self):
        if self.date_range:
            date = datetime.today()
            if self.date_range == 'today':
                self.date_from = date.strftime("%Y-%m-%d")
                self.date_to = date.strftime("%Y-%m-%d")
            if self.date_range == 'this_week':
                day_today = date - timedelta(days=date.weekday())
                self.date_from = (day_today - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                self.date_to = (day_today + timedelta(days=6)).strftime("%Y-%m-%d")
            if self.date_range == 'this_month':
                self.date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                self.date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")
            if self.date_range == 'this_quarter':
                if int((date.month - 1) / 3) == 0:  # First quarter
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 3, calendar.mdays[3]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 6, calendar.mdays[6]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 9, calendar.mdays[9]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    self.date_from = datetime(date.year, 10, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, calendar.mdays[12]).strftime("%Y-%m-%d")
            if self.date_range == 'this_financial_year':
                if self.financial_year == 'january_december':
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'april_march':
                    if date.month < 4:
                        self.date_from = datetime(date.year - 1, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 3, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'july_june':
                    if date.month < 7:
                        self.date_from = datetime(date.year - 1, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 6, 30).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 6, 30).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(days=1))
            if self.date_range == 'yesterday':
                self.date_from = date.strftime("%Y-%m-%d")
                self.date_to = date.strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(days=7))
            if self.date_range == 'last_week':
                day_today = date - timedelta(days=date.weekday())
                self.date_from = (day_today - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                self.date_to = (day_today + timedelta(days=6)).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(months=1))
            if self.date_range == 'last_month':
                self.date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                self.date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(months=3))
            if self.date_range == 'last_quarter':
                if int((date.month - 1) / 3) == 0:  # First quarter
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 3, calendar.mdays[3]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 6, calendar.mdays[6]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 9, calendar.mdays[9]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    self.date_from = datetime(date.year, 10, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, calendar.mdays[12]).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(years=1))
            if self.date_range == 'last_financial_year':
                if self.financial_year == 'january_december':
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'april_march':
                    if date.month < 4:
                        self.date_from = datetime(date.year - 1, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 3, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'july_june':
                    if date.month < 7:
                        self.date_from = datetime(date.year - 1, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 6, 30).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 6, 30).strftime("%Y-%m-%d")

    @api.onchange('comparison_date_range', 'financial_year')
    def onchange_comparison_date_range(self):
        if self.comparison_date_range:
            date = datetime.today()
            if self.comparison_date_range == 'today':
                self.comparison_date_from = date.strftime("%Y-%m-%d")
                self.comparison_date_to = date.strftime("%Y-%m-%d")
            if self.comparison_date_range == 'this_week':
                day_today = date - timedelta(days=date.weekday())
                self.comparison_date_from = (day_today - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                self.comparison_date_to = (day_today + timedelta(days=6)).strftime("%Y-%m-%d")
            if self.comparison_date_range == 'this_month':
                self.comparison_date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                self.comparison_date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime(
                    "%Y-%m-%d")
            if self.comparison_date_range == 'this_quarter':
                if int((date.month - 1) / 3) == 0:  # First quarter
                    self.comparison_date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 3, calendar.mdays[3]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    self.comparison_date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 6, calendar.mdays[6]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    self.comparison_date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 9, calendar.mdays[9]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    self.comparison_date_from = datetime(date.year, 10, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 12, calendar.mdays[12]).strftime("%Y-%m-%d")
            if self.comparison_date_range == 'this_financial_year':
                if self.financial_year == 'january_december':
                    self.comparison_date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'april_march':
                    if date.month < 4:
                        self.comparison_date_from = datetime(date.year - 1, 4, 1).strftime("%Y-%m-%d")
                        self.comparison_date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.comparison_date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.comparison_date_to = datetime(date.year + 1, 3, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'july_june':
                    if date.month < 7:
                        self.comparison_date_from = datetime(date.year - 1, 7, 1).strftime("%Y-%m-%d")
                        self.comparison_date_to = datetime(date.year, 6, 30).strftime("%Y-%m-%d")
                    else:
                        self.comparison_date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                        self.comparison_date_to = datetime(date.year + 1, 6, 30).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(days=1))
            if self.comparison_date_range == 'yesterday':
                self.comparison_date_from = date.strftime("%Y-%m-%d")
                self.comparison_date_to = date.strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(days=7))
            if self.comparison_date_range == 'last_week':
                day_today = date - timedelta(days=date.weekday())
                self.comparison_date_from = (day_today - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                self.comparison_date_to = (day_today + timedelta(days=6)).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(months=1))
            if self.comparison_date_range == 'last_month':
                self.comparison_date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                self.comparison_date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime(
                    "%Y-%m-%d")
            date = (datetime.now() - relativedelta(months=3))
            if self.comparison_date_range == 'last_quarter':
                if int((date.month - 1) / 3) == 0:  # First quarter
                    self.comparison_date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 3, calendar.mdays[3]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    self.comparison_date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 6, calendar.mdays[6]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    self.comparison_date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 9, calendar.mdays[9]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    self.comparison_date_from = datetime(date.year, 10, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 12, calendar.mdays[12]).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(years=1))
            if self.comparison_date_range == 'last_financial_year':
                if self.financial_year == 'january_december':
                    self.comparison_date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.comparison_date_to = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'april_march':
                    if date.month < 4:
                        self.comparison_date_from = datetime(date.year - 1, 4, 1).strftime("%Y-%m-%d")
                        self.comparison_date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.comparison_date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.comparison_date_to = datetime(date.year + 1, 3, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'july_june':
                    if date.month < 7:
                        self.comparison_date_from = datetime(date.year - 1, 7, 1).strftime("%Y-%m-%d")
                        self.comparison_date_to = datetime(date.year, 6, 30).strftime("%Y-%m-%d")
                    else:
                        self.comparison_date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                        self.comparison_date_to = datetime(date.year + 1, 6, 30).strftime("%Y-%m-%d")

    def prepare_where(self):
        where = " WHERE (m.state = 'posted') "
        if self.journal_ids:
            where += ' AND j.id IN %s ' % str(tuple(self.journal_ids.ids) + tuple([0]))
        if self.company_id:
            where += ' AND l.company_id = %s ' % self.company_id.id
        return where

    def _compute_account_balance(self, accounts, report, mode='current'):
        """ compute the balance, debit and credit for the provided accounts
        """
        cr = self.env.cr
        # Validation
        if report.type in ['accounts','account_type'] and not report.range_selection:
            raise UserError(_('Please choose "Custom Date Range" for the report head %s') % (report.name))

        where = self.prepare_where()
        # Range Based Separation
        if report.type in ['accounts', 'account_type']:
            if mode == 'current':
                if report.range_selection == 'from_the_beginning':
                    where += " AND l.date <= '%s'" % self.date_to
                if report.range_selection == 'current_date_range':
                    where += " AND l.date >= '%s' AND l.date <= '%s'" % (self.date_from, self.date_to)
                if report.range_selection == 'initial_date_range':
                    where += " AND l.date < '%s'" % self.date_from
            else:
                if report.range_selection == 'from_the_beginning':
                    where += " AND l.date <= '%s'" % self.comparison_date_to
                if report.range_selection == 'current_date_range':
                    where += " AND l.date >= '%s' AND l.date <= '%s'" % (self.comparison_date_from, self.comparison_date_to)
                if report.range_selection == 'initial_date_range':
                    where += " AND l.date < '%s'" % self.comparison_date_from
        result = {}
        for account in accounts:
            new_where = where + " AND a.id = %s " % account.id
            sql = """
                SELECT
                    COALESCE(SUM(debit), 0) as debit,
                    COALESCE(SUM(credit), 0) as credit,
                    COALESCE(SUM(balance), 0) as balance
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                JOIN account_journal j ON (l.journal_id=j.id)
            """ + new_where
            cr.execute(sql)
            financial = cr.dictfetchone()
            result.update({
                account.id: financial
            })
        return result

    def _compute_report_balance(self, reports, mode='current'):
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                if self.account_report_id != self.env.ref(
                        'account_dynamic_reports.ins_account_financial_report_cashflow0'):
                    res[report.id]['account'] = self._compute_account_balance(report.account_ids, report, mode=mode)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
                else:
                    if report in [
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_operation_cash_in'),
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_investing_cash_in'),
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_financial_cash_in')]:

                        res2 = self._compute_account_balance(report.parent_id.account_ids, report, mode=mode)
                        for key, value in res2.items():
                            res[report.id]['debit'] += value['debit']
                            res[report.id]['balance'] += value['debit']
                    elif report in [
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_operation_cash_out'),
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_investing_cash_out'),
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_financial_cash_out')]:

                        res2 = self._compute_account_balance(report.parent_id.account_ids, report, mode=mode)
                        for key, value in res2.items():
                            res[report.id]['credit'] += value['credit']
                            res[report.id]['balance'] += -(value['credit'])
                    else:
                        res[report.id]['account'] = self._compute_account_balance(report.account_ids, report, mode=mode)
                        for value in res[report.id]['account'].values():
                            for field in fields:
                                res[report.id][field] += value.get(field)

            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search(
                    [('account_type', 'in', report.account_type_ids.mapped('type'))]
                )
                res[report.id]['account'] = self._compute_account_balance(accounts, report, mode=mode)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id, mode=mode)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids, mode=mode)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
                accounts = report.account_ids
                res[report.id]['account'] = self._compute_account_balance(accounts, report, mode=mode)
                for values in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += values.get(field)
        return res

    def prepare_lines(self, res, child_reports):
        lines = []
        for report in child_reports:
            company_id = self.env.company
            currency_id = company_id.currency_id
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * int(report.sign),
                'debit': res[report.id]['debit'],
                'credit': res[report.id]['credit'],
                'parent': report.parent_id.id if report.parent_id.type in ['accounts','account_type'] else 0,
                'self_id': report.id,
                'type': 'report',
                'level': report.level,
                'class': 'clickable py-fin-main-tr py-tr-level-'+str(report.level),
                'company_currency_id': self.env.company.currency_id.id,
                'fin_report_type': report.type,
                'display_detail': report.display_detail,
                'range_selection': report.range_selection,
                'time_string': fields.Datetime.now().strftime("%H:%M:%S")+str(report.id),
            }
            lines.append(vals)

            if report.display_detail == 'no_detail':
                continue

            if res[report.id].get('account'):
                sub_lines = []
                cnt = 1
                for account_id, value in res[report.id]['account'].items():
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'account': account.id,
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * int(report.sign) or 0.0,
                        'debit': value['debit'],
                        'credit': value['credit'],
                        'type': 'account',
                        'parent': report.id if report.type in ['accounts', 'account_type'] else 0,
                        'self_id': str(report.id * 1000) + str(cnt),
                        'level': report.level + 1,
                        'class': 'a' + str(report.id) + ' collapse py-fin-main-tr py-tr-level-' + str(report.level + 1),
                        'company_currency_id': self.env.company.currency_id.id,
                        'fin_report_type': 'account',
                        'display_detail': report.display_detail,
                        'range_selection': report.range_selection,
                        'time_string': fields.Datetime.now().strftime("%H:%M:%S")+str(report.id)+str(account.id),
                    }
                    sub_lines.append(vals)
                    cnt += 1
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines

    def calculate_percentage(self, old_value, new_value):
        if old_value == 0:
            return 0  # Or you can return any other value you prefer
        else:
            percentage = ((new_value - old_value) / old_value) * 100
            return round(percentage, 2)

    def get_account_lines(self):
        lines = []
        account_report = self.account_report_id
        child_reports = account_report._get_children_by_order(strict_range=True)
        res = self._compute_report_balance(child_reports, mode='current')
        lines.extend(self.prepare_lines(res, child_reports))
        if self.comparison_date_from and self.comparison_date_to:
            res = self._compute_report_balance(child_reports, mode='comparison')
            lines_comparison = self.prepare_lines(res, child_reports)

            lookup = {item['self_id']: item['balance'] for item in lines_comparison}
            for item in lines:
                item['comparison_balance'] = lookup.get(item['self_id'], 0)
                item['percentage_change'] = self.calculate_percentage(item['balance'], lookup.get(item['self_id'], 0))

        if self.hide_zero_balance == 'yes':
            new_lines = []
            for item in lines:
                if item['type'] in ['account', 'account_type']:
                    if item['balance'] or item.get('comparison_balance'):
                        new_lines.append(item)
                        continue
                    else:
                        continue
                else:
                    new_lines.append(item)
            return new_lines
        return lines

    def get_report_values(self):
        self.ensure_one()
        self.onchange_date_range()
        report_lines = self.get_account_lines()
        print('aaaa', report_lines)
        return report_lines

    @api.model
    def _get_default_report_id(self):
        if self.env.context.get('report_name', False):
            return self.env.context.get('report_name', False)
        return self.env.ref('account_dynamic_reports.ins_account_financial_report_balancesheet0').id

    @api.model
    def _get_default_date_range(self):
        return self.env.company.date_range

    @api.depends('account_report_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.account_report_id.name or 'Financial Report'
            res.append((record.id, name))
        return res

    @api.depends('account_report_id')
    def _get_default_report_name(self):
        if self.account_report_id:
            self.report_name = self.account_report_id.name

    report_name = fields.Char(string='Report Name', compute='_get_default_report_name', store=True)
    financial_year = fields.Selection(
        [('april_march', '1 April to 31 March'),
         ('july_june', '1 july to 30 June'),
         ('january_december', '1 Jan to 31 Dec')],
        string='Financial Year', default=lambda self: self.env.company.financial_year, required=True)

    date_range = fields.Selection(
        [('today', 'Today'),
         ('this_week', 'This Week'),
         ('this_month', 'This Month'),
         ('this_quarter', 'This Quarter'),
         ('this_financial_year', 'This financial Year'),
         ('yesterday', 'Yesterday'),
         ('last_week', 'Last Week'),
         ('last_month', 'Last Month'),
         ('last_quarter', 'Last Quarter'),
         ('last_financial_year', 'Last Financial Year')],
        string='Date Range', default=_get_default_date_range
    )
    comparison_date_range = fields.Selection(
        [('today', 'Today'),
         ('this_week', 'This Week'),
         ('this_month', 'This Month'),
         ('this_quarter', 'This Quarter'),
         ('this_financial_year', 'This financial Year'),
         ('yesterday', 'Yesterday'),
         ('last_week', 'Last Week'),
         ('last_month', 'Last Month'),
         ('last_quarter', 'Last Quarter'),
         ('last_financial_year', 'Last Financial Year')],
        string='Date Range'
    )
    view_format = fields.Selection([
        ('vertical', 'Vertical'),
        ('horizontal', 'Horizontal')],
        default='vertical',
        string="Format")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    strict_range = fields.Boolean(
        string='Strict Range',
        default=lambda self: self.env.company.strict_range)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                   default=lambda self: self.env['account.journal'].search(
                                       [('company_id', '=', self.company_id.id)]))
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    hide_zero_balance = fields.Selection([('yes', 'Yes'),
                                        ('no', 'No'),
                                    ], string='Hide Zero Balance', required=True, default='yes')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    enable_filter = fields.Boolean(
        string='Enable Comparison',
        default=False)
    account_report_id = fields.Many2one(
        'ins.account.financial.report',
        string='Account Reports',
        required=True, default=_get_default_report_id)

    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        default=True,
        help="Help to identify debit and credit with balance line for better understanding.")
    analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Accounts'
    )
    # analytic_tag_ids = fields.Many2many(
    #     'account.analytic.tag', string='Analytic Tags'
    # )
    comparison_date_from = fields.Date(string='Start Date')
    comparison_date_to = fields.Date(string='End Date')
    filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], string='Filter by',
                                  required=True, default='filter_date')
    label_filter = fields.Char(string='Column Label', default='Comparison Period',
                               help="This label will be displayed on report to show the balance computed for the given comparison filter.")

    @api.model
    def create(self, vals):
        ret = super(InsFinancialReport, self).create(vals)
        return ret

    def write(self, vals):
        ret = super(InsFinancialReport, self).write(vals)
        return ret

    def prepare_values_for_component(self):
        self.onchange_date_range()
        self.onchange_comparison_date_range()
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.financial.report')], limit=1)

        date_range = {'choices': [], 'selectedValue': {'value': self.date_range}}
        comparison_date_range = {'choices': [], 'selectedValue': {'value': self.comparison_date_range}}
        hide_zero_balance = {'choices': [], 'selectedValue': {'value': self.hide_zero_balance}}

        for field in model_id.field_id:
            if field.name == 'date_range':
                date_range['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
            if field.name == 'comparison_date_range':
                comparison_date_range['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
            if field.name == 'hide_zero_balance':
                hide_zero_balance['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]

        current_range_string = self.get_current_date_range_string()
        comparison_range_string = self.get_comparison_date_range_string()

        return {
            'defaultJournalValues': [{'value': a.id, 'label': a.name, 'code': a.code} for a in self.journal_ids],
            'date_from': self.date_from,
            'date_to': self.date_to,
            'comparison_date_from': self.comparison_date_from,
            'comparison_date_to': self.comparison_date_to,
            'date_range': date_range,
            'comparison_date_range': comparison_date_range,
            'current_range_string': current_range_string,
            'comparison_range_string': comparison_range_string,
            'hide_zero_balance': hide_zero_balance,
            'report_name': self.report_name
        }

    def get_current_date_range_string(self):
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.financial.report')], limit=1)
        date_range = {'choices': [], 'selectedValue': {'value': self.date_range}}
        for field in model_id.field_id:
            if field.name == 'date_range':
                date_range['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]

        if self.date_range:
            return [i['label'] for i in date_range['choices'] if i['value'] == self.date_range][0]
        else:
            user_lang = self.env.user.lang
            frm = ''
            to = ''
            if self.date_from:
                frm = self.date_from.strftime(self.env['res.lang']._lang_get(user_lang).date_format)
            if self.date_to:
                to = self.date_to.strftime(self.env['res.lang']._lang_get(user_lang).date_format)
            return "%s - %s" % (frm, to)

    def get_comparison_date_range_string(self):
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.financial.report')], limit=1)
        comparison_date_range = {'choices': [], 'selectedValue': {'value': self.comparison_date_range}}
        for field in model_id.field_id:
            if field.name == 'comparison_date_range':
                comparison_date_range['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]

        if self.comparison_date_range:
            return [i['label'] for i in comparison_date_range['choices'] if i['value'] == self.comparison_date_range][0]
        else:
            user_lang = self.env.user.lang
            frm = ''
            to = ''
            if self.comparison_date_from and self.comparison_date_to:
                frm = self.comparison_date_from.strftime(self.env['res.lang']._lang_get(user_lang).date_format)
                to = self.comparison_date_to.strftime(self.env['res.lang']._lang_get(user_lang).date_format)
                return "%s - %s" % (frm, to)
            else:
                return ''

    def update_values_from_component(self, vals):
        update_dict = {}
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.financial.report')], limit=1)
        for field in model_id.field_id:
            if field.name in vals.keys():
                if field.ttype == 'many2many':
                    if vals[field.name]:
                        update_dict.update({field.name: [int(a['value']) for a in vals[field.name]]})
                    else:
                        update_dict.update({field.name: [(5,)]})
                if field.ttype == 'selection':
                    update_dict.update({field.name: vals[field.name]['selectedValue']['value']})
                if field.ttype == 'date':
                    update_dict.update({field.name: vals[field.name]})
        self.write(update_dict)
        self.onchange_date_range()
        self.onchange_comparison_date_range()
        return self.get_report_values()

    def action_go_to_gl(self, account_id, range_selection):
        date_from = self.date_from
        date_to = self.date_to
        min_date = self.env['account.move.line'].search_read([], ['date'], limit=1, order='date asc')

        if range_selection == 'from_the_beginning':
            date_from = min_date[0]['date']
        if range_selection == 'initial_date_range':
            date_from = min_date[0]['date']
            date_to = self.date_to - timedelta(days=1)

        gl_id = self.env['ins.general.ledger'].create(
            {
                'date_range': False,
                'date_from': date_from,
                'date_to': date_to,
                'account_ids': [account_id],
                'journal_ids': self.journal_ids.ids,
            }
        )
        return gl_id.id

    def action_pdf(self):
        return self.env.ref(
            'account_dynamic_reports'
            '.action_print_financial_report').with_context(landscape=False).report_action(
                self, data={})

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'Financial Report View',
            'tag': 'account_dynamic_reports.action_dynamic_allinone_bs_report',
            'context': {'wizard_id': self.id},
            'params': {
                'wizard_id': self.id
            }
        }
        return res

    def action_xlsx(self):
        data = self.read()[0]
        # Initialize
        #############################################################
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(data['account_report_id'][1])
        sheet.set_zoom(95)
        sheet2 = workbook.add_worksheet('Filters')
        sheet2.protect()

        # Get record and data
        record = self.env['ins.financial.report'].browse(data.get('id', [])) or False

        filter = record.prepare_values_for_component()
        account_lines = record.get_report_values()

        # Formats
        ############################################################
        sheet.set_column(0, 0, 50)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)


        sheet2.set_column(0, 0, 25)
        sheet2.set_column(1, 1, 25)
        sheet2.set_column(2, 2, 25)
        sheet2.set_column(3, 3, 25)
        sheet2.set_column(4, 4, 25)
        sheet2.set_column(5, 5, 25)
        sheet2.set_column(6, 6, 25)
        sheet.freeze_panes(4, 0)
        sheet.screen_gridlines = False
        sheet2.screen_gridlines = False
        sheet2.protect()

        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'border': False,
            'font': 'Arial',
        })
        format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'bottom': False
        })
        format_header_right = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bottom': False
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            # 'num_format': 'dd/mm/yyyy',
        })
        line_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bottom': False
        })
        line_header_bold = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bottom': True
        })
        line_header_bold_background = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bottom': True,
            'bg_color': '#bababa',
            'color': 'white'
        })
        line_header_string = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'bottom': False
        })
        line_header_string_bold = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'bottom': True,
        })
        line_header_string_bold_background = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'bottom': True,
            'bg_color': '#bababa',
            'color': 'white'
        })
        dummy_line = workbook.add_format({})

        lang = self.env.user.lang
        lang_id = self.env['res.lang'].search([('code', '=', lang)])[0]
        currency_id = self.env.user.company_id.currency_id
        line_header.num_format = currency_id.excel_format
        line_header_bold.num_format = currency_id.excel_format
        line_header_bold_background.num_format = currency_id.excel_format
        content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

        # Write data
        ################################################################
        row_pos_2 = 0
        row_pos = 0
        sheet2.write(row_pos_2, 0, _('Date from'), format_header)
        datestring = fields.Date.from_string(str(filter['date_from'])).strftime(lang_id.date_format)
        sheet2.write(row_pos_2, 1, datestring, content_header_date)
        row_pos_2 += 1
        # Date to
        sheet2.write(row_pos_2, 0, _('Date to'), format_header)
        datestring = fields.Date.from_string(str(filter['date_to'])).strftime(lang_id.date_format)
        sheet2.write(row_pos_2, 1, datestring, content_header_date)
        # Comparison Date from
        if filter['comparison_date_from']:
            row_pos_2 += 1
            sheet2.write(row_pos_2, 0, _('Comparison Date from'), format_header)
            datestring = fields.Date.from_string(str(filter['comparison_date_from'])).strftime('%Y-%m-%d')
            sheet2.write(row_pos_2, 1, datestring, content_header_date)
        # Comparison Date to
        if filter['comparison_date_to']:
            row_pos_2 += 1
            sheet2.write(row_pos_2, 0, _('Comparison Date to'), format_header)
            datestring = fields.Date.from_string(str(filter['comparison_date_to'])).strftime('%Y-%m-%d')
            sheet2.write(row_pos_2, 1, datestring, content_header_date)

        # Write Ledger details
        row_pos += 3

        sheet.write(row_pos, 0, _('Name'), format_header)
        if filter['comparison_range_string']:
            sheet.write(row_pos, 1, filter['comparison_range_string'], format_header_right)
        sheet.write(row_pos, 2, filter['current_range_string'], format_header_right)
        if filter['comparison_range_string']:
            sheet.write(row_pos, 3, _('%'), format_header_right)

        for line in account_lines:
            row_pos += 1

            if line['level'] == 1:
                sheet.write(row_pos, 1, '', dummy_line)
                row_pos += 1
                tmp_style_str = line_header_string_bold_background
                tmp_style_num = line_header_bold_background
            else:
                if line['type'] == 'account':
                    tmp_style_str = line_header_string
                    tmp_style_num = line_header
                else:
                    tmp_style_str = line_header_string_bold
                    tmp_style_num = line_header_bold

            sheet.write(row_pos, 0, '   ' * (line['level'] * 2) + line.get('name'), tmp_style_str)
            if filter['comparison_range_string']:
                sheet.write(row_pos, 1, float(line.get('comparison_balance') or 0), tmp_style_num)
            else:
                sheet.write(row_pos, 1, '', tmp_style_num)
            sheet.write(row_pos, 2, float(line.get('balance') or 0), tmp_style_num)
            if filter['comparison_range_string']:
                sheet.write(row_pos, 3, float(line.get('percentage_change') or 0), tmp_style_num)

        # Close and return
        #################################################################
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'FIN.xls'})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xls' % (
                report_id.id, filter['report_name']),
            'target': 'new',
        }

        output.close()
