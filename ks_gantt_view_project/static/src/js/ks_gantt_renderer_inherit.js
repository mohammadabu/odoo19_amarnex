/** @odoo-module **/

import {ksGanttRenderer} from "@ks_gantt_view_base/js/ks_gantt_renderer_new";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { renderToElement,renderToFragment,renderToString} from "@web/core/utils/render";
import {formatDate,formatDateTime,serializeDate, serializeDateTime} from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";
import {parseDateTime,parseDate,} from "@web/core/l10n/dates";
import { session } from "@web/session";


patch(ksGanttRenderer.prototype,{
    setup(){
        super.setup()
    },

    willstart(){
        var ks_def;
      var ks_pub_hol;
      var ks_super = super.willstart();
      if (this.active_id && this.ks_model_name == "project.task") {
        ks_def = rpc("/web/dataset/call_kw/project.project/ks_project_config",{
          model: "project.project",
          method: "ks_project_config",
          args: [this.active_id],
          kwargs:{}
        }).then(
          function (result) {
            this.ks_project_start = result.ks_project_start
              ? result.ks_project_start
              : false;
            this.ks_project_end = result.ks_project_end
              ? result.ks_project_end
              : false;
            this.ks_enable_project_deadline = result.ks_enable_project_deadline;
            this.ks_enable_task_dynamic_text =
              result.ks_enable_task_dynamic_text;
            this.ks_enable_task_dynamic_progress =
              result.ks_enable_task_dynamic_progress;
            this.ks_enable_weekends = result.ks_enable_weekends;
            this.ks_days_off = result.ks_days_off;
            this.ks_days_off_selection = result.ks_days_off_selection;
            this.ks_enable_quickinfo_extension =
              result.ks_enable_quickinfo_extension;
            this.ks_project_tooltip_config = result.ks_project_tooltip_config
              ? result.ks_project_tooltip_config
              : false;
            this.ks_hide_date = result.ks_hide_date;
            this.ks_allow_subtasks = result.ks_allow_subtasks;
          }.bind(this)
        );
      }
      // Get Project Public Holiday list
      ks_pub_hol = rpc("/web/dataset/call_kw/project.project/ks_public_holidays",{
        model: "project.project",
        method: "ks_public_holidays",
        args: [],
        kwargs:{}
      }).then(
        function (result) {
          this.ks_exclude_holiday = result;
        }.bind(this)
      );

      return Promise.all([ks_def, ks_pub_hol, ks_super]);



    },

    ks_data_update(each_task,ks_links,ks_data,ks_gantt_fields,parent_group_id) {
      if(this.props.model.modelName == "project.task"){
          if (each_task[ks_gantt_fields.ks_task_link]) {
            console.log(each_task[ks_gantt_fields.ks_task_link]);

            JSON.parse(each_task[ks_gantt_fields.ks_task_link]).forEach(
              (item, index) => {


                ks_links.push({
                  id: item.id,
                  source: item.source,
                  target: item.target,
                  type: item.type,
                  lag:item.lag
                });
                gantt.config.ks_link_data.push({
                  id: item.id,
                  source: item.source,
                  target: item.target,
                  type: item.type,
                  lag:item.lag
                });
              }
            );  
            
            
          }

          var ks_resource_hours_available = {};
          if (each_task[ks_gantt_fields.ks_resource_hours_available])
            ks_resource_hours_available = JSON.parse(
              each_task[ks_gantt_fields.ks_resource_hours_available]
            );

            // Update task type.
            var ks_task_type = each_task[ks_gantt_fields.ks_task_type];
              if (ks_gantt_fields.ks_project_row) {
                ks_task_type = "project";
              }
            var ks_gantt_data = {
            id: each_task[ks_gantt_fields.ks_task_id],
            text: each_task[ks_gantt_fields.ks_task_name],
            planned_hours: each_task[ks_gantt_fields.planned_hours],
            color: each_task[ks_gantt_fields.ks_task_color]
              ? each_task[ks_gantt_fields.ks_task_color]
              : false,
            start_date:
              this.ks_fieldDetail[ks_gantt_fields.ks_task_start_date].type == "date"
                ? (parseDate(each_task[ks_gantt_fields.ks_task_start_date],localization.dateFormat)).toJSDate()
                : this.ksConversionUtcToLocal(parseDateTime(each_task[ks_gantt_fields.ks_task_start_date],localization.dateTimeFormat)) ,
            end_date:
              this.ks_fieldDetail[ks_gantt_fields.ks_task_end_date].type == "date"
                ? (parseDate(each_task[ks_gantt_fields.ks_task_end_date],localization.dateFormat)).toJSDate()
                : this.ksConversionUtcToLocal(parseDateTime(each_task[ks_gantt_fields.ks_task_end_date],localization.dateTimeFormat)),

            mark_as_important: each_task[ks_gantt_fields.ks_mark_as_important],
            deadline: gantt.config.ks_toggle_deadline
              ? this.ks_fieldDetail[ks_gantt_fields.ks_task_deadline].type == "date" ?
              (parseDateTime(each_task[ks_gantt_fields.ks_task_deadline],localization.dateTimeFormat)).toJSDate() :
              this.ksConversionUtcToLocal(parseDateTime(each_task[ks_gantt_fields.ks_task_deadline],localization.dateTimeFormat))
              : false,
            ks_deadline_tooltip: each_task[ks_gantt_fields.ks_task_deadline]
              ? this.ks_fieldDetail[ks_gantt_fields.ks_task_deadline].type == "date" ?
              (parseDateTime(each_task[ks_gantt_fields.ks_task_deadline],localization.dateTimeFormat)).toJSDate() :
              this.ksConversionUtcToLocal(parseDateTime(each_task[ks_gantt_fields.ks_task_deadline],localization.dateTimeFormat))
              : false,
            progress: each_task[ks_gantt_fields.ks_task_progress],
            ks_progress: each_task[ks_gantt_fields.ks_task_progress],
            ks_progress_enable: true,
            sequence: each_task[ks_gantt_fields.sequence],
            parent: each_task[ks_gantt_fields.ks_parent_task]
              ? each_task[ks_gantt_fields.ks_parent_task][0]
              : parent_group_id,
            //                'project_id': each_task.project_id,
            ks_allow_subtask: each_task[ks_gantt_fields.ks_allow_subtask],
            ks_schedule_mode: each_task[ks_gantt_fields.ks_schedule_mode],
            auto_scheduling:
              each_task[ks_gantt_fields.ks_schedule_mode] == "auto" ? true : false,
            constraint_type: each_task[ks_gantt_fields.ks_constraint_task_type]
              ? each_task[ks_gantt_fields.ks_constraint_task_type]
              : false,
            ks_constraint_type: each_task[ks_gantt_fields.ks_constraint_task_type]
              ? each_task[ks_gantt_fields.ks_constraint_task_type]
              : false,
            constraint_date: each_task[ks_gantt_fields.ks_constraint_task_date]
              ? this.ksConversionUtcToLocal(parseDateTime(each_task[ks_gantt_fields.ks_constraint_task_date],localization.dateTimeFormat))
              : false,
            constraint_date_enable: each_task[
              ks_gantt_fields.ks_constraint_task_date
            ]
              ? true
              : false,
            stage_id: this.ks_get_stage_data(
              ks_gantt_fields.ks_task_stage_id,
              each_task[ks_gantt_fields.ks_task_stage_id]
            ),
            unscheduled: each_task[ks_gantt_fields.ks_unschedule],
            ks_owner_task: each_task[ks_gantt_fields.ks_owner_task],
            user: each_task[ks_gantt_fields.ks_owner_task]
              ? each_task[ks_gantt_fields.ks_owner_task][0]
              : 0,
            resource_working_hours:
              each_task[ks_gantt_fields.ks_resource_hours_per_day],
            ks_resource_hours_available: ks_resource_hours_available,
            type: ks_task_type,
            create_date: this.ksConversionUtcToLocal(parseDateTime(each_task.create_date),localization.dateTimeFormat),
            ks_task_link_ids: each_task.ks_task_link_json,
            project_id: each_task[ks_gantt_fields.project_id],
            partner_id: each_task[ks_gantt_fields.partner_id],
            company_id: each_task[ks_gantt_fields.company_id],
            ks_enable_task_duration:
              each_task[ks_gantt_fields.ks_enable_task_duration],
            ks_task_no_drag: this.ks_compute_task_drag(each_task),
            ks_task_duration: each_task[ks_gantt_fields.ks_task_duration],
            open: true,
          };

            // Manage multiple users.
            if (
            ks_gantt_fields &&
            ks_gantt_fields.ks_owner_task &&
            this.ks_fieldDetail[ks_gantt_fields.ks_owner_task].type == "many2many"
          )
            ks_gantt_data["user"] = each_task[ks_gantt_fields.ks_owner_task];

                //       Check if parent task is available then set add parent otherwise set to false.

            if (each_task.parent_id && !this.props.model.ksDataForGantt.KsAllTaskIds.includes(each_task.parent_id[0])){
                ks_gantt_data["parent"] = false
            }

            if (this.ks_export_field) {
            for (var index = 0; index <= this.ks_export_field.length; index++) {
              ks_gantt_data[this.ks_export_field[index]] =
                each_task[this.ks_export_field[index]];
            }
          }

            if (
            ks_gantt_data.start_date instanceof Date &&
            isFinite(ks_gantt_data.start_date) &&
            ks_gantt_data.end_date instanceof Date &&
            isFinite(ks_gantt_data.end_date)
          ) {
                ks_data.push(ks_gantt_data);
            } else {
                var record =this.props.model.ksDataForGantt.records.find(record => record.id === ks_gantt_data.id)
                if(!record.ks_tip){
                record.ks_tip=true
                gantt.message({
                  type: "warning",
                  text: _t(
                    ks_gantt_data.text +
                      " not shown due to start/end date is not found."
                  ),
                });
              }

      }

            if (!gantt.config.ks_owner_task_list) {
            gantt.config.ks_owner_task_list = [
              { key: "0", label: "N/A", id: "0", text: "N/A" },
            ];
            gantt.config.ks_owner_task_dict = [];
          }
            if (each_task[ks_gantt_fields.ks_owner_task] &&each_task[ks_gantt_fields.ks_owner_task][0] &&gantt.config.ks_owner_task_dict.indexOf(each_task[ks_gantt_fields.ks_owner_task][0]) < 0) {
                gantt.config.ks_owner_task_dict.push(
                  each_task[ks_gantt_fields.ks_owner_task][0]
                );
            if (each_task["ks_user_ids"]) {
              var ks_iterator = JSON.parse(
                each_task["ks_user_ids"].replace(/'/g, '"')
              );
              for (var i in ks_iterator) {
                gantt.config.ks_owner_task_list.push({
                  key: ks_iterator[i][0],
                  label: ks_iterator[i][1],
                  id: ks_iterator[i][0],
                  text: ks_iterator[i][1],
                });
              }
            } else {
              gantt.config.ks_owner_task_list.push({
                key: each_task[ks_gantt_fields.ks_owner_task][0],
                label: each_task[ks_gantt_fields.ks_owner_task][1],
                id: each_task[ks_gantt_fields.ks_owner_task][0],
                text: each_task[ks_gantt_fields.ks_owner_task][1],
              });
            }
            }
        }else{
            super.ks_data_update(each_task,ks_links,ks_data,ks_gantt_fields,parent_group_id)
        }
    },

    ks_project_task_data_update(
      each_project_task,
      ks_links,
      ks_data,
      project_id
    ) {
        if(this.props.model.modelName == "project.project"){

      var ks_resource_hours_available = {};
      if (each_project_task.ks_resource_hours_available)
        ks_resource_hours_available = JSON.parse(
          each_project_task.ks_resource_hours_available
        );

      if (each_project_task.ks_task_link_json) {
        JSON.parse(each_project_task.ks_task_link_json).forEach(
          (item, index) => {
            ks_links.push({
              id: item.id,
              source: "task_" + item.source,
              target: "task_" + item.target,
              type: item.type,
              lag:item.lag
            });
            // dict to check to duplicate link.
            gantt.config.ks_link_data.push({
              id: item.id,
              source: item.source,
              target: item.target,
              type: item.type,
              lag:item.lag
            });
          }
        );
      }

      var ks_gantt_datas = {
        id: each_project_task.id,
        text: each_project_task.ks_task_name,
        color: each_project_task.ks_task_color
          ? each_project_task.ks_task_color
          : false,
        start_date: this.ksConversionUtcToLocal(
         parseDateTime(each_project_task.ks_task_start_date,localization.dateTimeFormat)
        ),
        end_date: this.ksConversionUtcToLocal(
          parseDateTime(each_project_task.ks_task_end_date,localization.dateTimeFormat)
        ),
        parent: each_project_task.parent_id
          ? each_project_task.parent_id
          : project_id,
        mark_as_important: each_project_task.mark_as_important,
        deadline: gantt.config.ks_toggle_deadline
          ? this.ksConversionUtcToLocal(parseDateTime(each_project_task.deadline,localization.dateTimeFormat))
          : false,
        ks_deadline_tooltip: each_project_task.deadline
          ? this.ksConversionUtcToLocal(parseDateTime(each_project_task.deadline,localization.dateTimeFormat))
          : false,
        progress: each_project_task.progress ,
        ks_progress: each_project_task.progress,
        ks_progress_enable: false,
        sequence: each_project_task.sequence,
        ks_allow_subtask: each_project_task.ks_allow_subtask,
//                        'ks_allow_parent_task': each_project_task.ks_allow_subtask,
        ks_schedule_mode: each_project_task.ks_schedule_mode,
        auto_scheduling:
          each_project_task.ks_schedule_mode == "auto" ? true : false,
        constraint_type: each_project_task.constraint_type
          ? each_project_task.constraint_type
          : false,
        constraint_date: each_project_task.constraint_date
          ? this.ksConversionUtcToLocal(
              parseDateTime(each_project_task.constraint_date,localization.dateTimeFormat)
            )
          : false,
        constraint_date_enable: each_project_task.constraint_date
          ? true
          : false,
        stage_id: each_project_task.stage_id
          ? each_project_task.stage_id
          : undefined,
        unscheduled: each_project_task.unscheduled,
        resource_working_hours: each_project_task.resource_working_hours,
        ks_task_model: each_project_task.ks_task_model,
        ks_owner_task: each_project_task.ks_owner_task,
        user: each_project_task.ks_owner_task
          ? each_project_task.ks_owner_task[0]
          : 0,
        type: each_project_task.type,
        ks_resource_hours_available: ks_resource_hours_available,
        project_id: each_project_task.project_id,
        create_date: each_project_task.create_date? this.ksConversionUtcToLocal(
          parseDateTime(each_project_task.create_date,localization.dateTimeFormat)):false,
        project_id: each_project_task.project_id,
        ks_task_link_ids: each_project_task.ks_task_link_json,
        partner_id: each_project_task.partner_id,
        company_id: each_project_task.company_id,
        ks_enable_task_duration: each_project_task.ks_enable_task_duration,
        ks_task_duration: each_project_task.ks_task_duration,
        open: true,
      };


      if (this.ks_export_field) {
        for (var index = 0; index <= this.ks_export_field.length; index++) {
          ks_gantt_datas[this.ks_export_field[index]] =
            each_task[this.ks_export_field[index]];
        }
      }

      if (
        ks_gantt_datas.start_date instanceof Date &&
        isFinite(ks_gantt_datas.start_date) &&
        ks_gantt_datas.end_date instanceof Date &&
        isFinite(ks_gantt_datas.end_date)
      ) {
        ks_data.push(ks_gantt_datas);
      } else {
        gantt.message({
          type: "warning",
          text: _t(
            ks_gantt_data.text +
              " not shown due to start/end date is not found."
          ),
        });
      }

      if (!gantt.config.ks_owner_task_list) {
        gantt.config.ks_owner_task_list = [
          { key: "0", label: "N/A", id: "0", text: "N/A" },
        ];
        gantt.config.ks_owner_task_dict = [];
      }
      if (
        each_project_task.ks_owner_task &&
        each_project_task.ks_owner_task[0] &&
        gantt.config.ks_owner_task_dict.indexOf(
          each_project_task.ks_owner_task[0]
        ) < 0
      ) {
        gantt.config.ks_owner_task_dict.push(
          each_project_task.ks_owner_task[0]
        );
        gantt.config.ks_owner_task_list.push({
          key: each_project_task.ks_owner_task[0],
          label: each_project_task.ks_owner_task[1],
          id: each_project_task.ks_owner_task[0],
          text: each_project_task.ks_owner_task[1],
        });
      }
        }else{
            super.ks_project_task_data_update( each_project_task,ks_links,ks_data,project_id)
        }
    },

})
