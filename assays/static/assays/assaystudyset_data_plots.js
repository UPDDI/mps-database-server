// TODO NOT DRY
$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(show_plots);

    var charts_name = 'charts';

    // TODO TODO TODO
    window.GROUPING.refresh_function = show_plots;

    var study_set_id = Math.floor(window.location.href.split('/')[5]);

    window.CHARTS.call = 'fetch_data_points_from_study_set';
    window.CHARTS.study_set_id = study_set_id;

    // PROCESS GET PARAMS INITIALLY
    window.GROUPING.process_get_params();

    // TO DEAL WITH INITIAL POST FILTER, SHOULD IT EXIST
    var first_run = true;

    // Injected from study list
    // Please stop copying this, we need to have this be DRY!
    // Also, the styles are divergent among other things...
    var table_created = false;
    var studies_table = $('#studies');
    // Hide initially
    studies_table.hide();

    var at_least_one_pie_chart = false;

    function reproPie() {
        studies_table.show();

        var pieOptions = {
            legend: 'none',
            slices: {
                0: {color: '#74ff5b'},
                1: {color: '#fcfa8d'},
                2: {color: '#ff7863'}
            },
            pieSliceText: 'none',
            pieSliceTextStyle: {
                color: 'black',
                bold: true,
                fontSize: 12
            },
            'chartArea': {'width': '90%', 'height': '90%'},
            backgroundColor: {fill: 'transparent'},
            pieSliceBorderColor: "black",
            tooltip: {
                textStyle: {
                    fontName: 'verdana', fontSize: 10
                }
            }
            // enableInteractivity: false
        };

        var number_of_rows = studies_table.find('tr').length - 1;
        var pie, pieData, pieChart;
        for (x = 0; x < number_of_rows; x++) {
            pieData = null;

            if ($("#piechart" + x)[0]) {
                pie = $("#piechart" + x).data('nums');
                if (pie !== '0|0|0' && pie) {
                    pie = pie.split("|");
                    pieData = google.visualization.arrayToDataTable([
                        ['Status', 'Count'],
                        ['Excellent', parseInt(pie[0])],
                        ['Acceptable', parseInt(pie[1])],
                        ['Poor', parseInt(pie[2])]
                    ]);

                    at_least_one_pie_chart = true;
                }
                // else {
                //     pieData = google.visualization.arrayToDataTable([
                //         ['Status', 'Count'],
                //         ['NA', 1]
                //     ]);
                //     pieOptions = {
                //         legend: 'none',
                //         pieSliceText: 'label',
                //         'chartArea': {'width': '90%', 'height': '90%'},
                //         slices: {
                //             0: { color: 'Grey' }
                //         },
                //         tooltip: {trigger : 'none'},
                //         backgroundColor: {fill: 'transparent'},
                //         pieSliceTextStyle: {
                //             color: 'white',
                //             bold: true,
                //             fontSize: 12
                //         }
                //     };
                // }

                if (pieData) {
                    pieChart = new google.visualization.PieChart(document.getElementById('piechart' + x));
                    pieChart.draw(pieData, pieOptions);
                }
            }
        }

        // Hide again
        studies_table.hide();

        // PLEASE NOTE THAT: sck added two columns to table 20200515 (8 and 9) and moved later columns down 2
        studies_table.DataTable({
            dom: '<Bl<"row">frptip>',
            fixedHeader: {headerOffset: 50},
            responsive: true,
            "iDisplayLength": 50,
            // Initially sort on start date (descending), not ID
            "order": [ 2, "desc" ],
            "aoColumnDefs": [
                {
                    "bSortable": false,
                    "aTargets": [0]
                },
                {
                    "width": "10%",
                    "targets": [0]
                },
                {
                    "type": "numeric-comma",
                    "targets": [6, 7, 8, 9, 10, 11, 12]
                },
                {
                    'visible': false,
                    'targets': [5, 9, 10, 11, 12, 16, 18, 19]
                },
                {
                    'className': 'none',
                    'targets': [12]
                },
                {
                    'sortable': false,
                    'targets': [13]
                }
            ],
            initComplete: function() {
                // CRUDE WAY TO DISCERN IF IS EDITABLE STUDIES / NO PIE CHARTS
                if (!at_least_one_pie_chart) {
                    // Hide the column for pie charts
                    studies_table.DataTable().column(10).visible(false);
                }
            },
            drawCallback: function () {
                // Show when done
                studies_table.show('slow');
                // Swap positions of filter and length selection; clarify filter
                $('.dataTables_filter').css('float', 'left').prop('title', 'Separate terms with a space to search multiple fields');
                $('.dataTables_length').css('float', 'right');
                // Reposition download/print/copy
                $('.DTTT_container').css('float', 'none');
            }
        });
    }

    function show_plots() {
        // On first run, make the table
        if (!table_created) {
            reproPie();
            table_created = true;
        }

        var data = {
            // TODO TODO TODO CHANGE CALL
            call: 'fetch_data_points_from_study_set',
            intention: 'charting',
            study_set_id: study_set_id,
            filters: JSON.stringify(window.GROUPING.filters),
            criteria: JSON.stringify(window.GROUPING.get_grouping_filtering()),
            post_filter: JSON.stringify(window.GROUPING.current_post_filter),
            full_post_filter: JSON.stringify(window.GROUPING.full_post_filter),
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

    // On load
    document.getElementById('id_current_url_input').value = window.location.href

    // On click of copy to URL button (DEPRECATED)
    $('#id_copy_url_button').click(function() {
        var current_url = document.getElementById('id_current_url_input'); current_url.select();
        document.execCommand('copy');
    });
});
