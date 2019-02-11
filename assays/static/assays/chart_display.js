// Contains functions for making charts for data
// TODO TODO TODO THE USE OF THE WORD "options" IS CONFUSING
// DO NOT DESCRIBE AJAX CRITERIA *AND* CHART OPTIONS AS OPTIONS PLEASE

// TODO TODO TODO REFACTOR ALL STUFF REGARDING "OPTIONS"

// Global variable for charts
window.CHARTS = {
    study_id: '',
    matrix_id: '',
    matrix_item_id: '',
    filter: '{}',
    call: '',
    global_options: {}
};

// Load the Visualization API and the corechart package.
// google.charts.load('current', {'packages':['corechart']});

// Set a callback to run when the Google Visualization API is loaded.
// THE CALLBACK FUNCTION IS NOT DEFINED HERE BUT IN THE RESPECTIVE MAIN FILE
// SUBJECT TO CHANGE
// google.charts.setOnLoadCallback(window.CHARTS.callback);

$(document).ready(function () {
    // Charts
    // SUBJECT TO REVISION
    // Maybe would be more intelligible to have a single object?
    var all_charts = {
        charts: [],
        popup: []
    };
    var all_events = {
        // charts: [],
        // popup: []
        charts: {
            'in': [],
            'out': []
        },
        popup: {
            'in': [],
            'out': []
        }
    };
    var all_options = {
        charts: [],
        popup: []
    };

    var all_data = {
        charts: [],
        popup: []
    };

    // Contrived
    var conversion_to_label = {
        1: 'Time (Days)',
        24: 'Time (Hours)',
        1440: 'Time (Minutes)',
    };

    // BOOLEAN INDICATING WHETHER THE SIDEBAR IS FOR GLOBAL OR LOCAL
    var side_bar_global = true;

    // Semi-arbitrary at the moment
    var treatment_group_table = $('#treatment_group_table');
    var treatment_group_display = $('#treatment_group_display');
    var treatment_group_head = $('#treatment_group_head');
    var treatment_group_data_table = null;

    var group_display = $('#group_display');
    var group_display_body = $('#group_display_body');
    var group_display_head = $('#group_display_head');

    var show_hide_plots_popup = $('#show_hide_plots_popup');
    var show_hide_plots_table = $('#show_hide_plots_popup table');
    var show_hide_plots_body = $('#show_hide_plots_popup table tbody');
    var show_hide_plots_data_table = null;

    var chart_visibility = {};
    var chart_filter_buffer = {};

    // NOTE: At the moment superfluous, HOWEVER: will become useful if we need to keep show/hide after refresh
    var name_to_chart = {};

    function apply_show_hide() {
        // Iterate over the charts to hide
        chart_visibility = $.extend(true, {}, chart_filter_buffer);

        $.each(chart_visibility, function(chart_name, status) {
            var chart_id = name_to_chart[chart_name];
            if (status) {
                $(chart_id).show('slow');
            }
            else {
                $(chart_id).hide('slow');
            }
        });
    }

    // Some global options of note
    // TODO MAKE SURE REVISIONS ARE PROPER
    window.CHARTS.global_options = {
        // TOO SPECIFIC, OBVIOUSLY
        // title: assay,
        interpolateNulls: true,
        // Changes styling and prevents flickering issue
        // tooltip: {
        //     isHtml: true
        // },
        titleTextStyle: {
            fontSize: 18,
            bold: true,
            underline: true
        },
        // curveType: 'function',
        legend: {
            position: 'top',
            maxLines: 5,
            textStyle: {
                // fontSize: 8,
                bold: true
            }
        },
        hAxis: {
            // Begins empty
            title: 'Time (Days)',
            textStyle: {
                bold: true
            },
            titleTextStyle: {
                fontSize: 14,
                bold: true,
                italic: false
            }
            // ADD PROGRAMMATICALLY
            // viewWindowMode:'explicit',
            // viewWindow: {
            //     max: current_max_x + 0.05 * current_x_range,
            //     min: current_min_x - 0.05 * current_x_range
            // }
            // baselineColor: 'none',
            // ticks: []
        },
        vAxis: {
            title: '',
            // If < 1000 and > 0.001 don't use scientific! (absolute value)
            // y_axis_label_type
            format: '',
            textStyle: {
                bold: true
            },
            titleTextStyle: {
                fontSize: 14,
                bold: true,
                italic: false
            },
            // This doesn't seem to interfere with displaying negative values
            minValue: 0,
            viewWindowMode: 'explicit'
            // baselineColor: 'none',
            // ticks: []
        },
        pointSize: 5,
        'chartArea': {
            'width': '75%',
            'height': '65%'
        },
        'height': min_height,
        // Individual point tooltips, not aggregate
        focusTarget: 'datum',
        intervals: {
            // style: 'bars'
            'lineWidth': 0.75
        },
        tracking: {
            is_default: true,
            use_dose_response: false,
            // A little too odd
            // use_percent_control: false,
            time_conversion: 1,
            chart_type: 'scatter',
            tooltip_type: 'datum',
            revised_unit: null
        },
        ajax_data: {
            key: 'device',
            mean_type: 'arithmetic',
            interval_type: 'ste',
            number_for_interval: '1',
            percent_control: '',
            truncate_negative: ''
        }
    };

    if (show_hide_plots_popup[0]) {
        show_hide_plots_popup.dialog({
            // Causes problems on small devices
            width: 825,
            close: function () {
                // Purge the buffer
                chart_filter_buffer = {};
                $.ui.dialog.prototype.options.close();
            },
            buttons: [
            {
                text: 'Apply',
                click: function() {
                    apply_show_hide();
                    $(this).dialog("close");
                }
            },
            {
                text: 'Cancel',
                click: function() {
                   $(this).dialog("close");
                }
            }]
        });
        show_hide_plots_popup.removeProp('hidden');
    }

    // Probably should just have full data!
    var group_to_data = {
        charts: [],
        popup: []
    };
    var device_to_group = {};
    var all_treatment_groups = [];

    var min_height = 400;

    // Conversion dictionary
    // TERRIBLE, SPAGHETTI CODE
    // TERRIBLE, SPAGHETTI CODE
    // TERRIBLE, SPAGHETTI CODE
    var headers = {
        // 'device': 'Device',
        'Study': 'Study',
        'Matrix': 'Matrix',
        'MPS Model': 'MPS Model',
        'Cells': 'Cells Added',
        'Compounds': 'Compound Treatment',
        'Settings': 'Settings (Non-Compound Treatments)',
        'Items with Same Treatment': 'Matrix Items (Chips/Wells) in Group'
    };

    // var filter_popup_header = filter_popup.find('h5');

    // Prepare individual plot stuff
    var current_chart = null;
    var current_chart_id = null;
    var current_chart_name = null;
    // var current_chart_options = null;
    var individual_plot_type = $('#individual_plot_type');
    var individual_plot_popup = $('#individual_plot_popup');

    var popup_chart = null;

    var plot_is_visible = $('#plot_is_visible');
    var use_percent_control = $('#use_percent_control');
    var use_dose_response = $('#use_dose_response');

    var individual_plot_popup_options_section = $('#individual_plot_popup_options_section');
    var individual_plot_popup_plot_section = $('#individual_plot_popup_plot_section');
    // var individual_plot_popup_plot_container = $('#individual_plot_popup_plot_container');
    var individual_plot_popup_plot_container = $('#popup_0');

    var specific_graph_properties_container = $('#specific_graph_properties_container');

    // TODO NEED TO DEAL GRACEFULLY WITH REFRESH TODO
    function refresh_preview() {
        // Kill events
        destroy_events('popup');

        // Clear all charts
        // OBJECTIVELY DUMB
        all_charts['popup'] = [];
        all_events['popup'] = {
            'in': [],
            'out': []
        };

        all_options['popup'] = [null];

        group_to_data['popup'] = [];

        individual_plot_popup_options_section.hide();
        individual_plot_popup_plot_section.show();

        // Goofy
        all_options['popup'][0] = window.CHARTS.prepare_chart_options();

        get_individual_chart('popup', individual_plot_popup_plot_container[0], all_options['popup'][0]);

        $('#back_to_options_button').show('slow');

        // Change button text
        $('#view_preview_button').find('.ui-button-text').text('Refresh');
    }

    if (individual_plot_popup[0]) {
        individual_plot_popup.dialog({
            // Causes problems on small devices
            width: 825,
            close: function () {
                $.ui.dialog.prototype.options.close();

                side_bar_global = true;

                // Remove bg-info from sidebar stuff
                $('#charting_sidebar_section').removeClass('bg-info');
                // specific_graph_properties_container.hide('slow');

                apply_options_to_sidebar(window.CHARTS.global_options, false);
            },
            open: function () {
                $.ui.dialog.prototype.options.open();

                individual_plot_popup_options_section.show('slow');
                individual_plot_popup_plot_section.hide('slow');
                // Plot needs to be visible for you to, you know, see it here
                plot_is_visible.prop('checked', true);
                side_bar_global = false;

                // Add bg-info from sidebar stuff
                $('#charting_sidebar_section').addClass('bg-info');
                // specific_graph_properties_container.show('slow');

                $('#back_to_options_button').hide();

                // Apply options to sidebar
                apply_options_to_sidebar(all_options['charts'][current_chart_id], true);

                // Change button text
                $('#view_preview_button').find('.ui-button-text').text('View Preview');
            },
            buttons: [
            {
                // text: 'Make Popup Plot',
                text: 'View Preview',
                id: 'view_preview_button',
                click: refresh_preview
            },
            {
                text: 'Apply to Plot',
                click: function() {
                    // Kill events
                    // $.each(all_events['charts'], function(event_type, current_events) {
                    //     if (current_events[current_chart_id]) {
                    //         google.visualization.events.removeListener(current_events[current_chart_id]);
                    //         current_events[current_chart_id] = null;
                    //     }
                    // });
                    // destroy_events('charts');

                    // A little goofy
                    all_options['charts'][current_chart_id] = window.CHARTS.prepare_chart_options();
                    all_options['charts'][current_chart_id].tracking.is_default = false;

                    if (!plot_is_visible.prop('checked')) {
                        // HIDE THE CHART
                        // A LITTLE MESSY TO MAKE SURE THAT THE SHOW/HIDE PLOTS MATCHES
                        show_hide_plots_data_table.page.len(-1).draw();

                        $('.chart-filter-checkbox[data-table-index="' + current_chart_id + '"]').trigger('click');

                        apply_show_hide();

                        show_hide_plots_data_table.order([[1, 'asc']]);
                        show_hide_plots_data_table.page.len(10).draw();
                    }
                    else {
                        // Tricky, may create unpleasant scenarios however...
                        get_individual_chart('charts', current_chart, all_options['charts'][current_chart_id]);
                    }

                    // Apply new events
                    // prep_event('charts', false, current_chart_id);
                    // create_events('charts', false);

                    $(this).dialog("close");
                }
            },
            {
                text: 'Back to Options',
                id: 'back_to_options_button',
                click: function() {
                    // NOTE NOT DRY
                    individual_plot_popup_options_section.show('slow');
                    individual_plot_popup_plot_section.hide('slow');

                    $('#back_to_options_button').hide('slow');

                    $('#view_preview_button').find('.ui-button-text').text('View Preview');
                }
            },
            {
                text: 'Revert to Default',
                id: 'revert_to_default_button',
                click: function() {
                    use_dose_response.prop('checked', false);
                    use_percent_control.prop('checked', false);

                    apply_options_to_sidebar(window.CHARTS.global_options, false);

                    // Apply to the preview if the preview is up
                    if ($('#back_to_options_button').is(':visible')) {
                        refresh_preview();
                    }
                }
            },
            {
                text: 'Cancel',
                click: function() {
                   $(this).dialog("close");
                }
            }]
        });
        individual_plot_popup.removeProp('hidden');
    }

    function get_individual_chart(charts, chart_selector, options) {
        // DESTROY EVENTS
        destroy_events(charts);

        var index_to_use = current_chart_id;

        var individual_post_filter = $.extend(true, {}, window.GROUPING.current_post_filter);

        // TODO TODO TODO METHODS
        // Modify post filter to be for only current plot
        var current_ids_of_interest = all_data['charts'].assay_ids[current_chart_name];

        individual_post_filter.assay.target_id__in = {};
        individual_post_filter.assay.target_id__in[current_ids_of_interest.target] = '';

        individual_post_filter.assay.unit_id__in = {};
        individual_post_filter.assay.unit_id__in[current_ids_of_interest.unit] = '';

        if (current_ids_of_interest.method) {
            individual_post_filter.assay.method_id__in = {};
            individual_post_filter.assay.method_id__in[current_ids_of_interest.method] = '';
        }

        var data = {
            // Only for when filter is needed, but still (will never have repro intention)
            intention: 'charting',
            // TODO TODO TODO CHANGE CALL
            call: window.CHARTS.call,
            // TODO TODO TODO NEED TO GET
            study: window.CHARTS.study_id,
            // TODO TODO TODO MIGHT BE USING A FILTER
            filters: window.CHARTS.filters,
            // TODO MATRIX AND MATRIX ITEM
            matrix: window.CHARTS.matrix_id,
            matrix_item: window.CHARTS.matrix_item_id,
            criteria: JSON.stringify(window.GROUPING.get_grouping_filtering()),
            post_filter: JSON.stringify(individual_post_filter),
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };

        // ONLY APPLICABLE TO IN PLACE CHANGES
        // if (!options) {
        //     options = window.CHARTS.prepare_chart_options('charts');
        // }

        // NOTE THAT FALSE IS ACTUALY AN EMPTY STRING
        options.ajax_data.percent_control = use_percent_control.prop('checked') ? true : '';

        data = $.extend(true, data, options.ajax_data);

        options.tracking.use_dose_response = use_dose_response.prop('checked');

        if (options.tracking.use_dose_response) {
            data.key = 'dose';
            // Change hAxis title
            options.hAxis.title = 'Dose (µM)';
        }

        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );

        // TODO TODO TODO
        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                // Stop spinner
                window.spinner.stop();

                // Empty the chart
                $(chart_selector).empty();

                // Always 0 index methinks for popup
                if (charts === 'popup') {
                    index_to_use = 0;
                    // Store all data if popup
                    all_data[charts] = $.extend(true, {}, json);
                }
                else {
                    // Store just the numbers if in-place change
                    if (json.assays && json.assays[0]) {
                        all_data[charts].assays[index_to_use] = json.assays[0];
                    }
                    else {
                        all_data[charts].assays[index_to_use] = [];
                    }
                }

                // Not a great exception
                if (options.ajax_data.percent_control) {
                    var assay_unit = json.sorted_assays[0];
                    var assay = assay_unit.split('\n')[0];
                    var unit = assay_unit.split('\n')[1];
                    options.tracking.revised_unit = unit;
                }
                else {
                    delete options.tracking.revised_unit;
                }

                // Make the plot
                build_individual_chart(charts, chart_selector, index_to_use, options);

                create_events(charts, charts==='popup');
            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();

                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    function build_individual_chart(charts, chart_selector, index, options) {
        // Clear old chart (when applicable)
        $(chart_selector).empty();

        // Aliases
        var sorted_assays = all_data[charts].sorted_assays;
        // Note that this keeps the original data (to avoid refreshes etc.)
        // var assays = JSON.parse(JSON.stringify(all_data[charts].assays));
        var assay_data = JSON.parse(JSON.stringify(all_data[charts].assays[index]));

        // Don't bother if empty
        if (assay_data[1] === undefined) {
            return;
        }

        var assay_unit = sorted_assays[index];
        var assay = assay_unit.split('\n')[0];
        var unit = assay_unit.split('\n')[1];

        if (options.tracking.revised_unit) {
            unit = options.tracking.revised_unit;
        }

        if (!options) {
            options = $.extend(true, {}, window.CHARTS.global_options);
        }

        all_options[charts][index] = options;

        // REVISE TIME AS NECESSARY
        $.each(assay_data, function(assay_index, row) {
            if (assay_index) {
                if (!options.tracking.use_dose_response) {
                    row[0] *= options.tracking.time_conversion;
                }
            }
            else {
                row[0] = options.hAxis.title;
            }
        });

        // Go through y values
        $.each(assay_data.slice(1), function(current_index, current_values) {
            // Idiomatic way to remove NaNs
            var trimmed_values = current_values.slice(1).filter(isNumber);

            var current_max_y = Math.abs(Math.max.apply(null, trimmed_values));
            var current_min_y = Math.abs(Math.min.apply(null, trimmed_values));

            if (current_max_y > 1000 || current_max_y < 0.001) {
                options.vAxis.format = '0.00E0';
                return false;
            }
            else if (Math.abs(current_max_y - current_min_y) < 10 && Math.abs(current_max_y - current_min_y) > 0.1 && Math.abs(current_max_y - current_min_y) !== 0) {
                options.vAxis.format = '0.00';
                return false;
            }
            else if (Math.abs(current_max_y - current_min_y) < 0.1 && Math.abs(current_max_y - current_min_y) !== 0) {
                options.vAxis.format = '0.00E0';
                return false;
            }
        });

        var current_min_x = assay_data[1][0];
        var current_max_x = assay_data[assay_data.length - 1][0];
        var current_x_range = current_max_x - current_min_x;

        // Tack on change
        options.title = assay;
        options.vAxis.title = unit;

        // NAIVE: I shouldn't perform a whole refresh just to change the scale!
        // if (document.getElementById('category_select').checked) {
        //     options.focusTarget = 'category';
        // }

        // Removed for now
/*
        if (document.getElementById(charts + 'log_x').checked) {
            options.hAxis.scaleType = 'log';
        }
        if (document.getElementById(charts + 'log_y').checked) {
            options.vAxis.scaleType = 'log';
        }
*/

        // Merge options with the specified changes
        // REMOVED FOR NOW
        // $.extend(options, changes_to_options);

        // REMOVED FOR NOW
        // Find out whether to shrink text
        // $.each(assay_data[0], function(index, column_header) {
        //     if (column_header.length > 12) {
        //         options.legend.textStyle.fontSize = 10;
        //     }
        // });

        var chart = null;

        var num_colors = 0;

        $.each(assay_data[0].slice(1), function(index, value) {
            if (value.indexOf('     ~@i1') === -1) {
                num_colors++;
            }
        });

        var data = google.visualization.arrayToDataTable(assay_data);

        // Line chart if more than two time points and less than 101 colors
        if (assay_data.length > 3 && num_colors < 101) {
            chart = new google.visualization.LineChart(chart_selector);

            // Change the options
            options.hAxis.viewWindowMode = 'explicit';
            options.hAxis.viewWindow = {
                max: current_max_x + 0.1 * current_x_range,
                min: current_min_x - 0.1 * current_x_range
            };
        }
        // Nothing if more than 100 colors
        else if (num_colors > 100) {
            chart_selector.innerHTML = '<div class="alert alert-danger" role="alert">' +
                '<span class="glyphicon glyphicon-warning-sign" aria-hidden="true"></span>' +
                '<span class="sr-only">Danger:</span>' +
                ' <strong>' + assay + ' ' + unit + '</strong>' +
                '<br>This plot has too many data points, please try filtering.' +
            '</div>'
        }
        // Bar chart if only one time point
        else if (assay_data.length > 1) {
            // Crude...
            delete options.hAxis.viewWindow;
            // Convert to categories
            data.insertColumn(0, 'string', data.getColumnLabel(0));
            // copy values from column 1 (old column 0) to column 0, converted to numbers
            for (var i = 0; i < data.getNumberOfRows(); i++) {
                var val = data.getValue(i, 1);
                // I don't mind this type-coercion, null, undefined (and maybe 0?) don't need to be parsed
                if (val != null) {
                    // PLEASE NOTE: Floats are truncated to 3 decimals
                    data.setValue(i, 0, parseFloat(val.toFixed(3)) + ''.valueOf());
                }
            }
            // remove column 1 (the old column 0)
            data.removeColumn(1);

            chart = new google.visualization.ColumnChart(chart_selector);
        }

        if (chart) {
            var dataView = new google.visualization.DataView(data);

            // Change interval columns to intervals
            var interval_setter = [0];

            i = 1;
            while (i < data.getNumberOfColumns()) {
                interval_setter.push(i);
                if (i + 2 < data.getNumberOfColumns() && assay_data[0][i+1].indexOf('     ~@i1') > -1) {
                    interval_setter.push({sourceColumn: i + 1, role: 'interval'});
                    interval_setter.push({sourceColumn: i + 2, role: 'interval'});
                    i += 2;
                }
                i += 1;
            }
            dataView.setColumns(interval_setter);

            chart.draw(dataView, options);

            chart.chart_index = index;

            // SLOPPY
            // Add new
            if (!all_charts[charts][index]) {
                all_charts[charts].push(chart);
                // Add the options
                // all_options[charts].push(options);
            }
            // Modify existing
            else {
                all_charts[charts][index] = chart;
                // Add the options
                // all_options[charts][index] = options;
            }
        }
    }

    window.CHARTS.prepare_chart_options = function() {
        var options = $.extend(true, {}, window.CHARTS.global_options);

        //$.each($('#' + charts + 'chart_options').find('input'), function() {
        // Object extraneous as there is only one option set now
        $.each($('#charting_options_tables').find('input'), function() {
            // var current_category = $(this).attr('data-category');
            var current_category = 'ajax_data';
            // For radio and checkboxes
            if (this.checked) {
                options[current_category][this.name] = this.value;
            }
            // For numeric
            else if (this.type === 'number') {
                options[current_category][this.name] = this.value;
            }
        });

        options.hAxis.title = 'Time (Days)';
        // Still need to work in dose-response
        // if (window.CHARTS.global_options.tracking.is_dose) {
        //     window.CHARTS.global_options.hAxis.title = 'Dose (μM)';
        // }

        var time_conversion = 1;
        var time_label = 'Time (Days)';

        // CRUDE: Perform time unit conversions
        // GLOBALLY APPLYING THIS WILL CONFILICT WITH THE INDIVIDUAL CHART CHANGES (possibly)
        // TODO TODO TODO MUST BE MOVED
        time_conversion = Math.floor($('#id_chart_option_time_unit').val());

        time_label = conversion_to_label[time_conversion];

        if (time_conversion) {
            options.tracking.time_conversion = time_conversion;
            options.hAxis.title = time_label;
        }

        // NAIVE: I shouldn't perform a whole refresh just to change the scale!
        if (document.getElementById('category_select').checked) {
            options.focusTarget = 'category';
        }
        else {
            options.focusTarget = 'datum';
        }

        return options;
    };

    // TODO I NEED THIS FUNCTION TO MAKE SURE THAT THE SIDEBAR MATCHES THE POPUP/GLOBAL
    function apply_options_to_sidebar(options, popup) {
        $.each(options.ajax_data, function(field_name, value) {
            var current = $('input[name="' + field_name + '"][value="' + value + '"]');
            if (current[0]) {
                // Note that this does not trigger change
                $('input[name="' + field_name + '"][value="' + value + '"]').prop('checked', true);
            }
            else {
                current = $('input[name="' + field_name + '"]');
                if (current.attr('type') === 'checkbox') {
                    current.prop('checked', value);
                }
                else {
                    current.val(value);
                }
            }
        });

        // SPECIAL EXCEPTION FOR TIMEUNIT
        $('#id_chart_option_time_unit').find('option[value="' + options.tracking.time_conversion + '"]').prop('selected', true);

        // TODO YOU ALSO NEED TO MAKE SURE THE POPUP IS CHANGED (percent control etc.)
        if (popup) {
            // PLEASE NOTE THAT IT IS EMPTY STRING, NOT FALSE
            use_percent_control.prop('checked', options.ajax_data.percent_control ? true : '');
            // Check if using dose
            use_dose_response.prop('checked', options.tracking.use_dose_response);
        }

        // Make sure proper options are greyed out
        restrict_error_bar_options(false);
    }

    window.CHARTS.prepare_side_by_side_charts = function(json, charts) {
        // Store all data
        all_data[charts] = $.extend(true, {}, json);

        // Clear existing charts
        var charts_id = $('#' + charts);
        charts_id.empty();

        // If errors, report them and then terminate
        if (json.errors) {
            alert(json.errors);
            return;
        }

        var sorted_assays = json.sorted_assays;
        var assays = json.assays;

        // Hide sidebar if no data
        if (assays.length < 1) {
            $('.toggle_sidebar_button').first().trigger('click');
        }

        // Revise show/hide plots
        // NOTE: POPULATE THE SELECTION TABLE
        // Clear current contents
        if (show_hide_plots_data_table) {
            show_hide_plots_data_table.clear();
            show_hide_plots_data_table.destroy();

            // KILL ALL LINGERING HEADERS
            $('.fixedHeader-locked').remove();
        }

        show_hide_plots_body.empty();

        var html_to_append = [];

        for (var index in sorted_assays) {
            if (assays[index].length > 1) {
                // Populate each row
                // SLOPPY NOT DRY
                var row = '<tr>';
                var full_name = sorted_assays[index];
                var title = full_name.split('\n')[0];
                var unit = full_name.split('\n')[1];

                var current_index = html_to_append.length;

                charts_id.append($('<div>')
                    .attr('id', charts + '_' + index)
                    .attr('data-chart-name', full_name)
                    .addClass('col-sm-12 col-md-6 chart-container')
                    .css('min-height', min_height)
                );

                row += '<td width="10%" class="text-center"><input data-table-index="' + current_index + '" data-obj-name="' + full_name + '" class="big-checkbox chart-filter-checkbox" type="checkbox" value="' + full_name + '" checked="checked"></td>';

                // WARNING: NAIVE REPLACE
                row += '<td>' + title + '</td>';
                row += '<td>' + unit + '</td>';

                row += '</tr>';

                name_to_chart[full_name] = '#charts_' + current_index;

                html_to_append.push(row);
            }
        }

        if (!html_to_append) {
            html_to_append.push('<tr><td></td><td>No data to display.</td></tr>');
        }

        show_hide_plots_body.html(html_to_append.join(''));

        show_hide_plots_data_table = show_hide_plots_table.DataTable({
            destroy: true,
            dom: '<"wrapper"lfrtip>',
            deferRender: true,
            iDisplayLength: 10,
            order: [1, 'asc'],
            columnDefs: [
                // Try to sort on checkbox
                { "sSortDataType": "dom-checkbox", "targets": 0, "width": "10%" }
            ]
        });
    };

    window.CHARTS.prepare_row_by_row_charts = function(json, charts) {
        // Clear existing charts
        var charts_id = $('#' + charts);
        charts_id.empty();

        // If errors, report them and then terminate
        if (json.errors) {
            alert(json.errors);
            return;
        }

        var sorted_assays = json.sorted_assays;
        var assays = json.assays;

        var previous = null;
        for (var index in sorted_assays) {
            if (assays[index].length > 1) {
                new_div = $('<div>')
                //.addClass('padded-row')
                    .css('min-height', min_height);
                charts_id.append(new_div
                    .append($('<div>')
                        .attr('id', charts + '_' + index)
                        .addClass('chart-container')
                    )
                );
            }
        }
    }

    // No longer in use
    window.CHARTS.prepare_charts_by_table = function(json, charts) {
        // Clear existing charts
        var charts_id = $('#' + charts);
        charts_id.empty();

        // If errors, report them and then terminate
        if (json.errors) {
            alert(json.errors);
            return;
        }

        var sorted_assays = json.sorted_assays;
        var assays = json.assays;

        for (var index in sorted_assays) {
            if (assays[index].length > 1) {
                $('<div>')
                    .attr('id', charts + '_' + index)
                    .attr('align', 'right')
                    .addClass('chart-container')
                    .appendTo(charts_id);
            }
        }
    };

    window.CHARTS.display_treatment_groups = function(treatment_groups, header_keys) {
        device_to_group = {};
        all_treatment_groups = [];

        // TODO KIND OF UGLY
        if (!header_keys) {
            header_keys = [
                // 'device',
                'MPS Model',
                'Cells',
                'Compounds',
                'Settings',
                'Items with Same Treatment'
            ];
        }

        if (treatment_group_data_table) {
            treatment_group_table.DataTable().clear();
            treatment_group_table.DataTable().destroy();

            // KILL ALL LINGERING HEADERS
            $('.fixedHeader-locked').remove();
        }

        treatment_group_display.empty();

        treatment_group_head.empty();

        var new_row =  $('<tr>').append(
            $('<th>').html('Group')
        );

        $.each(header_keys, function(index, item) {
            var new_td = $('<th>').html(headers[item]);
            new_row.append(new_td);
        });

        treatment_group_head.append(new_row);
        // Add the header to the group display as well
        group_display_head.empty();
        group_display_head.append(new_row.clone().addClass('bg-warning'));

        $.each(treatment_groups, function(index, treatment) {
            var group_index = (index + 1);
            var group_name = 'Group ' + group_index;
            var group_id = group_name.replace(' ', '_');

            var new_row = $('<tr>')
                .attr('id', group_id)
                .append(
                $('<td>').html(group_name)
            );

            $.each(header_keys, function(header_index, current_header) {
                // Replace newlines with breaks
                var new_td = $('<td>').html(treatment[current_header].split("\n").join("<br />"));
                new_row.append(new_td);

                // Somewhat sloppy conditional
                if (current_header === 'Items with Same Treatment') {
                    $.each(new_td.find('a'), function (anchor_index, anchor) {
                        device_to_group[anchor.text] = index;
                    });
                }
            });

            all_treatment_groups.push(new_row.clone());
            // group_to_data[group_index] = new_row.clone();

            treatment_group_display.append(new_row);
        });

        treatment_group_data_table = treatment_group_table.DataTable({
            // Cuts out extra unneeded pieces in the table
            dom: 'B<"row">lfrtip',
            fixedHeader: {headerOffset: 50},
            responsive: true,
            // paging: false,
            order: [[ 0, "asc" ]],
            // Needed to destroy old table
            bDestroy: true,
            // Try to get a more reasonable size for cells
            columnDefs: [
                // Treat the group column as if it were just the number
                { "type": "brute-numeric", "targets": 0, "width": "10%" }
            ]
        });

        // TODO NOT DRY
        // Swap positions of filter and length selection; clarify filter
        $('.dataTables_filter').css('float', 'left').prop('title', 'Separate terms with a space to search multiple fields');
        $('.dataTables_length').css('float', 'right');
        // Reposition download/print/copy
        $('.DTTT_container').css('float', 'none');

        // Make sure the header is fixed and active
        treatment_group_data_table.fixedHeader.enable();
    };

    // TODO THIS SHOULDN'T BE REDUNDANT
    function isNumber(obj) {
        return obj !== undefined && typeof(obj) === 'number' && !isNaN(obj);
    }

    function destroy_events(charts) {
        if (all_events[charts]) {
            $.each(all_events[charts], function(event_type_index, current_events) {
                $.each(current_events, function(event_index, event) {
                    google.visualization.events.removeListener(event);
                    event = null;
                });
            });
        }

        all_events[charts] = {
            'in': [],
            'out': []
        };
    }

    // function revise_event(charts, is_popup, index) {
    //     // NOT DRY NOT DRY
    //     $.each(all_events[charts], function(event_type, current_events) {
    //         if (current_events[index]) {
    //             google.visualization.events.removeListener(current_events[index]);
    //             event = null;
    //         }
    //     });
    //
    //     prep_event(charts, is_popup, index);
    // }

    // DUMB PARAMETERS
    function modify_group_to_data(group_to_data, assays, charts, index, i, key) {
        // Need to link EACH CHARTS values to the proper group
        // EMPHASIS ON EACH CHART
        // Somewhat naive
        if (key === 'group') {
            // NOTE -1
            group_to_data[charts][index][i] = assays[index][0][i].split(' || ')[0].replace(/\D/g, '') - 1;
        }
        else {
            var device = assays[index][0][i].split(' || ')[0];
            group_to_data[charts][index][i] = device_to_group[device];
        }
    }

    function prep_event(charts, is_popup, index) {
        if (!group_to_data[charts][index]) {
            group_to_data[charts].push({});
        }

        var assays = all_data[charts].assays;

        for (i=0; i < assays[index][0].length; i++) {
            if (assays[index][0][i].indexOf('     ~@i1') === -1 && assays[index][0][i].indexOf('     ~@i2') === -1) {
                modify_group_to_data(group_to_data, assays, charts, index, i, all_options[charts][index].ajax_data.key);
            }
        }

        // Makes use of a rather zany closure
        var current_event = google.visualization.events.addListener(all_charts[charts][index], 'onmouseover', (function (charts, chart_index, is_popup) {
            return function (entry) {
                // Only attempts to display if there is a valid treatment group
                if (all_treatment_groups[group_to_data[charts][chart_index][entry.column]]) {
                    var current_pos = $(all_charts[charts][chart_index].container).position();

                    var current_top = current_pos.top + 75;
                    var current_left = $('#breadcrumbs').position().left;

                    if (is_popup) {
                        current_pos = $(all_charts[charts][chart_index].container).parent().parent().parent().position();
                        current_top = current_pos.top + 200;
                        current_left = current_pos.left;
                    }

                    if (entry.row === null && entry.column) {
                        var row_clone = all_treatment_groups[group_to_data[charts][chart_index][entry.column]].clone().addClass('bg-warning');
                        if (row_clone) {
                            group_display_body.empty().append(row_clone);

                            group_display.show()
                                .css({top: current_top, left: current_left, position: 'absolute'});
                        }
                    }
                }
            }
        })(charts, index, is_popup));
        all_events[charts]['in'][index] = current_event;

        current_event = google.visualization.events.addListener(all_charts[charts][index], 'onmouseout', function () {
            group_display.hide();
        });
        // TODO NOTE: CONTRIVED
        all_events[charts]['out'][index] = current_event;
    }

    function create_events(charts, is_popup) {
        // TODO NEEDS TO BE MADE GENERIC
        for (var index=0; index < all_charts[charts].length; index++) {
            prep_event(charts, is_popup, index);
        }
    }

    // PLEASE NOTE THAT THIS WILL WIPE ALL INDIVIDUAL EDITS
    window.CHARTS.make_charts = function(json, charts) {
        // post_filter setup
        window.GROUPING.set_grouping_filtering(json.post_filter);

        // Remove triggers
        destroy_events(charts);
        // if (all_events[charts]) {
        //     $.each(all_events[charts], function(index, event) {
        //         google.visualization.events.removeListener(event);
        //     });
        // }

        // Clear all charts
        all_charts[charts] = [];
        all_events[charts] = {
            'in': [],
            'out': []
        };

        all_options[charts] = [];

        group_to_data[charts] = [];

        // Show the chart options
        // NOTE: the chart options are currently shown by default, subject to change

        // heatmap WIP
        // heatmap_data = json.heatmap;
        //
        // window.CHARTS.get_heatmap_dropdowns(0);

        // Naive way to learn whether dose vs. time
        // GLOBAL CANNOT CURRENTLY EVEN BE DOSE RESPONSE (SCRUB)
        // window.CHARTS.global_options.tracking.is_dose = $('#dose_select').prop('checked');

        // window.CHARTS.global_options.hAxis.title = 'Time (Days)';
        // Still need to work in dose-response
        // if (window.CHARTS.global_options.tracking.is_dose) {
        //     window.CHARTS.global_options.hAxis.title = 'Dose (μM)';
        // }

        // If nothing to show
        if (!json.assays) {
            $('#' + charts).html('No data to display');
        }

        var sorted_assays = json.sorted_assays;
        var assays = json.assays;

        for (index in sorted_assays) {
            build_individual_chart('charts', document.getElementById('charts_' + index), index, window.CHARTS.global_options);
        }

        window.CHARTS.display_treatment_groups(json.treatment_groups, json.header_keys);

        create_events('charts');
    };

    // TODO TODO TODO NOT DRY
    function modify_chart_checkbox(checkbox, add_or_remove) {
        var current_index = $(checkbox).attr('data-table-index');

        // Visibly make checked
        $(checkbox).prop('checked', add_or_remove);

        if ($(checkbox).prop('checked')) {
            $(checkbox).attr('checked', 'checked');

            show_hide_plots_data_table.data()[current_index][0] = show_hide_plots_data_table.data()[current_index][0].replace('>', ' checked="checked">');
        }
        else {
            $(checkbox).removeAttr('checked');

            show_hide_plots_data_table.data()[current_index][0] = show_hide_plots_data_table.data()[current_index][0].replace(' checked="checked">', '>');
        }

        chart_filter_buffer[$(checkbox).val()] = $(checkbox).prop('checked');
    }

    $(document).on('click', '.chart-filter-checkbox', function() {
        modify_chart_checkbox(this, $(this).prop('checked'));
    });

    // Triggers for select all
    $('#show_hide_plots_select_all').click(function() {
        show_hide_plots_data_table.page.len(-1).draw();

        $('.chart-filter-checkbox').each(function() {
            modify_chart_checkbox(this, true);
        });

        show_hide_plots_data_table.order([[1, 'asc']]);
        show_hide_plots_data_table.page.len(10).draw();
    });

    // Triggers for deselect all
    $('#show_hide_plots_deselect_all').click(function() {
        show_hide_plots_data_table.page.len(-1).draw();

        $('.chart-filter-checkbox').each(function() {
            modify_chart_checkbox(this, false);
        });

        show_hide_plots_data_table.order([[1, 'asc']]);
        show_hide_plots_data_table.page.len(10).draw();
    });

    $('.show_hide_plots').click(function() {
        show_hide_plots_popup.dialog('open');
    });

    $('#id_make_plot_form_data').click(function() {
        alert('TODO');
    });

    function create_popup_for_individual_plot(chart) {
        current_chart = chart;
        current_chart_name = $(chart).attr('data-chart-name');
        current_chart_id = Math.floor($(chart).attr('id').split('_')[1]);
        // Contrived
        // current_chart_options = all_options['charts'][current_chart_id];
        individual_plot_popup.dialog('open');
    }

    // CONTEXT MENU
    $(document).on('contextmenu', '.chart-container', function() {
        create_popup_for_individual_plot(this);
    });

    // TRIGGER CONTEXT MENU ON LONG PRESS
    // ATTEMPT TO TRIGGER ON TOUCH EVENTS AS WELL
    var long_press_timer;
    $(document).on('mousedown touchstart', '.chart-container', function() {
        var chart = this;
        long_press_timer = setTimeout(function() {
            create_popup_for_individual_plot(chart);
        }, 1500);
    });
    $(document).on('mouseup mouseleave touchend touchcancel', '.chart-container', function() {
        clearTimeout(long_press_timer);
    });

    // THESE ARE SPECIAL TRIGGERS TO PREVENT SELECTING MEDIAN AND STE/STD
    // ALSO PREVENTS SELECTING MEAN AND IQR
    // ALSO THE SELECTORS ARE NOT SO GOOD
    var iqr_selector = $('#iqr_select');
    var std_selector = $('#std_select');
    var ste_selector = $('#ste_select');

    // TODO TODO TODO IDIOTIC PLEASE FIX ASAP
    function restrict_error_bar_options(refresh) {
        if ($('#arithmetic_select').prop('checked') || $('#geometric_select').prop('checked')) {
            // Enable proper options
            std_selector.removeAttr('disabled');
            ste_selector.removeAttr('disabled');

            // At the end, see if iqr is selected, if so then default to ste
            // (mean and iqr are forbidden together)
            if (iqr_selector.prop('checked')) {
                ste_selector.trigger('click');
            }
            else if(refresh) {
                trigger_refresh();
            }

            // Forbid iqr
            iqr_selector.attr('disabled', 'disabled');
        }
        else {
            // Enable proper options
            iqr_selector.removeAttr('disabled');

            // At the end, see if iqr is selected, if so then default to ste
            // (mean and iqr are forbidden together)
            if (std_selector.prop('checked') || ste_selector.prop('checked')) {
                iqr_selector.trigger('click');
            }
            else if(refresh) {
                // Odd, perhaps innapropriate!
                trigger_refresh();
            }

            // Forbid std and ste
            std_selector.attr('disabled', 'disabled');
            ste_selector.attr('disabled', 'disabled');
        }
    }

    $('#arithmetic_select, #geometric_select, #median_select').change(function() {
        restrict_error_bar_options(true);
    });

    // Initially, just block iqr for now
    // SLOPPY: PLEASE NOTE PLEASE NOTE
    iqr_selector.attr('disabled', 'disabled');

    // Set up triggers all other triggers
    function trigger_refresh() {
        // Odd
        if (side_bar_global) {
            window.CHARTS.global_options = window.CHARTS.prepare_chart_options();

            // Odd, perhaps innapropriate!
            window.GROUPING.refresh_wrapper();
        }
        else {
            // IF THE PREVIEW IS VISIBLE AND NOT MANUAL REFRESH, APPLY IT NOW
            if (!document.getElementById("id_manually_refresh").checked) {
                refresh_preview();
            }
        }
    }

    $('#sidebar')
        .find('input, select')
        // Exceptions to refresh (manually done elsewhere)
        .not('#arithmetic_select, #geometric_select, #median_select')
        .change(trigger_refresh);
});
