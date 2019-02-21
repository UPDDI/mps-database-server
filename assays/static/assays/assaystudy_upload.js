// This script allows previews to be shown for bulk uploads
// CURRENTLY ONLY CHIP PREVIEWS ARE SHOWN
// TODO CONSOLIDATE CODE WITH ASSAYSTUDY SUMMARY (DRY)
$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    // google.charts.setOnLoadCallback(get_readouts);

    window.GROUPING.refresh_function = refresh_current;

    function refresh_current() {
        // Not currently used
        // get_readouts();

        if ($('#id_bulk_file').val()) {
            validate_bulk_file();
        }
    }

    var study_id = Math.floor(window.location.href.split('/')[5]);

    window.CHARTS.call = 'validate_data_file';
    window.CHARTS.study_id = study_id;

    // PROCESS GET PARAMS INITIALLY
    // window.GROUPING.process_get_params();
    // window.GROUPING.generate_get_params();

    // Not currently used
    function get_readouts() {
        var charts_name = 'current_charts';

        var data = {
            call: 'fetch_data_points',
            study: study_id,
            criteria: JSON.stringify(window.GROUPING.group_criteria),
            post_filter: JSON.stringify(window.GROUPING.current_post_filter),
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
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
                window.CHARTS.make_charts(json, charts_name);
            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();

                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    // Please note that bulk upload does not currently allow changing QC or notes
    // Before permitting this, ensure that the update_number numbers are accurate!
    function validate_bulk_file() {
        // var charts_name = 'new_charts';
        var charts_name = 'charts';

        // var dynamic_quality = $.extend(true, {}, dynamic_quality_current, dynamic_quality_new);

        var data = {
            call: 'validate_data_file',
            study: study_id,
            criteria: JSON.stringify(window.GROUPING.group_criteria),
            post_filter: JSON.stringify(window.GROUPING.current_post_filter),
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        //    dynamic_quality: JSON.stringify(dynamic_quality),
        //    include_table: include_table
        };

        window.CHARTS.global_options = window.CHARTS.prepare_chart_options();
        var options = window.CHARTS.global_options.ajax_data;

        data = $.extend(data, options);

        var serializedData = $('form').serializeArray();
        var formData = new FormData();
        $.each(serializedData, function(index, field) {
            formData.append(field.name, field.value);
        });
        formData.append('bulk_file', $('#id_bulk_file')[0].files[0]);

        $.each(data, function(index, contents) {
            formData.append(index, contents);
        });

        if ($("#id_bulk_file")[0].files[0]) {
            // Show spinner
            window.spinner.spin(
                document.getElementById("spinner")
            );

            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                cache: false,
                contentType: false,
                processData: false,
                data: formData,
                success: function (json) {
                    // Stop spinner
                    window.spinner.stop();

                    // console.log(json);
                    if (json.errors) {
                        // Display errors
                        alert(json.errors);
                        // Remove file selection
                        $('#id_bulk_file').val('');
                        // $('#new_charts').empty();
                        $('#charts').empty();
                    }
                    else {
                        // TODO TODO TODO ALERTS ARE EVIL
                        alert('Success! Please see "New Chip Data" below for preview.' +
                            '\n\nPlease note that changes will not be made until you press the "Submit" button at the bottom of the page.');

                        if (json.number_of_conflicting_entries) {
                            alert(
                                '***Submitting this file will replace ' + json.number_of_conflicting_entries + ' point(s).***' +
                                '\n\nPlease note that changes will not be made until you press the "Submit" button at the bottom of the page.');
                        }

                        window.CHARTS.prepare_side_by_side_charts(json.readout_data, charts_name);
                        window.CHARTS.make_charts(json.readout_data, charts_name);

                        // CRUDE: SIMPLY UNBIND ALL CHART CONTAINER EVENTS
                        $(document).off('.chart_context');
                    }
                },
                error: function (xhr, errmsg, err) {
                    // Stop spinner
                    window.spinner.stop();

                    alert('An unknown error has occurred. \nIf you have the file open, you may need to close it.');
                    console.log(xhr.status + ": " + xhr.responseText);
                    // Remove file selection
                    $('#id_bulk_file').val('');
                    //$('#new_charts').empty();
                    $('#charts').empty();
                }
            });
        }
    }

    // Validate file if file selected
    $('#id_bulk_file').change(function() {
        validate_bulk_file();
    });

    // NOTE: FOR NOW FILTERING WILL BE FORBIDDEN
    // CRUDE: JUST DISABLE THE BUTTONS
    $('.post-filter-spawn').html('X').attr('disabled', 'disabled');

    // NOTE MAGIC STRING HERE
    // Commented out for now, will just have preview (not current data to avoid ambiguity with only one sidebar)
/*
    $('#new_chartschart_options').find('input').change(function() {
        validate_bulk_file();
    });

    // NOTE MAGIC STRING HERE
    $('#current_chartschart_options').find('input').change(function() {
        get_readouts();
    });
*/
});
