odoo.define('account_dynamic_reports.DynamicTbMain', function (require) {
'use strict';

var ActionManager = require('web.ActionManager');
var AbstractAction = require('web.AbstractAction');
var Dialog = require('web.Dialog');
var FavoriteMenu = require('web.FavoriteMenu');
var web_client = require('web.web_client');
var ajax = require('web.ajax');
var core = require('web.core');
var Widget = require('web.Widget');
var field_utils = require('web.field_utils');
var rpc = require('web.rpc');
var time = require('web.time');
var session = require('web.session');

//var formats = require('web.formats');
var utils = require('web.utils');
var round_di = utils.round_decimals;

var QWeb = core.qweb;
var _t = core._t;

var exports = {};

var DynamicFrMain = AbstractAction.extend({
    template:'DynamicFrMain',

    events: {
        'click #filter_apply_button': 'update_with_filter',
        'click #pdf': 'print_pdf',
        'click #xlsx': 'print_xlsx',
        'click .view-source': 'view_gl',
    },

    init : function(view, code){
        this._super(view, code);
        this.wizard_id = code.context.wizard_id | null;
        this.account_report_id = code.context.account_report_id | null;
        this.session = session;
    },

    start : function(){
	    var self = this;
	    self.initial_render = true;
        if(! self.wizard_id){
            self._rpc({
                model: 'ins.financial.report',
                method: 'create',
                context: {report_name: this.account_report_id},
                args: [{
                    res_model: this.res_model,
                    }]
                }).then(function (record) {
                    self.wizard_id = record;
                    self.plot_data(self.initial_render);
                })
            }else{
                self.plot_data(self.initial_render);
            }
        },

	print_pdf : function(e){
	    e.preventDefault();
	    var self = this;
	    self._rpc({
            model: 'ins.financial.report',
                method: 'get_report_values',
                args: [[self.wizard_id]],
            }).then(function(data){
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'account_dynamic_reports.ins_report_financial',
                    'report_file': 'account_dynamic_reports.ins_report_financial',
                    'data': {'js_data':data},
                    'context': {'active_model':'ins.financial.report',
                                'landscape':1,
                                'from_js': true
                                },
                    'display_name': 'Finance Report',
                };
                return self.do_action(action);
            });
	},

	print_xlsx : function(){
	    var self = this;

	    self._rpc({
            model: 'ins.financial.report',
                method: 'action_xlsx',
                args: [[self.wizard_id]],
            }).then(function(action){
                action.context.active_ids = [self.wizard_id];
                return self.do_action(action);
            });
	},

	formatWithSign : function(amount, formatOptions, sign){
	    var currency_id = formatOptions.currency_id;
	    currency_id = session.get_currency(currency_id);

	    // get monetary without sign
	    var without_sign = field_utils.format.monetary(Math.abs(amount), {}, formatOptions);

	    if(!amount){return '-'};

        // add sign to monetary
	    if (currency_id.position === "after") {
            return sign + '&nbsp;' + without_sign + '&nbsp;' + currency_id.symbol;
        } else {
            return currency_id.symbol + '&nbsp;' + sign + '&nbsp;' + without_sign;
        }
	    return without_sign;
	},

	plot_data : function(initial_render = true){
	    var self = this;

	    // Remove all the child contents first
        var node = self.$('.py-data-container');
        var last;
        while (last = node.lastChild) node.removeChild(last);

        // Initialize wizard with default values
        self._rpc({
            model: 'ins.financial.report',
                method: 'get_report_values',
                args: [[self.wizard_id]],
            }).then(function (datas) {
                self.filter_data = datas.form;
                self.account_data = datas.report_lines;
                _.each(self.account_data, function (k, v){

                    var formatOptions = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };

                    k.debit = self.formatWithSign(k.debit, formatOptions, k.debit < 0 ? '-' : '');
                    k.credit = self.formatWithSign(k.credit, formatOptions, k.credit < 0 ? '-' : '');
                    k.balance = self.formatWithSign(k.balance, formatOptions, k.balance < 0 ? '-' : '');
                    k.balance_cmp = self.formatWithSign(k.balance_cmp, formatOptions, k.balance < 0 ? '-' : '');

                });

                if(initial_render){
                    self.$('.py-control-panel').html(QWeb.render('FilterSectionFr', {
                        filter_data : self.filter_data,
                        }));
                    self.$el.find('#date_from').datepicker({ dateFormat: 'dd-mm-yy' });
                    self.$el.find('#date_to').datepicker({ dateFormat: 'dd-mm-yy' });
                    self.$el.find('#date_from_cmp').datepicker({ dateFormat: 'dd-mm-yy' });
                    self.$el.find('#date_to_cmp').datepicker({ dateFormat: 'dd-mm-yy' });

                    self.$el.find('.date_filter-multiple').select2({
                        maximumSelectionSize: 1,
                        placeholder:'Select Date...',
                        });

                    self.$el.find('.journal-multiple').select2({
                        placeholder:'Select Journal...',
                        });

                    self.$el.find('.extra-multiple').select2({
                        placeholder:'Extra Options...',
                        })
                        .val('debit_credit').trigger('change')
                        ;

                }

                // Render data lines
                self.$('.py-data-container').html(QWeb.render('DataSectionFr', {
                    account_data : self.account_data,
                    filter_data : self.filter_data,
                    }));
            });

	    }, //start

	/* Used to redirect to move record */
	view_gl : function(event){
	    event.preventDefault();
        var self = this;
        var domains = {
                account_ids : [$(event.currentTarget).data('account-id')] }
        var context = {};

	    // Get custom dates
	    if ($("#date_from").val()){
	        var dateObject = $("#date_from").datepicker("getDate");
            var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
	        domains.date_from = dateString;
	    }
	    if ($("#date_to").val()){
	        var dateObject = $("#date_to").datepicker("getDate");
            var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
	        domains.date_to = dateString;
	    }

        var fr_wizard_id = 0;

        self._rpc({
            model: 'ins.general.ledger',
            method: 'create',
            args: [{}]
            }).then(function (record){
                fr_wizard_id = record;
                self._rpc({
                    model: 'ins.general.ledger',
                    method: 'write',
                    args: [fr_wizard_id, domains]
                }).then(function () {
                    var action = {
                        type: 'ir.actions.client',
                        name: 'GL View',
                        tag: 'dynamic.gl',
                        nodestroy: true ,
                        target: 'new',
                        context: {
                            wizard_id:fr_wizard_id,
                            active_id: self.wizard_id,
                            active_model:'ins.financial.report'
                            }
                    }
                    return self.do_action(action);
                })
            })

        }, //Redirect to FR

    update_with_filter : function(event){
        event.preventDefault();
        var self = this;
        self.initial_render = false;
        var output = {date_range:false, enable_filter:false, debit_credit:false};

        // Get date filter
	    if($(".date_filter-multiple").select2('data').length === 1){
	        output.date_range = $(".date_filter-multiple").select2('data')[0].id
	    }

	    // Get custom dates
	    if ($("#date_from").val()){
	        var dateObject = $("#date_from").datepicker("getDate");
            var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
	        output.date_from = dateString;
	    }
	    if ($("#date_to").val()){
	        var dateObject = $("#date_to").datepicker("getDate");
            var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
	        output.date_to = dateString;
	    }
	    // Get compariosn dates
	    if ($("#date_from_cmp").val()){
	        var dateObject = $("#date_from_cmp").datepicker("getDate");
            var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
	        output.date_from_cmp = dateString;
	        output.enable_filter = true;
	    }
	    if ($("#date_to_cmp").val()){
	        var dateObject = $("#date_to_cmp").datepicker("getDate");
            var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
	        output.date_to_cmp = dateString;
	        output.enable_filter = true;
	    }

	    // Get journals
	    var journal_ids = [];
	    var journal_list = $(".journal-multiple").select2('data')
	    for (var i=0; i < journal_list.length; i++){
	        journal_ids.push(parseInt(journal_list[i].id))
	        }
	    output.journal_ids = journal_ids

	    // Get optionals
	    var options_list = $(".extra-multiple").select2('data')
	    for (var i=0; i < options_list.length; i++){
	        if(options_list[i].id === 'debit_credit'){
	            output.debit_credit = true;
	            }
	        }

	    self._rpc({
                model: 'ins.financial.report',
                method: 'write',
                args: [self.wizard_id, output],
            }).then(function(res){
                self.plot_data(self.initial_render);
            });

        }, // update_with_filter

    }); //DynamicFrMain

core.action_registry.add('dynamic.fr', DynamicFrMain);

return DynamicFrMain;

});
