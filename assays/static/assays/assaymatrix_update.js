// The matrix's ID
window.MASS_EDIT.matrix_id = Math.floor(window.location.href.split('/')[5]);

// NOT DRY
$(document).ready(function () {
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(get_readouts);

    // Name for the charts for binding events etc
    var charts_name = 'charts';
    var first_run = true;

    window.GROUPING.refresh_function = get_readouts;

    window.CHARTS.call = 'fetch_data_points';
    window.CHARTS.matrix_id = window.MASS_EDIT.matrix_id;

    // PROCESS GET PARAMS INITIALLY
    window.GROUPING.process_get_params();
    // window.GROUPING.generate_get_params();

    function get_readouts() {
        var data = {
            // TODO TODO TODO CHANGE CALL
            call: 'fetch_data_points',
            matrix: window.MASS_EDIT.matrix_id,
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
                window.CHARTS.make_charts(json, charts_name, first_run);

                // Recalculate responsive and fixed headers
                $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
                $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();

                first_run = false;
            },
            error: function (xhr, errmsg, err) {
                first_run = false;

                // Stop spinner
                window.spinner.stop();

                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
});
