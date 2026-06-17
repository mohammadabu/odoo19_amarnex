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
const { DateTime } = luxon;
import { useService,  } from "@web/core/utils/hooks";
import { PycusFilters } from "../pycus_filters/pycus_filters";

export class PycusAgeingReportFilters extends PycusFilters {
    setup(){
        super.setup();
        this.state.defaultPartnerTagsValues = this.props.filterValues.defaultPartnerTagsValues;
        this.state.as_on_date = luxon.DateTime.now();
        this.state.partner_category_ids = [];
        this.state.bucket_1 = this.props.filterValues.bucket_1;
        this.state.bucket_2 = this.props.filterValues.bucket_2;
        this.state.bucket_3 = this.props.filterValues.bucket_3;
        this.state.bucket_4 = this.props.filterValues.bucket_4;
        this.state.bucket_5 = this.props.filterValues.bucket_5;

        this.state.report_type = {
            choices: [],
            selectedValue: {}
        };
        this.state.partner_type = {
            choices: [],
            selectedValue: {}
        };
        this.state.include_details = {
            choices: [],
            selectedValue: {}
        };

        onMounted(() => {
            this.state.report_type = this.props.filterValues.report_type
            this.state.partner_type = this.props.filterValues.partner_type
            this.state.include_details = this.props.filterValues.include_details
            this.state.as_on_date = luxon.DateTime.fromISO(this.props.filterValues.as_on_date)
            this.state.partner_category_ids = this.props.filterValues.partner_category_ids
            this.state.partner_ids = this.props.filterValues.partner_ids
            this.state.account_ids = this.props.filterValues.account_ids
            this.state.journal_ids = this.props.filterValues.journal_ids
            this.state.defaultPartnerTagsValues = this.props.filterValues.defaultPartnerTagsValues
        });

        this.handleReportTypeSelect = async (val) => {
            this.state.report_type.selectedValue.value = val
            this.props.updateValues(this)
        }

        this.handlePartnerTypeSelect = async (val) => {
            this.state.partner_type.selectedValue.value = val
            this.props.updateValues(this)
        }

        this.handleIncludeDetailsSelect = async (val) => {
            this.state.include_details.selectedValue.value = val
            this.props.updateValues(this)
        }
    }

    onAsOnDateChanged(asOnDate) {
        this.state.as_on_date = asOnDate
        this.props.updateValues(this)
    }

    onBucket1Changed(bucket) {
        let value = bucket.target.value
        value = value.replace(/\D/g, '')
        this.state.bucket_1 = parseInt(value)
        this.props.updateValues(this)
    }

    onBucket2Changed(bucket) {
        let value = bucket.target.value
        value = value.replace(/\D/g, '')
        this.state.bucket_2 = parseInt(value)
        this.props.updateValues(this)
    }

    onBucket3Changed(bucket) {
        let value = bucket.target.value
        value = value.replace(/\D/g, '')
        this.state.bucket_3 = parseInt(value)
        this.props.updateValues(this)
    }

    onBucket4Changed(bucket) {
        let value = bucket.target.value
        value = value.replace(/\D/g, '')
        this.state.bucket_4 = parseInt(value)
        this.props.updateValues(this)
    }

    onBucket5Changed(bucket) {
        let value = bucket.target.value
        value = value.replace(/\D/g, '')
        this.state.bucket_5 = parseInt(value)
        this.props.updateValues(this)
    }

    selectedPartnerTags(vals) {
        this.state.partner_category_ids = vals
        this.props.updateValues(this)
    }
}
PycusAgeingReportFilters.template = 'account_dynamic_reports.PycusAgeingReportFilters';