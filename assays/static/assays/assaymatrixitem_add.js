// TODO refactor
$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(get_readout);

    window.GROUPING.refresh_function = get_readout;

    var device = $('#id_device');
    var organ_model = $('#id_organ_model');
    var protocol = $('#id_organ_model_protocol');

    window.device = device;
    window.organ_model = organ_model;
    window.organ_model_protocol = protocol;

    // var protocol_display = $('#protocol_display');
    //
    // var organ_model_div = $('#organ_model_div');
    // var protocol_div = $('#protocol_div');
    // var variance_div = $('#variance_div');

    // TODO BEGIN
    // Tracks the excluded of data to indicate whether to exclude or include in plots
    var dynamic_excluded_current = {};
    var dynamic_excluded_new = {};

    var matrix_item_id = get_matrix_item();
    var study_id = get_study_id();

    window.CHARTS.call = 'fetch_data_points';
    window.CHARTS.matrix_item_id = matrix_item_id;

    // Name for the charts for binding events etc
    var charts_name = 'charts';

    var changes_to_chart_options = {
        chartArea: {
            // Slight change in width
            width: '78%',
            height: '65%'
        }
    };

    var current_data_table = null;

    function is_true(element, index, array) {
        if (!element && element !== 0) {
            return false;
        }
        else {
            return true;
        }
    }

    function data_format(value, ratio, id) {
        var format = d3.format(',.3f');
        if (value > 10000 || value < 0.01) {
            format = d3.format('.3e');
        }
        else if (value % 1 === 0) {
            format = d3.format(',d');
        }
        return format(value);
    }

    function get_study_id() {
        var study_id = Math.floor(window.location.href.split('/')[4]);
        if (study_id) {
            return study_id
        }
        else {
            return ''
        }
    }

    function get_matrix_item() {
        var current_id = Math.floor(window.location.href.split('/')[5]);

        if (!current_id) {
            current_id = '';
        }

        return current_id;
    }

    function get_readout() {
        if (matrix_item_id) {
            // Get the table
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    // TODO TODO TODO CALL FOR DATA
                    call: 'fetch_item_data',
                    matrix_item: matrix_item_id,
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                success: function (json) {
                    var exist = true;
                    process_data(json, exist);
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
            // Get the plots
            plot_existing_data();
        }
    }

    function clear_new_data() {
        $('.new-value').each(function() {
            // Delete this value from data
            // delete data[$(this).attr('data-chart-index')];
            // Remove the row itself
            $(this).remove();
        });
    }

    // REMOVED FOR NOW, CONSIDER ADDING BACK EVENTUALLY
    // function validate_readout_file(include_table) {
    //     // Purge dynamic_excluded_new if table if being reset
    //     if (include_table) {
    //         dynamic_excluded_new = {};
    //     }
    //
    //     var dynamic_excluded = $.extend(true, {}, dynamic_excluded_current, dynamic_excluded_new);
    //
    //     var data = {
    //         call: 'validate_individual_chip_file',
    //         study: study_id,
    //         readout: matrix_item_id,
    //         csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
    //         dynamic_excluded: JSON.stringify(dynamic_excluded),
    //         include_table: include_table
    //     };
    //
    //     window.CHARTS.global_options = window.CHARTS.prepare_chart_options();
    //
    //     data = $.extend(data, options);
    //
    //     var serialized_data = $('form').serializeArray();
    //     var form_data = new FormData();
    //     $.each(serialized_data, function(index, field) {
    //         form_data.append(field.name, field.value);
    //     });
    //     form_data.append('file', $('#id_file')[0].files[0]);
    //
    //     $.each(data, function(index, contents) {
    //         form_data.append(index, contents);
    //     });
    //
    //     $.ajax({
    //         url: "/assays_ajax/",
    //         type: "POST",
    //         dataType: "json",
    //         cache: false,
    //         contentType: false,
    //         processData: false,
    //         data: form_data,
    //         success: function (json) {
    //             // console.log(json);
    //             if (json.errors) {
    //                 // Display errors
    //                 alert(json.errors);
    //                 // Remove file selection
    //                 $('#id_file').val('');
    //                 // $('#table_body').empty();
    //                 clear_new_data();
    //                 // plot();
    //                 plot_existing_data();
    //             }
    //             else {
    //                 var exist = false;
    //                 alert('Success! Please see "New Chip Data" below for preview.' +
    //                     '\n\nPlease note that changes will not be made until you press the "Submit" button at the bottom of the page.');
    //
    //                 if (json.number_of_conflicting_entries) {
    //                     alert(
    //                         '***Submitting this file will replace ' + json.number_of_conflicting_entries + ' point(s).***' +
    //                         '\n\nPlease note that changes will not be made until you press the "Submit" button at the bottom of the page.');
    //                 }
    //
    //                 if (include_table) {
    //                    process_data(json.table, exist);
    //                 }
    //
    //                 window.CHARTS.prepare_side_by_side_charts(json.charts, charts_name);
    //                 window.CHARTS.make_charts(json.charts, charts_name, changes_to_chart_options);
    //
    //                 // Recalculate responsive and fixed headers
    //                 $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
    //                 $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
    //             }
    //         },
    //         error: function (xhr, errmsg, err) {
    //             alert('An unknown error has occurred. \nIf you have the file open, you may need to close it.');
    //             console.log(xhr.status + ": " + xhr.responseText);
    //             // Remove file selection
    //             $('#id_file').val('');
    //             // $('#table_body').empty();
    //             clear_new_data();
    //             // plot();
    //             plot_existing_data();
    //         }
    //     });
    // }

    var process_data = function (json, exist) {
        var table_body = $('#table_body');

        // Do not empty entire table, only delete new values
        // table_body.empty();
        clear_new_data();

        if (!json) {
            return;
        }

        // Current index for saving QC values
        var current_index = 0;

        // var table = '';

        // PLEASE NOTE THAT THE DATA POINTS ARE REVERSED
        var data_points = json.data_points.reverse();
        var study_assays = json.study_assays;
        var sample_locations = json.sample_locations;

        // TODO USE THE ACTUAL DATAPOINT PK FOR EXCLUSION
        $.each(data_points, function(index, data_point) {
            var name = data_point.name;

            var assay_plate_id = data_point.assay_plate_id;
            var assay_well_id = data_point.assay_well_id;

            var day = Math.floor(data_point.day);
            var hour = Math.floor(data_point.hour);
            var minute = Math.floor(data_point.minute);

            // Just convert to day for now
            var time_in_minutes = data_point.time_in_minutes;
            var time_in_days = time_in_minutes / 1440.0;

            var study_assay_id = data_point.study_assay_id;
            var target_name = study_assays[study_assay_id].target_name;
            var method_name = study_assays[study_assay_id].method_name;

            var sample_location_id = data_point.sample_location_id;
            var sample_location_name = sample_locations[sample_location_id].name;

            var value = data_point.value;
            var value_unit = study_assays[study_assay_id].unit;

            var caution_flag = data_point.caution_flag;
            var excluded = data_point.excluded;
            // var replaced = data_point.replaced;

            var notes = data_point.notes;
            var replicate = data_point.replicate;
            var update_number = data_point.update_number;

            var data_file_upload_url = data_point.data_file_upload_url;
            var data_file_upload_name = data_point.data_file_upload_name;

            var new_row = $('<tr>');
            //     .attr('data-chart-index', index);

            // Need to take a slice to avoid treating missing QC as invalid
            // Allow QC changes for NULL value row
            var every = [name, time_in_minutes, study_assay_id, sample_location_id].every(is_true);

            if (exist) {
                new_row.addClass('force-bg-success');
            }

            else {
                new_row.addClass('new-value');
            }

            if (!exist && !every) {
                new_row.addClass('force-bg-danger');
            }

            else if (value === null || value === '') {
                new_row.css('background', '#606060');
            }

            else if (excluded) {
                new_row.addClass('force-bg-danger');
            }

            else if (caution_flag) {
                new_row.addClass('force-bg-warning');
            }

            var col_name = $('<td>').text(name);

            var col_time = $('<td>').text('D' + day + ' H' + hour + ' M' + minute)
                .append($('<input>')
                    .addClass('time_in_minutes')
                    .val(time_in_minutes)
                    .hide()
                );

            var col_target = $('<td>').text(target_name);
            var col_method = $('<td>').text(method_name);
            var col_sample_location = $('<td>').text(sample_location_name);
            var col_value = $('<td>').text(value ? data_format(value) : value);
            var col_value_unit = $('<td>').text(value_unit);

            var col_caution_flag = $('<td>').text(caution_flag);

            var col_excluded = $('<td>');

            var excluded_input = $('<input>')
                .attr('type', 'checkbox')
                // .attr('id', i)
                .css('width', 50)
                .attr('data-matrix-item-pk', data_point.id)
                // .attr('name', 'assaydatapoint-' + data_point.id + '-exclude')
                // .attr('id', 'id_assaydatapoint-' + data_point.id + '-exclude')
                .addClass('excluded excluded-input');

            if (excluded) {
                excluded_input.prop('checked', true);
            }

            if (exist || every) {
                col_excluded.append(
                    excluded_input
                );
            }

            var col_notes = $('<td>').text(notes);

            var col_data_file_upload = $('<td>').append(
                $('<a>')
                    .text(data_file_upload_name)
                    .attr('href', data_file_upload_url)
            );

            new_row.append(
                col_name,
                col_time,
                col_target,
                col_method,
                col_sample_location,
                col_value,
                col_value_unit,
                col_caution_flag
            );

            // Technically a magic value SUBJECT TO CHANGE
            // Finds if there is a column to put exclude into
            if ($('#id_exclude_header')[0]) {
                new_row.append(col_excluded)
            }

            new_row.append(
                col_notes,
                col_data_file_upload
            );

            if (excluded) {
                new_row.addClass('initially-excluded')
            }

            table_body.prepend(new_row);
        });

        // Refresh exclusions
        toggle_excluded();

        var all_excluded = null;

        if (exist) {
            all_excluded = $('.excluded');
        }
        else {
            all_excluded = $('.new-value').find('.excluded');
        }

        // Bind change event to excluded
        all_excluded.change(function() {
            var current_value = $(this).prop('checked');
            var current_row = $(this).parent().parent();
            var current_pk = Math.floor($(this).attr('data-matrix-item-pk'));

            // Change color of parent if there is input
            if (current_value) {
                current_row.addClass('force-bg-danger');
                current_row.removeClass('unexcluded');
            }
            else if (!current_value && current_row.hasClass('initially-excluded')) {
                current_row.addClass('force-bg-info');
                current_row.addClass('unexcluded');
                current_row.removeClass('force-bg-success force-bg-danger');
            }
            else {
                current_row.removeClass('force-bg-danger');
            }

            if (exist) {
                // TODO
                dynamic_excluded_current[current_pk] = current_value;
            }
            else {
                // TODO
                dynamic_excluded_new[current_pk] = current_value;
            }

            // Validate again if there is a file
            // Only affects charts
            refresh_chart_only();
        });

        var current_data_table_selector = $('#current_data_table');
        // Clear old (if present)
        current_data_table_selector.DataTable().destroy();

        // KILL ALL LINGERING HEADERS
        $('.fixedHeader-locked').remove()

        // Make the datatable
        current_data_table = current_data_table_selector.DataTable({
            dom: 'B<"row">frti',
            fixedHeader: {headerOffset: 50},
            iDisplayLength: -1,
            columnDefs: [
                {
                    "sType": "numeric",
                    "sSortDataType": "time-in-minutes",
                    "targets": [1]
                },
                {
                    sortable: false,
                    "targets": [8]
                }
            ]
        });

        // Add listener to search
        $('input[type=search]').change(function() {
            toggle_excluded();
        });

        // TODO DEFINETELY NOT DRY
        // Swap positions of filter and length selection; clarify filter
        $('.dataTables_filter').css('float', 'left').prop('title', 'Separate terms with a space to search multiple fields');
        $('.dataTables_length').css('float', 'right');
        // Reposition download/print/copy
        $('.DTTT_container').css('float', 'none');

        // Clarify usage of sort
        $('.sorting').prop('title', 'Click a column to change its sorting\n Hold shift and click columns to sort multiple');
        $('.sorting_asc').prop('title', 'Click a column to change its sorting\n Hold shift and click columns to sort multiple');
        $('.sorting_desc').prop('title', 'Click a column to change its sorting\n Hold shift and click columns to sort multiple');
    };

    function plot_existing_data() {
        var dynamic_excluded = $.extend(true, {}, dynamic_excluded_current, dynamic_excluded_new);

        var data = {
            call: 'fetch_data_points',
            study: study_id,
            matrix_item: matrix_item_id,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
            criteria: JSON.stringify(window.GROUPING.get_grouping_filtering()),
            post_filter: JSON.stringify(window.GROUPING.current_post_filter),
            dynamic_excluded: JSON.stringify(dynamic_excluded)
        };

        window.CHARTS.global_options = window.CHARTS.prepare_chart_options();
        var options = window.CHARTS.global_options.ajax_data;

        data = $.extend(data, options);

        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );

        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                // Stop spinner
                window.spinner.stop();

                window.CHARTS.prepare_side_by_side_charts(json, charts_name);
                // TODO TODO TODO FIX FIX FIX
                // window.CHARTS.make_charts(json, charts_name, changes_to_chart_options);
                window.CHARTS.make_charts(json, charts_name);
                // Recalculate responsive and fixed headers
                $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
                $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();

                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    var refresh_table_and_charts = function() {
        if ($('#id_file')[0] && $('#id_file')[0].files[0]) {
            // resetChart();
            validate_readout_file('True');
            // getText(file);
        }
        else {
            plot_existing_data();
        }

        toggle_excluded();
    };

    var refresh_chart_only = function() {
        if ($('#id_file')[0] && $('#id_file')[0].files[0]) {
            // resetChart();
            validate_readout_file('');
            // getText(file);
        }
        else {
            plot_existing_data();
        }

        toggle_excluded();
    };

    function toggle_excluded() {
        // Stop gap: magic string
        var include_all = $('#chartsinclude_all').prop('checked');

        if (include_all) {
            $('.initially-excluded').show();
        }
        else {
            $('.initially-excluded').hide();
        }

        // Show initially-excluded items that have had their exclusion removed
        $('.unexcluded').show();
    }

    // Refresh on file change
    $('#id_file').change(function(evt) {
        refresh_table_and_charts();
    });

    // Refresh on change in overwrite option NEED REPLCATE TO BE ACCURATE
    $('#id_overwrite_option').change(function() {
        refresh_table_and_charts();
    });

    // Handling Device flow
    // Make sure global var exists before continuing
    if (window.get_organ_models) {
        device.change(function() {
            // Get organ models
            window.get_organ_models(device.val());
        });

        window.get_organ_models(device.val());

        organ_model.change(function() {
            // Get and display correct protocol options
            window.get_protocols(organ_model.val());
        });

        window.get_protocols(organ_model.val());

        protocol.change(function() {
            window.display_protocol(protocol.val());
        });

        window.display_protocol(protocol.val());
    }

    // Post submission operation
    // Special operations for pre-submission
    $('form').submit(function() {
        if (current_data_table) {
            current_data_table.search('');
            $('input[type=search]').val('');
            current_data_table.draw();
            $('.initially-excluded').show();
        }
        // Add the exclusions
        $('#id_dynamic_exclusion').val(JSON.stringify(dynamic_excluded_current));
    });
});
