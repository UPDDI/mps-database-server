$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(loadRepro);

    window.GROUPING.refresh_function = loadRepro;

    // FILE-SCOPE VARIABLES
    var study_id = Math.floor(window.location.href.split('/')[5]);

    var gas_list = null;
    var mad_list = null;
    var comp_list = null;
    var lists = {
        chip_list: null,
        cv_list: null
    };
    var pie = null;

    // CRUDE NOT DRY
    var cv_tooltip = "The CV is calculated for each time point and the value reported is the max CV across time points, or the CV if a single time point is present.  The reproducibility status is excellent if Max CV/CV < 5% (Excellent (CV)), acceptable if Max CV/CV < 15% (Acceptable (CV)), and poor if CV > 15% for a single time point (Poor (CV))";
    var icc_tooltip = "The ICC Absolute Agreement of the measurements across multiple time points is a correlation coefficient that ranges from -1 to 1 with values closer to 1 being more correlated.  When the Max CV > 15%, the reproducibility status is reported to be excellent if > 0.8 (Excellent (ICC), acceptable if > 0.2 (Acceptable (ICC)), and poor if < 0.2 (Poor (ICC))";
    var repro_tooltip = "Our classification of this grouping\'s reproducibility (Excellent > Acceptable > Poor/NA). If Max CV < 15% then the status is based on the  Max CV criteria, otherwise the status is based on the ICC criteria when the number of overlapping time points is more than one. For single time point data, if CV <15% then the status is based on the CV criteria, otherwise the status is based on the ANOVA P-Value";
    var missing_tooltip = "Quantity of data values whose values were missing from the data provided and were interpolated by the average of the data values at the same time point";
    var mad_tooltip = "Median Absolute Deviation (MAD) scores of all chip measurement population at every time point. A score > 3.5 or < -3.5 indicates that the chip is an outlier relative to the median of chip measurement population at a that time point";
    var comp_tooltip = "The ICC is calculated for each chip relative to the median of all of the chips.";

    var gasTable = null;

    function escapeHtml(html) {
        return $('<div>').text(html).html();
    }

    function make_escaped_tooltip(title_text) {
        var new_span = $('<div>').append($('<span>')
            .attr('data-toggle', "tooltip")
            .attr('data-title', escapeHtml(title_text))
            .addClass("glyphicon glyphicon-question-sign")
            .attr('aria-hidden', "true")
            .attr('data-placement', "bottom"));
        return new_span.html();
    }

    function draw_tables(){
        //Clone reproducibility section per row
        gasTable.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
            var data = this.data();
            var icc_status = data[7];
            if (icc_status){
                // console.log("DATA: ", data);
                var organModel = data_group_to_organ_models[data[0]].join('<br>');
                var targetAnalyte = data_groups[data[0]][0];;
                var methodKit = "";
                var sampleLocation = data_group_to_sample_locations[data[0]].join('<br>');
                var compoundTreatments = treatment_groups[data_groups[data[0]][data_groups[data[0]].length - 1]]['Trimmed Compounds'];
                var valueUnit = data_groups[data[0]][value_unit_index];
                var group = data[0];
                // console.log("GROUP: ", group);

                var $elem = $( "#repro-data" );
                var $clone = $elem.clone( true ).removeAttr('id').addClass('repro-'+group).appendTo("#clone-container");
                mad_list[group]['columns'].unshift("Time");
                $clone.find('#repro-title').text('Set ' + group);
                $clone.find('#selection-parameters').html(buildSelectionParameters(studyID, organModel, targetAnalyte, methodKit, sampleLocation, compoundTreatments, valueUnit));
                $clone.find('#selection-parameters').find('td, th').css('padding','8px 10px');
                $clone.find('#chip-rep-rep-ind').html(buildCV_ICC(data[5],data[6]));
                $clone.find('#chip-rep-rep-ind').find('td, th').css('padding','8px 10px');
                $clone.find('#chart1').attr('id', 'chart1-'+group);
                $clone.find('#chart2').attr('id', 'chart2-'+group);
                $clone.find('#mad-score-label').html($clone.find('#mad-score-label').html() + make_escaped_tooltip(mad_tooltip));
                $clone.find('#med-comp-label').html($clone.find('#med-comp-label').html() + make_escaped_tooltip(comp_tooltip));
                if (icc_status[0] === 'E'){
                    $clone.find('#repro-status').html('<em>'+icc_status+'</em>').css("background-color", "#74ff5b");
                } else if (icc_status[0] === 'A'){
                    $clone.find('#repro-status').html('<em>'+icc_status+'</em>').css("background-color", "#fcfa8d");
                } else if (icc_status[0] === 'P'){
                    $clone.find('#repro-status').html('<em>'+icc_status+'</em>').css("background-color", "#ff7863");
                } else {
                    $clone.find('#repro-status').html('<em>'+icc_status+'</em><small style="color: black;"><span data-toggle="tooltip" title="'+data[14]+'" class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></small>').css("background-color", "Grey");
                }

                $clone.find('#mad-score-matrix').DataTable({
                    columns: mad_columns(group),
                    data: mad_list[group]['data'],
                    searching: false,
                    paging: false,
                    info: false
                    // fixedColumns: {leftColumns: 1},
                    // scrollX: true
                });

                $clone.find('#chip-comp-med').DataTable({
                    columns: [
                        { title: "Chip ID", data: '0' },
                        { title: "ICC Absolute Agreement", data: '1' },
                        { title: "Missing Data Points "+make_escaped_tooltip(missing_tooltip), data: '2' }
                    ],
                    data: comp_list[group],
                    searching: false,
                    paging: false,
                    info: false
                });
            }
        });
    }

    var studyID = $( "#selection-parameters" ).find(".studyId").text();

    // Activates Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});

    //Checkbox click event
    $(document).on("click", ".repro-checkbox", function() {
        var checkbox = $(this);
        var number = checkbox.attr('data-repro-set');
        var current_repro = $('.repro-' + number);
        if (checkbox.is(':checked')) {
            current_repro.removeClass('hidden');
            draw_charts(number);
        } else {
            current_repro.addClass('hidden')
        }
        // Activates Bootstrap tooltips
        $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
    });

    function order_info(orderList){
        for (var i=0; i < orderList.length; i++) {
            $('#clone-container .repro-'+orderList[i]).appendTo('#clone-container');
        }
    }

    // Piecharts
    function loadRepro() {
        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );

        if (gasTable) {
            gasTable.clear();
            gasTable.destroy();
        }

        $('#gas-table').find('body').empty();

        var loading_data = google.visualization.arrayToDataTable([
            ['Status', 'Count'],
            ['Loading...', 1]
        ]);

        var loading_options = {
            legend: 'none',
            pieSliceText: 'label',
            'chartArea': {'width': '90%', 'height': '90%'},
            tooltip: {trigger : 'none'},
            pieSlliceTextStyle: {
                color: 'white',
                bold: true,
                fontSize: 12
            }
        };
        var chart = new google.visualization.PieChart(document.getElementById('piechart'));
        chart.draw(loading_data, loading_options);

        var columns = [
            {
                title: "Show Details",
                "render": function (data, type, row, meta) {
                    if (type === 'display') {
                        return '<input type="checkbox" class="big-checkbox repro-checkbox" data-table-index="' + meta.row + '" data-repro-set="' + row[0] + '">';
                    }
                    return '';
                },
                "className": "dt-body-center",
                "createdCell": function (td, cellData, rowData, row, col) {
                    if (cellData) {
                        $(td).css('vertical-align', 'middle')
                    }
                },
                "sortable": false,
                width: '7.5%'
            },
            {
                title: "Set",
                type: "brute-numeric",
                "render": function (data, type, row) {
                        return '<span class="badge badge-primary repro-set-info">' + row[0] + '</span>';
                }
            },
            {
                title: "Target/Analyte",
                "render": function (data, type, row) {
                    return data_groups[row[0]][0];
                },
                width: '20%'
            },
            {
                title: "Unit",
                "render": function (data, type, row) {
                    return data_groups[row[0]][value_unit_index];
                }
            },
            {
                title: "Compounds",
                "render": function (data, type, row) {
                    return treatment_groups[data_groups[row[0]][data_groups[row[0]].length - 1]]['Trimmed Compounds'];
                },
                width: '20%'
            },
            {
                title: "MPS Models",
                "render": function (data, type, row) {
                    return data_group_to_organ_models[row[0]].join('<br>');
                }
            },
            {
                title: "Sample Locations",
                "render": function (data, type, row) {
                    return data_group_to_sample_locations[row[0]].join('<br>');
                }
            },
            {title: "<span style='white-space: nowrap;'>Max CV<br>or CV " + make_escaped_tooltip(cv_tooltip) + "</span>", data: '5'},
            {title: "<span style='white-space: nowrap;'>ICC " + make_escaped_tooltip(icc_tooltip) + "</span>", data: '6'},
            {
                title: "Reproducibility<br>Status " + make_escaped_tooltip(repro_tooltip),
                data: '7',
                render: function (data, type, row, meta) {
                    if (data[0] === 'E') {
                        return '<td><span class="hidden">3</span>' + data + '</td>';
                    } else if (data[0] === 'A') {
                        return '<td><span class="hidden">2</span>' + data + '</td>';
                    } else if (data[0] === 'P') {
                        return '<td><span class="hidden">1</span>' + data + '</td>';
                    } else {
                        return '<td><span class="hidden">0</span>' + data + '<span data-toggle="tooltip" title="' + row[9] + '" class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></td>';
                    }
                }
            },
            {title: "Cells", data: '1', 'className': 'none'},
            {title: "Settings", data: '7', 'className': 'none'},
            {title: "NA Explanation", data: '11', visible: false, 'name': 'naText' }
        ];

        gasTable = $('#gas-table').DataTable({
            ajax: {
                url: '/assays_ajax/',
                data: {
                    call: 'fetch_assay_study_reproducibility',
                    criteria: JSON.stringify(window.GROUPING.get_grouping_filtering()),
                    post_filter: JSON.stringify(window.GROUPING.current_post_filter),
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                    study: study_id
                },
                type: 'POST',
                dataSrc: function(json) {
                    $("#clone-container").empty();

                    gas_list = json.gas_list;
                    mad_list = json.mad_list;
                    comp_list = json.comp_list;
                    lists.cv_list = json.cv_list;
                    lists.chip_list = json.chip_list;
                    header_keys = json.header_keys;
                    data_groups = json.data_groups;
                    treatment_groups = json.treatment_groups;
                    pie = json.pie;

                    data_group_to_sample_locations = json.data_group_to_sample_locations;
                    data_group_to_organ_models = json.data_group_to_organ_models;
                    value_unit_index = header_keys.indexOf('Value Unit');

                    var pie_all_zero = pie.every(function(x){
                        if (!x){
                            return true;
                        }
                        return false;
                    })
                    if (pie_all_zero){
                        var na_data = google.visualization.arrayToDataTable([
                            ['Status', 'Count'],
                            ['NA', 1]
                        ]);
                        var na_options = {
                            legend: 'none',
                            pieSliceText: 'label',
                            'chartArea': {'width': '90%', 'height': '90%'},
                            slices: {
                                0: { color: 'Grey' }
                            },
                            tooltip: {trigger : 'none'},
                            pieSliceTextStyle: {
                                color: 'white',
                                bold: true,
                                fontSize: 12
                            }
                        };
                        chart = new google.visualization.PieChart(document.getElementById('piechart'));
                        chart.draw(na_data, na_options);
                    } else {
                        var pie_data = google.visualization.arrayToDataTable([
                            ['Status', 'Count'],
                            ['Excellent', pie[0]],
                            ['Acceptable', pie[1]],
                            ['Poor', pie[2]]
                        ]);
                        var pie_options = {
                            legend: 'none',
                            slices: {
                                0: { color: '#74ff5b' },
                                1: { color: '#fcfa8d' },
                                2: { color: '#ff7863' }
                            },
                            pieSliceText: 'label',
                            pieSliceTextStyle: {
                                color: 'black',
                                bold: true,
                                fontSize: 12
                            },
                            'chartArea': {'width': '90%', 'height': '90%'},
                            pieSliceBorderColor: "black"
                        };
                        chart = new google.visualization.PieChart(document.getElementById('piechart'));
                        chart.draw(pie_data, pie_options);
                    }

                    if (window.GROUPING.full_post_filter === null) {
                        window.GROUPING.full_post_filter = json.post_filter;
                        window.GROUPING.current_post_filter = JSON.parse(JSON.stringify(json.post_filter));
                    }

                    // Stop spinner
                    window.spinner.stop();

                    return gas_list;
                },
                // Error callback
                error: function (xhr, errmsg, err) {
                    $("#clone-container").empty();

                    // Stop spinner
                    window.spinner.stop();

                    alert('An error has occurred, please try different selections.');
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            },
            columns: columns,
            columnDefs: [
                { "aTargets": [9], "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    if (sData[0] === "E") {
                        $(nTd).css('background-color', '#74ff5b').css('font-weight', 'bold');
                    } else if (sData[0] === "A") {
                        $(nTd).css('background-color', '#fcfa8d').css('font-weight', 'bold');
                    } else if (sData[0] === "P") {
                        $(nTd).css('background-color', '#ff7863').css('font-weight', 'bold');
                    } else {
                        $(nTd).css('background-color', 'Grey').css('font-weight', 'bold');
                    }
                }}
            ],
            "order": [[9, 'desc'], [ 1, "asc" ]],
            "responsive": true,
            dom: 'B<"row">lfrtip',
            fixedHeader: {headerOffset: 50},
            deferRender: true,
            initComplete: function () {
                draw_tables();
            },
            drawCallback: function() {
                // Make sure tooltips displayed properly
                $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
            }
        });

        // On reorder
        gasTable.on( 'order.dt', function () {
            var setOrder = [];
            gasTable.column(1, { search:'applied' } ).data().each(function(value, index) {
                setOrder.push(value);
            });
            order_info(setOrder);
        });

        // This function filters the dataTable rows
        $.fn.dataTableExt.afnFiltering.push(function(oSettings, aData, iDataIndex) {
            // This is a special exception to make sure that other tables are not filtered on the page
            if (oSettings.nTable.getAttribute('id') !== 'gas-table') {
                return true;
            }

            if (aData[11]) {
                return true;
            }
        });
    }

    function draw_charts(set) {
        var value_unit = data_groups[set][value_unit_index];
        var cv_chart_data, chip_chart_data = null;
        if (passes_null_check(lists.cv_list[set])) {
            cv_chart_data = google.visualization.arrayToDataTable(lists.cv_list[set]);
        } else {
            console.log("CV Chart fails null check. Determine what to do.");
        }
        if (passes_null_check(lists.chip_list[set])) {
            chip_chart_data = google.visualization.arrayToDataTable(lists.chip_list[set]);
        } else {
            console.log("Chip Value Chart fails null check. Determine what to do.");
        }
        var cv_chart_options = {
            interpolateNulls: true,
            legend: {
                position: 'top',
                maxLines: 5,
                textStyle: {
                    bold: true
                }
            },
            hAxis: {
                title: 'Time (Days)',
                textStyle: {
                    bold: true
                },
                titleTextStyle: {
                    fontSize: 14,
                    bold: true,
                    italic: false
                }
            },
            vAxis: {
                title: value_unit,
                format: 'scientific',
                textStyle: {
                    bold: true
                },
                titleTextStyle: {
                    fontSize: 14,
                    bold: true,
                    italic: false
                },
                minValue: 0,
                viewWindowMode: 'explicit'
            },
            pointSize: 5,
            'chartArea': {
                'width': '70%',
                'height': '75%'
            },
            'height':250,
            'width':450,
            // Individual point tooltips, not aggregate
            focusTarget: 'datum',
            intervals: {
                'lineWidth': 0.75
            }
        };
        chip_chart_options = $.extend( {}, cv_chart_options );
        // First chip value series will be the Median, with special formatting.
        chip_chart_options['series'] = {
            0: {
                lineDashStyle: [4, 4], pointShape: {
                    type: 'diamond', sides: 4
                }
            }
        };
        // CV Chart will have a different label on its vAxis, min-max 0-100.
        cv_chart_options['vAxis'] = {
            title: 'CV(%)',
            format: 'short',
            textStyle: { bold: true },
            titleTextStyle: {
                fontSize: 14,
                bold: true,
                italic: false
            },
            minValue: 0,
            maxValue: 100,
            viewWindowMode: 'explicit'
        };
        var cv_chart = null;
        var chip_chart = null;
        if (chip_chart_data.length === 2) {
            chip_chart = new google.visualization.ColumnChart(document.getElementById('chart1-'+set));
            options['bar'] = {groupWidth: '25%'};
            options['hAxis']['ticks'] = [{v:chip_chart_data[1][0], f:chip_chart_data[1][0].toString()}]
        } else {
            chip_chart = new google.visualization.LineChart(document.getElementById('chart1-'+set));
        }
        if (cv_chart_data.length === 2) {
            cv_chart = new google.visualization.ColumnChart(document.getElementById('chart2-'+set));
            options['bar'] = {groupWidth: '25%'};
            options['hAxis']['ticks'] = [{v:cv_chart_data[1][0], f:cv_chart_data[1][0].toString()}]
        } else {
            cv_chart = new google.visualization.LineChart(document.getElementById('chart2-'+set));
        }
        chip_chart.draw(chip_chart_data, chip_chart_options);
        cv_chart.draw(cv_chart_data, cv_chart_options);
    }

    function passes_null_check(values){
        if (values == null){
            return false;
        }
        var all_null = true;
        for (var i = 1; i < values.length; i++) {
            for (var j = 1; j < values[i].length; j++) {
                if (values[i][j] === ""){
                    values[i][j] = null;
                } else {
                    all_null = false;
                }
            }
        }
        return !all_null;
    }

    function buildSelectionParameters(studyId, organModel, targetAnalyte, methodKit, sampleLocation, compoundTreatments, valueUnit){
        content =
        '<tr><th><h4><strong>Target/Analyte</strong></h4></th><td id="target-analyte-value"><h4><strong>'+targetAnalyte+'</strong></h4></td></tr>'+
        '<tr><th>Study ID</th><td>'+studyId+'</td></tr>'+
        '<tr><th>MPS Model</th><td>'+organModel+'</td></tr>'+
        '<tr><th>Method/Kit</th><td>'+methodKit+'</td></tr>'+
        '<tr><th>Sample Location</th><td>'+sampleLocation+'</td></tr>'+
        '<tr><th>Compound Treatment(s)</th><td>'+compoundTreatments+'</td></tr>'+
        '<tr><th>Value Unit</th><td id="value-unit">'+valueUnit+'</td></tr>'
        return content;
    }

    function buildCV_ICC(cv, icc){
        content = '<tr><th>CV(%)</th><th>ICC-Absolute Agreement</th></tr><tr><td>'+cv+'</td><td>'+icc+'</td></tr>'
        return content;
    }

    function mad_columns(counter){
        var columns = [];
        $.each(mad_list[counter]['columns'], function (i, value) {
            var obj = { 'title' : value };
            columns.push(obj);
        });
        return columns
    }
});
