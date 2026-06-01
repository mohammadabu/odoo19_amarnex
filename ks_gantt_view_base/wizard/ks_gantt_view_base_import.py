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


class KsGanttViewBaseImport(models.TransientModel):
    _name = 'ks.gantt.base.import.wizard'
    _description = 'Gantt View Import'

    ks_file_type = fields.Selection([('xlsx', 'Excel'), ('json', 'JSON')], string='File Type', default='xlsx',
                                    required=True)
    ks_file = fields.Binary(string='Upload File', required=True)

    def ks_import_xlsx_file(self, ks_model):
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

        # df = df.astype(str)
        values = {}
        column = df.columns.tolist()

        ks_sheet_columns = column
        ks_model_obj = self.env[ks_model].sudo()

        # parsing xlsx data.
        for row_no in (range(df.shape[0])):
            row = list(df.iloc[row_no])
            ks_model_write_val = {}
            # read imported data rows and creates a dictionary/
            for index, val in enumerate(ks_sheet_columns):
                # Check if the field is not available in the model.
                if not ks_model_obj._fields.get(val):
                    raise UserError(_('%s is not present in the %s model' % (val, ks_model)))
                if ks_model_obj._fields[val].type in ['char', 'selection', 'float', 'integer']:
                    if val == 'name' and ks_model_obj._fields[val].type == 'char':
                        ks_model_write_val[val] = row[index] + '_copy'
                    else:
                        ks_model_write_val[val] = row[index]
                elif ks_model_obj._fields[val].type == 'many2one':
                    ks_model_write_val[val] = self.ks_valid_many_to_one_data(
                        ks_model_obj._fields[val].comodel_name, row[index])
                elif ks_model_obj._fields[val].type in ['datetime', 'date']:
                    if row[index]:
                        ks_model_write_val[val] = pd.to_datetime(row[index]).to_pydatetime()
                    else:
                        if row[index] == False:
                            ks_model_write_val[val] = False
                        else:
                            ks_model_write_val[val] = True

                elif ks_model_obj._fields[val].type == 'boolean':
                    ks_model_write_val[val] = bool(row[index])
                else:
                    _logger.warning(
                        _("%s field type can't imported since it is not supported" % ks_model_obj._fields[
                            val].type))
            try:
                ks_model_obj.create(ks_model_write_val)
            except Exception as e:
                _logger.error(e)
                if e.args and e.args[0]:
                    error_msg = e.args[0]
                else:
                    error_msg = _('Some required fields are not available in the file.')
                raise UserError(error_msg)



    def ks_import_json_file(self, ks_model, ks_import_fields):
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        fp.write(binascii.a2b_base64(self.ks_file))
        fp.seek(0)
        try:
            parsed_data = json.load(fp)
        except Exception as e:
            raise ValidationError(_("File can't be read please upload correct file"))
        if 'config' in parsed_data and 'ks_gantt_task_data' in parsed_data.get('config') and \
                'data' in parsed_data.get('config').get('ks_gantt_task_data')  and parsed_data.get('config') and parsed_data.get('config').get('ks_gantt_task_data') and \
                parsed_data.get('config').get('ks_gantt_task_data').get('data'):
            # create dictionary for model data.
            ks_model_data = parsed_data['config']['ks_gantt_task_data']['data']

            # project task object
            ks_model_obj = self.env[ks_model].sudo()

            for model_data in ks_model_data:
                ks_model_write_val = {}
                # check if model data is values and this record should not group by.
                if model_data and 'ks_group_lvl' not in model_data:
                    for field_import in ks_import_fields:
                        if not ks_model_obj._fields.get(field_import):
                            raise UserError(_('%s is not present in the %s model' % (field_import, ks_model)))
                        if ks_model_obj._fields[field_import].type in ['char', 'selection', 'float', 'integer']:
                            if field_import == 'name' and ks_model_obj._fields[field_import].type == 'char':
                                if field_import not in model_data:
                                    raise UserError(_("The field '%s' is missing in the provided data." % field_import))
                                ks_model_write_val[field_import] = model_data.get(field_import) + '_copy'
                            else:
                                ks_model_write_val[field_import] = model_data.get(field_import)

                        elif ks_model_obj._fields[field_import].type == 'many2one':
                            # need to check if field_import is available or not.
                            ks_value = model_data[field_import] if model_data.get(field_import) else False
                            ks_model_write_val[field_import] = self.ks_valid_many_to_one_data(
                                ks_model_obj._fields[field_import].comodel_name, ks_value)
                        elif ks_model_obj._fields[field_import].type in ['datetime', 'date']:
                            if model_data.get(field_import):
                                ks_model_write_val[field_import] = fields.Datetime.from_string(datetime.datetime.strftime(datetime.datetime.strptime((str(dateutil.parser.parse(model_data[field_import])).split("+")[0]).split('.')[0], '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))
                        elif ks_model_obj._fields[field_import].type == 'boolean':
                            ks_model_write_val[field_import] = bool(model_data.get(field_import))
                        else:
                            _logger.warning(
                                _("%s field type can't imported since it is not supported" %
                                  ks_model_obj._fields[
                                      field_import].type))
                    try:
                        ks_model_obj.create(ks_model_write_val)
                    except Exception as e:
                        if e.args and e.args[0]:
                            error_msg = e.args[0]
                        else:
                            error_msg = _('Some required fields are not available in the file.')
                        raise UserError(error_msg)
        else:
            wrong_file_msg = _('Required data not found in the json file, please upload correct json file.')
            _logger.info(wrong_file_msg)
            raise UserError(wrong_file_msg)

    def ks_valid_many_to_one_data(self, comodel, value):
        """
        Function to check if data is available then return its id otherwise return false.
        :param comodel:
        :param value:
        :return:
        """

        if not value:
            return False
        # Create domain to search the records.
        if type(value) is list:
            if len(value) > 0:
                ks_domain = [('id', '=', value[0])]
            else:
                return False
        else:
            ks_id = int(value.split(',')[0])
            ks_domain = [('id', '=', ks_id)]

        ks_res = self.env[comodel].sudo().search(ks_domain, limit=1)

        if ks_res:
            return ks_res.id
        else:
            return False
