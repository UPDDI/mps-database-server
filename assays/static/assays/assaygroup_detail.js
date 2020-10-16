// TODO refactor
$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(get_data);

    window.GROUPING.refresh_function = get_data;

    var group_id = get_group_id();

    var first_run = true;

    window.CHARTS.call = 'fetch_data_points';
    window.CHARTS.group_id = group_id;

    // Name for the charts for binding events etc
    var charts_name = 'charts';

    // var changes_to_chart_options = {
    //     chartArea: {
    //         // Slight change in width
    //         width: '78%',
    //         height: '65%'
    //     }
    // };

    function get_group_id() {
        var current_id = Math.floor(window.location.href.split('/')[5]);

        if (!current_id) {
            current_id = '';
        }

        return current_id;
    }

    // PROCESS GET PARAMS INITIALLY
    window.GROUPING.process_get_params();

    function get_data() {
        if (group_id) {
            let data = {
                // TODO TODO TODO CALL FOR DATA
                call: 'fetch_data_points',
                group: group_id,
                criteria: JSON.stringify(window.GROUPING.group_criteria),
                post_filter: JSON.stringify(window.GROUPING.current_post_filter),
                full_post_filter: JSON.stringify(window.GROUPING.full_post_filter),
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            };

            window.CHARTS.global_options = window.CHARTS.prepare_chart_options();
            let options = window.CHARTS.global_options.ajax_data;

            data = $.extend(data, options);

            // Show spinner
            window.spinner.spin(
                document.getElementById("spinner")
            );

            // Get the table
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
    }
});
