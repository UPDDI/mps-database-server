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
    var power_analysis_two_sample_container_selector = $('#two-sample-power-analysis-container');
    var power_analysis_one_sample_container_selector = $('#one-sample-power-analysis-container');
    var power_analysis_values_graph = $("#pa-value-graph")[0];
    var power_analysis_p_value_graph = $("#pa-p-value-graph")[0];
    var power_analysis_power_graph = $("#pa-power-graph")[0];
    var power_analysis_sample_size_graph = $("#pa-sample-size-graph")[0];
    var one_sample_power_analysis_report_container = $("#one-sample-power-analysis-report");
    var one_sample_summary_table = $("#one-sample-summary-table");
    var one_sample_multi_graph = $("#one-sample-multi-graph")[0];
    var one_sample_power_analysis_container = $("#one-sample-power-analysis-container");

    var cohen_tooltip = "Cohen's D is the mean difference divided by the square root of the pooled variance.";
    var glass_tooltip = "Glass' Δ is the mean difference dividied by the standard deviation of the 'control' group.";
    var hedge_g_tooltip = "Hedges' g is the mean difference divided by the unbiased estimate of standard deviation for two treatment groups.";
    var hedge_gs_tooltip = "Hedges' g* is Hedges' g normalized by the gamma function of the sample size.";
    var sig_level_tooltip = "Significance level can be any value between (but exlcuding) 0 and 1.";
    var power_near_one_tooltip = "There is no power-sample curve at this time point because the power is too close to 1."

    $('#pam-cohen-d').next().html($('#pam-cohen-d').next().html() + make_escaped_tooltip(cohen_tooltip));
    $('#pam-glass-d').next().html($('#pam-glass-d').next().html() + make_escaped_tooltip(glass_tooltip));
    $('#pam-hedge-g').next().html($('#pam-hedge-g').next().html() + make_escaped_tooltip(hedge_g_tooltip));
    $('#pam-hedge-gstar').next().html($('#pam-hedge-gstar').next().html() + make_escaped_tooltip(hedge_gs_tooltip));
    $('#sig-level').next().html($('#sig-level').next().html() + make_escaped_tooltip(sig_level_tooltip));

    var active_compounds_checkboxes = 0;
    var significance_level = 0.05;
    var one_sample_time_point;

    var one_sample_difference;
    var one_sample_percent;
    var one_sample_sample_size;
    var one_sample_power;

    var time_points_full = [];
    var time_points_to_ignore = [];
    var sample_size_data = [];

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
        {title: "# of Time Points", data: '5', width: '10%'}
    ];

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
        }
    ];

    time_points_table_columns = [
        {
            title: "Include",
            "render": function (data, type, row, meta) {
                if (type === 'display') {
                    if (time_points_to_ignore.indexOf(row) >= 0) {
                        return '<input type="checkbox" class="big-checkbox power-analysis-time-points-checkbox" data-time-point="'+ row +'">';
                    } else {
                        return '<input type="checkbox" class="big-checkbox power-analysis-time-points-checkbox" data-time-point="'+ row +'" checked>';
                    }
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
                return row.replace("Day ", "");
            },
            "className": "dt-body-center",
        }
    ];

    // one_sample_time_points_table_columns = [
    //     {
    //         title: "Include",
    //         "render": function (data, type, row, meta) {
    //             if (type === 'display') {
    //                 return '<input type="checkbox" class="big-checkbox one-sample-time-point-checkbox" data-time-point="'+ row[1] +'">';
    //             }
    //             return '';
    //         },
    //         "className": "dt-body-center",
    //         "createdCell": function (td, cellData, rowData, row, col) {
    //             if (cellData) {
    //                 $(td).css('vertical-align', 'middle');
    //             }
    //         },
    //         "sortable": false,
    //         width: '5%'
    //     },
    //     {
    //         title: "Time Points",
    //         "render": function (data, type, row) {
    //             return row[1];
    //         },
    //         "className": "dt-body-center",
    //     }
    // ];

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
            },
            minValue: 0,
            scaleType: 'mirrorLog'
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
            'width': '90%',
            'height': '65%'
        },
        'height': 400,
        // Individual point tooltips, not aggregate
        focusTarget: 'datum',
        // series: contrived_line_dict
    };

    // SLOPPY: NOT DRY: MAKE TABLES FOR HOVERING
    // TODO REPRO JS IS NOT DRY
    function populate_selection_tables() {
        // TODO
        // Probably should cache this better
        var data_group_selections = $('#data_group_selections');
        data_group_selections.empty();

        current_tables = [];

        $.each(data_groups, function(set, set_data) {
            var rows = [];

            $.each(header_keys['data'], function(index, key) {
                if (key === 'Target') {
                    rows.push(
                        '<tr><th><h4><strong>Target/Analyte</strong></h4></th><td><h4><strong>' + data_groups[set][index] + '</strong></h4></td></tr>'
                    );
                } else {
                    rows.push(
                        '<tr><th>' + key + '</th><td>' + data_groups[set][index] + '</td></tr>'
                    );
                }
            });

            var current_treatment_group = data_groups[set][data_groups[set].length - 1];

            $.each(header_keys['treatment'], function(index, key) {
                rows.push(
                    '<tr><th>' + key + '</th><td>' + treatment_groups[current_treatment_group][key] + '</td></tr>'
                );
            });

            rows = rows.join('');

            // Not a great way to use classes
            var current_table = '<div><table class="table table-striped table-condensed table-bordered bg-white data-group-' + set + '"><tbody>' + rows + '</tbody></table></div>';

            current_tables.push(current_table);
        });

        data_group_selections.html(current_tables.join(''));
    }

    data_group_info_table_display = $('#data_group_info_table_display');

    $(document).on('mouseover', '.data-power-analysis-group-info', function() {
        var current_position = $(this).offset();

        var current_top = current_position.top + 20;
        var current_left = current_position.left - 100;

        var current_group = Math.floor($(this).html());
        var current_table = $('.data-group-' + current_group);
        var clone_table = current_table.parent().html();
        data_group_info_table_display.html(clone_table)
            .show()
            .css({top: current_top, left: current_left, position:'absolute'});
    });

    $(document).on('mouseout', '.data-power-analysis-group-info', function() {
        data_group_info_table_display.hide();
    });

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
                    value_unit_index = header_keys.data.indexOf('Value Unit');
                    method_index = header_keys.data.indexOf('Method');
                    setting_index = header_keys.data.indexOf('Settings');
                    cells_index = header_keys.data.indexOf('Cells');
                    target_index = header_keys.data.indexOf('Target');

                    // post_filter setup
                    window.GROUPING.set_grouping_filtering(json.post_filter);

                    // Generate selection TABLES
                    populate_selection_tables();

                    // Stop spinner
                    window.spinner.stop();
                    return power_analysis_group_table;
                },
                // Error callback
                error: function (xhr, errmsg, err) {
                    // Stop spinner
                    window.spinner.stop();

                    alert('An error has occurred, please try different selections.');
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            },
            columns: group_table_columns,
            "order": [1, 'asc'],
            dom: 'B<"row">lfrtip',
            paging: false,
            fixedHeader: {headerOffset: 50},
            deferRender: true,
        });

        active_compounds_checkboxes = 0;
        if (compounds_table) {
            unmake_compounds_datatable();
        }
        empty_graph_containers();
    }

    function empty_graph_containers() {
        // Empty old graph containers
        $(power_analysis_p_value_graph).empty();
        $(power_analysis_power_graph).empty();
        $(power_analysis_sample_size_graph).empty();
        $('#time-points-table_wrapper').hide();
        $('#error-container').hide();
        avg_val_graph_check();
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

        empty_graph_containers();
    });

    // Compounds Table Checkbox click event
    $(document).on("click", ".power-analysis-compounds-checkbox", function() {
        time_points_to_ignore = [];
        var checkbox = $(this);

        // Hide One Sample Time Points Table if it exists
        if ($('#one-sample-time-points-table_wrapper')) {
            $('#one-sample-time-points-table_wrapper').hide();
        }
        $(one_sample_power_analysis_container).hide();

        if ($('#power-analysis-options input[type="radio"][name="sample-num"]:checked').val() === 'two-sample') {
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
        } else if ($('#power-analysis-options input[type="radio"][name="sample-num"]:checked').val() === 'one-sample') {
            if (active_compounds_checkboxes < 2) {
                if (checkbox.is(':checked')) {
                    active_compounds_checkboxes += 1;
                    if (active_compounds_checkboxes === 1) {
                        $('.power-analysis-compounds-checkbox').each(function() {
                            if (!this.checked) {
                                $(this).parent().parent().hide();
                            }
                        });
                        $('#power-analysis-button').attr('disabled', true);
                        create_one_sample_content();
                    }
                } else {
                    active_compounds_checkboxes -= 1;
                    if (active_compounds_checkboxes === 0) {
                        $('.power-analysis-compounds-checkbox').each(function() {
                            if (!this.checked) {
                                $(this).parent().parent().show();
                            }
                        });
                    }
                    $('#power-analysis-button').attr('disabled', true);
                }
            }
        }

        empty_graph_containers();
    });

    // Time Point Table Checkbox click event
    $(document).on("click", ".power-analysis-time-points-checkbox", function() {
        var checkbox = $(this);
        var time_point = checkbox.attr('data-time-point');
        if (checkbox.is(':checked')) {
            var index = $.inArray(time_point, time_points_to_ignore);
            if (index>=0) time_points_to_ignore.splice(index, 1);
        } else {
            time_points_to_ignore.push(time_point);
        }
        draw_power_vs_sample_size_chart();
    });

    // // One Sample Time Point Table Checkbox click event
    // $(document).on("click", ".one-sample-time-point-checkbox", function() {
    //     var checkbox = $(this);
    //     one_sample_time_point = checkbox.attr('data-time-point');
    //     if (checkbox.is(':checked')) {
    //         $('.one-sample-time-point-checkbox').each(function() {
    //             if (!this.checked) {
    //                 $(this).attr('disabled', true);
    //             }
    //         });
    //         $('#power-analysis-button').attr('disabled', false);
    //         $('#summary-time').text(one_sample_time_point);
    //         var current_group = $('.power-analysis-group-checkbox:visible').first().attr('data-power-analysis-group');
    //         var compound_only = $('.power-analysis-compounds-checkbox:visible').first().attr('data-power-analysis-compound');
    //         var one_sample_data = JSON.parse(JSON.stringify(pass_to_power_analysis_dict[current_group][compound_only]));
    //         var the_goods = [];
    //         var mean, std;
    //         remove_col(one_sample_data, 0);
    //         remove_col(one_sample_data, 1);
    //         remove_col(one_sample_data, 1);
    //         for (var x = 0; x < one_sample_data.length; x++) {
    //             if (one_sample_data[x][0] === one_sample_time_point * 1440) {
    //                 the_goods.push(one_sample_data[x][1]);
    //             }
    //         }
    //         mean = the_goods.reduce((a,b) => a+b)/(the_goods.length);
    //         std = Math.sqrt(the_goods.map(x => Math.pow(x-mean,2)).reduce((a,b) => a+b)/(the_goods.length));
    //         $('#summary-sample-number').text(the_goods.length);
    //         $('#summary-mean').text(mean.toFixed(5));
    //         $('#summary-std').text(std.toFixed(5));
    //     } else {
    //         $('.one-sample-time-point-checkbox').each(function() {
    //             if ($(this).attr('disabled')) {
    //                 $(this).attr('disabled', false);
    //             }
    //         });
    //         $('#power-analysis-button').attr('disabled', true);
    //         $('#summary-time').html('&nbsp;');
    //         $('#summary-sample-number').html('&nbsp;');
    //         $('#summary-mean').html('&nbsp;');
    //         $('#summary-std').html('&nbsp;');
    //     }
    // });

    function make_compounds_datatable(group_num){
        compounds_table = $('#compounds-table').DataTable({
            data: compounds_table_data[group_num],
            columns: compounds_table_columns,
            paging: false,
            "order": [1, 'asc'],
        });

        $('#compounds-table tr').each(function(){
            if ($(this).find('.chip-num-cell').text() === '1') {
                $(this).find('input').attr('disabled', true);
                $(this).find('input').attr('title', 'Cannot perform power analysis on single-chip samples.');
            }
        });

        compounds_table_container.show();
    }

    function unmake_compounds_datatable() {
        compounds_table.clear();
        compounds_table.destroy();
        compounds_table_container.hide();
        compounds_table = null;
    }

    function draw_power_vs_sample_size_chart() {
        var sample_size_data_copy = $.extend(true, [], sample_size_data);
        var special_tps = [];
        for (var x = 0; x < sample_size_data_copy.length; x++) {
            var current_time = sample_size_data_copy[x][0]/1440;
            if (current_time % 1 !== 0) {
                current_time = current_time.toFixed(3);
            }
            if (sample_size_data_copy[x][3] !== null) {
                // Don't ask
                sample_size_data_copy[x][1] = sample_size_data_copy[x][1]+.002-.002;
                sample_size_data_copy[x][2] = sample_size_data_copy[x][2]+.002-.002;

                special_tps.push((sample_size_data_copy[x][0]/1440).toString());
            }
            sample_size_data_copy[x][0] = "Day " + String(current_time);
        }

        sample_size_data_prepped = get_pivot_array(sample_size_data_copy, 2, 0, 1);

        for (x = 1; x < sample_size_data_prepped.length; x++) {
            sample_size_data_prepped[x][0] = parseFloat(sample_size_data_prepped[x][0]);
        }

        var column_to_check = [];
        var columns_to_axe = [];
        for (x = 1; x < sample_size_data_prepped[0].length; x++) {
            for (y = 1; y < sample_size_data_prepped.length; y++) {
                column_to_check.push(sample_size_data_prepped[y][x]);
            }
            if (column_to_check.join('').length === 0) {
                columns_to_axe.push(x);
            }
            column_to_check = [];
        }
        column_to_check = [];

        for (x = columns_to_axe.length-1; x >= 0; x--) {
            remove_col(sample_size_data_prepped, columns_to_axe[x]);
        }
        columns_to_axe = [];

        // Populate full list of time points only if this is the first instance of power analysis being run on this set
        time_points_full = sample_size_data_prepped[0].filter(
            function(value, index, arr){
                return value !== 'Sample Size' && value !== 'POWER';
            }
        );

        var index_to_remove;
        for (var i = 0; i < time_points_to_ignore.length; ++i) {
            index_to_remove = sample_size_data_prepped[0].indexOf(time_points_to_ignore[i]);
            if (index_to_remove >= 0) {
                for (var j = 0; j < sample_size_data_prepped.length; ++j) {
                    sample_size_data_prepped[j].splice(index_to_remove, 1);
                }
            }
        }

        if (sample_size_data_prepped.length < 2) {
            return null;
        }

        var sample_size_google_data = null;
        sample_size_google_data = google.visualization.arrayToDataTable(sample_size_data_prepped);

        // TODO Replace with Original Time Points array
        time_points_table = $('#time-points-table').DataTable({
            data: time_points_full,
            columns: time_points_table_columns,
            paging: false,
            searching: false,
            info: false,
            destroy: true,
            "scrollY": "340px",
            "order": [1, 'asc'],
        });

        sample_size_chart = new google.visualization.LineChart(power_analysis_sample_size_graph);
        sample_size_chart.draw(sample_size_google_data, sample_size_google_options);

        // Add tooltip to near-1 power value days
        $('.power-analysis-time-points-checkbox').each(function() {
            if (special_tps.indexOf($(this).parent().next().html()) !== -1) {
                $(this).parent().next().html($(this).parent().next().html() + ' ' + make_escaped_tooltip(power_near_one_tooltip));
            }
        });

        // Activates Bootstrap tooltips
        $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
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
                '</div>';
            return;
        }

        var min_height = 400;
        if (selector == power_analysis_p_value_graph || selector == power_analysis_power_graph) {
            min_height = 250;
        }
        options = {
            // TOO SPECIFIC, OBVIOUSLY
            // title: assay,
            interpolateNulls: true,
            tooltip: {
                isHtml: true
            },
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
                'width': '70%',
                'height': '70%'
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
        if (options.hAxis.scaleType !== 'mirrorLog') {
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
    };

    function timeSortFunction(a, b) {
        if (a[0] === b[0]) {
            return 0;
        }
        else {
            return (a[0] < b[0]) ? -1 : 1;
        }
    }

    $('#power-analysis-button').click(function() {
        if ($('#power-analysis-options input[type="radio"][name="sample-num"]:checked').val() === 'two-sample') {
            fetch_two_sample_power_analysis_results();
        }
        else if ($('#power-analysis-options input[type="radio"][name="sample-num"]:checked').val() === 'one-sample') {
            fetch_one_sample_power_analysis_results();
        }
    });

    // Handle changes to Sample Numbering type
    $('input[type=radio][name=sample-num]').change(function() {
        // Hide One Sample Time Points Table if it exists
        if ($('#one-sample-time-points-table_wrapper')) {
            $('#one-sample-time-points-table_wrapper').hide();
        }
        $(one_sample_power_analysis_container).hide();

        if (this.value == 'two-sample') {
            $('#power-analysis-button').attr('disabled', true);
            $('#power-analysis-method').show();
            $('#one-sample-time-points-table').hide();
            $('.power-analysis-compounds-checkbox').each(function(){
                if (!this.checked) {
                    $(this).parent().parent().show();
                }
            });
        }
        else if (this.value == 'one-sample') {
            $('#power-analysis-method').hide();
            $('#one-sample-time-points-table').show();
            $('#power-analysis-button').attr('disabled', true);
            if (active_compounds_checkboxes === 1) {
                create_one_sample_content();
                $('.power-analysis-compounds-checkbox').each(function(){
                    if (!this.checked) {
                        $(this).parent().parent().hide();
                    }
                });
            } else {
                active_compounds_checkboxes = 0;
                $('#power-analysis-button').attr('disabled', true);
                $('.power-analysis-compounds-checkbox').each(function(){
                    if (!this.checked) {
                        $(this).parent().parent().show();
                    } else {
                        $(this).attr("checked", false);
                    }
                });
            }

            empty_graph_containers();
        }
    });

    // Handle changes to significance level input
    $('#sig-level').change(function() {
        significance_level = $('#sig-level').val();
        if (significance_level <= 0 || significance_level >= 1 || significance_level == '') {
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

    // // Handle changes to one sample power level input
    // $('#one-sample-power').change(function() {
    //     one_sample_power = $('#one-sample-power').val();
    //     if (one_sample_power < 0 || one_sample_power > 1 || one_sample_power == '') {
    //         one_sample_power = 0.8;
    //         $('#one-sample-power').val('0.8');
    //     }
    // });
    //
    // // Manage input to one sample power level input
    // document.querySelector('#one-sample-power').addEventListener("keypress", function (e) {
    //     if (e.key.length === 1 && e.key !== '.' && isNaN(e.key) && !e.ctrlKey && isNaN(e.key) && !e.metaKey || e.key === '.' && e.target.value.toString().indexOf('.') > -1) {
    //         e.preventDefault();
    //     }
    // });

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

        // TODO (not intelligent) The Replace is to accomodate "Day" in the Sample Size graph's legend while maintaining an order
        new_cols.sort(function(a, b) {
            return parseFloat(a.replace("Day ", "")) > parseFloat(b.replace("Day ", "")) ? 1 : -1;
        });
        var item = [];

        //Add Header Row
        item.push('Sample Size');
        item.push.apply(item, new_cols);
        ret.push(item);

        //Add content
        for (var key in result) {
            item = [];
            item.push(key);
            for (i = 0; i < new_cols.length; i++) {
                item.push(result[key][new_cols[i]] || null);
            }
            ret.push(item);
        }
        return ret;
    }

    function avg_val_graph_check() {
        var current_group, compound_first, compound_second;
        if ($('#power-analysis-options input[type="radio"][name="sample-num"]:checked').val() === 'two-sample') {
            current_group = $('.power-analysis-group-checkbox:checked').first().attr('data-power-analysis-group');
            compound_first = $('.power-analysis-compounds-checkbox:checked').first().attr('data-power-analysis-compound');
            compound_second = $('.power-analysis-compounds-checkbox:checked').last().attr('data-power-analysis-compound');
            if (active_compounds_checkboxes === 2) {
                $(power_analysis_values_graph).show();
                draw_avg_val_graph(current_group, compound_first, compound_second);
            } else if (active_compounds_checkboxes === 1) {
                $(power_analysis_values_graph).show();
                draw_avg_val_graph(current_group, compound_first, null);
            } else {
                $(power_analysis_values_graph).hide();
            }
        } else if ($('#power-analysis-options input[type="radio"][name="sample-num"]:checked').val() === 'one-sample') {
            if (active_compounds_checkboxes === 1) {
                current_group = $('.power-analysis-group-checkbox:checked').first().attr('data-power-analysis-group');
                compound_first = $('.power-analysis-compounds-checkbox:checked').first().attr('data-power-analysis-compound');
                $(power_analysis_values_graph).show();
                draw_avg_val_graph(current_group, compound_first, null);
            } else {
                $(power_analysis_values_graph).hide();
            }
        }
    }

    function draw_avg_val_graph(current_group, comp1, comp2) {
        // Values vs Time
        if (!final_chart_data[current_group]) {
            return null;
        }
        var chart_data = JSON.parse(JSON.stringify(final_chart_data[current_group]));
        var compounds_to_keep = [comp1, comp1+'     ~@i1', comp1+'     ~@i2', comp2, comp2+'     ~@i1', comp2+'     ~@i2']
        var current_header;
        var header_list = [];
        for (var x = chart_data[0].length; x > 0; x--){
            current_header = chart_data[0][x];
            if (current_header !== "Time" && compounds_to_keep.indexOf(current_header) === -1) {
                remove_col(chart_data, x);
            } else {
                for (var y = 0; y < current_header.split('\n').length; y+=2) {
                    header_list.push(current_header.split('\n')[y]+'; ');
                }
                if (current_header.indexOf('     ~@i1') !== -1) {
                    header_list[header_list.length-1] += '     ~@i1';
                } else if (current_header.indexOf('     ~@i2') !== -1) {
                    header_list[header_list.length-1] += '     ~@i2';
                }
                chart_data[0][x] = header_list.join('');
                //
                // FIX THE LENGTH OF THE BITS IN THE LEGEND HERE TOO
                //
            }
            header_list = [];
        }
        make_chart(row_info[0], 'Avg (Value)', power_analysis_values_graph, chart_data);
    }

    // Generate table for selection of one-sample power analysis time points
    // function create_one_sample_content() {
    //     var current_group = $('.power-analysis-group-checkbox:visible').first().attr('data-power-analysis-group');
    //     var compound_one_sample = $('.power-analysis-compounds-checkbox:visible').first().attr('data-power-analysis-compound');
    //     var raw_time_points_data = pass_to_power_analysis_dict[current_group][compound_one_sample];
    //     var one_sample_time_points_table_data = [];
    //     var timepoints_present = {};
    //     for (var x = 0; x < raw_time_points_data.length; x++) {
    //         if (!timepoints_present[raw_time_points_data[x][1]/1440]) {
    //             timepoints_present[raw_time_points_data[x][1]/1440] = true;
    //             one_sample_time_points_table_data.push(['', raw_time_points_data[x][1]/1440]);
    //         }
    //     }
    //
    //     one_sample_time_points_table = $('#one-sample-time-points-table').DataTable({
    //         data: one_sample_time_points_table_data,
    //         columns: one_sample_time_points_table_columns,
    //         paging: false,
    //         searching: false,
    //         info: false,
    //         destroy: true,
    //         "scrollY": "340px",
    //         "order": [1, 'asc'],
    //     });
    //
    //     // Reveal One Sample Time Points Table
    //     if ($('#one-sample-time-points-table_wrapper')) {
    //         $('#one-sample-time-points-table_wrapper').show();
    //     }
    //     $(one_sample_power_analysis_container).show();
    // }
    //
    // $('#one-sample-diff').focus(function() {
    //     $('#one-sample-percent').val('');
    // });
    //
    // $('#one-sample-percent').focus(function() {
    //     $('#one-sample-diff').val('');
    // });

    function fetch_two_sample_power_analysis_results() {
        var current_group = $('.power-analysis-group-checkbox:visible').first().attr('data-power-analysis-group');
        var compound_first = $('.power-analysis-compounds-checkbox:visible').first().attr('data-power-analysis-compound');
        var compound_second = $('.power-analysis-compounds-checkbox:visible').last().attr('data-power-analysis-compound');

        var power_analysis_method = $("input[name='pam']:checked").val();

        empty_graph_containers();

        window.spinner.spin(
            document.getElementById("spinner")
        );

        // NOTE: AJAX "success" and "error" are deprecated for 1.8, need to use "done" and "fail"
        // Consider calling AJAX functions directly
        $.ajax(
                "/assays_ajax/",
                {
                    data: {
                        call: 'fetch_two_sample_power_analysis_results',
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

                power_analysis_two_sample_container_selector.show();
                $('#time-points-table_wrapper').show();
                remove_col(data.power_analysis_data.power_results_report, 0);
                remove_col(data.power_analysis_data.power_vs_sample_size_curves_matrix, 0);
                remove_col(data.power_analysis_data.power_prediction_matrix, 0);
                remove_col(data.power_analysis_data.sample_size_prediction_matrix, 0);
                remove_col(data.power_analysis_data.sig_level_prediction_matrix, 0);

                // First Chart and Second Chart - P Values vs Time and Power vs Time
                var p_value_data = JSON.parse(JSON.stringify(data.power_analysis_data.power_results_report));
                var power_data = JSON.parse(JSON.stringify(data.power_analysis_data.power_results_report));
                remove_col(p_value_data, 1);
                remove_col(p_value_data, 2);
                remove_col(power_data, 2);
                remove_col(power_data, 2);
                p_value_data.sort(timeSortFunction);
                power_data.sort(timeSortFunction);
                for (var x = 0; x < p_value_data.length; x++){
                    p_value_data[x][0] = p_value_data[x][0]/1440;
                    power_data[x][0] = power_data[x][0]/1440;
                }
                p_value_data.unshift(["Time", "P Value"]);
                power_data.unshift(["Time", "Power"]);

                // Third Chart - Sample Size vs Power Value
                sample_size_data = data.power_analysis_data.power_vs_sample_size_curves_matrix.sort();

                $('#time_points_table_wrapper').show();

                make_chart('P Value for ' + row_info[0], 'P Value', power_analysis_p_value_graph, p_value_data);
                make_chart('Power for ' + row_info[0], 'Power', power_analysis_power_graph, power_data);
                draw_power_vs_sample_size_chart();

                if ($('div[id^="google-visualization-errors-all"]')[0]) {
                    power_analysis_two_sample_container_selector.hide();
                    $('#error-container').show();
                } else {
                    $('#error-container').hide();
                }
            })
            .fail(function(xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();

                alert('An error has occurred, please try different selections.');
                console.log(xhr.status + ": " + xhr.responseText);
            });
    }

    // function fetch_one_sample_power_analysis_results() {
    //     var current_group = $('.power-analysis-group-checkbox:visible').first().attr('data-power-analysis-group');
    //     var compound_only = $('.power-analysis-compounds-checkbox:visible').first().attr('data-power-analysis-compound');
    //
    //     empty_graph_containers();
    //
    //     window.spinner.spin(
    //         document.getElementById("spinner")
    //     );
    //
    //     // NOTE: AJAX "success" and "error" are deprecated for 1.8, need to use "done" and "fail"
    //     // Consider calling AJAX functions directly
    //     $.ajax(
    //             "/assays_ajax/",
    //             {
    //                 data: {
    //                     call: 'fetch_one_sample_power_analysis_results',
    //                     csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
    //                     full_data: JSON.stringify(pass_to_power_analysis_dict[current_group][compound_only]),
    //                     one_sample_compound: compound_only,
    //                     sig: significance_level,
    //                     one_sample_tp: one_sample_time_point,
    //                     diff: one_sample_time_point,
    //                     diff_percentage: one_sample_time_point,
    //                     sample_size: one_sample_time_point,
    //                     power: one_sample_time_point
    //                 },
    //                 type: 'POST',
    //             }
    //         )
    //         .done(function(data) {
    //             // Stop spinner
    //             window.spinner.stop();
    //
    //             power_analysis_one_sample_container_selector.attr('hidden', false);
    //         })
    //         .fail(function(xhr, errmsg, err) {
    //             // Stop spinner
    //             window.spinner.stop();
    //
    //             alert('An error has occurred, please try different selections.');
    //             console.log(xhr.status + ": " + xhr.responseText);
    //         });
    // }
});
