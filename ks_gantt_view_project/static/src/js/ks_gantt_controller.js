/** @odoo-module **/

import {KsGanttController} from "@ks_gantt_view_base/js/ks_gantt_controller_new";
import { patch } from "@web/core/utils/patch";
import { download } from "@web/core/network/download";
import { BlockUI } from "@web/core/ui/block_ui";

patch(KsGanttController.prototype,{
    async _ksExportReport(ev){
        var ks_report_type = $(ev.currentTarget).attr("report_type");
        if (ks_report_type == "excel" && (this.model.modelName == "project.task" || this.model.modelName == "project.project")){
            const blockUI = new BlockUI();
            await download({
                 url: "/web/ksgantt/export/xlsx/",
                data: {
                    project_id: this.model.context.default_project_id
                    ? this.model.context.default_project_id
                    : false,
                },
                complete: ()=> unblockUI,
                error: (error) => this.call("crash_manager", "rpc_error", error),
            })
        }else{
            super._ksExportReport(...arguments);
        }

    }

})
