import {ReportAction} from "@web/webclient/actions/reports/report_action";
import {patch} from "@web/core/utils/patch";
import {useEnrichWithActionLinks} from "./report.esm";

const MODULE_NAME = "account_financial_report";

patch(ReportAction.prototype, {
    setup() {
        super.setup(...arguments);
        this.accountFinancialReportName = this._getReportName();
        this.isAccountFinancialReport = this.accountFinancialReportName?.startsWith(
            `${MODULE_NAME}.`
        );
        useEnrichWithActionLinks(this.iframe);
    },

    print() {
        if (!this.isAccountFinancialReport) {
            return super.print(...arguments);
        }
        return this._printXlsxReport();
    },

    export() {
        if (!this.isAccountFinancialReport) {
            return;
        }
        return this._printXlsxReport();
    },

    _printXlsxReport() {
        const reportName = this.accountFinancialReportName || this._getReportName();
        if (!reportName) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.report",
            report_type: "xlsx",
            report_name: this._get_xlsx_name(reportName),
            report_file: this._get_xlsx_name(this.props.report_file || reportName),
            data: this.props.data || {},
            context: this.props.context || {},
            display_name: this.title,
        });
    },

    _getReportName() {
        if (typeof this.props.report_name === "string") {
            return this.props.report_name;
        }
        if (typeof this.props.report_url !== "string") {
            return undefined;
        }
        const match = this.props.report_url.match(/\/report\/[^/]+\/([^/?#]+)/);
        return match ? decodeURIComponent(match[1]) : undefined;
    },

    /**
     * @param {String} str
     * @returns {String}
     */
    _get_xlsx_name(str) {
        if (typeof str !== "string") {
            return str;
        }
        const parts = str.split(".");
        return `a_f_r.report_${parts[parts.length - 1]}_xlsx`;
    },
});
