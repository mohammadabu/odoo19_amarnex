/** @odoo-module **/

import { registry } from '@web/core/registry';
import { loadJS } from "@web/core/assets"
import { SelectMenu } from "@web/core/select_menu/select_menu";
import { useBus, useService,  } from "@web/core/utils/hooks";
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

export class PycusDropdown extends Component {

    static props = {
        updateToParent: { type: Function, optional: true },
        tableName: { optional: true },
        multiSelect: { type: String, optional: true },
        defaultValues: { type: Array, optional: true },
        placeholder: { type: String, optional: true },
        class: { type: String, optional: true },
    };

    setup() {
        this.ormService = useService("orm");

        this.state = useState({
            choices: [],
            selectedValue: { value: []},
            selectedItemsWithLabels: [],
            defaultValues: [], // list of {'value': 2, 'label': 'Xyz'}

            placeholder: this.props.placeholder,
            tableName: this.props.tableName,
            class: this.props.class,
        })

        onWillStart(async () => {
            // Fetch from Table
            await this.fetchOptions();

            // Set default state from props
            if (this.props.defaultValues){
                this.state.selectedValue = { value: this.props.defaultValues.map(obj => obj.value)}
                this.props.defaultValues.forEach(item => {
                    this.state.selectedItemsWithLabels.push({ value: item.value, label: item.label})
                })
            }

        });

        onMounted(() => {

        });

        this.handleSearch = async (term) => {
          await this.fetchOptions(term);
        }

        this.fetchOptions = async (term = '') => {
            const options = await this.ormService.call(this.props.tableName, "name_search", [], {
                name: term,
                //args: [],
                operator: "ilike",
                limit: 80,
                context: {},
            });

            this.state.choices = options.map(option => ({
                value: option[0], // Adjust based on your data structure
                label: option[1],
            }));

            this.state.selectedItemsWithLabels.forEach(item => {
                // Check if the value is not already in options array
                if (!this.state.choices.find(option => option.value === item.value)) {
                    this.state.choices.push(item);
                }
            });
        };

        this.handleSelect = async (val) => {
            try {
                if (Array.isArray(val)) { // Handle list case
                    this.state.selectedItemsWithLabels = val.map((value) => {
                        const choice = this.state.choices.find((item) => item.value === value);
                        return choice ? { value, label: choice.label } : null;
                    }).filter(Boolean);

                    this.state.selectedValue.value = val
                } else { // Handle single ID case
                    this.state.selectedItemsWithLabels = [
                        {value: val, label: 'aaaaa' }
                    ]

                    this.state.selectedValue.value = val; // Ensure it's a list
                }
                // Trigger event to parent to notify
                this.props.updateToParent(this.state.selectedItemsWithLabels)
                this.handleSearch('')
            } catch (error) {
                console.error("Error in handleSelect:", error);
                // Handle error appropriately, e.g., display a user-friendly message
            }
        }
    }

}
// Define the template for the dropdown component
//PycusDropdown.props = { updateToParent: Function, tableName: '', multiSelect: true, defaultValues: '', placeholder: '', class: ''};
PycusDropdown.template = 'account_dynamic_reports.PycusDropdown';
PycusDropdown.components = { SelectMenu };