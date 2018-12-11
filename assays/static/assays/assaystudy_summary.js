$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(get_readouts);

    window.GROUPING.refresh_function = get_readouts;

    var charts = $('#charts');
    var study_id = Math.floor(window.location.href.split('/')[5]);

    // Name for the charts for binding events etc
    var charts_name = 'charts';

    // Datatable for assays
    $('#assay_table').DataTable( {
        dom: 'B<"row">lfrtip',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "iDisplayLength": 10,
        // Initially sort on target (ascending)
        "order": [ 0, "asc" ]
    });

    function get_readouts() {
        var data = {
            // TODO TODO TODO CHANGE CALL
            call: 'fetch_data_points',
            study: study_id,
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

    $('#exportinclude_all').change(function() {
        var export_button = $('#export_button');
        if ($(this).prop('checked')) {
            export_button.attr('href', export_button.attr('href') + '?include_all=true');
        }
        else {
            export_button.attr('href', export_button.attr('href').split('?')[0]);
        }
    }).trigger('change');
});
