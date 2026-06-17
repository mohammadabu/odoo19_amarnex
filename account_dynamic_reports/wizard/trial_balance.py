from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from operator import itemgetter
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


class InsTrialBalance(models.TransientModel):
    _name = "ins.trial.balance"

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
                self.comparison_date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")
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
                self.comparison_date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")
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

    @api.model
    def _get_default_date_range(self):
        return self.env.company.date_range

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Trial Balance'))
        return res

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
    strict_range = fields.Boolean(
        string='Strict Range',
        default=lambda self: self.env.company.strict_range
    )
    show_hierarchy = fields.Boolean(
        string='Show hierarchy'
    )
    target_moves = fields.Selection(
        [('all_entries', 'All entries'),
         ('posted_only', 'Posted Only')], string='Target Moves',
        default='posted_only', required=True
    )
    display_accounts = fields.Selection(
        [('all', 'All'),
         ('balance_not_zero', 'With balance not zero')], string='Display accounts',
        default='balance_not_zero', required=True
    )
    date_from = fields.Date(
        string='Start date',
    )
    date_to = fields.Date(
        string='End date',
    )
    comparison_date_from = fields.Date(
        string='Comparison Date From'
    )
    comparison_date_to = fields.Date(
        string='Comparison Date To'
    )
    account_ids = fields.Many2many(
        'account.account', string='Accounts'
    )
    account_tag_ids = fields.Many2many(
        'account.account.tag', string='Account Tags'
    )
    partner_ids = fields.Many2many(
        'res.partner', string='Partners'
    )
    # analytic_ids = fields.Many2many(
    #     'account.analytic.account', string='Analytic Accounts'
    # )
    journal_ids = fields.Many2many(
        'account.journal', string='Journals',
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )

    def write(self, vals):
        ret = super(InsTrialBalance, self).write(vals)
        return ret

    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('"Date from" must be less than or equal to "Date to"'))
        return True

    ################################################################################
    ############################# Core Methods Start ###############################
    ################################################################################

    def prepare_where(self, mode='strict'):
        '''
        :param mode: 'strict', 'initial', 'ending', 'comparison'
        :return:
        '''
        where = 'WHERE (1=1) '

        cmpny_ids = self.env.company.ids + self.env.company.child_ids.ids
        where += ' AND l.company_id in %s ' % str(tuple(cmpny_ids) + tuple([0]))

        if self.journal_ids:
            where += ' AND j.id IN %s ' % str(tuple(self.journal_ids.ids) + tuple([0]))
        if self.partner_ids:
            where += ' AND p.id IN %s ' % str(tuple(self.partner_ids.ids) + tuple([0]))
        #if self.company_id:
        #    where += ' AND l.company_id = %s ' % self.company_id.id
        if self.target_moves == 'posted_only':
            where += " AND m.state = 'posted' "

        if mode == 'strict':
            where += ''' AND l.date >= '%s' AND l.date <= '%s' ''' % (self.date_from, self.date_to)
        elif mode == 'initial':
            where += ''' AND l.date < '%s' ''' % self.date_from
        elif mode == 'ending':
            where += ''' AND l.date <= '%s' ''' % self.date_to
        else:
            where += ''' AND l.date >= '%s' AND l.date <= '%s' ''' % \
                     (self.comparison_date_from or self.date_from,
                      self.comparison_date_to or self.date_to)
        return where

    def prepare_from(self):
        sql_from = '''
            FROM account_move_line l
            JOIN account_move m ON (l.move_id=m.id)
            JOIN account_account a ON (l.account_id=a.id)
            --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
            LEFT JOIN res_currency c ON (l.currency_id=c.id)
            LEFT JOIN res_partner p ON (l.partner_id=p.id)
            JOIN account_journal j ON (l.journal_id=j.id)
        '''
        return sql_from

    def execute_query(self, account, mode='strict'):
        cr = self.env.cr
        if mode == 'strict':
            select = """ SELECT
                    array_agg(l.id) AS id_list,
                    COUNT(l.id) AS size,
                    EXTRACT(HOUR FROM CURRENT_TIME)::TEXT || ':' ||
                    EXTRACT(MINUTE FROM CURRENT_TIME)::TEXT || ':' ||
                    EXTRACT(SECOND FROM CURRENT_TIME)::TEXT || ':' || '%s' AS time_string,
                    CASE
                        WHEN COALESCE(SUM(l.balance)) >= 0 THEN COALESCE(SUM(l.balance))
                        ELSE 0
                        END AS debit,
                    CASE
                        WHEN COALESCE(SUM(l.balance)) >= 0 THEN 0
                        ELSE ABS(COALESCE(SUM(l.balance)))
                        END AS credit,
                    COALESCE(SUM(l.balance),0) AS balance
            """ % account.id
        if mode == 'initial':
            select = """ SELECT
                    CASE
                        WHEN COALESCE(SUM(l.balance)) >= 0 THEN COALESCE(SUM(l.balance))
                        ELSE 0
                        END AS initial_debit,
                    CASE
                        WHEN COALESCE(SUM(l.balance)) >= 0 THEN 0
                        ELSE ABS(COALESCE(SUM(l.balance)))
                        END AS initial_credit,
                    COALESCE(SUM(l.balance),0) AS initial_balance
            """
        if mode == 'ending':
            select = """ SELECT
                    CASE
                        WHEN COALESCE(SUM(l.balance)) >= 0 THEN COALESCE(SUM(l.balance))
                        ELSE 0
                        END AS ending_debit,
                    CASE
                        WHEN COALESCE(SUM(l.balance)) >= 0 THEN 0
                        ELSE ABS(COALESCE(SUM(l.balance)))
                        END AS ending_credit,
                    COALESCE(SUM(l.balance),0) AS ending_balance
            """
        if mode == 'comparison':
            select = """ SELECT
                    CASE
                        WHEN COALESCE(SUM(l.balance)) >= 0 THEN COALESCE(SUM(l.balance))
                        ELSE 0
                        END AS comparison_debit,
                    CASE
                        WHEN COALESCE(SUM(l.balance)) >= 0 THEN 0
                        ELSE ABS(COALESCE(SUM(l.balance)))
                        END AS comparison_credit,
                    COALESCE(SUM(l.balance),0) AS comparison_balance
            """
        sql = (select + self.prepare_from() + self.prepare_where(mode=mode) +
               ''' AND l.account_id = %s 
               ''' % account.id)
        cr.execute(sql)
        return cr.dictfetchone() or {}

    def add_retained_earnings(self, data):
        # Step 1: Calculate sum of initial_debit where carry_forward = True
        sum_initial_debit = sum(entry['initial_debit'] for entry in data if not entry['carry_forward'] and entry['initial_debit'])
        sum_initial_credit = sum(entry['initial_credit'] for entry in data if not entry['carry_forward'] and entry['initial_credit'])
        sum_initial_balance = sum(entry['initial_balance'] for entry in data if not entry['carry_forward'] and entry['initial_balance'])

        # Step 2: Update dictionaries with carry_forward = True
        for entry in data:
            if not entry['carry_forward']:
                # P&L
                entry['ending_debit'] = entry['debit'] or 0
                entry['ending_credit'] = entry['credit'] or 0
                entry['ending_balance'] = entry['balance'] or 0

                entry['initial_debit'] = 0
                entry['initial_credit'] = 0
                entry['initial_balance'] = 0

        # Step 3: Add a new entry for 'Unallocated Earnings'
        unallocated_earnings_entry = {
            'id_list': [],
            'size': 0,
            'debit': 0.0,
            'credit': 0.0,
            'balance': 0.0,
            'initial_debit': sum_initial_debit,
            'initial_credit': sum_initial_credit,
            'initial_balance': sum_initial_balance,
            'ending_debit': sum_initial_debit,
            'ending_credit': sum_initial_credit,
            'ending_balance': sum_initial_balance,
            'comparison_debit': 0.0,
            'comparison_credit': 0.0,
            'comparison_balance': 0.0,
            'time_string': '',  # You may add a time_string or leave it empty
            'account_id': 0,  # Adjust as needed
            'account_name': 'Unallocated Earnings',  # Adjust as needed
            'account_code': '',  # Adjust as needed
            'currency_id': 1,
            'carry_forward': False  # Assuming this should be False for Unallocated Earnings
        }

        # Append unallocated_earnings_entry to data
        data.append(unallocated_earnings_entry)

        # Add Total line
        total = {
            'account_id': 88888888, 'account_name': "", 'account_code': 'Total',
            'currency_id': self.currency_id.id,
            'id_list': [], 'size': 0,
            'time_string': fields.Datetime.now().strftime("%Y%m%d%H%M%S") + 'total',
            'debit': sum([a.get('debit', 0) or 0 for a in data]) or 0,
            'credit': sum([a.get('credit', 0) or 0 for a in data]) or 0,
            'balance': sum([a.get('balance', 0) or 0 for a in data]) or 0,
            'comparison_debit': sum([a.get('comparison_debit', 0) or 0 for a in data]) or 0,
            'comparison_credit': sum([a.get('comparison_credit', 0) or 0 for a in data]) or 0,
            'comparison_balance': sum([a.get('comparison_balance', 0) or 0 for a in data]) or 0,
            'initial_debit': sum([a.get('initial_debit', 0) or 0 for a in data]) or 0,
            'initial_credit': sum([a.get('initial_credit', 0) or 0 for a in data]) or 0,
            'initial_balance': sum([a.get('initial_balance', 0) or 0 for a in data]) or 0,
            'ending_debit': sum([a.get('ending_debit', 0) or 0 for a in data]) or 0,
            'ending_credit': sum([a.get('ending_credit', 0) or 0 for a in data]) or 0,
            'ending_balance': sum([a.get('ending_balance', 0) or 0 for a in data]) or 0,
            'carry_forward': False
        }
        data.append(total)
        return data

    def prepare_main_lines(self):
        '''
        It is the method for showing summary details of each accounts. Just basic details to show up
        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        :return:
        '''
        cr = self.env.cr

        if not self.date_from or not self.date_to:
            return []

        account_company_domain = []
        if self.account_tag_ids:
            account_company_domain.append(('tag_ids', 'in', self.account_tag_ids.ids))
        if self.account_ids:
            account_company_domain.append(('id', 'in', self.account_ids.ids))

        account_ids = self.env['account.account'].search(account_company_domain, order='code asc')
        gl_lines = []
        for account in account_ids:
            carry_forward = True if account.internal_group not in ['income', 'expense'] else False

            result = {
                'id_list': [], 'size': 0, 'debit': 0, 'credit': 0, 'balance': 0,
                'initial_debit': 0, 'initial_credit': 0, 'initial_balance': 0,
                'ending_debit': 0, 'ending_credit': 0, 'ending_balance': 0,
                'comparison_debit': 0, 'comparison_credit': 0, 'comparison_balance': 0,
            }
            # Initial
            res = self.execute_query(account, mode='initial')
            result.update(res)

            # Current
            res = self.execute_query(account, mode='strict')
            result.update(res)

            # Ending
            res = self.execute_query(account, mode='ending')
            result.update(res)

            # Comparison
            res = self.execute_query(account, mode='comparison')
            result.update(res)

            # Extra args
            result.update(
                {
                    'account_id': account.id,
                    'account_name': account.name,
                    'account_code': account.code,
                    'currency_id': self.currency_id.id,
                    'carry_forward': carry_forward
                }
            )
            if self.display_accounts == 'balance_not_zero' and self.currency_id.is_zero(result.get('ending_balance')):
                continue

            gl_lines.append(result)

        updated_gl_lines = self.add_retained_earnings(gl_lines)
        print("-------------------->>", updated_gl_lines)
        return updated_gl_lines

    def prepare_detailed_lines(self, move_line_ids=[], account_id=False):
        cr = self.env.cr
        final_list = []
        # Initial
        where_initial = self.prepare_where(mode='initial')
        sql = ('''
                SELECT
                    'initial' AS ttype,
                    COALESCE(SUM(l.debit),0) AS debit, 
                    COALESCE(SUM(l.credit),0) AS credit, 
                    COALESCE(SUM(l.debit - l.credit),0) AS balance
                    ''' + self.prepare_from() + where_initial +
               ''' AND l.account_id = %s 
      ''' % account_id)
        cr.execute(sql)
        dt_initial = cr.dictfetchone()
        dt_initial.update({'lid': str(account_id) + 'initial'})
        final_list.append(dt_initial)

        # Current
        where_current = self.prepare_where(mode='strict') + ' AND l.id in %s ' % str(
            tuple(move_line_ids) + tuple([0]))
        sql = ('''
                SELECT
                    'strict' AS ttype,
                    l.id AS lid,
                    l.date AS ldate,
                    j.code AS lcode,
                    p.name AS partner_name,
                    m.name AS move_name,
                    m.id AS move_id,
                    l.name AS lname,
                    l.debit AS debit,
                    l.credit AS credit,
                    (l.debit - l.credit) AS balance
                    ''' + self.prepare_from() + where_current +
               ''' AND l.account_id = %s 
               GROUP BY
                   l.date, l.id, m.id ,j.code, p.name, m.name, l.name, l.debit, l.credit
               ORDER BY l.date
           ''' % account_id)
        cr.execute(sql)
        final_list += cr.dictfetchall()

        # Ending
        where_ending = self.prepare_where(mode='ending')
        sql = ('''
                SELECT
                    'ending' AS ttype,
                    COALESCE(SUM(l.debit),0) AS debit, 
                    COALESCE(SUM(l.credit),0) AS credit, 
                    COALESCE(SUM(l.debit - l.credit),0) AS balance
                    ''' + self.prepare_from() + where_ending +
               ''' AND l.account_id = %s 
           ''' % account_id)
        cr.execute(sql)
        dt_ending = cr.dictfetchone()
        dt_ending.update({'lid': str(account_id) + 'ending'})
        final_list.append(dt_ending)

        return final_list

    def prepare_values_for_component(self):
        self.onchange_date_range()
        self.onchange_comparison_date_range()
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.trial.balance')], limit=1)

        date_range = {'choices': [], 'selectedValue': {'value': self.date_range}}
        comparison_date_range = {'choices': [], 'selectedValue': {'value': self.comparison_date_range}}
        target_moves = {'choices': [], 'selectedValue': {'value': self.target_moves}}
        display_accounts = {'choices': [], 'selectedValue': {'value': self.display_accounts}}

        for field in model_id.field_id:
            if field.name == 'date_range':
                date_range['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
            if field.name == 'comparison_date_range':
                comparison_date_range['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
            if field.name == 'target_moves':
                target_moves['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
            if field.name == 'display_accounts':
                display_accounts['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]

        current_range_string = self.get_current_date_range_string()
        comparison_range_string = self.get_comparison_date_range_string()

        return {
            'defaultAccountValues': [{'value': a.id, 'label': a.name, 'code': a.code} for a in self.account_ids],
            'defaultJournalValues': [{'value': a.id, 'label': a.name, 'code': a.code} for a in self.journal_ids],
            'defaultPartnerValues': [{'value': a.id, 'label': a.name} for a in self.partner_ids],
            'defaultAccountTagValues': [{'value': a.id, 'label': a.name} for a in self.account_tag_ids],
            'date_from': self.date_from,
            'date_to': self.date_to,
            'comparison_date_from': self.comparison_date_from,
            'comparison_date_to': self.comparison_date_to,
            'date_range': date_range,
            'comparison_date_range': comparison_date_range,
            'target_moves': target_moves,
            'display_accounts': display_accounts,
            'current_range_string': current_range_string,
            'comparison_range_string': comparison_range_string,
        }

    def get_current_date_range_string(self):
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.trial.balance')], limit=1)
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
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.trial.balance')], limit=1)
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
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.trial.balance')], limit=1)
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
        return self.prepare_main_lines()
        # Query the account details and share here..

    ################################################################################
    ############################# Core Methods END #################################
    ################################################################################

    def action_pdf(self):
        return self.env.ref(
            'account_dynamic_reports'
            '.action_print_trial_balance').with_context(landscape=True).report_action(
            self, data={})

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'GL View',
            'tag': 'account_dynamic_reports.action_trial_balance',
            'context': {'wizard_id': self.id},
            'params': {
                'wizard_id': self.id
            }
        }
        return res

    def action_xlsx(self):
        data = self.read()[0]
        lang_code = self.env.user.lang
        # Initialize
        #############################################################
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Trial Balance')
        sheet.set_zoom(100)
        sheet_2 = workbook.add_worksheet('Filters')
        sheet_2.protect()

        # Get record and data
        record = self.env['ins.trial.balance'].browse(data.get('id', [])) or False

        filter = record.prepare_values_for_component()
        account_lines = record.prepare_main_lines()

        # Formats
        ############################################################
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 10)
        sheet.set_column(2, 2, 10)
        sheet.set_column(3, 3, 10)
        sheet.set_column(4, 4, 10)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 10)
        sheet.set_column(7, 7, 10)
        sheet.set_column(8, 8, 10)
        sheet.set_column(9, 9, 10)

        sheet_2.set_column(0, 0, 35)
        sheet_2.set_column(1, 1, 25)
        sheet_2.set_column(2, 2, 25)
        sheet_2.set_column(3, 3, 25)
        sheet_2.set_column(4, 4, 25)
        sheet_2.set_column(5, 5, 25)
        sheet_2.set_column(6, 6, 25)

        sheet.freeze_panes(5, 0)
        sheet.screen_gridlines = False
        sheet_2.screen_gridlines = False
        sheet_2.protect()

        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
        })
        format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font': 'Arial',
            'align': 'center',
            'border': True
        })
        format_header_initial_ending = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font': 'Arial',
            'align': 'center',
            'border': True,
            'bg_color': '#e8e8e8'
        })
        format_merged_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'border': True,
            'font': 'Arial',
        })
        format_merged_header_without_border = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'font': 'Arial',
        })
        line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
        })
        line_header_total = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        line_header_left = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
        })
        line_header_left_total = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'top': True,
            'bottom': True
        })
        line_header_light_initial_ending = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bg_color': '#e8e8e8',
            'top': True,
            'bottom': True
        })
        line_header_light_initial_ending_total = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bg_color': '#e8e8e8',
            'top': True,
            'bottom': True
        })
        line_header_light_total = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        line_header_light_left = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
        })
        line_header_highlight = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'top': True,
            'bottom': True
        })
        line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'top': True,
            'bottom': True
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': True,
            'align': 'center',
            'font': 'Arial',
        })

        lang = self.env.user.lang
        lang_id = self.env['res.lang'].search([('code', '=', lang)])[0]
        currency_id = self.env.user.company_id.currency_id
        line_header.num_format = currency_id.excel_format
        line_header_light.num_format = currency_id.excel_format
        line_header_highlight.num_format = currency_id.excel_format
        line_header_light_initial_ending.num_format = currency_id.excel_format
        line_header_light_initial_ending_total.num_format = currency_id.excel_format
        line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        format_merged_header_without_border.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

        # Write data
        ################################################################
        row_pos_2 = 0
        row_pos = 0
        sheet.merge_range(0, 0, 0, 10, 'Trial Balance' + ' - ' + data['company_id'][1], format_title)

        # Write filters
        sheet_2.write(row_pos_2, 0, _('Date from'), format_header)
        datestring = fields.Date.from_string(str(filter['date_from'])).strftime(lang_id.date_format)
        sheet_2.write(row_pos_2, 1, datestring or '', content_header_date)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Date to'), format_header)
        datestring = fields.Date.from_string(str(filter['date_to'])).strftime(lang_id.date_format)
        sheet_2.write(row_pos_2, 1, datestring or '', content_header_date)
        row_pos_2 += 1
        if filter.get('comparison_date_from'):
            sheet_2.write(row_pos_2, 0, _('Comparison Date from'), format_header)
            datestring = fields.Date.from_string(str(filter['comparison_date_from'])).strftime(lang_id.date_format)
            sheet_2.write(row_pos_2, 1, datestring or '', content_header_date)
            row_pos_2 += 1

        if filter.get('comparison_date_to'):
            sheet_2.write(row_pos_2, 0, _('Comparison Date to'), format_header)
            datestring = fields.Date.from_string(str(filter['comparison_date_to'])).strftime(lang_id.date_format)
            sheet_2.write(row_pos_2, 1, datestring or '', content_header_date)
            row_pos_2 += 1

        sheet_2.write(row_pos_2, 0, _('Target moves'), format_header)
        for choice in filter['target_moves']['choices']:
            if choice['value'] == filter['target_moves']['selectedValue']['value']:
                sheet_2.write(row_pos_2, 1, choice['label'], content_header)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Display accounts'), format_header)
        for choice in filter['display_accounts']['choices']:
            if choice['value'] == filter['display_accounts']['selectedValue']['value']:
                sheet_2.write(row_pos_2, 1, choice['label'], content_header)
        row_pos_2 += 1
        row_pos_2 += 2
        sheet_2.write(row_pos_2, 0, _('Journals'), format_header)
        j_list = ', '.join([lt['code'] or '' for lt in filter.get('defaultJournalValues')])
        sheet_2.write(row_pos_2, 1, j_list, content_header)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Partners'), format_header)
        p_list = ', '.join([lt['label'] or '' for lt in filter.get('defaultPartnerValues')])
        sheet_2.write(row_pos_2, 1, p_list, content_header)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Accounts'), format_header)
        a_list = ', '.join([lt['code'] or '' for lt in filter.get('defaultAccountValues')])
        sheet_2.write(row_pos_2, 1, a_list, content_header)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Account Tags'), format_header)
        a_list = ', '.join([lt['label'] or '' for lt in filter.get('defaultAccountTagValues')])
        sheet_2.write(row_pos_2, 1, a_list, content_header)

        # Write Ledger details
        row_pos += 3
        sheet.merge_range(row_pos, 1, row_pos, 2, 'Initial Balance', format_merged_header)
        tmp = 2
        if filter.get('comparison_range_string'):
            sheet.merge_range(row_pos, tmp+1, row_pos, tmp+2, filter.get('comparison_range_string'), format_merged_header)
            tmp = 4
        sheet.merge_range(row_pos, tmp+1, row_pos, tmp+2, filter.get('current_range_string'), format_merged_header)
        sheet.merge_range(row_pos, tmp+3, row_pos, tmp+4, 'Ending Balance', format_merged_header)

        row_pos += 1
        sheet.write(row_pos, 0, _('Account'), format_header)
        sheet.write(row_pos, 1, _('Debit'), format_header_initial_ending)
        sheet.write(row_pos, 2, _('Credit'), format_header_initial_ending)
        tmp = 2
        if filter.get('comparison_range_string'):
            sheet.write(row_pos, tmp+1, _('Debit'), format_header)
            sheet.write(row_pos, tmp+2, _('Credit'), format_header)
            tmp = 4
        sheet.write(row_pos, tmp+1, _('Debit'), format_header)
        sheet.write(row_pos, tmp+2, _('Credit'), format_header)
        sheet.write(row_pos, tmp+3, _('Debit'), format_header_initial_ending)
        sheet.write(row_pos, tmp+4, _('Credit'), format_header_initial_ending)

        if account_lines:
            for line in account_lines:  # Normal lines
                print("Acc Name", line.get('account_name'))
                if line['account_code'] != 'Total':
                    row_pos += 1
                    sheet.write(row_pos, 0, "%s - %s" % (line.get('account_code') or '', line.get('account_name') or ''),
                                            line_header_light_left)
                    sheet.write(row_pos, 1, float(line.get('initial_debit') or 0),
                                            line_header_light_initial_ending)
                    sheet.write(row_pos, 2, float(line.get('initial_credit') or 0),
                                            line_header_light_initial_ending)
                    tmp = 2
                    if filter.get('comparison_range_string'):
                        sheet.write(row_pos, tmp+1, float(line.get('comparison_debit') or 0),
                                                line_header_light)
                        sheet.write(row_pos, tmp+2, float(line.get('comparison_credit') or 0),
                                                line_header_light)
                        tmp = 4
                    sheet.write(row_pos, tmp+1, float(line.get('debit') or 0),
                                            line_header_light)
                    sheet.write(row_pos, tmp+2, float(line.get('credit') or 0),
                                            line_header_light)
                    sheet.write(row_pos, tmp+3, float(line.get('ending_debit') or 0),
                                            line_header_light_initial_ending)
                    sheet.write(row_pos, tmp+4, float(line.get('ending_credit') or 0),
                                            line_header_light_initial_ending)
                else:
                    row_pos += 1
                    sheet.write(row_pos, 0,
                                'Total',
                                line_header_highlight)
                    sheet.write(row_pos, 1, float(line.get('initial_debit') or 0),
                                line_header_light_initial_ending_total)
                    sheet.write(row_pos, 2, float(line.get('initial_credit') or 0),
                                line_header_light_initial_ending_total)
                    tmp = 2
                    if filter.get('comparison_range_string'):
                        sheet.write(row_pos, tmp + 1, float(line.get('comparison_debit') or 0),
                                    line_header_highlight)
                        sheet.write(row_pos, tmp + 2, float(line.get('comparison_credit') or 0),
                                    line_header_highlight)
                        tmp = 4
                    sheet.write(row_pos, tmp+1, float(line.get('debit') or 0),
                                line_header_highlight)
                    sheet.write(row_pos, tmp+2, float(line.get('credit') or 0),
                                line_header_highlight)
                    sheet.write(row_pos, tmp+3, float(line.get('ending_debit') or 0),
                                line_header_light_initial_ending_total)
                    sheet.write(row_pos, tmp+4, float(line.get('ending_credit') or 0),
                                line_header_light_initial_ending_total)

        # Close and return
        #################################################################
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'TrialBalance.xls'})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xls' % (
                report_id.id, 'Trial Balance.xls'),
            'target': 'new',
        }

        output.close()
