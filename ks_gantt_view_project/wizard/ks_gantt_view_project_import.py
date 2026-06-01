from odoo import models, fields, _
import xlrd
import tempfile
import binascii
import datetime
import logging
import json
import dateutil.parser
import pandas as pd
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class KsGanttViewImport(models.TransientModel):
    _name = 'ks.gantt.import.wizard'
    _description = 'Ks Project Import Wizard'

    ks_file_type = fields.Selection([('xlsx', 'Excel'), ('json', 'JSON')], string='File Type', default='xlsx',
                                    required=True)
    ks_file = fields.Binary(string='Upload File', required=True)

    def is_valid_ks_fields_for_excel_import(self,ks_model_obj,ks_sheet_columns,ks_model = "project.task"):
        for index, val in enumerate(ks_sheet_columns):
            # Check if the field is not available in the model.
            if not ks_model_obj._fields.get(val):
                raise UserError(_('%s is not present in the %s model' % (val, ks_model)))

    def ks_action_import(self):
        if self.ks_file_type == 'xlsx':
            self.ks_import_xlsx_file()
        elif self.ks_file_type == 'json':
            self.ks_import_json_file()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def ks_import_xlsx_file(self):
        # Read xlsx file.
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.ks_file))
        fp.seek(0)
        try:
            df = pd.read_excel(fp.name, engine='openpyxl')
            # workbook = xlrd.open_workbook(fp.name)
            # sheet = workbook.sheet_by_index(0)
        except Exception as e:
            raise ValidationError(_("File can't be read please upload correct file"))
        df = df.astype(str)
        values = {}
        column = df.columns.tolist()

        ks_project_task_obj = self.env['project.task'].sudo()

        ks_sheet_columns = column
        ks_sheet_columns.remove('id')
        ks_sheet_columns.remove('ks_target_task_id')
        ks_sheet_columns.remove('ks_task_link_type')
        self.is_valid_ks_fields_for_excel_import(ks_project_task_obj,ks_sheet_columns)
        ks_project_dict = {}

        updated_task_ids = {}

        # parsing xlsx data.
        for row_no in (range(df.shape[0])):
            row = list(df.iloc[row_no])
            ks_task_write_val = {}
            # read imported data rows and creates a dictionary/
            row_id = row.pop(0)
            if row[0] == 'False':
                continue
            row = row[:-2]
            for index, val in enumerate(ks_sheet_columns):
                # manage new project creation
                if val == 'project_id':
                    # check if duplicate project not created then created.
                    if row[index] not in ks_project_dict.keys():
                        # create new project.
                        project_name = row[index] + " " + str(datetime.datetime.now())
                        new_project_id = self.env['project.project'].sudo().create({
                            'name': project_name
                        })
                        # update project list info
                        ks_project_dict[row[index]] = new_project_id.id

                    # update dictionary for its project fields
                    ks_task_write_val[val] = ks_project_dict[row[index]]

                elif ks_project_task_obj._fields[val].type in ['char', 'selection']:
                    ks_task_write_val[val] = row[index]
                elif ks_project_task_obj._fields[val].type == 'many2one':
                    ks_task_write_val[val] = self.ks_valid_manny_to_one_data(
                        ks_project_task_obj._fields[val].comodel_name, row[index])
                elif ks_project_task_obj._fields[val].type in ['datetime', 'date']:
                    if row[index]:
                        try:
                            # ks_task_write_val[val] = fields.Datetime.from_string(datetime.datetime.strftime(datetime.datetime.strptime(row[index],'%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))
                            ks_task_write_val[val] = pd.to_datetime(row[index]).to_pydatetime()

                        except:
                            ks_task_write_val[val] = False
                    else:
                        ks_task_write_val[val] = False
                elif ks_project_task_obj._fields[val].type == 'boolean':
                    if row[index] == "False":
                        ks_task_write_val[val] = False
                    else:
                        ks_task_write_val[val] = True

                else:
                    _logger.warning(
                        _("%s field type can't imported since it is not supported" % ks_project_task_obj._fields[
                            val].type))
            created_task = ks_project_task_obj.create(ks_task_write_val)
            updated_task_ids[int(row_id)] = created_task.id

        df.dropna(subset=['ks_target_task_id', 'ks_task_link_type'], how='all', inplace=True)
        grouped = df.groupby('id').agg({
            'ks_target_task_id': list,
            'ks_task_link_type': list
        }).reset_index()

        for index, row in grouped.iterrows():
            id_val = int(row['id'])
            target_task_ids = row['ks_target_task_id']
            task_link_types = row['ks_task_link_type']

            if target_task_ids != ['nan'] and task_link_types != ['nan']:
                for i in range(len(target_task_ids)):
                    self.env['ks.task.link'].sudo().create({
                        'ks_source_task_id': updated_task_ids[id_val],
                        'ks_target_task_id': updated_task_ids[int(float(target_task_ids[i]))],
                        'ks_task_link_type': str(int(float(task_link_types[i]))),
                    })


    def ks_import_json_file(self):
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        fp.write(binascii.a2b_base64(self.ks_file))
        fp.seek(0)
        try:
            parsed_data = json.load(fp)
        except Exception as e:
            raise ValidationError(_("File can't be read please upload correct file"))


        if 'config' in parsed_data and 'ks_gantt_task_data' in parsed_data['config'] and \
                'data' in parsed_data['config']['ks_gantt_task_data'] and (parsed_data['config'] and \
                parsed_data['config']['ks_gantt_task_data'] and \
                parsed_data['config']['ks_gantt_task_data']['data']):
            # create dictionary for project tasks.
            task_data = parsed_data['config']['ks_gantt_task_data']['data']

            # project task object
            ks_project_task_obj = self.env['project.task'].sudo()
            ks_project_dict = {}

            # remove project data from the parsed list.
            filtered_task_data = [
                rec if 'type' in rec and rec['type'] != 'project'
                else (_ for _ in ()).throw(ValidationError("Wrong Module Data")) if 'type' not in rec
                else None
                for rec in task_data
            ]

            link_task_data = [eval(rec['ks_task_link_ids']) for rec in task_data if 'ks_task_link_ids' in rec and rec['ks_task_link_ids']!='[]']
            updated_task_ids = {}

            for task in filtered_task_data:
                ks_task_write_val = {}
                if task:
                    for key, value in self.ks_gantt_field_mapping().items():
                        if value == 'project_id':
                            if task[key] and task[key][1] and task[key][1] not in ks_project_dict.keys():
                                project_name = task[key][1] + " " + str(datetime.datetime.now())
                                new_project_id = self.env['project.project'].sudo().create({
                                    'name': project_name
                                })
                                # update project list info
                                ks_project_dict[task[key][1]] = new_project_id.id
                            # update task dict for new project.
                            if task[key]:
                                ks_task_write_val[value] = ks_project_dict[task[key][1]]

                        elif ks_project_task_obj._fields[value].type in ['char', 'selection']:
                            ks_task_write_val[value] = task.get(key)

                        elif ks_project_task_obj._fields[value].type == 'many2one':
                            # need to check if value is available or not.
                            ks_task_write_val[value] = self.ks_valid_manny_to_one_data(
                                ks_project_task_obj._fields[value].comodel_name, task[key][1]) if task.get(key) and \
                                                                                                  task[key][
                                                                                                      1] else False
                        elif ks_project_task_obj._fields[value].type in ['datetime', 'date']:
                            if task[key]:
                                # ks_task_write_val[value] = dateutil.parser.parse(task[key])
                                ks_task_write_val[value] = fields.Datetime.from_string(datetime.datetime.strftime(datetime.datetime.strptime((str(dateutil.parser.parse(task[key])).split("+")[0]).split('.')[0],'%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))

                        elif ks_project_task_obj._fields[value].type == 'boolean':
                            ks_task_write_val[value] = bool(task.get(key))
                        else:
                            _logger.warning(
                                _("%s field type can't imported since it is not supported" %
                                  ks_project_task_obj._fields[
                                      value].type))
                    created_task = ks_project_task_obj.create(ks_task_write_val)
                    updated_task_ids[task['id']] = created_task.id

            for task_links in link_task_data:
                for link in task_links:
                    try:
                        source_id = updated_task_ids[link['source']]
                        target_id = updated_task_ids[link['target']]
                    except KeyError:
                        source_id = updated_task_ids.get('task_' + str(link['source']))
                        target_id = updated_task_ids.get('task_' + str(link['target']))

                    self.env['ks.task.link'].sudo().create({
                        'ks_source_task_id': source_id,
                        'ks_target_task_id': target_id,
                        'ks_task_link_type': link['type'],
                        'ks_lag_days': link['lag']
                    })

        else:
            wrong_file_msg = _('Required data not found in the json file, please upload correct json file.')
            _logger.info(wrong_file_msg)
            raise UserError(wrong_file_msg)

    def ks_gantt_field_mapping(self):
        return {
            'text': 'name',
            'mark_as_important': 'priority',
            'project_id': 'project_id',
            'ks_owner_task': 'user_ids',
            'partner_id': 'partner_id',
            # 'company_id': 'company_id',
            'ks_deadline_tooltip': 'date_deadline',
            'unscheduled': 'ks_task_unschedule',
            'type': 'ks_task_type',
            'ks_enable_task_duration': 'ks_enable_task_duration',
            'start_date': 'ks_start_datetime',
            'end_date': 'ks_end_datetime',
            'ks_schedule_mode': 'ks_schedule_mode',
            'constraint_type': 'ks_constraint_task_type',
            'constraint_date': 'ks_constraint_task_date',
            'stage_id': 'stage_id',
            'planned_hours': 'planned_hours',
        }

    def ks_valid_manny_to_one_data(self, comodel, value):
        """
        Function to check if data is available then return its id otherwise return false.
        :param comodel:
        :param id:
        :return:
        """
        ks_domain = []
        # Create domain to search the records.
        if self.env[comodel].sudo()._fields['name']:
            ks_domain.append(('name', '=', value))
        else:
            ks_domain.append(('display_name', '=', value))

        ks_res = self.env[comodel].sudo().search(ks_domain, limit=1)
        if ks_res:
            return ks_res.id
        else:
            return False
