$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(show_plots);

    var charts_name = 'charts';

    // TODO TODO TODO
    window.GROUPING.refresh_function = show_plots;

    var filters = decodeURIComponent(window.location.search.split('?filters=')[1]);
    $('#back_button').attr('href', $('#back_button').attr('href') + filters);

    function show_plots() {
        current_context = 'plots';

        var data = {
            // TODO TODO TODO CHANGE CALL
            call: 'fetch_data_points_from_filters',
            intention: 'charting',
            filters: filters,
            criteria: JSON.stringify(window.GROUPING.get_grouping_filtering()),
            post_filter: JSON.stringify(window.GROUPING.current_post_filter),
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };

        var options = window.CHARTS.prepare_chart_options(charts_name);

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

                $('#results').show();
                $('#filter').hide();
                $('#grouping_filtering').show();

                // HIDE THE DATATABLE HEADERS HERE
                $('.filter-table').hide();

                window.CHARTS.prepare_side_by_side_charts(json, charts_name);
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

    // Setup triggers
    $('#' + charts_name + 'chart_options').find('input').change(function() {
        show_plots();
    });
});