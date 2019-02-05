$(document).ready(function() {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(show_repro);

    // TODO TODO TODO
    window.GROUPING.refresh_function = show_repro;

    // Filters acquired naively from GET
    var filters = decodeURIComponent(window.location.search.split('?filters=')[1]);
    // Change the hrefs to include the filters
    var submit_buttons_selector = $('.submit-button');
    submit_buttons_selector.each(function() {
        var current_download_href = $(this).attr('href');
        var initial_href = current_download_href.split('?')[0];
        var get_for_href = 'filters=' + filters;
        $(this).attr('href', initial_href + '?' + get_for_href);
    });

    // TODO TODO TODO REPRO STUFF
    // TODO: UGLY
    var cv_tooltip = "The CV is calculated for each time point and the value reported is the max CV across time points, or the CV if a single time point is present.  The reproducibility status is excellent if Max CV/CV < 5% (Excellent (CV)), acceptable if Max CV/CV < 15% (Acceptable (CV)), and poor if CV > 15% for a single time point (Poor (CV))";
    var icc_tooltip = "The ICC Absolute Agreement of the measurements across multiple time points is a correlation coefficient that ranges from -1 to 1 with values closer to 1 being more correlated.  When the Max CV > 15%, the reproducibility status is reported to be excellent if > 0.8 (Excellent (ICC), acceptable if > 0.2 (Acceptable (ICC)), and poor if < 0.2 (Poor (ICC))";
    var repro_tooltip = "Our classification of this grouping\'s reproducibility (Excellent > Acceptable > Poor/NA). If Max CV < 15% then the status is based on the  Max CV criteria, otherwise the status is based on the ICC criteria when the number of overlapping time points is more than one. For single time point data, if CV <15% then the status is based on the CV criteria, otherwise the status is based on the ANOVA P-Value";
    var anova_tooltip = "The ANOVA p-value is calculated for the single overlapping time point data across MPS centers or studies. The reproducibility status is Acceptable (P-Value) if ANOVA p-value >= 0.05, and Poor (P-Value) if ANOVA p-value <0.05.";
    // Bad
    var chart_tooltips = {
        'item': '“Item” graph displays selected Target/Analyte’s measurements on each item (chip or well) against time cross centers or studies.',
        'average': '“Average” graph displays the average plus error bar (standard deviation) of selected Target/Analyte’s measurements aggregated by centers or studies against time.',
        'trimmed': '“Trimmed” graph displays the average of selected Target/Analyte’s measurements aggregated by centers or studies against time by dropping the data points which timely consistent measurement is missing from one or more center/study. It means the time observations are excluded from the analysis when any observations by center/study  are missing at that time.',
        'interpolated': '“Interpolated” graph displays the average of selected Target/Analyte’s measurements aggregated by centers or studies against time by interpolating the data points which timely consistent measurement(s) is(are) missing from a center/study. Four interpolation methods are applied for filling missing points, which are “nearest”, “linear spline”,” quadratic spline” and “cubic spline”. The overlapped data against time from one of four interpolation methods which has highest ICC value is depicted as a graph . The inter reproducibility results from all four interpolation methods are displayed in the table above the graphs.'
    };

    // BAD NOT DRY
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

    var interpolation_tooltips = {
        'Trimmed': 'These values use no interpolation method, they are based only on overlapping data.',
        'Nearest': 'This method sets the value of an interpolated point to the value of the nearest data point.',
        'Linear': 'This method fits a different linear polynomial between each pair of data points for curves, or between sets of three points for surfaces.',
        'Quadratic': 'This method fits a different quadratic polynomial between each pair of data points for curves, or between sets of three points for surfaces.',
        'Cubic': 'This method fits a different cubic polynomial between each pair of data points for curves, or between sets of three points for surfaces.'
    };

    // For making the table
    var repro_table_data_full = null;
    var repro_table_data_best = null;
    // For making the charts
    var chart_data = null;
    var summary_pie = null;
    // For getting info on treatment groups
    var data_groups = null;
    var header_keys = null;

    var data_group_to_studies = null;
    var data_group_to_sample_locations = null;

    var value_unit_index = null;

    // Table for the broad results
    var repro_table = null;

    var repro_info_table_display = $('#repro_info_table_display');
    var area_to_copy_to = $("#expanded_data");

    var inter_level = $('#inter_level_by_center').prop('checked') ? 1 : 0;
    var max_interpolation_size = $('#max_interpolation_size').val();
    var initial_norm = $('#initial_norm').prop('checked') ? 1 : 0;

    var status_column_index = 14;
    var icc_column_index = 12;

    //  Pie chart options etc.
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

    var na_data = null;

    var pie_chart = null;

    function show_repro() {
        // Set na_data
        na_data = google.visualization.arrayToDataTable([
            ['Status', 'Count'],
            ['No Matching Records Found', 1]
        ]);

        inter_level = $('#inter_level_by_center').prop('checked') ? 1 : 0;
        max_interpolation_size = $('#max_interpolation_size').val();
        initial_norm = $('#initial_norm').prop('checked') ? 1 : 0;

        // Loading Piechart
        loadingPie();

        // Special check to see whether to default to studies (only one center selected)
        var filters_parsed = JSON.parse(filters);
        if (Object.keys(filters_parsed['groups']).length === 1) {
            $('#inter_level_by_center').prop('checked', false);
            $('#inter_level_by_study').prop('checked', true);
            inter_level = 0;
        }

        // Define what the legend is
        // TODO TODO TODO CONTRIVED FOR NOW
        var legend_key = 'Center Count';
        if (!inter_level) {
            legend_key = 'Study Count';
        }

        if (repro_table) {
            repro_table.clear();
            repro_table.destroy();
        }

        // Prevents some issues with spawning another table
        $('#repro_table').empty();

        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );

        // Center spinner
        // TODO NOT a satisfactory solution.
        // Displaces on resize, or if page is still "expanding" when center of #piechart check is made.
        $(".spinner").position({
            my: "center",
            at: "center",
            of: "#piechart"
        });

        var columns = [
            {
                title: "Show Details",
                "render": function (data, type, row, meta) {
                    // if (type === 'display' && row[1] === '') {
                    if (type === 'display') {
                        // var groupNum = row[10];
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
                title: "Studies",
                "render": function (data, type, row) {
                    return data_group_to_studies[row[0]].join('<br>');
                },
                width: '20%'
            },
            {
                title: "Compounds",
                "render": function (data, type, row) {
                    return treatment_groups[data_groups[row[0]][data_groups[row[0]].length - 1]]['Trimmed Compounds'];
                },
                width: '20%'
            },
            {
                title: "Organ Models",
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
            {
                title: "Interpolation",
                "render": function (data, type, row) {
                    if (type === 'display' && row[1] !== '') {
                        // var groupNum = row[10];
                        return row[1];
                    }
                    return '';
                }
            },
            // {title: "Max Interpolated", data: '2'},
            {title: legend_key, data: '3'},
            {title: "Time Point Overlap", data: '4', width: '5%'},
            {title: "<span style='white-space: nowrap;'>Max CV<br>or CV " + make_escaped_tooltip(cv_tooltip) + "</span>", data: '5'},
            {title: "<span style='white-space: nowrap;'>ICC " + make_escaped_tooltip(icc_tooltip) + "</span>", data: '6'},
            {title: "<span>ANOVA<br>P-Value " + make_escaped_tooltip(anova_tooltip) + "</span>", data: '7', width: '10%'},
            {
                title: "Reproducibility<br>Status " + make_escaped_tooltip(repro_tooltip),
                data: '8',
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
            }
        ];

        repro_table = $('#repro_table').DataTable({
            ajax: {
                url: '/assays_ajax/',
                data: {
                    // TODO TODO TODO THIS DEPENDS ON THE INTERFACE
                    call: 'fetch_data_points_from_filters',
                    intention: 'inter_repro',
                    filters: filters,
                    criteria: JSON.stringify(window.GROUPING.get_grouping_filtering()),
                    post_filter: JSON.stringify(window.GROUPING.current_post_filter),
                    inter_level: inter_level,
                    max_interpolation_size: max_interpolation_size,
                    initial_norm: initial_norm,
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                type: 'POST',
                dataSrc: function (json) {
                    // Stop spinner
                    window.spinner.stop();

                    // A little unpleasant
                    // Accommodate errors and die early
                    if (json.errors) {
                        alert(json.errors);

                        pie_chart = new google.visualization.PieChart(document.getElementById('piechart'));
                        pie_chart.draw(na_data, na_options);

                        return [];
                    }

                    repro_table_data_full = json.repro_table_data_full;
                    repro_table_data_best = json.repro_table_data_best;
                    chart_data = json.chart_data;
                    summary_pie = json.pie;
                    data_groups = json.data_groups;
                    header_keys = json.header_keys;
                    treatment_groups = json.treatment_groups;
                    sets_intra_points = json.sets_intra_points;

                    data_group_to_studies = json.data_group_to_studies;
                    data_group_to_sample_locations = json.data_group_to_sample_locations;
                    data_group_to_organ_models = json.data_group_to_organ_models;

                    value_unit_index = json.header_keys.data.indexOf('Value Unit');

                    // Piechart info
                    var pie_all_zero = summary_pie.every(function(x){
                        if (!x){
                            return true;
                        }
                        return false;
                    })
                    if (pie_all_zero){
                        pie_chart = new google.visualization.PieChart(document.getElementById('piechart'));
                        pie_chart.draw(na_data, na_options);
                    } else {
                        var pie_data = google.visualization.arrayToDataTable([
                            ['Status', 'Count'],
                            ['Excellent', summary_pie[0]],
                            ['Acceptable', summary_pie[1]],
                            ['Poor', summary_pie[2]]
                        ]);
                        pie_chart= new google.visualization.PieChart(document.getElementById('piechart'));
                        pie_chart.draw(pie_data, pie_options);
                    }

                    // post_filter setup
                    window.GROUPING.set_grouping_filtering(json.post_filter);

                    return repro_table_data_best;
                },
                // Error callback
                error: function (xhr, errmsg, err) {
                    // Stop spinner
                    window.spinner.stop();

                    alert('An error has occurred, please try different selections.');
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            },
            columns: columns,
            columnDefs: [
                { "responsivePriority": 1, "targets": 14 },
                { "responsivePriority": 2, "targets": [0,1,2,3] },
                { "responsivePriority": 3, "targets": 5 },
                { "responsivePriority": 4, "targets": 12 },
                { "responsivePriority": 5, "targets": 11 },
                { "responsivePriority": 6, "targets": 13 },
                { "responsivePriority": 7, "targets": 6 },
                { "responsivePriority": 8, "targets": 4 },
                { "aTargets": [14], "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
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
            "order": [[status_column_index, 'desc'], [icc_column_index, 'desc']],
            // Column visibility toggle would displace, hence new means of coloring.
            // "createdRow": function(row, data, dataIndex) {
            //     if (data[8][0] === "E") {
            //         $(row).find('td:eq(' + status_column_index + ')').css("background-color", "#74ff5b").css("font-weight", "bold");
            //     }
            //     else if (data[8][0] === "A") {
            //         $(row).find('td:eq(' + status_column_index + ')').css("background-color", "#fcfa8d").css("font-weight", "bold");
            //     }
            //     else if (data[8][0] === "P") {
            //         $(row).find('td:eq(' + status_column_index + ')').css("background-color", "#ff7863").css("font-weight", "bold");
            //     }
            //     else {
            //         $(row).find('td:eq(' + status_column_index + ')').css("background-color", "Grey").css("font-weight", "bold");
            //     }
            // },
            "responsive": true,
            dom: 'B<"row">lfrtip',
            fixedHeader: {headerOffset: 50},
            deferRender: true,
            destroy: true,
            initComplete: function () {
                // TODO TODO TODO
                // Draw necessary sections below
                draw_subsections();

                // TODO NOT DRY
                // Swap positions of filter and length selection; clarify filter
                $('.dataTables_filter').css('float', 'left').prop('title', 'Separate terms with a space to search multiple fields');
                $('.dataTables_length').css('float', 'right');

                // Stopgap: Remove compound column if no compound criteria selected
                if (!window.GROUPING.get_grouping_filtering()['compound'] || window.GROUPING.get_grouping_filtering()['compound'].indexOf('compound_instance.compound_id') === -1) {
                    // Note magic number
                    repro_table.column(5).visible(false);
                }
            },
            drawCallback: function () {
                // Make sure tooltips displayed properly
                // TODO TODO TODO
                $('[data-toggle="tooltip"]').tooltip({container: "body", html: true});
            }
        });

        // On reorder
        $('#repro_table').DataTable().on('order.dt', function () {
            var set_order = [];
            $('#repro_table').DataTable().column(0, {search:'applied'}).data().each(function(value, index) {
                set_order.push(value);
            });
            order_info(set_order);
        });
    }

    // This function filters the dataTable rows
    $.fn.dataTableExt.afnFiltering.push(function(oSettings, aData, iDataIndex) {
        // This is a special exception to make sure that other tables are not filtered on the page
        if (oSettings.nTable.getAttribute('id') !== 'repro_table') {
            return true;
        }

        // If show all is not toggled on, then exclude those without overlap
        // BEWARE MAGIC NUMBERS
        if ($('#show_all_repro').prop('checked') || aData[11] || aData[12] || aData[13]) {
            return true;
        }
    });

    // When a filter is clicked, set the filter values and redraw the table
    $('#show_all_repro').change(function() {
        // Redraw the table
        repro_table.draw();
    });

    function draw_subsections() {
        var item_to_copy = $("#clone_container").find('[data-id="repro-data"]');
        repro_table.rows().every(function() {
            var data = this.data();
            var group = data[0];
            // var method = data[1];
            var icc_status = data[8];
            var current_clone = item_to_copy.first().clone(true);
            current_clone.addClass('repro-'+group);
            var repro_title = current_clone.find('[data-id="repro-title"]');
            var repro_status = current_clone.find('[data-id="repro-status"]');
            var data_table = current_clone.find('[data-id="data-table"]');

            var icc_table = current_clone.find('[data-id="icc-table"]');

            repro_title.html('Set ' + group);

            get_repro_status(icc_status, data[9], repro_status);

            populate_selection_table(group, data_table);
            if (repro_table_data_full[group].best[1]) {
                populate_icc_table(group, icc_table);
            }
            else {
                icc_table.hide();
            }

            // UGLY
            $.each(chart_tooltips, function(tooltip_name, tooltip_title) {
                var charts_section_title = current_clone.find('[data-id="tooltip_' + tooltip_name + '"]');
                charts_section_title.html(help_span(tooltip_title));
            });

            area_to_copy_to.append(current_clone);

            // Activates Bootstrap tooltips
            $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
        });
    }

    function get_repro_status(icc_status, repro_status_string, repro_status) {
        if (icc_status[0] === 'E'){
            repro_status.html('<em>'+icc_status+'</em>').css("background-color", "#74ff5b");
        } else if (icc_status[0] === 'A'){
            repro_status.html('<em>'+icc_status+'</em>').css("background-color", "#fcfa8d");
        } else if (icc_status[0] === 'P'){
            repro_status.html('<em>'+icc_status+'</em>').css("background-color", "#ff7863");
        } else {
            repro_status.html('<em>'+repro_status_string+'</em>').css("background-color", "Grey");
        }
    }

    function populate_selection_table(set, current_table) {
        var current_body = current_table.find('tbody');

        var rows = [];

        $.each(header_keys['data'], function(index, key) {
            if (key === 'Target') {
                rows.push(
                    '<tr><th><h4><strong>Target/Analyte</strong></h4></th><td><h4><strong>' + data_groups[set][index] + '</strong></h4></td></tr>'
                );
            } else {
                rows.push(
                    '<tr><th>' + key + '</th><td>' + data_groups[set][index] + '</td></tr>'
                );
            }
        });

        var current_treatment_group = data_groups[set][data_groups[set].length - 1];

        $.each(header_keys['treatment'], function(index, key) {
            rows.push(
                '<tr><th>' + key + '</th><td>' + treatment_groups[current_treatment_group][key] + '</td></tr>'
            );
        });

        rows.push(
            '<tr><th>Studies</th><td>' + data_group_to_studies[set].join('<br>') + '</td></tr>'
        );

        rows = rows.join('');
        current_body.html(rows);
    }

    function help_span(title, pull) {
        if (pull) {
            return '<span data-toggle="tooltip" class="pull-right glyphicon glyphicon-question-sign" aria-hidden="true" title="' + title + '"></span>';
        }
        return '<span data-toggle="tooltip" class="glyphicon glyphicon-question-sign" aria-hidden="true" title="' + title + '"></span>';
    }

    function populate_icc_table(set, current_table) {
        var current_body = current_table.find('tbody');

        var rows = [];

        // TO SORT
        var all_icc = repro_table_data_full[set];
        var methods = [
            'Trimmed',
            'Nearest',
            'Linear',
            'Quadratic',
            'Cubic'
        ];

        $.each(methods, function(index, interpolation) {
            var data = all_icc[interpolation];
            if (data) {
                var row = '<tr>' +
                    '<td>' + interpolation + ' ' + help_span(interpolation_tooltips[interpolation], true) +'</td>' +
                    // '<td>' + data[2] + '</td>' +
                    '<td>' + data[5] + '</td>' +
                    '<td>' + data[6] +'</td>' +
                    '<td>' + data[7] +'</td>';

                repro_status = $('<td>');

                get_repro_status(data[8], data[9], repro_status);

                row += repro_status[0].outerHTML;

                row += '</tr>';

                rows.push(row);
            }
        });

        rows = rows.join('');
        current_body.html(rows);
    }

    function isNumber(obj) {
        return obj !== undefined && typeof(obj) === 'number' && !isNaN(obj);
    }

    function draw_charts(set) {
        var chart_content_types = [
            'item',
            'average',
            'trimmed',
            'nearest',
            'linear',
            'quadratic',
            'cubic'
        ];

        var value_unit = data_groups[set][value_unit_index];

        var item_data_set = chart_data[set]['item'];
        var first_time = item_data_set[1][0];
        var last_time = item_data_set[item_data_set.length - 1][0];

        var x_axis_min = Math.floor(first_time) - 1;
        var x_axis_max = Math.ceil(last_time) + 1;

        // var y_axis_label_type = 'scientific';
        //
        // $.each(item_data_set, function(index, values) {
        //     var current = Math.max.apply(null, values.slice(1));
        //     if (current > 10) {
        //         y_axis_label_type = 'short';
        //         return false;
        //     }
        // });

        $.each(chart_content_types, function(index, content_type) {
            var values = chart_data[set][content_type];

            var current_value_unit = value_unit;

            // Beware magic strings
            if (initial_norm && content_type !== 'item' && content_type !== 'average') {
                current_value_unit = 'Normalized by Median Value';
            }

            if (!values) {
                return true;
            }

            var all_null = true;
            for (var i = 1; i < values.length; i++) {
                for (var j = 1; j < values[i].length; j++) {
                    if (values[i][j] === "") {
                        values[i][j] = null;
                    } else {
                        all_null = false;
                    }
                }
            }
            if (all_null) {
                return true;
            }

            var y_axis_label_type = '';

            $.each(values.slice(1), function(index, current_values) {
                // Idiomatic way to remove NaNs
                var trimmed_values = current_values.slice(1).filter(isNumber);

                var current_max = Math.abs(Math.max.apply(null, trimmed_values));
                var current_min = Math.abs(Math.min.apply(null, trimmed_values));

                if (current_max > 1000 || current_max < 0.001) {
                    y_axis_label_type = '0.00E0';
                    return false;
                }
                else if (Math.abs(current_max - current_min) < 10 && Math.abs(current_max - current_min) > 0.1 && Math.abs(current_max - current_min) !== 0) {
                    y_axis_label_type = '0.00';
                    return false;
                }
                else if (Math.abs(current_max - current_min) < 0.1 && Math.abs(current_max - current_min) !== 0) {
                    y_axis_label_type = '0.00E0';
                    return false;
                }
            });

            var options = {
                // Make sure title case
                title: content_type[0].toUpperCase() + content_type.substr(1),
                interpolateNulls: true,
                titleTextStyle: {
                    fontSize: 18,
                    bold: true,
                    underline: true
                },
                legend: {
                    position: 'top',
                    maxLines: 5,
                    textStyle: {
                        // fontSize: 8,
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
                    },
                    viewWindowMode: 'explicit',
                    viewWindow: {
                        min: x_axis_min,
                        max: x_axis_max
                    }
                },
                vAxis: {
                    title: current_value_unit,
                    format: y_axis_label_type,
                    // format: 'scientific',
                    // format:'0.00E0',
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
                    'width': '75%',
                    'height': '75%'
                },
                'height': 400,
                // 'width': 450,
                // Individual point tooltips, not aggregate
                focusTarget: 'datum',
                // Use an HTML tooltip.
                // TODO TODO TODO
                // tooltip: {isHtml: true},
                intervals: {
                    // style: 'bars'
                    'lineWidth': 0.75
                }
            };

            // CONTRIVANCE FOR NOW
            // if (content_type !== 'item') {
                // chart = new google.visualization.LineChart(
                //     $('.repro-' + set).find(
                //         '[data-id="' + content_type + '_chart"]'
                //     ).first()[0]);
            // }
            // else {
                // chart = new google.visualization.ScatterChart(
                //     $('.repro-' + set).find(
                //         '[data-id="' + content_type + '_chart"]'
                //     ).first()[0]);

                // Make sure isHtml true for items
                // options.tooltip = {isHtml: true};
            // }

            var chart_type = 'LineChart';
            var container_id = $('.repro-' + set).find(
                    '[data-id="' + content_type + '_chart"]'
                ).first()[0];
            if (content_type === 'item') {
                chart_type = 'ScatterChart';
                // Make sure isHtml true for items
                options.tooltip = {isHtml: true};
            }


            if (chart_type) {
                // Change interval columns to intervals
                // ALSO CHANGES ROLE FOR STYLE COLUMNS
                var interval_setter = [0];

                i = 1;
                while (i < values[0].length) {
                    interval_setter.push(i);
                    if (i + 2 < values[0].length && values[0][i + 1].indexOf('     ~@i1') > -1) {
                        interval_setter.push({sourceColumn: i + 1, role: 'interval'});
                        interval_setter.push({sourceColumn: i + 2, role: 'interval'});

                        if (i + 3 < values[0].length && values[0][i + 3].indexOf('     ~@s') > -1) {
                            interval_setter.push({sourceColumn: i + 3, type: 'string', role: 'style'});
                            i += 1;
                        }

                        i += 2;
                    }
                    // Item only
                    if (i + 1 < values[0].length && values[0][i + 1].indexOf('     ~@t') > -1) {
                        for (var row_index = 1; row_index < values.length; row_index++) {
                            var current_contents = values[row_index][i + 1];
                            if (current_contents) {
                                values[row_index][i + 1] = generate_data_point_tooltip(
                                    current_contents[0],
                                    current_contents[1],
                                    current_contents[2],
                                    current_contents[3]
                                );
                            }
                        }

                        interval_setter.push(
                            {
                                sourceColumn: i + 1, type: 'string', role: 'tooltip', 'p': {'html': true}
                            }
                        );

                        i += 1;
                    }

                    i += 1;
                }

                var data = google.visualization.arrayToDataTable(values);
                // var dataView = new google.visualization.DataView(data);
                // dataView.setColumns(interval_setter);

                var wrapper = new google.visualization.ChartWrapper({
                    chartType: chart_type,
                    dataTable: data,
                    options: options,
                    containerId: container_id
                });

                wrapper.setView({columns:interval_setter});

                wrapper.draw();
            }
        });

        var interpolation_methods = [
            'Nearest',
            'Linear',
            'Quadratic',
            'Cubic'
        ];

        // Decide whether or not to show trimmed
        var current_repro_set_selector = $('.repro-' + set);
        var current_full_data = repro_table_data_full[set];

        current_repro_set_selector.find('[data-id="tooltip_trimmed"]').hide();
        current_repro_set_selector.find('[data-id="trimmed_chart"]').hide();

        if (current_full_data['Trimmed']) {
            current_repro_set_selector.find('[data-id="tooltip_trimmed"]').show();
            current_repro_set_selector.find('[data-id="trimmed_chart"]').show();
        }

        var current_max = 0;
        var current_min = 999;
        var method_to_show = '';

        // Hide all but highest interpolation
        // See which interpolation method is best
        // Also hide the charts at first
        // Redundant!
        current_repro_set_selector.find('[data-id="tooltip_interpolated"]').hide();

        $.each(interpolation_methods, function(index, method) {
            var current_row = current_full_data[method];
            var lower_method = method.toLowerCase();

            current_repro_set_selector.find(
                '[data-id="' + lower_method + '_chart"]'
            ).hide();

            if (current_row && current_row[6] > current_max) {
                current_max = current_row[6];
                method_to_show = lower_method;
            }
        });

        if (!method_to_show || !current_max) {
            $.each(interpolation_methods, function(index, method) {
                var current_row = current_full_data[method];
                var lower_method = method.toLowerCase();

                if (current_row && parseFloat(current_row[5]) < current_min) {
                    current_min = parseFloat(current_row[5]);
                    method_to_show = lower_method;
                }
            });
        }

        if (method_to_show) {
            // Show best
            current_repro_set_selector.find(
                '[data-id="' + method_to_show + '_chart"]'
            ).show();

            current_repro_set_selector.find('[data-id="tooltip_interpolated"]').show();
        }
    }

    function generate_data_point_tooltip(time, legend, value, chip_id) {
        // return '<div style="padding:5px 5px 5px 5px;">' +
        // '<table class="table">' +
        // '<tr>' +
        // '<td><b>' + time + '</b></td>' +
        // '</tr>' +
        // '<tr>' +
        // '<td><b>Value</b></td>' +
        // '<td>' + value + '</td>' +
        // '</tr>' +
        // '<tr>' +
        // '<td><b>Item</b></td>' +
        // '<td>' + chip_id + '</td>' +
        // '</tr>' +
        // '</table>' +
        // '</div>';
        return time + '\n' + legend + ': ' + value + '\n' + chip_id;
    }

    //Checkbox click event
    $(document).on("click", ".repro-checkbox", function() {
        var checkbox = $(this);
        var number = checkbox.attr('data-repro-set');
        var current_repro = $('.repro-' + number);
        if (checkbox.is(':checked')) {
            current_repro.removeClass('hidden');
            intra_in_inter(number);
            draw_charts(number);
        } else {
            current_repro.addClass('hidden')
        }
        // Activates Bootstrap tooltips
        $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
    });

    $(document).on('mouseover', '.repro-set-info', function() {
        var current_position = $(this).offset();

        var current_top = current_position.top + 20;
        var current_left = current_position.left - 100;

        var current_group = Math.floor($(this).html());
        var current_section = $('.repro-' + current_group);
        var current_table = current_section.find('[data-id="data-table"]');
        var clone_table = current_table.parent().html();
        repro_info_table_display.html(clone_table)
            .show()
            .css({top: current_top, left: current_left, position:'absolute'});
    });

    $(document).on('mouseout', '.repro-set-info', function() {
        repro_info_table_display.hide();
    });

    function order_info(orderList) {
        for (var i=0; i < orderList.length; i++) {
            $('#expanded_data .repro-'+orderList[i]).appendTo('#expanded_data');
        }
    }
    // TODO TODO TODO END REPRO STUFF

    // TODO, THESE TRIGGERS SHOULD BE BASED ON THE ANCHOR, NOT BUTTON CLICKS
    // function get_grouping_filtering() {
    //     // THIS IS A CRUDE WAY TO TEST THE GROUPING
    //     // Reset the criteria
    //     group_criteria = {};
    //     grouping_checkbox_selector.each(function() {
    //         if (this.checked) {
    //             if (!group_criteria[$(this).attr('data-group-relation')]) {
    //                 group_criteria[$(this).attr('data-group-relation')] = [];
    //             }
    //             group_criteria[$(this).attr('data-group-relation')].push(
    //                 $(this).attr('data-group')
    //             );
    //         }
    //     });
    // }

    // Setup triggers
    // Now handled in grouping_filtering
    // $('#' + charts_name + 'chart_options').find('input').change(function() {
    //     show_plots();
    // });

    // Piecharts
    function loadingPie(){
        var loading_data = google.visualization.arrayToDataTable([
            ['Status', 'Count'],
            ['Loading...', 1]
        ]);
        var loading_options = {
            legend: 'none',
            pieSliceText: 'label',
            'chartArea': {'width': '90%', 'height': '90%'},
            tooltip: {trigger : 'none'},
            pieSliceTextStyle: {
                color: 'white',
                bold: true,
                fontSize: 12
            },
        };
        var chart = new google.visualization.PieChart(document.getElementById('piechart'));
        chart.draw(loading_data, loading_options);
    }

    // Intra-Repro in Inter-Repro
    function intra_in_inter(number) {
        var repro_element = $('.repro-' + number);
        var studies_cell = $(repro_element).find('[data-id=data-table] tr:last td');
        var studies_anchors = $(studies_cell).find('a');
        var studies_raw = studies_cell.html().split('<br>');
        var datapoints = [];
        for (i=0; i<studies_raw.length; i++) {
            datapoints.push(sets_intra_points[number][studies_raw[i].substring(studies_raw[i].indexOf("\">")+2).split("<")[0]]);
        }
        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: {
                call: 'intra_repro_in_inter',
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                datapoints: JSON.stringify(datapoints)
            },
            success: function (json) {
                var content, color, repro_url;
                for (x=0; x<studies_anchors.length; x++) {
                    repro_url = $(studies_anchors[x]).attr("href") + "reproducibility/";
                    if (json[x][0] === 'E') {
                        color = "#74ff5b";
                    } else if (json[x][0] === 'A') {
                        color = "#fcfa8d";
                    } else if (json[x][0] === 'P') {
                        color = "#ff7863";
                    } else {
                        color = "Grey";
                    }
                    content = "&emsp;Reproducibility Status: <em style='padding:2px; background-color: " + color + "'><a style='color: #333;' href='" + repro_url + "' target='_blank'>" + json[x] + "</a></em>";
                    $(studies_anchors[x]).after(content);
                }
            },
            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
});
