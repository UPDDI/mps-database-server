$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(reproPie);

    var studies_table = $('#studies');
    // Hide initially
    studies_table.hide();

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


        studies_table.DataTable({
            dom: 'B<"row">lfrtip',
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
                    "targets": [5, 6, 7, 8]
                },
                {
                    'visible': false,
                    'targets': [7, 8, 12, 14, 15]
                },
                {
                    'className': 'none',
                    'targets': [9]
                },
                {
                    'sortable': false,
                    'targets': [10]
                }
            ],
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
