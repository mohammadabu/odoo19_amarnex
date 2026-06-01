/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, onWillUnmount, useEffect, useRef,onMounted, onPatched} from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { Layout } from "@web/search/layout";
import { standardViewProps } from "@web/views/standard_view_props";
import { useModelWithSampleData } from "@web/model/model";
import { usePager } from "@web/search/pager_hook";
import { useService } from "@web/core/utils/hooks";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSearchBarToggler } from "@web/search/search_bar/search_bar_toggler";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { download } from "@web/core/network/download";
import { BlockUI } from "@web/core/ui/block_ui";

import { useSetupView } from "@web/views/view_hook";

export class KsGanttController extends Component {
    static components = {
        CogMenu,
        Dropdown,
        DropdownItem,
        Layout,
        SearchBar,
    };
    static props = {
        ...standardViewProps,
        Model: Function,
        Renderer: Function,
        buttonTemplate: String,
        modelParams: Object,
        scrollPosition: { type: Object, optional: true },
    };
    static template = "ks_gantt_view_base.GanttController";

    setup() {
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.orm = useService("orm");
        this.export_type = [{type:'excel',value:'Excel'},{type:'pdf',value:'PDF'},{type:'png',value:'PNG'},{type:'json',value:'JSON'},{type:'ms-project',value:'MSProject (XML)'},{type:'primaverap6',value:'PrimaveraP6'},{type:'ical',value:'iCal'}]
        this.model = useModelWithSampleData(this.props.Model, this.props.modelParams);
        this.ks_export_field = this.model.metaData.info.ks_export_field

        this.searchBarToggler = useSearchBarToggler();
        gantt.showLightbox = (id)=>{
            this.openDialog({resId:id})
        }
        gantt.deleteTask = (id)=> {
        if (this.model.modelName == gantt.ks_model_name) {
          this._KsDeleteTask(parseInt(id));
        }
      }

      gantt.$click.buttons.delete = (id)=> {
        if (this.model.modelName == gantt.ks_model_name) {
          this._KsOnDeleteRecord(id);
        }
      }

    }


    get className() {
        if (this.env.isSmall) {
            const classList = (this.props.className || "").split(" ");
            classList.push("o_action_delegate_scroll");
            return classList.join(" ");
        }
        return this.props.className;
    }

    get showNoContentHelp() {
        return this.model.useSampleModel;
    }

    async _ksExportReport(ev) {
      ev.preventDefault();
      var ks_report_type = $(ev.currentTarget).attr("report_type");
      var ks_file_name =
        "gantt-chart-" +
        new Date()
          .toLocaleString()
          .replace(new RegExp("/", "g"), "-")
          .replace(new RegExp(", ", "g"), "-")
          .replace(new RegExp(":", "g"), "-");

      if (ks_report_type == "excel" && this.ks_export_field) {
        const blockUI = new BlockUI();
        await download({
          url: "/web/ksganttbase/export/xlsx",
          data: {
            ks_model_name: this.model.modelName,
            ks_fields: JSON.stringify(this.ks_export_field),
            ks_domain: JSON.stringify(this.model.domain),
            ks_context: JSON.stringify(this.model.context),
          },
          complete: () => unblockUI,
          error: (error) => this.call("crash_manager", "rpc_error", error),
        });
      } else if (ks_report_type == "excel") {
        ks_file_name += ".xlsx";
        gantt.exportToExcel({
          name: ks_file_name,
          columns: [
            {
              id: "text",
              header: "Title",
            },
            {
              id: "start_date",
              header: "Start date",
            },
            {
              id: "end_date",
              header: "End date",
            },
          ],
        });
      } else if (ks_report_type == "pdf") {
        ks_file_name += ".pdf";
        gantt.exportToPDF({
          name: ks_file_name,
        });
      } else if (ks_report_type == "png") {
        ks_file_name += ".png";
        gantt.exportToPNG({
          name: ks_file_name,
        });
      } else if (ks_report_type == "json") {
        ks_file_name += ".json";
        gantt.exportToJSON({
          name: ks_file_name,
        });
      } else if (ks_report_type == "ms-project") {
        ks_file_name += ".xml";
        gantt.exportToMSProject({
          name: ks_file_name,
        });
      } else if (ks_report_type == "primaverap6") {
        ks_file_name += ".xml";
        gantt.exportToPrimaveraP6({
          name: ks_file_name,
          skip_circular_links: false,
        });
      } else if (ks_report_type == "ical") {
        ks_file_name += ".ical";
        gantt.exportToICal();
      } else {
        gantt.message({
          type: "warning",
          text: _t("Format not available"),
        });
      }
    }

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    ksOnCreate() {
        const { createAction } = this.model.metaData;
        if (createAction) {
            this.actionService.doAction(createAction, {
                additionalContext: context,
                onClose: () => {
                    this.model._ksComputeData();
                },
            });
        } else {
            this.openDialog(this.model.context);
        }
    }

    /**
     * Opens dialog to add/edit/view a record
     *
     * @param {Record<string, any>} props FormViewDialog props
     * @param {Record<string, any>} [options={}]
     */
    openDialog(props, options = {}) {
        const { canDelete, ks_isEdit, formViewId: viewId } = this.model.metaData;

        const title = props.title || (props.resId ? _t("Open") : _t("Create"));

        var KsCapsuleModel = false;
        if (props.resId){
            var ks_gantt_task = gantt.getTask(props.resId);
                if (ks_gantt_task && ks_gantt_task.ks_task_model) {
                    var KsresID = parseInt(props.resId.split("_")[1]);
                    KsCapsuleModel = ks_gantt_task.ks_task_model;
                } else {
                    KsresID = parseInt(props.resId);
                }
        } else if (props && props.open_new_task_form && (this.model.metaData.resModel == "project.task" || this.model.metaData.resModel == "project.project") ){
                KsCapsuleModel = "project.task";
          }
         var resModel = KsCapsuleModel? KsCapsuleModel:this.model.metaData.resModel;

        let removeRecord;
        if (canDelete && props.resId) {
            removeRecord = () => {
                return new Promise((resolve) => {
                    this.dialogService.add(ConfirmationDialog, {
                        body: _t("Are you sure to delete this record?"),
                        confirm: async () => {
                            await this.orm.unlink(resModel, [KsresID]);
                            resolve();
                        },
                        cancel: () => {},
                    });
                });
            };
        }

        this.closeDialog = this.dialogService.add(
            FormViewDialog,
            {
                title,
                resModel,
                viewId,
                resId: KsresID,
                // mode: ks_isEdit ? "edit" : "readonly",
                context: props,
                removeRecord,
            },
            {
                ...options,
                onClose: () => {
                    this.closeDialog = null;
//                    this.model.ks_compute_data();
                },
            }
        );
    }

    _KsOnDeleteRecord(id){
        var KsCapsuleModel = false;
        var ks_gantt_task = gantt.getTask(id);
        if (ks_gantt_task && ks_gantt_task.ks_task_model) {
            var KsRecordId = parseInt(id.split("_")[1]);
            KsCapsuleModel = ks_gantt_task.ks_task_model;
        } else {
            KsRecordId = parseInt(id);
        }
        if (this.model.metaData.canDelete && id){
        const resModel =  KsCapsuleModel ? KsCapsuleModel : this.model.metaData.resModel;
        return new Promise((resolve) => {
                    this.dialogService.add(ConfirmationDialog, {
                        body: _t("Are you sure to delete this record?"),
                        confirm: async () => {
                            await this.orm.unlink(resModel, [KsRecordId]);
                            this.model.ks_compute_data();
                            resolve();
                        },
                        cancel: () => {},
                    });
                });

        }
        }


    // todo manage reload and below function
//    ksOnCapsuleClicked(ev) {
//      var self = this;
//      var ks_state = ev.data.target;
//      if (!this.ks_dialog_opened) {
//        var ksDialog = self._ksOpenDialog(ks_state.attr("task_id"));
//        if (ksDialog) {
//          ksDialog.on("closed", this, function () {
//            this.ks_reload = false;
//            this.ks_dialog_opened = false;
//          });
//        }
//      }
//    }

    ksGanttConfig () {
      var self = this;
      gantt.attachEvent("onBeforeLightbox", function (id) {
        // Leave blank this event to not render default task click.
      });

      gantt.attachEvent(
        "onBeforeLinkAdd",
        function (id, link) {
          // check linking from group_by task.
          if (
            this.model.modelName != "project.project" &&
            (!parseInt(link.source) || !parseInt(link.target))
          ) {
            gantt.message({
              type: "error",
              text: _t("You can't create link task with group"),
            });
            return false;
          }
          if (
            gantt.getTask(link.source).type == "project" ||
            gantt.getTask(link.target).type == "project" ||
            gantt.getTask(link.target).ks_group_lvl
          ) {
            gantt.message({
              type: "error",
              text: _t("You can't create link with project and group"),
            });
            return false;
          }
          if (this.model.modelName == 'project.project' && (gantt.getTask(link.source).project_id[0]  != gantt.getTask(link.target).project_id[0] )){
            gantt.message({
              type: "error",
              text: _t("can't create link with other project task."),
            });
            return false;
          }
          return true;
        }.bind(this)
      );

      gantt.attachEvent(
        "onBeforeRowDragEnd",
        function (id, parent, target) {
          var task = gantt.getTask(id);
          var ks_task_update_task = {};
          var ks_all_task = gantt.serialize().data;
          var ks_init_sequence = 0;
          // if sequence present then update the sequence number for the task.
          for (var ks_task = 0; ks_task < ks_all_task.length; ks_task++) {
            ks_task_update_task[ks_all_task[ks_task].id] = {
              id: ks_all_task[ks_task].id,
            };
            if (ks_all_task[ks_task].parent)
              ks_task_update_task[ks_all_task[ks_task].id].parent_id =
                ks_all_task[ks_task].parent;
            // init sequence number;
            if (ks_task == 0) {
              ks_init_sequence = ks_all_task[0].sequence;
            }

            if (ks_init_sequence >= ks_all_task[ks_task].sequence) {
              ks_init_sequence = ks_init_sequence + 1;
              ks_task_update_task[ks_all_task[ks_task].id]["sequence"] =
                ks_init_sequence;
            } else {
              ks_init_sequence = ks_all_task[ks_task].sequence;
              ks_task_update_task[ks_all_task[ks_task].id]["sequence"]=ks_all_task[ks_task].sequence;
            }
          }
          if (this.model.modelName == gantt.ks_model_name) {
            this.model
              .ksUpdateParentSequence(ks_task_update_task)
              .then(function (res) {
                // This is to update the state reload without render.
                gantt.ks_no_reload = true;
                self.model.ks_compute_data()
              });
          }
          return true;
        }.bind(this)
      );

      // Event to check if the task can be moved or not.
      gantt.attachEvent("onBeforeRowDragMove", function (id, parent, tindex) {
        if (gantt.getTask(id).ks_allow_subtask) {
          return true;
        }
        return false;
      });
    }

    ksGanttCreateDp (event) {
      var self = this;
      this.ks_dp = gantt.createDataProcessor(function (
        entity,
        action,
        data,
        id
      ) {
        switch (action) {
          case "update":
            switch (entity) {
              case "task":
                if (self.model.modelName == gantt.ks_model_name) {
                  self.model.updateTask(data).then(
                    function (res) {
                      gantt.render();
                      // This is to update the state reload without render.
                      gantt.ks_no_reload = true;
//                      self.reload();
                       self.model.ks_compute_data()
                    },
                    function (reason) {
                      gantt.render();
                    self.model.ks_compute_data();
                    }
                  );
                }
                break;
            }
            break;
          case "create":
            switch (entity) {
              case "link":
              var result= gantt.config.ks_link_data.filter((rec) => rec.source == data.source && rec.target == data.target && rec.lag == data.lag)
                // check for duplicate link.
                if (result.length) {
                  break;
                }
                gantt.config.ks_link_data.push({
                  source: data.source,
                  target: data.target,
                  lag:data.lag
                });
                if (self.model.modelName == gantt.ks_model_name) {
                  self.model.ksCreateLink(data).then(function (res) {
                    gantt.ks_no_reload = true;
//                    self.reload();
                    self.model.ks_compute_data()
                    gantt.render();
                  });
                }
                break;
            }
            break;
          case "delete":
            switch (entity) {
              case "link":
                self.model.ksDeleteLink(data);
                let link_index = gantt.config.ks_link_data.findLastIndex((item)=> item.source == data.source && item.target == data.target && item.lag == data.lag);
                if (link_index > -1) {
                  gantt.config.ks_link_data.splice(link_index, 1);
                }
                gantt.ks_no_reload = true;
//                self.reload();
                self.model.ks_compute_data();
                break;
            }
            break;
        }
      });
    }

}
