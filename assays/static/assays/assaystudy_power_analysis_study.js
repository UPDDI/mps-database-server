$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(refresh_power_analysis);

    window.GROUPING.refresh_function = refresh_power_analysis;
    window.GROUPING.process_get_params();

    // FILE-SCOPE VARIABLES
    var study_id = Math.floor(window.location.href.split('/')[5]);

    var group_table = null;
    var compounds_table = null;
    var time_points_table = null;

    var row_info = null;

    var compounds_table_container = $('#compounds-table-container');
    var average_values_chart_selector = $('#values-vs-time-graph')[0];
    var power_analysis_container_selector = $('#power-analysis-container');
    var power_analysis_values_graph = $("#pa-value-graph")[0];
    var power_analysis_p_value_graph = $("#pa-p-value-graph")[0];
    var power_analysis_power_graph = $("#pa-power-graph")[0];
    var power_analysis_sample_size_graph = $("#pa-sample-size-graph")[0];

    var cohen_tooltip = "Cohen's D is the mean difference divided by the square root of the pooled variance.";
    var glass_tooltip = "Glass' Δ is the mean difference dividied by the standard deviation of the 'control' group.";
    var hedge_g_tooltip = "Hedges' g is the mean difference divided by the unbiased estimate of standard deviation for two treatment groups.";
    var hedge_gs_tooltip = "Hedges' g* is Hedges' g normalized by the gamma function of the sample size.";
    var sig_level_tooltip = "Significance level can be any value between 0 and 1.";

    $('#pam-cohen-d').next().html($('#pam-cohen-d').next().html() + make_escaped_tooltip(cohen_tooltip));
    $('#pam-glass-d').next().html($('#pam-glass-d').next().html() + make_escaped_tooltip(glass_tooltip));
    $('#pam-hedge-g').next().html($('#pam-hedge-g').next().html() + make_escaped_tooltip(hedge_g_tooltip));
    $('#pam-hedge-gstar').next().html($('#pam-hedge-gstar').next().html() + make_escaped_tooltip(hedge_gs_tooltip));
    $('#sig-level').next().html($('#sig-level').next().html() + make_escaped_tooltip(sig_level_tooltip));

    var active_compounds_checkboxes = 0;
    var significance_level = 0.05;

    var time_points_to_ignore = [];

    function refresh_power_analysis() {
        window.spinner.spin(
            document.getElementById("spinner")
        );

        if (group_table) {
            group_table.clear();
            group_table.destroy();

            // KILL ALL LINGERING HEADERS
            $('.fixedHeader-locked').remove();
        }

        $('#gas-table').find('body').empty();

        var group_table_columns = [
            {
                title: "Show Details",
                "render": function (data, type, row, meta) {
                    if (type === 'display') {
                        return '<input type="checkbox" class="big-checkbox power-analysis-group-checkbox" data-table-index="' + meta.row + '" data-power-analysis-group="' + row[0] + '" data-compounds-table-info="' + data_groups[row[0]][0] + '$$$$$' + data_groups[row[0]][value_unit_index] + '$$$$$' + data_group_to_organ_models[row[0]].join('<br>') + '$$$$$' + data_group_to_sample_locations[row[0]].join('<br>') + '">';
                    }
                    return '';
                },
                "className": "dt-body-center",
                "createdCell": function (td, cellData, rowData, row, col) {
                    if (cellData) {
                        $(td).css('vertical-align', 'middle');
                    }
                },
                "sortable": false,
                width: '5%'
            },
            {
                title: "Set",
                type: "brute-numeric",
                "render": function (data, type, row) {
                    return '<span class="badge badge-primary data-power-analysis-group-info">' + row[0] + '</span>';
                },
                width: '5%'
            },
            {
                title: "Target/Analyte",
                "render": function (data, type, row) {
                    return data_groups[row[0]][0];
                },
                width: '20%'
            },
            {
                title: "Unit",
                "render": function (data, type, row) {
                    return data_groups[row[0]][value_unit_index];
                }
            },
            {
                title: "MPS Models",
                "render": function (data, type, row) {
                    return data_group_to_organ_models[row[0]].join('<br>');
                }
            },
            {
                title: "Sample Locations",
                "render": function (data, type, row) {
                    return data_group_to_sample_locations[row[0]].join('<br>');
                }
            },
            {title: "# of Chips", data: '4', width: '5%'},
            {title: "# of Time Points", data: '5', width: '10%'},
        ];

        group_table = $('#group-table').DataTable({
            ajax: {
                url: '/assays_ajax/',
                data: {
                    call: 'fetch_power_analysis_group_table',
                    criteria: JSON.stringify(window.GROUPING.group_criteria),
                    post_filter: JSON.stringify(window.GROUPING.current_post_filter),
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                    study: study_id
                },
                type: 'POST',
                dataSrc: function(json) {
                    $("#clone-container").empty();

                    data_groups = json.data_groups;
                    header_keys = json.header_keys;
                    data_groups = json.data_groups;
                    treatment_groups = json.treatment_groups;
                    power_analysis_group_table = json.power_analysis_group_table;
                    compounds_table_data = json.compound_table_data;
                    final_chart_data = json.final_chart_data;
                    pass_to_power_analysis_dict = json.pass_to_power_analysis_dict;

                    data_group_to_sample_locations = json.data_group_to_sample_locations;
                    data_group_to_organ_models = json.data_group_to_organ_models;
                    value_unit_index = header_keys.indexOf('Value Unit');
                    method_index = header_keys.indexOf('Method');
                    setting_index = header_keys.indexOf('Settings');
                    cells_index = header_keys.indexOf('Cells');
                    target_index = header_keys.indexOf('Target');


                    // post_filter setup
                    window.GROUPING.set_grouping_filtering(json.post_filter);
                    // Stop spinner
                    window.spinner.stop();
                    return power_analysis_group_table;
                },
                // Error callback
                error: function (xhr, errmsg, err) {
                    $("#clone-container").empty();

                    // Stop spinner
                    window.spinner.stop();

                    alert('An error has occurred, please try different selections.');
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            },
            columns: group_table_columns,
            columnDefs: [
                { "responsivePriority": 1, "targets": [0,1,2,3] },
                { "responsivePriority": 2, "targets": 5 },
            ],
            "order": [1, 'asc'],
            "responsive": true,
            dom: 'B<"row">lfrtip',
            paging: false,
            fixedHeader: {headerOffset: 50},
            deferRender: true,
        });
    }

    function escapeHtml(html) {
        return $('<div>').text(html).html();
    }

    function make_escaped_tooltip(title_text) {
        var new_span = $('<div>').append($('<span>')
            .attr('data-toggle', "tooltip")
            .attr('data-title', escapeHtml(title_text))
            .addClass("glyphicon glyphicon-question-sign")
            .attr('aria-hidden', "true")
            .attr('data-placement', "bottom"));
        return new_span.html();
    }

    // Group Table Checkbox click event
    $(document).on("click", ".power-analysis-group-checkbox", function() {
        var checkbox = $(this);
        var group_number = checkbox.attr('data-power-analysis-group');
        row_info = $(this).data('compounds-table-info').split('$$$$$');
        if (checkbox.is(':checked')) {
            $('.power-analysis-group-checkbox').each(function(){
                if (!this.checked) {
                    $(this).parent().parent().hide();
                }
            });
            $('#power-analysis-button').attr('disabled', true);
            active_compounds_checkboxes = 0;
            make_compounds_datatable(group_number);
            make_chart(row_info[0], row_info[1], average_values_chart_selector, final_chart_data[group_number]);
        } else {
            $('.power-analysis-group-checkbox').each(function(){
                if (!this.checked) {
                    $(this).parent().parent().show();
                }
            });
            unmake_compounds_datatable();
        }
        // Activates Bootstrap tooltips
        $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
        // Recalc Fixed Headers
        $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
    });

    // Compounds Table Checkbox click event
    $(document).on("click", ".power-analysis-compounds-checkbox", function() {
        var checkbox = $(this);
        var number = checkbox.attr('data-power-analysis-compound');
        if (active_compounds_checkboxes < 3) {
            if (checkbox.is(':checked')) {
                active_compounds_checkboxes += 1;
                if (active_compounds_checkboxes === 2) {
                    $('.power-analysis-compounds-checkbox').each(function(){
                        if (!this.checked) {
                            $(this).parent().parent().hide();
                        }
                    });
                    $('#power-analysis-button').attr('disabled', false);
                }
            } else {
                active_compounds_checkboxes -= 1;
                if (active_compounds_checkboxes === 1) {
                    $('.power-analysis-compounds-checkbox').each(function(){
                        if (!this.checked) {
                            $(this).parent().parent().show();
                        }
                    });
                }
                $('#power-analysis-button').attr('disabled', true);
            }
        }
    });

    // Time Point Table Checkbox click event
    $(document).on("click", ".power-analysis-time-points-checkbox", function() {
        var checkbox = $(this);
        var time_point = checkbox.attr('data-time-point');
        // console.log(time_point);
        if (checkbox.is(':checked')) {
            if ($('#time-points-table input:checked').length !== 1) {
                $('#power-analysis-button').attr('disabled', false);
            }
            var index = $.inArray("abc", time_points_to_ignore);
            if (index>=0) time_points_to_ignore.splice(index, 1);
            // console.log($('#time-points-table input:checked').length);
        } else {
            time_points_to_ignore.push(time_point);
            if ($('#time-points-table input:checked').length === 1) {
                $('#power-analysis-button').attr('disabled', true);
                // console.log("NO MORE UNCHECKING YO");
            }
        }
        // console.log(time_points_to_ignore);
    });

    function make_compounds_datatable(group_num){
        var compounds_table_columns = [
            {
                title: "Show Details",
                "render": function (data, type, row, meta) {
                    if (type === 'display') {
                        return '<input type="checkbox" class="big-checkbox power-analysis-compounds-checkbox" data-table-index="' + meta.row + '" data-power-analysis-compound="' + row[0] + '">';
                    }
                    return '';
                },
                "className": "dt-body-center",
                "createdCell": function (td, cellData, rowData, row, col) {
                    if (cellData) {
                        $(td).css('vertical-align', 'middle');
                    }
                },
                "sortable": false,
                width: '5%'
            },
            {
                title: "Compounds",
                "render": function (data, type, row) {
                    return row[0];
                }
            },
            {
                title: "# of Chips",
                "render": function (data, type, row) {
                    return '<span class="chip-num-cell">' + row[1] + '</span>';
                }
            },
            {
                title: "# of Time Points",
                "render": function (data, type, row) {
                    return row[2];
                }
            },

        ];

        compounds_table = $('#compounds-table').DataTable({
            data: compounds_table_data[group_num],
            columns: compounds_table_columns,
            paging: false,
            "order": [1, 'asc'],
            "responsive": true,
        });

        $('#compounds-table tr').each(function(){
            // console.log($(this).find('.chip-num-cell').text());
            if ($(this).find('.chip-num-cell').text() === '1') {
                $(this).find('input').data('enabled', false);
            }
        });

        // selection_parameters_table_container.removeAttr('hidden');
        compounds_table_container.removeAttr('hidden');
    }

    function unmake_compounds_datatable() {
        compounds_table.clear();
        compounds_table.destroy();
        compounds_table_container.attr('hidden', true);
    }

    function make_chart(assay, unit, selector, data) {
        // TODO MAKE SURE THE CHART_SELECTOR IS WHAT YOU WANT
        // Clear old chart (when applicable)
        $(selector).empty();

        // Aliases
        var assay_data = JSON.parse(JSON.stringify(data));

        // Don't bother if empty
        if (assay_data[1] === undefined) {
            selector.innerHTML = '<div class="alert alert-danger" role="alert">' +
                    '<span class="glyphicon glyphicon-warning-sign" aria-hidden="true"></span>' +
                    '<span class="sr-only">Danger:</span>' +
                    ' <strong>' + assay + ' ' + unit + '</strong>' +
                    '<br>This plot doesn\'t have any valid data.' +
                '</div>'
            return;
        }

        if (selector == power_analysis_p_value_graph || selector == power_analysis_power_graph) {
            var min_height = 200;
        } else {
            var min_height = 400;
        }
        options = {
            // TOO SPECIFIC, OBVIOUSLY
            // title: assay,
            interpolateNulls: true,
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
                revised_unit: null,
                // Log scale
                use_x_log: false,
                use_y_log: false
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

        if (options.tracking.revised_unit) {
            unit = options.tracking.revised_unit;
        }

        if (!options) {
            options = $.extend(true, {}, window.CHARTS.global_options);
        }

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
        // TODO CHANGE THE TITLE
        options.title = assay;
        // TODO GET THE UNIT IN QUESTION
        options.vAxis.title = unit;

        var chart = null;

        var num_colors = 0;
        var truncated_at_index = null;

        $.each(assay_data[0].slice(1), function(index, value) {
            if (value.indexOf('     ~@i') === -1) {
                // NOTE TRUNCATE PAST 40 COLORS
                if (num_colors >= 40) {
                    truncated_at_index = index;

                    if (assay_data[0][index + 1].indexOf('     ~@i') !== -1) {
                        truncated_at_index += 2;
                    }

                    $.each(assay_data, function(row_index, current_row) {
                        assay_data[row_index] = current_row.slice(0, truncated_at_index + 1);
                    });

                    // Indicate truncated in title?
                    options.title = options.title + ' {TRUNCATED}';

                    return false;
                }

                num_colors++;
            }
        });

        var data = google.visualization.arrayToDataTable(assay_data);

        chart = new google.visualization.LineChart(selector);

        // Change the options
        if (!options.hAxis.scaleType === 'mirrorLog') {
            options.hAxis.viewWindowMode = 'explicit';
            options.hAxis.viewWindow = {
                max: current_max_x + 0.1 * current_x_range,
                min: current_min_x - 0.1 * current_x_range
            };
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

            // chart.chart_index = index;
        }
    }

    // TODO THIS SHOULDN'T BE REDUNDANT
    function isNumber(obj) {
        return obj !== undefined && typeof(obj) === 'number' && !isNaN(obj);
    }

    var remove_col = function(arr, col_index) {
        for (var i = 0; i < arr.length; i++) {
            var row = arr[i];
            row.splice(col_index, 1);
        }
    }

    function timeSortFunction(a, b) {
        if (a[0] === b[0]) {
            return 0;
        }
        else {
            return (a[0] < b[0]) ? -1 : 1;
        }
    }

    $('#power-analysis-button').click(function() {
        if (time_points_table) {
            time_points_table.clear();
            time_points_table.destroy();
            // time_points_table.attr('hidden', true);
        }
        fetch_power_analysis_results();
    });

    // Handle changes to Sample Numbering type
    $('input[type=radio][name=sample-num]').change(function() {
        if (this.value == 'two-sample') {
            // $("#power-analysis-button").text("Perform Two-Sample Power Analysis");
        }
        else if (this.value == 'one-sample') {
            // $("#power-analysis-button").text("Perform One-Sample Power Analysis");
        }
    });

    // Handle changes to significance level input
    $('#sig-level').change(function() {
        significance_level = $('#sig-level').val();
        if (significance_level < 0 || significance_level > 1 || significance_level == '') {
            significance_level = 0.05;
            $('#sig-level').val('0.05');
        }
    });

    // Manage input to significance level input
    document.querySelector('#sig-level').addEventListener("keypress", function (e) {
        if (e.key.length === 1 && e.key !== '.' && isNaN(e.key) && !e.ctrlKey && isNaN(e.key) && !e.metaKey || e.key === '.' && e.target.value.toString().indexOf('.') > -1) {
            e.preventDefault();
        }
    });

    // Pivot the Sample Size vs Power data
    function get_pivot_array(data_array, row_index, col_index, data_index) {
        var result = {};
        var ret = [];
        var new_cols = [];
        for (var i = 0; i < data_array.length; i++) {
            if (!result[data_array[i][row_index]]) {
                result[data_array[i][row_index]] = {};
            }
            result[data_array[i][row_index]][data_array[i][col_index]] = data_array[i][data_index];

            //To get column names
            if (new_cols.indexOf(data_array[i][col_index]) == -1) {
                new_cols.push(data_array[i][col_index]);
            }
        }

        new_cols.sort(function(a, b) { return parseFloat(a) > parseFloat(b) ? 1 : -1});
        var item = [];

        //Add Header Row
        item.push('Sample Size');
        item.push.apply(item, new_cols);
        ret.push(item);

        //Add content
        for (var key in result) {
            item = [];
            item.push(key);
            for (var i = 0; i < new_cols.length; i++) {
                item.push(result[key][new_cols[i]] || null);
            }
            ret.push(item);
        }
        return ret;
    };

    function fetch_power_analysis_results() {
        var current_group = $('.power-analysis-group-checkbox:visible').first().attr('data-power-analysis-group');
        var compound_first = $('.power-analysis-compounds-checkbox:visible').first().attr('data-power-analysis-compound');
        var compound_second = $('.power-analysis-compounds-checkbox:visible').last().attr('data-power-analysis-compound');

        var power_analysis_method = $("input[name='pam']:checked").val();

        // Empty old graph containers
        $(power_analysis_values_graph).empty();
        $(power_analysis_p_value_graph).empty();
        $(power_analysis_power_graph).empty();
        $(power_analysis_sample_size_graph).empty();

        window.spinner.spin(
            document.getElementById("spinner")
        );

        // NOTE: AJAX "success" and "error" are deprecated for 1.8, need to use "done" and "fail"
        // Consider calling AJAX functions directly
        $.ajax(
                "/assays_ajax/",
                {
                    data: {
                        call: 'fetch_power_analysis_results',
                        csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                        full_data: JSON.stringify($.merge($.merge([], pass_to_power_analysis_dict[current_group][compound_first]), pass_to_power_analysis_dict[current_group][compound_second])),
                        pam: power_analysis_method,
                        sig: significance_level
                    },
                    type: 'POST',
                }
            )
            .done(function(data) {
                // Stop spinner
                window.spinner.stop();

                power_analysis_container_selector.attr('hidden', false);
                remove_col(data['power_analysis_data']['power_results_report'], 0);
                remove_col(data['power_analysis_data']['power_vs_sample_size_curves_matrix'], 0);
                remove_col(data['power_analysis_data']['power_prediction_matrix'], 0);
                remove_col(data['power_analysis_data']['sample_size_prediction_matrix'], 0);
                remove_col(data['power_analysis_data']['sig_level_prediction_matrix'], 0);

                // First Chart - Values vs Time
                var chart1_data = JSON.parse(JSON.stringify(final_chart_data[current_group]));
                var indices_to_remove = [];
                for (var x=0; x<chart1_data[0].length; x++){
                    if (chart1_data[0][x] !== "Time" && chart1_data[0][x].indexOf(compound_first) === -1 && chart1_data[0][x].indexOf(compound_second) === -1) {
                        indices_to_remove.push(x)
                    }
                }
                for (var x=0; x<indices_to_remove.length; x++){
                    remove_col(chart1_data, (indices_to_remove[x] - indices_to_remove.indexOf(indices_to_remove[x])));
                }

                // Second Chart and Third Chart - P Values vs Time and Power vs Time
                var p_value_data = JSON.parse(JSON.stringify(data['power_analysis_data']['power_results_report']));
                var power_data = JSON.parse(JSON.stringify(data['power_analysis_data']['power_results_report']));
                remove_col(p_value_data, 1);
                remove_col(power_data, 2);
                p_value_data.sort(timeSortFunction);
                power_data.sort(timeSortFunction);
                for (var x=0; x<p_value_data.length; x++){
                    p_value_data[x][0] = p_value_data[x][0]/1440;
                    power_data[x][0] = power_data[x][0]/1440;
                }
                p_value_data.unshift(["Time", "P Value"]);
                power_data.unshift(["Time", "Power"]);

                // Fourth Chart - Sample Size vs Power Value
                var sample_size_data = data['power_analysis_data']['power_vs_sample_size_curves_matrix'].sort();
                for (var x=0; x<sample_size_data.length; x++){
                    var current_time = sample_size_data[x][0]/1440;
                    sample_size_data[x][0] = String(current_time);
                }

                sample_size_data_prepped = get_pivot_array(sample_size_data, 2, 0, 1);
                sample_size_data_prepped.splice(1, 1);
                for (var x=1; x<sample_size_data_prepped.length; x++){
                    sample_size_data_prepped[x][0] = parseFloat(sample_size_data_prepped[x][0]);
                }

                make_chart(row_info[0], 'Avg (Value)', power_analysis_values_graph, chart1_data);
                make_chart(row_info[0], 'P Value', power_analysis_p_value_graph, p_value_data);
                make_chart('', 'Power', power_analysis_power_graph, power_data);

                // TODO .8 subject to change
                sample_size_data_prepped[0].push('POWER');
                for (var x=1; x<sample_size_data_prepped.length; x++){
                    sample_size_data_prepped[x].push(0.8);
                }

                contrived_line_dict = {};
                contrived_line_dict[sample_size_data_prepped[0].length-2] = {
                    type: 'linear',
                    color: 'black',
                    visibleInLegend: false,
                    enableInteractivity: false,
                    tooltip: false,
                    pointShape: {
                        type: 'diamond',
                        sides: 4
                    }
                };

                var sample_size_google_data = google.visualization.arrayToDataTable(sample_size_data_prepped);
                var sample_size_google_options = {
                    // TOO SPECIFIC, OBVIOUSLY
                    title: 'Power Curves - Time (Days)',
                    interpolateNulls: true,
                    curveType: 'function',
                    titleTextStyle: {
                        fontSize: 18,
                        bold: true,
                        underline: true
                    },
                    legend: {
                        title: 'Time (Days)',
                        position: 'top',
                        maxLines: 5,
                        textStyle: {
                            // fontSize: 8,
                            bold: true
                        }
                    },
                    hAxis: {
                        // Begins empty
                        title: 'Sample Size',
                        textStyle: {
                            bold: true
                        },
                        titleTextStyle: {
                            fontSize: 14,
                            bold: true,
                            italic: false
                        }
                    },
                    vAxis: {
                        title: 'Power Value',
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
                    pointSize: 0,
                    'chartArea': {
                        'width': '75%',
                        'height': '65%'
                    },
                    'height': 400,
                    // Individual point tooltips, not aggregate
                    focusTarget: 'datum',
                    series: contrived_line_dict
                }

                time_points_table_columns = [
                    {
                        title: "Include",
                        "render": function (data, type, row, meta) {
                            if (type === 'display') {
                                return '<input type="checkbox" class="big-checkbox power-analysis-time-points-checkbox" data-time-point="'+ row +'" checked>';
                            }
                            return '';
                        },
                        "className": "dt-body-center",
                        "createdCell": function (td, cellData, rowData, row, col) {
                            if (cellData) {
                                $(td).css('vertical-align', 'middle');
                            }
                        },
                        "sortable": false,
                        width: '5%'
                    },
                    {
                        title: "Time Points",
                        "render": function (data, type, row) {
                            return row;
                        },
                        "className": "dt-body-center",
                    }
                ];

                time_points_table = $('#time-points-table').DataTable({
                    data: sample_size_data_prepped[0].filter(function(value, index, arr){
                        return value !== 'Sample Size' && value !== 'POWER'
                    }),
                    columns: time_points_table_columns,
                    paging: false,
                    searching: false,
                    info: false,
                    "scrollY": "360px",
                    "order": [1, 'asc'],
                    "responsive": true,
                });

                // time_points_to_ignore =

                sample_size_chart = new google.visualization.LineChart(power_analysis_sample_size_graph);
                sample_size_chart.draw(sample_size_google_data, sample_size_google_options);
            })
            .fail(function(xhr, errmsg, err) {
                $("#clone-container").empty();

                // Stop spinner
                window.spinner.stop();

                alert('An error has occurred, please try different selections.');
                console.log(xhr.status + ": " + xhr.responseText);
            });
    }
});
