odoo.define('account_dynamic_reports.DynamicPlMain', function (require) {
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

var DynamicPlMain = AbstractAction.extend({
    template:'DynamicPlMain',

    events: {
        'click #filter_apply_button': 'update_with_filter',
        'click #pdf': 'print_pdf',
        'click #xlsx': 'print_xlsx',
        'click .view-source': 'view_move_line',
        'click .py-mline': 'fetch_move_lines',
        'click .py-mline-page': 'fetch_move_lines_by_page'
    },

    init : function(view, code){
        this._super(view, code);
        this.wizard_id = code.context.wizard_id | null;
        this.session = session;
    },

    start : function(){
	    var self = this;
	    self.initial_render = true;

        if(! self.wizard_id){
            self._rpc({
                model: 'ins.partner.ledger',
                method: 'create',
                args: [{res_model: this.res_model}]
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
            model: 'ins.partner.ledger',
                method: 'get_report_datas',
                args: [[self.wizard_id]],
            }).then(function(data){
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'account_dynamic_reports.partner_ledger',
                    'report_file': 'account_dynamic_reports.partner_ledger',
                    'data': {'js_data':data},
                    'context': {'active_model':'ins.partner.ledger',
                                'landscape':1,
                                'from_js': true
                                },
                    'display_name': 'Partner Ledger',
                };
                return self.do_action(action);
            });
	},

	print_xlsx : function(){
	    var self = this;

	    self._rpc({
            model: 'ins.partner.ledger',
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

        self.loader_disable_ui();

	    // Remove all the child contents first
        var node = self.$('.py-data-container-orig');
        var last;
        while (last = node.lastChild) node.removeChild(last);

        // Initialize wizard with default values
        self._rpc({
            model: 'ins.partner.ledger',
                method: 'get_report_datas',
                args: [[self.wizard_id]],
            }).then(function (datas) {
                self.filter_data = datas[0]
                self.account_data = datas[1]

                _.each(self.account_data, function (k, v){

                    var formatOptions = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };

                    k.debit = self.formatWithSign(k.debit, formatOptions, k.debit < 0 ? '-' : '');
                    k.credit = self.formatWithSign(k.credit, formatOptions, k.credit < 0 ? '-' : '');
                    k.balance = self.formatWithSign(k.balance, formatOptions, k.balance < 0 ? '-' : '');

                    k.ldate = field_utils.format.date(field_utils.parse.date(k.ldate, {}, {isUTC: true}));

                    _.each(k.lines, function (ks, vs){
                        ks.debit = self.formatWithSign(ks.debit, formatOptions, ks.debit < 0 ? '-' : '');
                        ks.credit = self.formatWithSign(ks.credit, formatOptions, ks.credit < 0 ? '-' : '');
                        ks.balance = self.formatWithSign(ks.balance, formatOptions, ks.balance < 0 ? '-' : '');

                        ks.ldate = field_utils.format.date(field_utils.parse.date(ks.ldate, {}, {isUTC: true}));

                    });
                });

                if(initial_render){
                    self.$('.py-control-panel').html(QWeb.render('FilterSectionPl', {
                        filter_data : datas[0],
                        }));

                    self.$el.find('#date_from').datepicker({ dateFormat: 'dd-mm-yy' });
                    self.$el.find('#date_to').datepicker({ dateFormat: 'dd-mm-yy' });

                    self.$el.find('.date_filter-multiple').select2({
                        maximumSelectionSize: 1,
                        placeholder:'Select Date...',
                        });

                    self.$el.find('.extra-multiple').select2({
                        placeholder:'Extra Options...',
                        })
                        .val(['include_details','initial_balance']).trigger('change')
                        ;

                    self.$el.find('.type-multiple').select2({
                        maximumSelectionSize: 1,
                        placeholder:'Select Account Type...',
                        });

                    self.$el.find('.reconciled-multiple').select2({
                        maximumSelectionSize: 1,
                        placeholder:'Select Reconciled...',
                        });

                    self.$el.find('.partner-multiple').select2({
                        placeholder:'Select Partner...',
                        });

                    self.$el.find('.partner-tag-multiple').select2({
                        placeholder:'Select Tag...',
                        });

                    self.$el.find('.account-multiple').select2({
                        placeholder:'Select Account...',
                        });

                    self.$el.find('.journal-multiple').select2({
                        placeholder:'Select Journal...',
                        });
                }

                // Render data lines
                self.$('.py-data-container-orig').html(QWeb.render('DataSectionPl', {
                    account_data : datas[1]
                    }));
                self.loader_enable_ui();

            });

	    }, //start

	pl_lines_by_page : function(offset, account_id){
	    // It is calling form 'fetch_move_lines' for initial fetch and 'fetch_move_lines_by_page' for page based click
	    var self = this;

	    return self._rpc({
            model: 'ins.partner.ledger',
                method: 'build_detailed_move_lines',
                args: [self.wizard_id, offset, account_id],
            })
	},

    fetch_move_lines_by_page : function(event){
	    /* Here this method used for fetching detailed pl lines when click a row. initially only */
	    event.preventDefault();
	    var self = this;
	    var account_id = $(event.currentTarget).data('account-id');
	    var offset = parseInt($(event.currentTarget).data('page-number')) - 1;
	    var total_rows = parseInt($(event.currentTarget).data('count'));

        self.loader_disable_ui();
        self.pl_lines_by_page(offset, account_id).then(function(datas){

            _.each(datas[2], function (k, v){
                var formatOptions = {
                    currency_id: k.company_currency_id,
                    noSymbol: true,
                };
                k.debit = self.formatWithSign(k.debit, formatOptions, k.debit < 0 ? '-' : '');
                k.credit = self.formatWithSign(k.credit, formatOptions, k.credit < 0 ? '-' : '');
                k.balance = self.formatWithSign(k.balance, formatOptions, k.balance < 0 ? '-' : '');

                k.ldate = field_utils.format.date(field_utils.parse.date(k.ldate, {}, {isUTC: true}));
            });

            $(event.currentTarget).parent().parent().parent().find('.py-mline-table-div').remove();
            $(event.currentTarget).parent().parent().find('a').css({'background-color': 'white','font-weight': 'normal'});
            $(event.currentTarget).parent().parent().after(
                QWeb.render('SubSectionPl', {
                count: datas[0],
                offset: datas[1],
                account_data : datas[2],
            }));
            $(event.currentTarget).css({
                'background-color': '#00ede8',
                'font-weight': 'bold',
                });
            self.loader_enable_ui()
        })

	},

	fetch_move_lines : function(event){
	    /* Here this method used for fetching detailed pl lines when click a row. initially only */
	    event.preventDefault();
	    var self = this;
	    var account_id = $(event.currentTarget).data('account-id');
	    var offset = 0;
	    var td = $(event.currentTarget).next('tr').find('td');
	    if (td.length == 1){
	        self.loader_disable_ui();
	        self.pl_lines_by_page(offset, account_id).then(function(datas){

	            _.each(datas[2], function (k, v){
                    var formatOptions = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    k.debit = self.formatWithSign(k.debit, formatOptions, k.debit < 0 ? '-' : '');
                    k.credit = self.formatWithSign(k.credit, formatOptions, k.credit < 0 ? '-' : '');
                    k.balance = self.formatWithSign(k.balance, formatOptions, k.balance < 0 ? '-' : '');

                    k.ldate = field_utils.format.date(field_utils.parse.date(k.ldate, {}, {isUTC: true}));
                });

	            $(event.currentTarget).next('tr').find('td .py-mline-table-div').remove();
	            $(event.currentTarget).next('tr').find('td ul').after(
	                QWeb.render('SubSectionPl', {
                    count: datas[0],
                    offset: datas[1],
                    account_data : datas[2],
                }))
                $(event.currentTarget).next('tr').find('td ul li:first a').css({
                    'background-color': '#00ede8',
                    'font-weight': 'bold',
                    });
                self.loader_enable_ui();
	        })
	    }
	},

	/* Used to redirect to move record */
	view_move_line : function(event){
	    event.preventDefault();
        var self = this;
        var context = {};

        var redirect_to_document = function (res_model, res_id, view_id) {

            var action = {
                type:'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_model: res_model,
                views: [[view_id || false, 'form']],
                res_id: res_id,
                target: 'current',
                context: context,
            };
            self.do_notify(_("Redirected"), "Window has been redirected");
            return self.do_action(action);
        };

        redirect_to_document('account.move',$(event.currentTarget).data('move-id'));

        }, //view_move_line

    update_with_filter : function(event){
        event.preventDefault();
        var self = this;
        self.initial_render = false;
        var output = {date_range:false};

        // defaults
        output.type = false;
        output.display_accounts = 'balance_not_zero';
        output.initial_balance = false;
        output.reconciled = false;
        output.include_details = false;

        // Get reconciled
	    if($(".reconciled-multiple").select2('data').length === 1){
	        output.reconciled = $(".reconciled-multiple").select2('data')[0].id
	    }

        // Get journals
	    var journal_ids = [];
	    var journal_list = $(".journal-multiple").select2('data')
	    for (var i=0; i < journal_list.length; i++){
	        journal_ids.push(parseInt(journal_list[i].id))
	        }
	    output.journal_ids = journal_ids

	    // Get partners
	    var partner_ids = [];
	    var partner_list = $(".partner-multiple").select2('data')
	    for (var i=0; i < partner_list.length; i++){
	        partner_ids.push(parseInt(partner_list[i].id))
	        }
	    output.partner_ids = partner_ids

	    // Get partner Tags
	    var partner_tag_ids = [];
	    var partner_tag_list = $(".partner-tag-multiple").select2('data')
	    for (var i=0; i < partner_tag_list.length; i++){
	        partner_tag_ids.push(parseInt(partner_tag_list[i].id))
	        }
	    output.partner_category_ids = partner_tag_ids

	    // Get accounts
        var account_ids = [];
	    var account_list = $(".account-multiple").select2('data')
	    for (var i=0; i < account_list.length; i++){
	        account_ids.push(parseInt(account_list[i].id))
	        }
	    output.account_ids = account_ids

	    // Get date filter
	    if($(".date_filter-multiple").select2('data').length === 1){
	        output.date_range = $(".date_filter-multiple").select2('data')[0].id
	    }

	    // Get type
	    if($(".type-multiple").select2('data').length === 1){
	        output.type = $(".type-multiple").select2('data')[0].id
	    }

	    // Get optionals
	    var options_list = $(".extra-multiple").select2('data')
	    for (var i=0; i < options_list.length; i++){
	        if(options_list[i].id === 'initial_balance'){
	            output.initial_balance = true;
	            }
	        if(options_list[i].id === 'bal_not_zero'){
	            output.display_accounts = 'balance_not_zero';
	            }
	        if(options_list[i].id === 'include_details'){
	            output.include_details = true;
	            }
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
	    self._rpc({
                model: 'ins.partner.ledger',
                method: 'write',
                args: [self.wizard_id, output],
            }).then(function(res){
                self.plot_data(self.initial_render);
            });

        }, // update_with_filter

    loader_disable_ui: function(){
        $('.py-main-container').addClass('ui-disabled');
        $('.py-main-container').css({'opacity': '0.4','cursor':'wait'});
        $('#loader').css({'visibility':'visible','opacity': '1'});
    },

    loader_enable_ui: function(){
        $('.py-main-container').removeClass('ui-disabled');
        $('#loader').css({'visibility':'hidden'});
        $('.py-main-container').css({'opacity': '1','cursor':'auto'});
    },

    }); //DynamicPlMain

core.action_registry.add('dynamic.pl', DynamicPlMain);

return DynamicPlMain;

});
