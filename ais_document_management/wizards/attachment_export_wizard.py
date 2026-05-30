# -*- coding: utf-8 -*-

from datetime import datetime
import base64
import time
import io
import zipfile

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AttachmentExportWizard(models.TransientModel):
    _name = "attachment.export.wizard"
    _description = 'Export Attachments as ZIP'

    @api.model
    def _default_filename(self):
        return "%s_%s" % (
            _("files_export"), 
            datetime.now().strftime('%Y%m%d%H%M') + '.zip'
        )

    filename = fields.Char(
        'Filename', 
        default=_default_filename, 
        required=True, 
        readonly=True
    )
    zip_file = fields.Binary("ZIP File")

    def action_download_zip(self):
        """Export selected attachments as ZIP file"""
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise UserError(_("No attachments selected for export."))
            
        file_records = self.env['ir.attachment'].browse(active_ids)
        
        if not file_records:
            raise UserError(_("No valid attachments found."))

        memory_file = io.BytesIO()
        zip_archive = zipfile.ZipFile(memory_file, mode="w")
        
        filename_count = {}
        exported_count = 0
        
        for file_record in file_records:
            if file_record.datas:
                try:
                    # Get original filename
                    original_name = file_record.name or 'unnamed_file'
                    
                    # Handle duplicate filenames by adding counter
                    if original_name in filename_count:
                        filename_count[original_name] += 1
                        # Split name and extension
                        if '.' in original_name:
                            name_parts = original_name.rsplit('.', 1)
                            unique_name = f"{name_parts[0]}_{filename_count[original_name]}.{name_parts[1]}"
                        else:
                            unique_name = f"{original_name}_{filename_count[original_name]}"
                    else:
                        filename_count[original_name] = 0
                        unique_name = original_name
                    
                    zip_archive.writestr(
                        unique_name, 
                        base64.b64decode(file_record.datas)
                    )
                    exported_count += 1
                except Exception as e:
                    continue

        zip_archive.close()
        
        if exported_count == 0:
            raise UserError(_("No files with content found to export."))
            
        self.write({'zip_file': base64.b64encode(memory_file.getvalue())})
        
        filename = self.filename
        action = {
            'name': filename,
            'type': 'ir.actions.act_url',
            'url': "/web/content/?model=" + self._name + "&id=" + str(self.id) + 
                   "&field=zip_file&download=true&filename=" + filename,
            'close': True,
        }
        return action
