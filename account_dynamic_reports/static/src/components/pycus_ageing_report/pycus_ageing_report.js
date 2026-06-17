/** @odoo-module **/

import { registry } from '@web/core/registry';
import { loadJS } from "@web/core/assets"
const { Component, useState, useRef, onMounted, onWillStart, useChildSubEnv} = owl
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { serializeDate, deserializeDate } from "@web/core/l10n/dates";
const { DateTime } = luxon;
import { useBus, useService,  } from "@web/core/utils/hooks";
import { PycusAgeingReportLine } from "../pycus_ageing_report/pycus_ageing_report_line";
import { PycusAgeingReportFilters } from "../pycus_ageing_report/pycus_ageing_report_filters";

export class PycusAgeingReport extends Component {
    setup(){
        this.ormService = useService("orm");
        this.action = useService("action");
        this.state = useState({
            activeId: 0,
            filterValues: {},
            ageing_lines: [],
            ageing_bucket: {},
            showLoader: true
        });

        onWillStart(async ()=> {
            await this.createGlWizard();
        })

        onMounted(() => {
            this.apply_filters();
            this.state.isFilterVisible = false;
        })

        this.createGlWizard = async () => {
            try {
                let glWizardId = 0
                if (this.props.action.context.active_id){
                    glWizardId = this.props.action.context.active_id
                }else{
                    glWizardId = await this.ormService.call('ins.partner.ageing', 'create', [{}]);
                }
                this.state.activeId = glWizardId
                this.readGlWizard(glWizardId);
            } catch (error) {
                console.log("Error on GL Creation", error)
            }
        };

        this.readGlWizard = async () => {
              try {
                const record = await this.ormService.call('ins.partner.ageing', 'prepare_values_for_component', [this.state.activeId]); // Choose relevant fields
                this.state.filterValues = record
              } catch (error) {
                console.error("Error reading record:", error);
              }
        };

        this.apply_filters = async () => {
            this.showSpinner()
            //update_values_from_component
            this.state.isFilterVisible = false;
            const filter_values = this.state.filterValues
            try {
                let ageing_data = await this.ormService.call('ins.partner.ageing', 'update_values_from_component', [this.state.activeId, filter_values]); // Choose relevant fields
                this.state.ageing_bucket = ageing_data[0]
                this.state.ageing_lines = ageing_data[1]
                this.readGlWizard()
              } catch (error) {
                console.error("Error reading record:", error);
              }
            this.hideSpinner()

        }

    }

    toggleVisibility() {
        this.state.isFilterVisible = !this.state.isFilterVisible;
    }

    getFilterValues(val){
        this.state.filterValues = val.state
    }

    async downloadXlsx($this) {
        const action = await this.ormService.call('ins.partner.ageing', 'action_xlsx', [this.state.activeId]);
        this.action.doAction(action);
    }

    async downloadPdf($this) {
        const action = await this.ormService.call('ins.partner.ageing', 'action_pdf', [this.state.activeId]);
        this.action.doAction(action);
    }

    showSpinner() {
        this.state.showLoader = true;
    }

    hideSpinner() {
       this.state.showLoader = false;
    }


}
PycusAgeingReport.template = 'account_dynamic_reports.ageingReport';
PycusAgeingReport.components = {
    Dropdown, DropdownItem, DatePicker: DateTimePicker, DateTimeInput,
    PycusAgeingReportLine,
    PycusAgeingReportFilters};
registry.category('actions').add('account_dynamic_reports.action_ageing_report', PycusAgeingReport)