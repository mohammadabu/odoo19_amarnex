/** @odoo-module */

import { Field } from "@web/views/fields/field";
import { visitXML } from "@web/core/utils/xml";
import { stringToOrderBy } from "@web/search/utils/order_by";
import { archParseBoolean, getActiveActions, getDecoration, processButton } from "@web/views/utils";
import { encodeObjectForTemplate } from "@web/views/view_compiler";
import { combineModifiers } from "@web/model/relational_model/utils";
import { Widget } from "@web/views/widgets/widget";
import { _t } from "@web/core/l10n/translation";

const ks_get_gantt_no_field_attribute = [
        "ks_task_link_info",
        "ks_gantt_config",
        "ks_context",
        "ks_export_field",
];

export class ksGanttArchParser {
    parse(arch) {
        let ksRootNodeinfo;
        const ks_requiredFields = [];
        let popoverTemplate = null;

        visitXML(arch, (node) => {
            switch (node.tagName) {
                case "ks_gantt": {
                    ksRootNodeinfo = getInfoFromRootNode(node);
                    break;
                }
                case "field": {
                    const fieldName = node.getAttribute("name");
                     ks_requiredFields.push(fieldName);
                    break;
                }
                case "templates": {
                    popoverTemplate = node.querySelector("[t-name=gantt-popover]") || null;
                    if (popoverTemplate) {
                        popoverTemplate.removeAttribute("t-name");
                    }
                }
            }
        });

        return {
            ...ksRootNodeinfo,
            ks_requiredFields,
            popoverTemplate,
        };

    }
}
function getInfoFromRootNode(rootNode) {
    const attrs = {};
    for (const { name, value } of rootNode.attributes) {
        attrs[name] = value;
    }

    var ks_gantt_no_field = [...ks_get_gantt_no_field_attribute];
    var info = {};
    ks_gantt_no_field.forEach(
        function (field_info) {
          if (attrs[field_info]) {
            try {
              info[field_info] = JSON.parse(attrs[field_info]);

              if (field_info == "ks_context") {
                let ks_context_info = JSON.parse(attrs[field_info]);
                let ks_new_context = Object.assign(
                  {},
                  ks_context_info
                );
                info['ks_context'] = ks_new_context;
              }
              if (field_info == "ks_export_field") {
                info[field_info] = JSON.parse(attrs[field_info]);
              }
            } catch (err) {
              console.error(err);
            }
            delete attrs[field_info];
          }
        }
      );

    const { create: canCreate, delete: canDelete, edit: canEdit } = getActiveActions(rootNode);
    var ks_hide_links = attrs && attrs.ks_hide_links == "true" ? true : false;
      // If links is visible but task link data is not available then hide the link.
    if (!ks_hide_links && !attrs.ks_task_link) {
        ks_hide_links = true;
    }
    var ks_formViewId =  attrs.form_view_id ? parseInt(attrs.form_view_id, 10) : false;

    return{
        ks_isCreate:canCreate,
        canDelete,
        ks_isEdit:canEdit,
        createAction: attrs.on_create || null,
        ks_defaultGroupBy: attrs.default_group_by ? attrs.default_group_by.split(",") : [],
        ks_no_drag:attrs.ks_no_drag == "true" ? true : false,
        ks_hide_links : ks_hide_links,
        string: attrs.string || _t("Gantt View").toString(),
        ks_gantt_arch : attrs,
        ks_dialogViews : [[ks_formViewId, "form"]],
        date_deadline:attrs.date_deadline,
        name:attrs.name,
        info:info,
        formViewId: attrs.form_view_id ? parseInt(attrs.form_view_id, 10) : false,
        offset: attrs.offset,
        pagerLimit: attrs.groups_limit ? parseInt(attrs.groups_limit, 10) : null,
    };
}
