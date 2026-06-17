from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
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

class InsAnalyticReport(models.TransientModel):
    _name = "ins.analytic.report"

    @api.onchange('date_range','financial_year')
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
                        self.date_from = datetime(date.year -1, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 3, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'july_june':
                    if date.month < 7:
                        self.date_from = datetime(date.year -1 , 7, 1).strftime("%Y-%m-%d")
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

    @api.model
    def _get_default_date_range(self):
        return self.env.company.date_range

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Analytic Report'))
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
    date_from = fields.Date(
        string='Start date',
    )
    date_to = fields.Date(
        string='End date',
    )
    include_details = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Include Details', default='yes')
    account_ids = fields.Many2many(
        'account.account', string='Accounts'
    )
    analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Account'
    )
    journal_ids = fields.Many2many(
        'account.journal', string='Journals',
    )
    partner_ids = fields.Many2many(
        'res.partner', string='Partners'
    )
    plan_ids = fields.Many2many(
        'account.analytic.plan', string='Plan',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('"Date from" must be less than or equal to "Date to"'))
        return True
    
    ################################ Private Methods #################
    
    def prepare_where(self):
        '''
        :param mode: 'strict', 'initial', 'ending'
        :return:
        '''
        where = 'WHERE (1=1) '

        cmpny_ids = self.env.company.ids + self.env.company.child_ids.ids
        where += ' AND anl_line.company_id in %s ' % str(tuple(cmpny_ids) + tuple([0]))

        if self.journal_ids:
            where += ' AND j.id IN %s ' % str(tuple(self.journal_ids.ids) + tuple([0]))
        if self.partner_ids:
            where += ' AND p.id IN %s ' % str(tuple(self.partner_ids.ids) + tuple([0]))
        if self.account_ids:
            where += ' AND a.id IN %s ' % str(tuple(self.account_ids.ids) + tuple([0]))
        #if self.company_id:
        #    where += ' AND anl_line.company_id = %s ' % self.company_id.id

        where += ''' AND anl_line.date >= '%s' AND anl_line.date <= '%s' ''' % (self.date_from, self.date_to)

        return where

    def prepare_from(self):
        sql_from = '''
            FROM account_analytic_line AS anl_line
            JOIN account_move_line m ON m.id = anl_line.move_line_id
            JOIN account_move move ON move.id = m.move_id
            JOIN account_analytic_account analytic ON analytic.id = anl_line.account_id
            JOIN account_analytic_plan analytic_plan ON analytic_plan.id = analytic.plan_id
            LEFT JOIN res_partner p ON p.id = anl_line.partner_id 
            LEFT JOIN account_journal j ON (anl_line.journal_id=j.id)
            LEFT JOIN account_account a ON a.id = anl_line.general_account_id
            LEFT JOIN product_product product ON product.id=anl_line.product_id
            LEFT JOIN product_template p_template ON (product.product_tmpl_id = p_template.id)
        '''
        return sql_from

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

        analytic_company_domain = [('company_id', '=', self.env.context.get('company_id') or self.env.company.id)]
        if self.plan_ids:
            analytic_company_domain.append(('plan_id', 'in', self.plan_ids.ids))
        if self.analytic_ids:
            analytic_company_domain.append(('id', 'in', self.analytic_ids.ids))

        analytic_ids = self.env['account.analytic.account'].search(analytic_company_domain, order='code asc')
        analytic_lines = []
        for analytic in analytic_ids:

            result = {
                'id_list': [],
                'size': 0,
                'amount': 0,
                'time_string': ''
            }
            # Current
            sql = ('''
                SELECT
                    array_agg(anl_line.id) AS id_list,
                    COUNT(anl_line.id) AS size,
                    COALESCE(SUM(anl_line.amount),0) AS amount,
                    EXTRACT(HOUR FROM CURRENT_TIME)::TEXT || ':' ||
                    EXTRACT(MINUTE FROM CURRENT_TIME)::TEXT || ':' ||
                    EXTRACT(SECOND FROM CURRENT_TIME)::TEXT || ':' || '%s' AS time_string
                ''' % str(analytic.id) + self.prepare_from() + self.prepare_where() +
                   ''' AND anl_line.account_id = %s 
                   ''' % analytic.id)
            cr.execute(sql)
            res = cr.dictfetchone() or {}

            result.update(res)
            # Extra args
            result.update(
                {
                    'analytic_id': analytic.id,
                    'analytic_name': analytic.name,
                    'analytic_code': analytic.code or '',
                    'currency_id': self.currency_id.id,
                }
            )
            if result.get('amount'):
                analytic_lines.append(result)
        return analytic_lines

    def prepare_detailed_lines(self, move_line_ids=[], analytic_account_id=False):
        cr = self.env.cr
        final_list = []
        user_language = self.env.user.lang

        # Current
        where_current = self.prepare_where() + ' AND anl_line.id in %s ' % str(tuple(move_line_ids) + tuple([0]))
        sql = ('''
                SELECT
                    anl_line.id AS id,
                    anl_line.date AS date,
                    move.id AS move_id,
                    p.name AS partner_name,
                    j.code AS journal_code,
                    COALESCE(a.name::jsonb ->> %(lang)s, a.name::jsonb ->> 'en_US') AS account_name,
                    a.code_store AS account_code,
                    COALESCE(analytic.name::jsonb ->> %(lang)s, analytic.name::jsonb ->> 'en_US') AS analytic_name,
                    anl_line.amount AS amount,
                    COALESCE(analytic_plan.name::jsonb ->> %(lang)s, analytic_plan.name::jsonb ->> 'en_US') AS plan,
                    COALESCE(p_template.name::jsonb ->> %(lang)s, p_template.name::jsonb ->> 'en_US') AS product
                    ''' + self.prepare_from() + where_current +
                    '''
                    GROUP BY
                        anl_line.date, p.name, move.id, anl_line.id, j.code, a.name, a.code_store ,j.code, analytic.name, analytic_plan.name, p_template.name, anl_line.amount
                    ORDER BY anl_line.date
                ''')
        cr.execute(sql, {'lang': user_language})
        final_list += cr.dictfetchall()
        return final_list

    def prepare_values_for_component(self):
        self.onchange_date_range()
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.analytic.report')], limit=1)

        date_range = {'choices': [], 'selectedValue': {'value': self.date_range}}
        include_details = {'choices': [], 'selectedValue': {'value': self.include_details}}

        for field in model_id.field_id:
            if field.name == 'date_range':
                date_range['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
            if field.name == 'include_details':
                include_details['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]

        return {
            'defaultAccountValues': [{'value': a.id, 'label': a.name, 'code': a.code_store} for a in self.account_ids],
            'defaultJournalValues': [{'value': a.id, 'label': a.name, 'code': a.code} for a in self.journal_ids],
            'defaultPartnerValues': [{'value': a.id, 'label': a.name} for a in self.partner_ids],
            'defaultPlanValues': [{'value': a.id, 'label': a.name} for a in self.plan_ids],
            'defaultAnalyticValues': [{'value': a.id, 'label': a.name} for a in self.analytic_ids],
            'include_details': include_details,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'date_range': date_range,
        }

    def update_values_from_component(self, vals):
        update_dict = {}
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.analytic.report')], limit=1)
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
        return self.prepare_main_lines()
    
    ##################################################################

    def action_pdf(self):
        return self.env.ref(
            'account_dynamic_reports'
            '.action_print_analytic_report').with_context(landscape=True).report_action(
                self, data={})

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'Analytic View',
            'tag': 'account_dynamic_reports.action_analytic_report',
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
        sheet = workbook.add_worksheet('Analytic Report')
        sheet.set_zoom(95)
        sheet_2 = workbook.add_worksheet('Filters')
        sheet_2.protect()

        # Get record and data
        record = self.env['ins.analytic.report'].browse(data.get('id', [])) or False

        filter = record.prepare_values_for_component()
        account_lines = record.prepare_main_lines()

        # Formats
        ############################################################
        sheet.set_column(0, 0, 18)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 35)
        sheet.set_column(3, 3, 22)
        sheet.set_column(4, 4, 13)
        sheet.set_column(5, 5, 13)
        sheet.set_column(6, 6, 13)

        sheet_2.set_column(0, 0, 35)
        sheet_2.set_column(1, 1, 25)
        sheet_2.set_column(2, 2, 25)
        sheet_2.set_column(3, 3, 25)
        sheet_2.set_column(4, 4, 25)
        sheet_2.set_column(5, 5, 25)
        sheet_2.set_column(6, 6, 25)

        sheet.freeze_panes(4, 0)

        sheet.screen_gridlines = False
        sheet_2.screen_gridlines = False

        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
            'border': False
        })
        format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font': 'Arial',
            'align': 'center',
            # 'border': True
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'border': True,
            'text_wrap': True,
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': True,
            'align': 'center',
            'font': 'Arial',
        })
        line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'bottom': True,
        })
        line_header_left = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'top': True,
            'font': 'Arial',
            'bottom': True,
        })
        line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            # 'top': True,
            # 'bottom': True,
            'font': 'Arial',
            'text_wrap': True,
            'valign': 'top'
        })
        line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            # 'top': True,
            # 'bottom': True,
            'font': 'Arial',
            'align': 'center',
        })
        line_header_light_initial = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'bottom': True,
            'text_wrap': True,
            'valign': 'top'
        })
        line_header_light_initial_bold = workbook.add_format({
            'bold': True,
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'text_wrap': True,
            'valign': 'top'
        })
        line_header_light_ending = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'text_wrap': True,
            'valign': 'top'
        })
        line_header_light_ending_bold = workbook.add_format({
            'bold': True,
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'text_wrap': True,
            'valign': 'top'
        })

        lang = self.env.user.lang
        lang_id = self.env['res.lang'].search([('code', '=', lang)])[0]
        currency_id = self.env.user.company_id.currency_id
        line_header.num_format = currency_id.excel_format
        line_header_light.num_format = currency_id.excel_format
        line_header_light_initial.num_format = currency_id.excel_format
        line_header_light_ending.num_format = currency_id.excel_format
        line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

        # Write data
        ################################################################
        row_pos_2 = 0
        row_pos = 0
        sheet.merge_range(0, 0, 0, 8, 'Analytic Report' + ' - ' + data['company_id'][1], format_title)

        # Write filters
        sheet_2.write(row_pos_2, 0, _('Date from'), format_header)
        datestring = fields.Date.from_string(str(filter['date_from'])).strftime(lang_id.date_format)
        sheet_2.write(row_pos_2, 1, datestring or '', content_header_date)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Date to'), format_header)
        datestring = fields.Date.from_string(str(filter['date_to'])).strftime(lang_id.date_format)
        sheet_2.write(row_pos_2, 1, datestring or '', content_header_date)
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

        # Write Ledger details
        row_pos += 3
        sheet.write_string(row_pos, 0, _('Date'), format_header)
        sheet.write_string(row_pos, 1, _('Partner'), format_header)
        sheet.write_string(row_pos, 2, _('Journal'), format_header)
        sheet.write_string(row_pos, 3, _('Account'), format_header)
        sheet.write_string(row_pos, 4, _('Plan'), format_header)
        sheet.write_string(row_pos, 5, _('Product'), format_header)
        sheet.write_string(row_pos, 6, _('Amount'), format_header)

        if account_lines:
            for line in account_lines:
                row_pos += 1
                sheet.merge_range(row_pos, 0, row_pos, 5,
                                  '            ' + line.get('analytic_code', '') + ' - ' + line.get('analytic_name', ''),
                                  line_header_left)
                sheet.write(row_pos, 6, float(line.get('amount')), line_header)

                sub_lines = record.prepare_detailed_lines(line.get('id_list'), line.get('account_id'))
                if record.include_details == 'yes':
                    for sub_line in sub_lines:
                        row_pos += 1
                        datestring = fields.Date.from_string(str(sub_line.get('date'))).strftime(lang_id.date_format)
                        sheet.write(row_pos, 0, datestring, line_header_light_date)
                        sheet.write(row_pos, 1, sub_line.get('partner_name') or '', line_header_light)
                        sheet.write(row_pos, 2, sub_line.get('journal_code') or '', line_header_light)
                        sheet.write(row_pos, 3, sub_line.get('account_name') or '', line_header_light)
                        sheet.write(row_pos, 4, sub_line.get('plan') or '', line_header_light)
                        sheet.write(row_pos, 5, sub_line.get('product') or '', line_header_light)
                        sheet.write(row_pos, 6, float(sub_line.get('amount')), line_header_light)

        # Close and return
        #################################################################
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())

        report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'GL.xls'})
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xls' % (
                report_id.id, 'Analytic Report.xls'),
            'target': 'new',
        }

        output.close()