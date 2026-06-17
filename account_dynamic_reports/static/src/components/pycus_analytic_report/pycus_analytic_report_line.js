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
import { PycusAnalyticReportFilters } from "../pycus_general_ledger/pycus_general_ledger_filters";

export class PycusAnalyticReportLine extends Component {
    setup(){
        this.action = useService("action");
        this.ormService = useService("orm");
        this.state = useState({
            account_line: this.props.gl_line,
            filterValues: this.props.filterValues,
            activeId: this.props.activeId,
            currentPage: 1,
            rowsPerPage: 2000,
            subLinesVisibility: false,
            viewGlVisibility: false,
            active_ids: this.props.gl_line.id_list ? this.props.gl_line.id_list.slice(0, 2000) : [], // To hold current active ids for pagination
            data: [], //Holds move lines data [{}],
        })

        onMounted(() => {
            this.state.account_line.length = 0
            this.state.account_line = this.props.gl_line
        })

        this.onGlLineClicked = async (ev) => {
            this.state.subLinesVisibility = !this.state.subLinesVisibility
            this.fetchMoveLines()
        }

        this.goToPage = async (pageNumber) => {
            this.state.currentPage = pageNumber;
            const rowsPerPage = this.state.rowsPerPage; // assuming you have this variable defined
            const startIndex = (pageNumber - 1) * rowsPerPage;
            const endIndex = pageNumber * rowsPerPage;
            this.state.active_ids = this.state.account_line.id_list.slice(startIndex, endIndex);
            this.fetchMoveLines()
        }

        this.fetchMoveLines = async () => {
            if(this.state.active_ids.length > 0){
                this.state.data = await this.ormService.call(
                    'ins.analytic.report', 'prepare_detailed_lines',
                    [parseInt(this.state.activeId), this.state.active_ids, this.state.account_line.account_id]
                    );
            }
        }

    }

    renderPageNumbers() {
        const totalPages = Math.ceil(this.state.account_line.size / this.state.rowsPerPage);
        const pageNumbers = Array.from({ length: totalPages }, (_, i) => i + 1);
        return pageNumbers
    }

    handleHover(ev, st) {
        this.state.viewGlVisibility = st
    }

    viewGlLinesAction(ev, id_list) {
        ev.preventDefault();
        return this.action.doAction({
            name: _t("Account Analytic Lines"),
            type: "ir.actions.act_window",
            res_model: "account.analytic.line",
            domain: [["id", "in", id_list]],
            views: [[false, "list"]],
            view_mode: "list",
            target: "new",
        });
    }

    viewJournalEnryAction(ev, rec_id) {
        ev.preventDefault();
        return this.action.doAction({
            name: _t("Journal Entry"),
            type: "ir.actions.act_window",
            res_model: "account.move",
            res_id: rec_id,
            domain: [["id", "=", rec_id]],
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
        });
    }

    formatFieldMonetary(value) {
        if(!value){
            value = 0
        }
        return formatMonetary(value, { currencyId: this.state.account_line.currency_id })
    }

    formatDate(date) {
        return formatDate(parseDate(date));
    }
}
PycusAnalyticReportLine.components = { }
PycusAnalyticReportLine.template = 'account_dynamic_reports.analyticReportLine';