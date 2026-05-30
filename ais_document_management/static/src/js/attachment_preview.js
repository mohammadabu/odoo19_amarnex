/** @odoo-module **/

import { _t } from "@web/core/l10n/translation"
import { BinaryField } from "@web/views/fields/binary/binary_field"
import { patch } from "@web/core/utils/patch"
import { useService } from "@web/core/utils/hooks"
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook"

patch(BinaryField.prototype, {
  setup(...args) {
    super.setup(...args)
    this.mailStore = useService("mail.store")
    this.documentViewer = useFileViewer()
    this.notificationService = useService("notification")
  },

  /**
   * Handle document preview button click
   * Opens file viewer for supported formats (images, videos, PDFs, text)
   */
  async _onDocumentPreview(ev) {
    ev.preventDefault()
    ev.stopPropagation()

    const currentRecord = this.props.record
    const fileType = currentRecord.data.mimetype

    // Check if file type is supported for preview
    const isSupportedFormat = fileType && fileType.match("(image|video|application/pdf|text)")

    if (isSupportedFormat) {
      // Create attachment object for file viewer
      const documentAttachment = this.mailStore["ir.attachment"].insert({
        id: currentRecord.resId,
        filename: currentRecord.data.name,
        name: currentRecord.data.name,
        mimetype: currentRecord.data.mimetype,
      })

      // Open in file viewer
      this.documentViewer.open(documentAttachment)
    } else {
      // Show error notification for unsupported formats
      this.notificationService.add(_t("Preview not available for this file format."), {
        type: "warning",
      })
    }
  },
})
