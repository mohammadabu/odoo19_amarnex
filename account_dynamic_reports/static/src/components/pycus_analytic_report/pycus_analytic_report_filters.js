/** @odoo-module **/

import { registry } from '@web/core/registry';
import { loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { parseDate, formatDate } from "@web/core/l10n/dates";
import { formatFloat, formatFloatTime, formatMonetary } from "@web/views/fields/formatters";
import {
    Component,
    EventBus,
    onWillStart,
    onMounted,
    status,
    useEffect,
    useExternalListener,
    useRef,
    useState,
    useChildSubEnv,
} from "@odoo/owl";
import { useService,  } from "@web/core/utils/hooks";
import { PycusFilters } from "../pycus_filters/pycus_filters";

export class PycusAnalyticReportFilters extends PycusFilters {
    setup(){
        super.setup();
        this.state.defaultAnalyticValues = this.props.filterValues.defaultAnalyticValues;
        this.state.defaultPlanValues = this.props.filterValues.defaultPlanValues;
        this.analytic_ids = [];
        this.plan_ids = [];

        this.state.include_details = {
            choices: [],
            selectedValue: {}
        };

        onMounted(() => {
            this.state.include_details = this.props.filterValues.include_details
        });

        this.handleIncludeDetailsSelect = async (val) => {
            this.state.include_details.selectedValue.value = val
            this.props.updateValues(this)
        }
    }

    selectedAnalytics(vals) {
        this.state.analytic_ids = vals
        this.props.updateValues(this)
    }

    selectedPlans(vals) {
        this.state.plan_ids = vals
        this.props.updateValues(this)
    }
}
PycusAnalyticReportFilters.template = 'account_dynamic_reports.PycusAnalyticReportFilters';