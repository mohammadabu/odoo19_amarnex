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
import { PycusGeneralLedgerLine } from "../pycus_general_ledger/pycus_general_ledger_line";
import { PycusGeneralLedgerFilters } from "../pycus_general_ledger/pycus_general_ledger_filters";

export class PycusGeneralLedger extends Component {
    setup(){
        this.ormService = useService("orm");
        this.action = useService("action");
        this.state = useState({
            activeId: 0,
            filterValues: {},
            gl_lines: [],
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
                    glWizardId = await this.ormService.call('ins.general.ledger', 'create', [{}]);
                }
                this.state.activeId = glWizardId
                this.readGlWizard(glWizardId);
            } catch (error) {
                console.log("Error on GL Creation", error)
            }
        };

        this.readGlWizard = async () => {
              try {
                const record = await this.ormService.call('ins.general.ledger', 'prepare_values_for_component', [this.state.activeId]); // Choose relevant fields
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
                const gl_lines = await this.ormService.call('ins.general.ledger', 'update_values_from_component', [this.state.activeId, filter_values]); // Choose relevant fields
                this.state.gl_lines = gl_lines
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
        const action = await this.ormService.call('ins.general.ledger', 'action_xlsx', [this.state.activeId]);
        this.action.doAction(action);
    }

    async downloadPdf($this) {
        const action = await this.ormService.call('ins.general.ledger', 'action_pdf', [this.state.activeId]);
        this.action.doAction(action);
    }

    showSpinner() {
        this.state.showLoader = true;
    }

    hideSpinner() {
       this.state.showLoader = false;
    }


}
PycusGeneralLedger.template = 'account_dynamic_reports.generalLedger';
PycusGeneralLedger.components = {
    Dropdown, DropdownItem, DatePicker: DateTimePicker, DateTimeInput,
    PycusGeneralLedgerLine, PycusGeneralLedgerFilters};
registry.category('actions').add('account_dynamic_reports.action_general_ledger', PycusGeneralLedger)