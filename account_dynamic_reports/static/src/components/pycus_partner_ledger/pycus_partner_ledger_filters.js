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

export class PycusPartnerLedgerFilters extends PycusFilters {
    setup(){
        super.setup();
        this.state.defaultPartnerTagsValues = this.props.filterValues.defaultPartnerTagsValues;
        this.partner_tag_ids = [];
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
        this.state.reconciled = {
                choices: [],
                selectedValue: {}
            }
        this.state.account_type = {
                choices: [],
                selectedValue: {}
            }

        onMounted(() => {
            this.state.target_moves = this.props.filterValues.target_moves
            this.state.include_initial_balance = this.props.filterValues.include_initial_balance
            this.state.display_accounts = this.props.filterValues.display_accounts
            this.state.reconciled = this.props.filterValues.reconciled
            this.state.account_type = this.props.filterValues.account_type
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

        this.handleReconciledSelect = async (val) => {
            this.state.reconciled.selectedValue.value = val
            this.props.updateValues(this)
        }

        this.handleAccountTypeSelect = async (val) => {
            this.state.account_type.selectedValue.value = val
            this.props.updateValues(this)
        }
    }

    selectedPartnerTags(vals) {
        this.state.partner_category_ids = vals
        this.props.updateValues(this)
    }
}
PycusPartnerLedgerFilters.template = 'account_dynamic_reports.PycusPartnerLedgerFilters';