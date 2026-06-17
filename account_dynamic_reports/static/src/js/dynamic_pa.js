odoo.define('account_dynamic_reports.DynamicPaMain', function (require) {
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

var DynamicPaMain = AbstractAction.extend({
    template:'DynamicPaMain',

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
                model: 'ins.partner.ageing',
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
            model: 'ins.partner.ageing',
                method: 'get_report_datas',
                args: [[self.wizard_id]],
            }).then(function(data){
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'account_dynamic_reports.partner_ageing',
                    'report_file': 'account_dynamic_reports.partner_ageing',
                    'data': {'js_data':data},
                    'context': {'active_model':'ins.partner.ageing',
                                'landscape':1,
                                'from_js': true
                                },
                    'display_name': 'Partner Ageing',
                };
                return self.do_action(action);
            });
	},

	print_xlsx : function(){
	    var self = this;

	    self._rpc({
            model: 'ins.partner.ageing',
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
            model: 'ins.partner.ageing',
                method: 'get_report_datas',
                args: [[self.wizard_id]],
            }).then(function (datas) {
                self.filter_data = datas[0]
                self.ageing_data = datas[1]
                self.period_dict = datas[2]
                self.period_list = datas[3]

                _.each(self.ageing_data, function (k, v){
                    var formatOptions = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    for(var z = 0; z < self.period_list.length; z++){
                        //k[self.period_list[z]] = field_utils.format.monetary(Math.abs(k[self.period_list[z]]), {}, formatOptions);
                        k[self.period_list[z]] = self.formatWithSign(k[self.period_list[z]], formatOptions, k[self.period_list[z]] < 0 ? '-' : '');
                    }
                    //k.total = field_utils.format.monetary(Math.abs(k.total), {}, formatOptions);
                    k.total = self.formatWithSign(k.total, formatOptions, k.total < 0 ? '-' : '');


                });

                if(initial_render){
                    self.$('.py-control-panel').html(QWeb.render('FilterSectionPa', {
                        filter_data : self.filter_data,
                        }));

                    self.$el.find('#as_on_date').datepicker({ dateFormat: 'dd-mm-yy' });

                    self.$el.find('.type-multiple').select2({
                        maximumSelectionSize: 1,
                        placeholder:'Select Account Type...',
                        });

                    self.$el.find('.partner-type-multiple').select2({
                        maximumSelectionSize: 1,
                        placeholder:'Select Partner Type...',
                        });

                    self.$el.find('.partner-multiple').select2({
                        placeholder:'Select Partner...',
                        });

                    self.$el.find('.partner-tag-multiple').select2({
                        placeholder:'Select Tag...',
                        });

                    self.$el.find('.extra-multiple').select2({
                        placeholder:'Extra Options...',
                        })
                        .val('include_details').trigger('change')
                        ;
                }

                // Render data lines
                self.$('.py-data-container-orig').html(QWeb.render('DataSectionPa', {
                    ageing_data : self.ageing_data,
                    period_dict : self.period_dict,
                    period_list : self.period_list
                    }));
                self.loader_enable_ui();

            });

	    }, //start

	ageing_lines_by_page : function(offset, account_id){
	    // It is calling from 'fetch_move_lines' for initial fetch and 'fetch_move_lines_by_page' for page based click
	    var self = this;

	    return self._rpc({
            model: 'ins.partner.ageing',
                method: 'process_detailed_data',
                args: [self.wizard_id, offset, account_id],
            })
	},

    fetch_move_lines_by_page : function(event){
	    /* Here this method used for fetching detailed gl lines when click a page button. */
	    event.preventDefault();
	    var self = this;
	    var partner_id = $(event.currentTarget).data('partner-id');
	    var offset = parseInt($(event.currentTarget).data('page-number')) - 1;
	    var total_rows = parseInt($(event.currentTarget).data('count'));

        self.loader_disable_ui();
        self.ageing_lines_by_page(offset, partner_id).then(function(datas){

            var count = datas[0];
            var offset = datas[1];
            var account_data = datas[2];
            var period_list = datas[3];

            _.each(account_data, function (k, v){
                var formatOptions = {
                    currency_id: k.company_currency_id,
                    noSymbol: true,
                };
                k.range_0 = self.formatWithSign(k.range_0, formatOptions, k.range_0 < 0 ? '-' : '');
                k.range_1 = self.formatWithSign(k.range_1, formatOptions, k.range_1 < 0 ? '-' : '');
                k.range_2 = self.formatWithSign(k.range_2, formatOptions, k.range_2 < 0 ? '-' : '');
                k.range_3 = self.formatWithSign(k.range_3, formatOptions, k.range_3 < 0 ? '-' : '');
                k.range_4 = self.formatWithSign(k.range_4, formatOptions, k.range_4 < 0 ? '-' : '');
                k.range_5 = self.formatWithSign(k.range_5, formatOptions, k.range_5 < 0 ? '-' : '');
                k.range_6 = self.formatWithSign(k.range_6, formatOptions, k.range_6 < 0 ? '-' : '');

                k.date_maturity = field_utils.format.date(field_utils.parse.date(k.date_maturity, {}, {isUTC: true}));
            });

            $(event.currentTarget).parent().parent().parent().find('.py-mline-table-div').remove();
            $(event.currentTarget).parent().parent().find('a').css({'background-color': 'white','font-weight': 'normal'});
            $(event.currentTarget).parent().parent().after(
                QWeb.render('SubSectionPa', {
                count: count,
                offset: offset,
                account_data : account_data,
                period_list: period_list
            }));
            $(event.currentTarget).css({
                'background-color': '#00ede8',
                'font-weight': 'bold',
                });
            self.loader_enable_ui()
        })

	},

	fetch_move_lines : function(event){
	    /* Here this method used for fetching detailed gl lines when click a row. initially only */
	    event.preventDefault();
	    var self = this;
	    var partner_id = $(event.currentTarget).data('partner-id');
	    var offset = 0;
	    var td = $(event.currentTarget).next('tr').find('td');
	    if (td.length == 1){
	        self.loader_disable_ui();
	        self.ageing_lines_by_page(offset, partner_id).then(function(datas){
	            var count = datas[0];
                var offset = datas[1];
                var account_data = datas[2];
                var period_list = datas[3];

	            _.each(account_data, function (k, v){
                    var formatOptions = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    k.range_0 = self.formatWithSign(k.range_0, formatOptions, k.range_0 < 0 ? '-' : '');
                    k.range_1 = self.formatWithSign(k.range_1, formatOptions, k.range_1 < 0 ? '-' : '');
                    k.range_2 = self.formatWithSign(k.range_2, formatOptions, k.range_2 < 0 ? '-' : '');
                    k.range_3 = self.formatWithSign(k.range_3, formatOptions, k.range_3 < 0 ? '-' : '');
                    k.range_4 = self.formatWithSign(k.range_4, formatOptions, k.range_4 < 0 ? '-' : '');
                    k.range_5 = self.formatWithSign(k.range_5, formatOptions, k.range_5 < 0 ? '-' : '');
                    k.range_6 = self.formatWithSign(k.range_6, formatOptions, k.range_6 < 0 ? '-' : '');

                    k.date_maturity = field_utils.format.date(field_utils.parse.date(k.date_maturity, {}, {isUTC: true}));

                });

	            $(event.currentTarget).next('tr').find('td .py-mline-table-div').remove();
	            $(event.currentTarget).next('tr').find('td ul').after(
	                QWeb.render('SubSectionPa', {
                    count: count,
                    offset: offset,
                    account_data: account_data,
                    period_list: period_list
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
        var output = {}

        // defaults
        output.type = false;
        output.include_details = false;
        output.partner_type = false;

        // Get buckets
        output.bucket_1 = $("#bucket_1").val();
        output.bucket_2 = $("#bucket_2").val();
        output.bucket_3 = $("#bucket_3").val();
        output.bucket_4 = $("#bucket_4").val();
        output.bucket_5 = $("#bucket_5").val();

        if((parseInt(output.bucket_1) >= parseInt(output.bucket_2)) | (parseInt(output.bucket_2) >= parseInt(output.bucket_3)) |
                (parseInt(output.bucket_3) >= parseInt(output.bucket_4)) | (parseInt(output.bucket_4) >= parseInt(output.bucket_5))){
            alert('Bucket order must be ascending');
            return;
        }

        // Get type
	    if($(".type-multiple").select2('data').length === 1){
	        output.type = $(".type-multiple").select2('data')[0].id
	    }

	    // Get partner type
	    if($(".partner-type-multiple").select2('data').length === 1){
	        output.partner_type = $(".partner-type-multiple").select2('data')[0].id
	    }

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

	    // Get custom dates
	    if ($("#as_on_date").val()){
	        var dateObject = $("#as_on_date").datepicker("getDate");
            var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
	        output.as_on_date = dateString;
	    }

	    // Get optionals
	    var options_list = $(".extra-multiple").select2('data')
	    for (var i=0; i < options_list.length; i++){
	        if(options_list[i].id === 'include_details'){
	            output.include_details = true;
	            }
	        }

	    self._rpc({
                model: 'ins.partner.ageing',
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

    }); //DynamicPaMain

core.action_registry.add('dynamic.pa', DynamicPaMain);

return DynamicPaMain;

});
