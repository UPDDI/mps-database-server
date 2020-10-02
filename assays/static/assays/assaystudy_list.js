$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(reproPie);

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
                    "targets": [5, 6, 7, 8, 9, 10, 11]
                },
                {
                    'visible': false,
                    'targets': [8, 9, 10, 11, 15, 17, 18]
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
});
