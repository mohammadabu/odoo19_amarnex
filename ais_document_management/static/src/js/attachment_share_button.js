/** @odoo-module */

import { FormRenderer } from "@web/views/form/form_renderer"
import { patch } from "@web/core/utils/patch"
import { useService } from "@web/core/utils/hooks"
import { _t } from "@web/core/l10n/translation"

import { onMounted, onWillUnmount, onPatched } from "@odoo/owl";

patch(FormRenderer.prototype, {
  setup(...args) {
    super.setup(...args)
    this.actionService = useService("action")
    onPatched(this._addShareButtonToForm.bind(this))
    onMounted(this._addShareButtonToForm.bind(this))

    onWillUnmount(() => {
      const btn = document.querySelector(".ais_document_share_container")
      if (btn) {
        btn.remove()
      }
    })
  },

  /**
   * Render share button on attachment form views
   * Only shows when record exists and has file data
   */
  _addShareButtonToForm() {
    if (this.props.record.resModel !== "ir.attachment") {
      return
    }

    // Remove existing button to prevent duplicates
    const existingButton = document.querySelector(".ais_document_share_container")
    if (existingButton) {
      existingButton.remove()
    }

    // Create share button container
    const buttonContainer = document.createElement("div")
    buttonContainer.classList.add("ais_document_share_container")
    buttonContainer.style.cssText = "position: fixed; top: 200px; right: 20px; z-index: 1000;"

    // Create share button
    const shareBtn = document.createElement("button")
    shareBtn.classList.add("btn", "btn-primary")
    shareBtn.style.cssText = "display: flex; align-items: center; gap: 8px; padding: 8px 16px;"

    // Add share icon
    const shareIconEl = document.createElement("i")
    shareIconEl.classList.add("fa", "fa-share-alt")

    // Add button text
    const buttonText = document.createElement("span")
    buttonText.textContent = _t("Share")

    shareBtn.appendChild(shareIconEl)
    shareBtn.appendChild(buttonText)
    buttonContainer.appendChild(shareBtn)

    // Attach click handler
    buttonContainer.addEventListener("click", this._handleShareButtonClick.bind(this))

    // Add to form if record exists and has file data
    const formSheet = document.querySelector(".o_form_sheet")
    if (formSheet && this.props.record.resId && this.props.record.data.datas) {
      document.body.appendChild(buttonContainer)
    }
  },

  /**
   * Handle share button click - opens share wizard
   */
  _handleShareButtonClick: function (ev) {
    ev.stopPropagation()
    ev.preventDefault()

    const currentRecord = this.props.record

    // Open share wizard dialog
    this.actionService.doAction({
      type: "ir.actions.act_window",
      name: _t("Share Document"),
      res_model: "attachment.share.wizard",
      views: [[false, "form"]],
      view_mode: "form",
      target: "new",
      context: {
        active_model: currentRecord.resModel || false,
        default_res_id: currentRecord.resId || false,
        active_id: currentRecord.resId || false,
      },
    })
  },
})

export default FormRenderer
