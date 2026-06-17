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

FETCH_RANGE = 2500

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

class InsPartnerAgeing(models.TransientModel):
    _name = "ins.partner.ageing"

    @api.onchange('partner_type')
    def onchange_partner_type(self):
        self.partner_ids = [(5,)]
        if self.partner_type:
            if self.partner_type == 'customer':
                partner_company_domain = [('parent_id', '=', False),
                                          ('customer_rank', '>', 0),
                                          '|',
                                          ('company_id', '=', self.env.company.id),
                                          ('company_id', '=', False)]

                self.partner_ids |= self.env['res.partner'].search(partner_company_domain)
            if self.partner_type == 'supplier':
                partner_company_domain = [('parent_id', '=', False),
                                          ('supplier_rank', '>', 0),
                                          '|',
                                          ('company_id', '=', self.env.company.id),
                                          ('company_id', '=', False)]

                self.partner_ids |= self.env['res.partner'].search(partner_company_domain)

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Ageing'))
        return res

    as_on_date = fields.Date(string='As on date', required=True, default=fields.Date.today())
    bucket_1 = fields.Integer(string='Bucket 1', required=True, default=lambda self:self.env.company.bucket_1)
    bucket_2 = fields.Integer(string='Bucket 2', required=True, default=lambda self:self.env.company.bucket_2)
    bucket_3 = fields.Integer(string='Bucket 3', required=True, default=lambda self:self.env.company.bucket_3)
    bucket_4 = fields.Integer(string='Bucket 4', required=True, default=lambda self:self.env.company.bucket_4)
    bucket_5 = fields.Integer(string='Bucket 5', required=True, default=lambda self:self.env.company.bucket_5)
    include_details = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Include Details', default='yes')
    report_type = fields.Selection([('asset_receivable', 'Receivable Accounts Only'),
                              ('liability_payable', 'Payable Accounts Only')], string='Type')
    partner_type = fields.Selection([('customer', 'Customer Only'),
                             ('supplier', 'Supplier Only')], string='Partner Type')

    partner_ids = fields.Many2many(
        'res.partner', required=False
    )
    partner_category_ids = fields.Many2many(
        'res.partner.category', string='Partner Tag',
    )
    account_ids = fields.Many2many(
        'account.account', string='Accounts'
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
        ret = super(InsPartnerAgeing, self).write(vals)
        return ret

    def validate_data(self):
        if not(self.bucket_1 < self.bucket_2 and self.bucket_2 < self.bucket_3 and self.bucket_3 < self.bucket_4 and \
            self.bucket_4 < self.bucket_5):
            raise ValidationError(_('"Bucket order must be ascending"'))
        return True

    ################################################################################
    ############################# Core Methods Start ###############################
    ################################################################################

    def prepare_bucket_list(self):
        periods = {}
        date_from = self.as_on_date
        date_from = fields.Date.from_string(date_from)

        lang = self.env.user.lang
        language_id = self.env['res.lang'].search([('code', '=', lang)])[0]

        bucket_list = [self.bucket_1, self.bucket_2, self.bucket_3, self.bucket_4, self.bucket_5]

        start = False
        stop = date_from
        name = 'Not Due'
        periods[0] = {
            'bucket': 'As on',
            'name': name,
            'start': '',
            'stop': stop.strftime('%Y-%m-%d'),
        }

        stop = date_from
        final_date = False
        for i in range(5):
            ref_date = date_from - relativedelta(days=1)
            start = stop - relativedelta(days=1)
            stop = ref_date - relativedelta(days=bucket_list[i])
            name = '0 - ' + str(bucket_list[0]) if i == 0 else str(str(bucket_list[i - 1] + 1)) + ' - ' + str(
                bucket_list[i])
            final_date = stop
            periods[i + 1] = {
                'bucket': bucket_list[i],
                'name': name,
                'start': start.strftime('%Y-%m-%d'),
                'stop': stop.strftime('%Y-%m-%d'),
            }

        start = final_date - relativedelta(days=1)
        stop = ''
        name = str(self.bucket_5) + ' +'

        periods[6] = {
            'bucket': 'Above',
            'name': name,
            'start': start.strftime('%Y-%m-%d'),
            'stop': '',
        }
        return periods

    def prepare_main_lines(self):
        ''' Query Start Here
                ['partner_id':
                    {'0-30':0.0,
                    '30-60':0.0,
                    '60-90':0.0,
                    '90-120':0.0,
                    '>120':0.0,
                    'as_on_date_amount': 0.0,
                    'total': 0.0}]
                1. Prepare bucket range list from bucket values
                2. Fetch partner_ids and loop through bucket range for values
                '''
        period_dict = self.prepare_bucket_list()

        domain = ['|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)]
        if self.partner_type == 'customer':
            domain.append(('customer_rank', '>', 0))
        if self.partner_type == 'supplier':
            domain.append(('supplier_rank', '>', 0))

        if self.partner_category_ids:
            domain.append(('category_id', 'in', self.partner_category_ids.ids))

        partner_ids = self.partner_ids or self.env['res.partner'].search(domain)
        as_on_date = self.as_on_date
        company_currency_id = self.env.company.currency_id.id
        company_id = self.env.company

        type = ('asset_receivable', 'liability_payable')
        if self.report_type:
            type = tuple([self.report_type, 'none'])

        partner_dict = {}
        for partner in partner_ids:
            partner_dict.update({partner.id: {}})

        partner_dict.update({'Total': {}})
        for period in period_dict:
            partner_dict['Total'].update({period_dict[period]['name']: 0.0})
        partner_dict['Total'].update({'total': 0.0, 'partner_name': 'ZZZZZZZZZ'})
        partner_dict['Total'].update({'company_currency_id': company_currency_id})

        ageing_lines = []
        total = {
            'time_string': fields.Datetime.now().strftime("%H:%M:%S") + 'total',
            'partner_name': 'Total',
            'currency_id': company_currency_id
        }
        for partner in partner_ids:
            age_dict = {
                'partner_name': partner.name,
                'partner_id': partner.id,
                'id_list': [],
                'size': 0,
                'currency_id': company_currency_id,
                'total': 0
            }
            id_list = []
            for period in period_dict:

                total.update({period_dict[period]['name']: 0})

                where = " AND l.partner_id = %s AND COALESCE(l.date_maturity,l.date) " % partner.id
                if period_dict[period].get('start') and period_dict[period].get('stop'):
                    where += " BETWEEN '%s' AND '%s'" % (
                        period_dict[period].get('stop'), period_dict[period].get('start'))
                elif not period_dict[period].get('start'):  # ie just
                    where += " >= '%s'" % (period_dict[period].get('stop'))
                else:
                    where += " <= '%s'" % (period_dict[period].get('start'))

                if self.account_ids:
                    where += " AND a.id in %s " % str(tuple(self.account_ids.ids) + tuple([0]))

                sql = """
                            SELECT
                                array_agg(l.id) AS id_list,
                                sum(
                                    l.balance
                                    ) AS balance,
                                sum(
                                    COALESCE(
                                        (SELECT 
                                            SUM(amount)
                                        FROM account_partial_reconcile
                                        WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                        )
                                    ) AS sum_debit,
                                sum(
                                    COALESCE(
                                        (SELECT 
                                            SUM(amount) 
                                        FROM account_partial_reconcile 
                                        WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                        )
                                    ) AS sum_credit
                            FROM
                                account_move_line AS l
                            LEFT JOIN
                                account_move AS m ON m.id = l.move_id
                            LEFT JOIN
                                account_account AS a ON a.id = l.account_id
                            WHERE
                                l.balance <> 0
                                AND m.state = 'posted'
                                AND a.account_type IN %s
                                AND l.company_id = %s
                        """ % (as_on_date, as_on_date, type, company_id.id)
                self.env.cr.execute(sql + where)
                fetch_dict = self.env.cr.dictfetchall() or 0.0

                if not fetch_dict[0].get('balance'):
                    amount = 0.0
                else:
                    amount = fetch_dict[0]['balance'] + fetch_dict[0]['sum_debit'] - fetch_dict[0]['sum_credit']

                age_dict.update({period_dict[period]['name']: amount or 0})
                age_dict['total'] += amount or 0

                if fetch_dict[0].get('id_list'):
                    id_list.extend(fetch_dict[0].get('id_list'))

            age_dict.update({
                'id_list': id_list,
                'size': len(id_list) or 0,
                'time_string': fields.Datetime.now().strftime("%H:%M:%S") + str(partner.id)
            })
            # Add only when a valid ageing found
            for p in period_dict:
                if age_dict[period_dict[p]['name']]:
                    ageing_lines.append(age_dict)
                    break

        grand_total = 0
        for ln in ageing_lines:
            for p in period_dict:
                grand_total += ln[period_dict[p]['name']]
                total[period_dict[p]['name']] += ln[period_dict[p]['name']]
        total['total'] = grand_total
        total['time_string'] = fields.Datetime.now().strftime("%H:%M:%S") + 'total'
        ageing_lines.append(total)
        return period_dict, ageing_lines

    def prepare_detailed_lines(self, move_line_ids=[], account_id=False):
        as_on_date = self.as_on_date
        period_dict = self.prepare_bucket_list()
        period_list = [period_dict[a]['name'] for a in period_dict]
        company_id = self.env.company
        user_language = self.env.user.lang
        if account_id:
            select = """SELECT m.name AS move_name,
                            l.id AS lid, 
                            m.id AS move_id,
                            l.date AS date,
                            l.date_maturity AS date_maturity, 
                            j.code AS journal_code,
                            cc.id AS company_currency_id,
                            COALESCE(a.code_store::jsonb ->> %(company)s, a.code_store::jsonb ->> '1') AS account_code,
                            """
            for period in period_dict:
                if period_dict[period].get('start') and period_dict[period].get('stop'):
                    select += """ CASE 
                        WHEN 
                            COALESCE(l.date_maturity,l.date) >= '%s' AND 
                            COALESCE(l.date_maturity,l.date) <= '%s'
                        THEN
                            sum(l.balance) +
                            sum(
                                COALESCE(
                                    (SELECT 
                                        SUM(amount)
                                    FROM account_partial_reconcile
                                    WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                    )
                                ) -
                            sum(
                                COALESCE(
                                    (SELECT 
                                        SUM(amount) 
                                    FROM account_partial_reconcile 
                                    WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                    )
                                )
                        ELSE
                            0
                        END AS %s,""" % (period_dict[period].get('stop'),
                                         period_dict[period].get('start'),
                                         as_on_date,
                                         as_on_date,
                                         'range_' + str(period),
                                         )
                elif not period_dict[period].get('start'):
                    select += """ CASE 
                            WHEN 
                                COALESCE(l.date_maturity,l.date) >= '%s' 
                            THEN
                                sum(
                                    l.balance
                                    ) +
                                sum(
                                    COALESCE(
                                        (SELECT 
                                            SUM(amount)
                                        FROM account_partial_reconcile
                                        WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                        )
                                    ) -
                                sum(
                                    COALESCE(
                                        (SELECT 
                                            SUM(amount) 
                                        FROM account_partial_reconcile 
                                        WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                        )
                                    )
                            ELSE
                                0
                            END AS %s,""" % (
                    period_dict[period].get('stop'), as_on_date, as_on_date, 'range_' + str(period))
                else:
                    select += """ CASE
                            WHEN
                                COALESCE(l.date_maturity,l.date) <= '%s' 
                            THEN
                                sum(
                                    l.balance
                                    ) +
                                sum(
                                    COALESCE(
                                        (SELECT 
                                            SUM(amount)
                                        FROM account_partial_reconcile
                                        WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                        )
                                    ) -
                                sum(
                                    COALESCE(
                                        (SELECT 
                                            SUM(amount) 
                                        FROM account_partial_reconcile 
                                        WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                        )
                                    )
                            ELSE
                                0
                            END AS %s """ % (
                    period_dict[period].get('start'), as_on_date, as_on_date, 'range_' + str(period))

            sql = """
                FROM
                    account_move_line AS l
                LEFT JOIN
                    account_move AS m ON m.id = l.move_id
                LEFT JOIN
                    account_account AS a ON a.id = l.account_id
                --LEFT JOIN
                --    account_account_type AS ty ON a.user_type_id = ty.id
                LEFT JOIN
                    account_journal AS j ON l.journal_id = j.id
                LEFT JOIN 
                    res_currency AS cc ON l.company_currency_id = cc.id
                WHERE
                    l.balance <> 0 and l.id in %s
                GROUP BY
                    l.date, l.date_maturity, m.id, m.name, j.code, a.code_store, cc.id, l.id
                
            """ % str(tuple(move_line_ids) + tuple([0]))

            self.env.cr.execute(select + sql,  {'company': company_id.id})
            final_list = self.env.cr.dictfetchall() or []
            move_lines = []
            for m in final_list:
                m['total'] = m['range_0'] + m['range_1'] + m['range_2'] + m['range_3'] + m['range_4'] + m['range_5'] + m['range_6']
                if (m['range_0'] or m['range_1'] or m['range_2'] or m['range_3'] or m['range_4'] or m['range_5'] or m['range_6']):
                    move_lines.append(m)
            return move_lines
        return []

    def prepare_values_for_component(self):
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.partner.ageing')], limit=1)

        report_type = {'choices': [], 'selectedValue': {'value': self.report_type}}
        partner_type = {'choices': [], 'selectedValue': {'value': self.partner_type}}
        include_details = {'choices': [], 'selectedValue': {'value': self.include_details}}

        for field in model_id.field_id:
            if field.name == 'report_type':
                report_type['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
            if field.name == 'partner_type':
                partner_type['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
            if field.name == 'include_details':
                include_details['choices'] = [{'value': a.value, 'label': a.name} for a in field.selection_ids]
        return {
            'defaultPartnerValues': [{'value': a.id, 'label': a.name} for a in self.partner_ids],
            'defaultPartnerTagsValues': [{'value': a.id, 'label': a.name} for a in self.partner_category_ids],
            'defaultAccountValues': [{'value': a.id, 'label': a.code_store, 'code': a.code_store} for a in self.account_ids],
            'as_on_date': self.as_on_date,
            'report_type': report_type,
            'partner_type':  partner_type,
            'include_details': include_details,
            'bucket_1': self.bucket_1,
            'bucket_2': self.bucket_2,
            'bucket_3': self.bucket_3,
            'bucket_4': self.bucket_4,
            'bucket_5': self.bucket_5,
        }

    def update_values_from_component(self, vals):
        update_dict = {}
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'ins.partner.ageing')], limit=1)
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
                if field.ttype == 'integer':
                    update_dict.update({field.name: vals[field.name]})
        self.write(update_dict)
        return self.prepare_main_lines()

    ################################################################################
    ############################# Core Methods END #################################
    ################################################################################

    def action_pdf(self):
        return self.env.ref(
            'account_dynamic_reports'
            '.action_print_partner_ageing').with_context(landscape=True).report_action(
            self, data={})

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'Ageing View',
            'tag': 'account_dynamic_reports.action_ageing_report',
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
        sheet = workbook.add_worksheet('Partner Ageing')
        sheet.set_zoom(95)
        sheet_2 = workbook.add_worksheet('Filters')
        sheet_2.protect()

        # Get record and data
        record = self.env['ins.partner.ageing'].browse(data.get('id', [])) or False

        filter = record.prepare_values_for_component()
        ageing_bucket, ageing_lines = record.prepare_main_lines()

        # Formats
        ############################################################
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 3, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)

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
        sheet_2.protect()
        sheet.set_zoom(75)

        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
            'font': 'Arial'
        })
        format_header = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'center',
            'font': 'Arial'
            # 'border': True
        })
        format_header_period = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'center',
            'font': 'Arial',
            'left': True,
            'right': True,
            # 'border': True
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial'
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial'
            # 'num_format': 'dd/mm/yyyy',
        })
        line_header = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'bold': True,
            'left': True,
            'right': True,
            'font': 'Arial'
        })
        line_header_total = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'bold': True,
            'border': True,
            'font': 'Arial'
        })
        line_header_period = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'bold': True,
            'left': True,
            'right': True,
            'font': 'Arial'
        })
        line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'border': False,
            'font': 'Arial',
            'text_wrap': True,
        })
        line_header_light_period = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'left': True,
            'right': True,
            'font': 'Arial',
            'text_wrap': True,
        })
        line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': False,
            'font': 'Arial',
            'align': 'center',
        })

        lang = self.env.user.lang
        lang_id = self.env['res.lang'].search([('code', '=', lang)])[0]
        currency_id = self.env.user.company_id.currency_id
        line_header.num_format = currency_id.excel_format
        line_header_light.num_format = currency_id.excel_format
        line_header_light_period.num_format = currency_id.excel_format
        line_header_total.num_format = currency_id.excel_format
        line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

        # Write data
        ################################################################
        row_pos_2 = 0
        row_pos = 0
        sheet.merge_range(0, 0, 0, 11, 'Partner Ageing' + ' - ' + data['company_id'][1], format_title)

        # Write filters
        row_pos_2 += 2
        sheet_2.write(row_pos_2, 0, _('As on Date'), format_header)
        datestring = fields.Date.from_string(str(filter['as_on_date'])).strftime(lang_id.date_format)
        sheet_2.write(row_pos_2, 1, datestring or '', content_header_date)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Partners'), format_header)
        p_list = ', '.join([lt['label'] or '' for lt in filter.get('defaultPartnerValues')])
        sheet_2.write(row_pos_2, 1, p_list, content_header)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Accounts'), format_header)
        a_list = ', '.join([lt['code'] or '' for lt in filter.get('defaultAccountValues')])
        sheet_2.write(row_pos_2, 1, a_list, content_header)
        row_pos_2 += 1
        sheet_2.write(row_pos_2, 0, _('Partner Tags'), format_header)
        a_list = ', '.join([lt['code'] or '' for lt in filter.get('defaultPartnerTagsValues')])
        sheet_2.write(row_pos_2, 1, a_list, content_header)

        # Write Ledger details
        row_pos += 3
        sheet.write(row_pos, 0,  _('Entry #'), format_header)
        sheet.write(row_pos, 1, _('Due Date'), format_header)
        sheet.write(row_pos, 2, _('Journal'), format_header)
        sheet.write(row_pos, 3, _('Account'), format_header)
        k = 4
        for bucket in ageing_bucket:
            sheet.write(row_pos, k, str(ageing_bucket[bucket].get('name')),
                                    format_header_period)
            k += 1
        sheet.write(row_pos, k, 'Total',
                    format_header_period)

        for line in ageing_lines:
            # Dummy vacant lines
            row_pos += 1
            sheet.write(row_pos, 4, '', line_header_light_period)
            sheet.write(row_pos, 5, '', line_header_light_period)
            sheet.write(row_pos, 6, '', line_header_light_period)
            sheet.write(row_pos, 7, '', line_header_light_period)
            sheet.write(row_pos, 8, '', line_header_light_period)
            sheet.write(row_pos, 9, '', line_header_light_period)
            sheet.write(row_pos, 10, '', line_header_light_period)
            sheet.write(row_pos, 11, '', line_header_light_period)
            row_pos += 1
            if line.get('id_list'):
                sheet.merge_range(row_pos, 0, row_pos, 3, line.get('partner_name'), line_header)
            else:
                sheet.merge_range(row_pos, 0, row_pos, 3, _('Total'), line_header_total)
            k = 4
            for bucket in ageing_bucket:
                sheet.write(row_pos, k, line[ageing_bucket[bucket]['name']], line_header)
                k += 1
            sheet.write(row_pos, k, line['total'], line_header)

            if record.include_details == 'yes':
                sub_lines = record.prepare_detailed_lines(line.get('id_list'), line.get('partner_id'))
                for sub_line in sub_lines:
                    row_pos += 1
                    sheet.write(row_pos, 0, sub_line.get('move_name') or '',
                                            line_header_light)
                    datestring = fields.Date.from_string(str(sub_line.get('date_maturity') or sub_line.get('date'))).strftime(
                        lang_id.date_format)
                    sheet.write(row_pos, 1, datestring, line_header_light_date)
                    sheet.write(row_pos, 2, sub_line.get('journal_code'), line_header_light)
                    sheet.write(row_pos, 3, sub_line.get('account_code') or '', line_header_light)
                    sheet.write(row_pos, 4, float(sub_line.get('range_0')), line_header_light_period)
                    sheet.write(row_pos, 5, float(sub_line.get('range_1')), line_header_light_period)
                    sheet.write(row_pos, 6, float(sub_line.get('range_2')), line_header_light_period)
                    sheet.write(row_pos, 7, float(sub_line.get('range_3')), line_header_light_period)
                    sheet.write(row_pos, 8, float(sub_line.get('range_4')), line_header_light_period)
                    sheet.write(row_pos, 9, float(sub_line.get('range_5')), line_header_light_period)
                    sheet.write(row_pos, 10, float(sub_line.get('range_6')), line_header_light_period)
                    sheet.write(row_pos, 11, '', line_header_light_period)
        row_pos += 1
        k = 4

        # Close and return
        #################################################################
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())

        report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'Ageing.xls'})
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xls' % (
                report_id.id, 'Partner Ageing.xls'),
            'target': 'new',
        }

        output.close()