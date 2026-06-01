/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { kanbanView } from "@web/views/kanban/kanban_view";

//
//export class CustomButton extends KanbanController {
//        setup() {
//        super.setup();
//    }
//}
export const kanbanViewinherit = {
    ...kanbanView,
    buttonTemplate: "ks_gantt_view_base.custom.button",
}


//CustomButton.template="ks_gantt_view_base.custom.button"
registry.category("views").add("gantt", kanbanViewinherit);