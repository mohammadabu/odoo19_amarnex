/** @odoo-module **/

import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { sprintf } from "@web/core/utils/strings";
import { formatFloat } from "@web/core/utils/numbers";
import { Model } from "@web/model/model";
import { Domain } from "@web/core/domain";
import {formatDate,formatDateTime,serializeDate, serializeDateTime} from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";
import {parseDateTime,parseDate,} from "@web/core/l10n/dates";
import { x2ManyCommands } from "@web/core/orm_service";
import { registry } from "@web/core/registry";
import { groupBy, unique } from "@web/core/utils/arrays";
import { KeepLast, Mutex } from "@web/core/utils/concurrency";
import { rpc } from "@web/core/network/rpc";
import { BlockUI } from "@web/core/ui/block_ui";


export class ksGanttModel extends Model{
    setup(params) {
        /** @type {Data} */
        this.data = {};
        this.ksDataForGantt = {}
        /** @type {MetaData} */
        this.metaData = params.metaData;

        this.searchParams = null;

        /** @type {Set<RowId>} */
        this.closedRows = new Set();

        // concurrency management
        this.keepLast = new KeepLast();
        /** @type {MetaData | null} */
        this._nextMetaData = null;
    }

    load(params) {
      this.searchParams = params;
      this.modelName = this.metaData.resModel;
      this.fields = this.metaData.fields;
      this.domain = params.domain;
      this.context = params.context;
      this.ks_export_field = this.metaData.info.ks_export_field;
      this.ks_requiredFields = this.metaData.ks_requiredFields;
      // Add arch fields.
      this.ks_gantt_arch = this.metaData.ks_gantt_arch;
      this.ks_gantt_link_info = this.metaData.info.ks_task_link_info
        ? this.metaData.info.ks_task_link_info
        : false;
      this.ks_defaultGroupBy = this.metaData.ks_defaultGroupBy
        ? this.metaData.ks_defaultGroupBy
        : [];
      if (!params.groupBy || !params.groupBy.length) {
        params.groupBy = this.ks_defaultGroupBy;
      }
      this.ksDataForGantt = {
        groupedBy: params.groupBy,
        name: this.metaData.name,
        fields: this.metaData.fields,
      };
      return this._ksComputeData().then(function () {
        return Promise.resolve();
      });
    }

    async ks_compute_data(){
        await this._ksComputeData();
        this.notify();
    }

    conversionToUTCTime(ksDate) {
     const ks_date = ksDate.minus({minutes:ksDate.offset});
     return formatDateTime(ks_date,{format:"yyyy-MM-dd HH:mm:ss"})
    }

       _ksComputeData() {

      var self = this;
      var KsFilter = this.domain;
      var ksGroupDefaultData;
      if (
        this.ksDataForGantt &&
        this.ksDataForGantt.groupedBy &&
        this.ksDataForGantt.groupedBy.length
      ) {
              // Remove date field group by.
//        this.ksDataForGantt.groupedBy[0] = this.ksDataForGantt.groupedBy[0].split(':')[0]

      // keeplast is used to handle the concurreny  problem because two requests are made to server//

      ksGroupDefaultData = rpc(`/web/dataset/call_kw/${this.modelName}/read_group`,{
          model: this.modelName,
          method: "read_group",
          args:[KsFilter,this.ksFetchDefaultFields(),this.ksDataForGantt.groupedBy],
          kwargs:{
            context: $.extend({},true,this.context,{group_by: this.ksDataForGantt.groupedBy}),lazy: this.ksDataForGantt.groupedBy.length === 1
          }

        });
      }

      var ksDefaultData = rpc(`/web/dataset/call_kw/${this.modelName}/search_read`,{
        model: this.modelName,
        method:"search_read",
        args:[KsFilter,this.ksFetchDefaultFields()],
        kwargs:{context: $.extend({},true,this.context,{group_by: this.ksDataForGantt.groupedBy}),}

      });
      return this.keepLast
        .add(Promise.all([ksGroupDefaultData, ksDefaultData]))
        .then(function (results) {
          self.ksDataForGantt.records = [];
          self.ksDataForGantt.KsAllTaskIds = [];
          var ksTasksRecord = [];

          // Set group_by_records data.
          if (results && results[0] && results[0].length) {
            self.ksDataForGantt.ks_group_by_records = results[0];
            ksTasksRecord = results[0];
          }
          // Set all task data.
          if (results && results[1]) {
            self.ksDataForGantt.records = results[1];
            ksTasksRecord = results[1];
          }

          // Get All Tasks IDs to verify task's parent.
          ksTasksRecord.forEach((element) => {
            self.ksDataForGantt.KsAllTaskIds.push(element.id);
          });
        });
    }
        ksFetchDefaultFields() {

      var ksRequireFiled = ["display_name"];
      var ks_fields_list = []
      if ("create" in this.ks_gantt_arch) {
        delete this.ks_gantt_arch["create"];
      }
      if ("ks_context" in this.ks_gantt_arch) {
        delete this.ks_gantt_arch["ks_context"];
      }
      if ("delete" in this.ks_gantt_arch) {
        delete this.ks_gantt_arch["delete"];
      }
      if ("edit" in this.ks_gantt_arch) {
        delete this.ks_gantt_arch["edit"];
      }
        if (this.ksDataForGantt.groupedBy.length !=0){
      for (var group_index in this.ksDataForGantt.groupedBy) {
      var ks_group_type = this.ksDataForGantt.groupedBy[group_index].split(':')[0]
      if (this.ksDataForGantt.fields[ks_group_type].type == 'datetime') {
       ks_fields_list.push(ks_group_type)
      }
      else {
       ks_fields_list.push(ks_group_type)
      }
      }
      }

      if (this.ksDataForGantt.groupedBy.length != 0){
        ksRequireFiled = ksRequireFiled.concat(
        ks_fields_list,
        Object.values(this.ks_gantt_arch)
      );
      }

      if (this.ksDataForGantt.groupedBy.length == 0){
      ksRequireFiled = ksRequireFiled.concat(
        this.ksDataForGantt.groupedBy,
        Object.values(this.ks_gantt_arch)
      );
      }
      ksRequireFiled = ksRequireFiled.filter(function (item) {
        return item != "ks_project_row";
      });
      // Adding create date to required data.
      if (ksRequireFiled.indexOf("create_date") < 0) {
        ksRequireFiled.push("create_date");
      }
      // Read field values which needs to export for json.
      if (this.ks_export_field && this.ks_export_field.length > 0) {
        ksRequireFiled = ksRequireFiled.concat(this.ks_export_field);
      }
      return [...new Set(ksRequireFiled)].sort()
//      return _.uniq(ksRequireFiled);
    }

    // Reload page on data change
    reload(ksAnyObj, ksGetObj) {
      if (ksGetObj.groupBy) {
        this.ksDataForGantt.groupedBy = ksGetObj.groupBy;
      }
      if (ksGetObj.domain) {
        this.domain = ksGetObj.domain;
      }
      return this._ksComputeData().then(function () {
        return Promise.resolve();
      });
    }

    // function to update the task.
    /**
     * Update task parent.
     */

    updateTask (data) {
      var ks_data_values = {};
      var id = data.id;
      var gantt_date_obj = gantt.date.str_to_date("%d-%m-%Y %h:%i");
      var date_start = gantt_date_obj(data.start_date);
      var date_end = gantt_date_obj(data.end_date);
      if (data.constraint_date && this.ks_gantt_arch.ks_constraint_task_date) {
        var constraint_date = gantt_date_obj(data.constraint_date);
        ks_data_values[this.ks_gantt_arch.ks_constraint_task_date] =
            this.conversionToUTCTime(luxon.DateTime.fromJSDate(constraint_date));
      }
      ks_data_values[this.ks_gantt_arch.ks_task_start_date] =
        this.fields[this.ks_gantt_arch.ks_task_start_date].type == "date"
          ? formatDate(luxon.DateTime.fromJSDate(date_start),{format:"yyyy-MM-dd"})
          : this.conversionToUTCTime(luxon.DateTime.fromJSDate(date_start));

      ks_data_values[this.ks_gantt_arch.ks_task_end_date] =
        this.fields[this.ks_gantt_arch.ks_task_end_date].type == "date"
          ? formatDate(luxon.DateTime.fromJSDate(date_end),{format:"yyyy-MM-dd"})
          : this.conversionToUTCTime(luxon.DateTime.fromJSDate(date_end));

      if (this.ks_gantt_arch.ks_constraint_task_type) {
        ks_data_values[this.ks_gantt_arch.ks_constraint_task_type] =
          data.constraint_type;
      }
      if (data.ks_task_model) {
        return this.ksUpdateProjectGanttTask(data);
      }
      return rpc(`/web/dataset/call_kw/${this.modelName}/write`,{
        model: this.modelName,
        method: "write",
        args: [id, ks_data_values],
        kwargs:{}
      });
    }

    ksUpdateProjectGanttTask(data) {
      var id = parseInt(data.id.split("_")[1]);
      var ks_data_values = {};
      var gantt_date_obj = gantt.date.str_to_date("%d-%m-%Y %h:%i");
      var date_start = gantt_date_obj(data.start_date);
      var date_end = gantt_date_obj(data.end_date);

      if (data.constraint_date && this.ks_gantt_arch.ks_constraint_task_date) {
        var constraint_date = gantt_date_obj(data.constraint_date);
        ks_data_values["ks_constraint_task_date"] = this.conversionToUTCTime(
          luxon.DateTime.fromJSDate(constraint_date)
        );
      }

      ks_data_values["ks_start_datetime"] = this.conversionToUTCTime(
        luxon.DateTime.fromJSDate(date_start)
      );
      ks_data_values["ks_end_datetime"] = this.conversionToUTCTime(
        luxon.DateTime.fromJSDate(date_end)
      );
      if (data.ks_constraint_task_type) {
        ks_data_values["ks_constraint_task_type"] = data.constraint_type;
      }

      var projects_data = this.ksDataForGantt.records;
      var project_id = data.project_id[0]
      const projectDict = projects_data.find(dict => dict['id'] === project_id);
      var project_start_date = false;
      var project_end_date = false;
      var project_tasks = JSON.parse(projectDict.ks_project_task_json).filter(item => item.id !== data.id);
      const minDateDict = project_tasks.reduce((minDict, currentDict) => {
          return currentDict.ks_task_start_date < minDict.ks_task_start_date ? currentDict : minDict;
      });
      const maxDateDict = project_tasks.reduce((maxDict, currentDict) => {
          return currentDict.ks_task_end_date > maxDict.ks_task_end_date ? currentDict : maxDict;
      });
       project_start_date = minDateDict['ks_task_start_date']
       project_end_date = maxDateDict['ks_task_end_date']
      if(ks_data_values['ks_start_datetime'] < project_start_date){
        project_start_date = ks_data_values['ks_start_datetime']
      }
      if(ks_data_values['ks_end_datetime'] >  project_end_date){
        project_end_date = ks_data_values['ks_end_datetime']
      }
      var project_new_dates = {
            ks_project_start: project_start_date,
            ks_project_end: project_end_date
      }
      if(project_start_date != projectDict['ks_project_start'] || project_end_date != projectDict['ks_project_end']){
          rpc("/web/dataset/call_kw/project.project/write", {
            model: 'project.project',
            method: "write",
            args: [projectDict.id, project_new_dates],
            kwargs:{}
          });
      }

      return rpc(`/web/dataset/call_kw/${data.ks_task_model}/write`,{
        model: data.ks_task_model,
        method: "write",
        args: [id, ks_data_values],
        kwargs:{}
      });
    }

    /**
     * Update task parent.
     */
    ksUpdateParent(data) {
      var ks_data_values = {};
      var id = data.id;
      ks_data_values["parent_id"] = data[this.ks_gantt_arch.ks_parent_task];

      return jsonrpc(`/web/dataset/call_kw/${this.modelName}/write`,{
        model: this.modelName,
        method: "write",
        args: [id, ks_data_values],
        kwargs:{}
      });
    }

    /*
     * Update Task Parent and Sequence.
     */
    ksUpdateParentSequence (data) {
      if (this.modelName == "project.project") {
        return false;
      }
       new BlockUI();
      return rpc(`/web/dataset/call_kw/${this.modelName}/ks_update_task_sequence`,{
        model: this.modelName,
        method: "ks_update_task_sequence",
        args: [data],
        kwargs:{}
      });

    }

    /**
     * Create task link.
     */
    ksCreateLink (data) {
      var create_dict = {
        ks_task_link_type: data.type,
        ks_lag_days:data.lag

      };
      if (this.modelName == "project.project") {
        create_dict["ks_source_task_id"] = parseInt(
          data.source.split("task_")[1]
        );
        create_dict["ks_target_task_id"] = parseInt(
          data.target.split("task_")[1]
        );
      } else {
        create_dict[this.ks_gantt_link_info.ks_link_source] = parseInt(
          data.source
        );
        create_dict[this.ks_gantt_link_info.ks_link_target] = parseInt(
          data.target
        );
      }
      return rpc("/web/dataset/call_kw/ks.task.link/create",{
        model: "ks.task.link",
        method: "create",
        args: [create_dict],
        kwargs:{}
      }).then(
        function (results) {
          // after create link update gantt link id.
          gantt.changeLinkId(this.id, results);
        }.bind(data)
      );
    }

    /**
     * Delete task link
     */
    ksDeleteLink(data) {
      return rpc("/web/dataset/call_kw/ks.task.link/unlink",{
        model: "ks.task.link",
        method: "unlink",
        args: [[data.id]],
        kwargs:{}
      });
    }
}