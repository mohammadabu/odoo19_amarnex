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

export class PycusGeneralLedgerFilters extends PycusFilters {
    setup(){
        super.setup();
        //this.state.defaultCompanyValues = this.props.filterValues.defaultCompanyValues;
        this.state.include_initial_balance = {
                choices: [],
                selectedValue: {}
            };
        this.state.target_moves = {
                choices: [],
                selectedValue: {}
            };
        this.state.display_accounts = {
                choices: [],
                selectedValue: {}
            }

        onMounted(() => {
            this.state.target_moves = this.props.filterValues.target_moves
            this.state.include_initial_balance = this.props.filterValues.include_initial_balance
            this.state.display_accounts = this.props.filterValues.display_accounts
        });

        this.handleTargetMovesSelect = async (val) => {
            this.state.target_moves.selectedValue.value = val
            this.props.updateValues(this)
        }

        this.handleInitialBalanceSelect = async (val) => {
            this.state.include_initial_balance.selectedValue.value = val
            this.props.updateValues(this)
        }

        this.handleDisplayAccountsSelect = async (val) => {
            this.state.display_accounts.selectedValue.value = val
            this.props.updateValues(this)
        }
    }

//    selectedCompanies(vals) {
//        this.state.company_ids = vals
//        this.props.updateValues(this)
//    }
}
PycusGeneralLedgerFilters.template = 'account_dynamic_reports.PycusGeneralLedgerFilters';