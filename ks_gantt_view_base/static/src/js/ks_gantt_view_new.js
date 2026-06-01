/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
//import { scrollSymbol } from "@web/webclient/actions/action_hook";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { KsGanttController } from "@ks_gantt_view_base/js/ks_gantt_controller_new";
import { ksGanttArchParser } from "@ks_gantt_view_base/js/Gantt_arch_parser";
import { ksGanttModel } from "@ks_gantt_view_base/js/ks_gantt_model_new";
import { ksGanttRenderer } from "@ks_gantt_view_base/js/ks_gantt_renderer_new"

//
const viewRegistry = registry.category("views");

export const KsGanttView = {
    type: "ks_gantt",
    display_name: _t("Gantt View"),
    icon: "fa fa-tasks",
    multiRecord: true,
    Controller:  KsGanttController,
    Renderer: ksGanttRenderer,
    Model: ksGanttModel,
    ArchParser: ksGanttArchParser,
    searchMenuTypes: ["filter", "groupBy", "favorite"],
    buttonTemplate: "ks_gantt_view_base.GanttView.Buttons",

    props: (genericProps, view, config) => {
        const modelParams = {};
//        let scrollPosition;
//        if (genericProps.state) {
//            scrollPosition = genericProps.state[scrollSymbol];
//            modelParams.metaData = genericProps.state.metaData;
//        } else {
            const { arch, fields, resModel } = genericProps;
            const parser = new view.ArchParser();
            const archInfo = parser.parse(arch);

            let formViewId = archInfo?.formViewId;
            if (!formViewId) {
                const formView = config.views.find((v) => v[1] === "form");
                if (formView) {
                    formViewId = formView[0];
                }
            }

            modelParams.metaData = {
                ...archInfo,
                fields,
                resModel,
                formViewId,
            };


        return {
            ...genericProps,
            modelParams,
            Model: view.Model,
            Renderer: view.Renderer,
            buttonTemplate: view.buttonTemplate,
//            scrollPosition,
        };
    },
};

viewRegistry.add("ks_gantt", KsGanttView);
