$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(show_plots);

    var charts_name = 'charts';

    // TODO TODO TODO
    window.GROUPING.refresh_function = show_plots;

    window.CHARTS.call = 'fetch_data_points_from_filters';

    // PROCESS GET PARAMS INITIALLY
    window.GROUPING.process_get_params();
    // window.GROUPING.generate_get_params();

    // TO DEAL WITH INITIAL POST FILTER, SHOULD IT EXIST
    var first_run = true;

    function show_plots() {
        var data = {
            // TODO TODO TODO CHANGE CALL
            call: 'fetch_data_points_from_filters',
            intention: 'charting',
            filters: JSON.stringify(window.GROUPING.filters),
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

        // // Center spinner
        // $(".spinner").position({
        //     my: "center",
        //     at: "center",
        //     of: "#piechart"
        // });

        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                // Stop spinner
                window.spinner.stop();

                if (first_run && $.urlParam('p')) {
                    first_run = false;

                    window.GROUPING.set_grouping_filtering(json.post_filter);
                    window.GROUPING.process_get_params();
                    window.GROUPING.refresh_wrapper();
                }
                else {
                    window.CHARTS.prepare_side_by_side_charts(json, charts_name);
                    window.CHARTS.make_charts(json, charts_name);

                    // Recalculate responsive and fixed headers
                    $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
                    $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
                }
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
