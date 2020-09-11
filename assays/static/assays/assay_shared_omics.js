//GLOBAL-SCOPE
window.OMICS = {
    draw_plots: null,
    omics_data: null
};

$(document).ready(function () {

    var lowestL2FC, highestL2FC, lowestPVAL, highestPVAL;

    // Swap between Volcano and MA plots
    $("#toggle-plot-type").click(function() {
        if ($("#ma-plots").css("display") == "none") {
            $("#toggle-plot-type").text("Switch to Volcano Plots");
            $("#ma-plots").prependTo($("#plots"));
        } else {
            $("#toggle-plot-type").text("Switch to MA Plots");
            $("#volcano-plots").prependTo($("#plots"));
        }
        $("#volcano-plots").toggle();
        $("#ma-plots").toggle();
    });

    // Swap between P-value and -Log10(P-value)
    $(".swap-pvalue").click(function() {
        $("#pvalue-filter1").toggle();
        $("#pvalue-filter2").toggle();
    });

    // Swap between Log2(FoldChange) and Absolute Log2(FoldChange)
    $(".swap-l2fc").click(function() {
        $("#l2fc-filter1").toggle();
        $("#l2fc-filter2").toggle();
    });

    // Correct filter inputs on slider change
    $(".filter-input").change(function() {
        $("#slider-range-log2foldchange").slider("option", "values", [$("#log2foldchange-low").val(), $("#log2foldchange-high").val()])
        $("#slider-log2foldchange-abs").slider("option", "value", [$("#log2foldchange-abs").val()])
        $("#slider-range-pvalue").slider("option", "values", [$("#pvalue-low").val(), $("#pvalue-high").val()])
        $("#slider-range-pvalue-neg").slider("option", "values", [$("#pvalue-low-neg").val(), $("#pvalue-high-neg").val()])
    })

    // Apply filters and thresholds before drawing graphs
    $("#apply-filters").click(function() {
        window.spinner.spin(
            document.getElementById("spinner")
        );

        // Update threshold colors
        volcanoOptions['series'] = {
            0: { color: $("#color-over-expressed").val() },
            1: { color: $("#color-under-expressed").val() },
            2: { color: $("#color-not-significant").val() }
        };
        maOptions['series'] = {
            0: { color: $("#color-over-expressed").val() },
            1: { color: $("#color-under-expressed").val() },
            2: { color: $("#color-not-significant").val() }
        };

        // Draw filtered plots
        window.OMICS.draw_plots(
            window.OMICS.omics_data,
            false,
            $("#slider-range-pvalue").slider("option", "values")[0],
            $("#slider-range-pvalue").slider("option", "values")[1],
            $("#slider-range-log2foldchange").slider("option", "values")[0],
            $("#slider-range-log2foldchange").slider("option", "values")[1],
            $("#slider-range-pvalue-neg").slider("option", "values")[0],
            $("#slider-range-pvalue-neg").slider("option", "values")[1],
            $("#slider-log2foldchange-abs").slider("option", "value")
        );
    })

    function createSliders() {
        //P-value filter slider
        $("#slider-range-pvalue").slider({
            range: true,
            min: lowestPVAL,
            max: highestPVAL+0.001,
            step: 0.001,
            values: [lowestPVAL, highestPVAL],
            slide: function(event, ui) {
                $("#pvalue-low").val(ui.values[0].toFixed(3));
                $("#pvalue-high").val(ui.values[1].toFixed(3));
            }
        });
        $("#pvalue-low").val($("#slider-range-pvalue").slider("values", 0).toFixed(3));
        $("#pvalue-high").val($("#slider-range-pvalue").slider("values", 1).toFixed(3));

        // -Log10(P-value) filter slider
        $("#slider-range-pvalue-neg").slider({
            range: true,
            min: -Math.log10(highestPVAL),
            max: -Math.log10(lowestPVAL)+0.001,
            step: 0.001,
            values: [-Math.log10(highestPVAL), -Math.log10(lowestPVAL)],
            slide: function(event, ui) {
                $("#pvalue-low-neg").val(ui.values[0].toFixed(3));
                $("#pvalue-high-neg").val(ui.values[1].toFixed(3));
            }
        });
        $("#pvalue-low-neg").val($("#slider-range-pvalue-neg").slider("values", 0).toFixed(3));
        $("#pvalue-high-neg").val($("#slider-range-pvalue-neg").slider("values", 1).toFixed(3));

        // Log2(FoldChange) filter slider
        $("#slider-range-log2foldchange").slider({
            range: true,
            min: lowestL2FC,
            max: highestL2FC,
            step: 0.001,
            values: [lowestL2FC, highestL2FC],
            slide: function(event, ui) {
                $("#log2foldchange-low").val(ui.values[0].toFixed(3));
                $("#log2foldchange-high").val(ui.values[1].toFixed(3));
            }
        });
        $("#log2foldchange-low").val($("#slider-range-log2foldchange").slider("values", 0).toFixed(3));
        $("#log2foldchange-high").val($("#slider-range-log2foldchange").slider("values", 1).toFixed(3));

        // Absolute Log2(FoldChange) filter slider
        let log2foldchange_absolute = Math.max(-lowestL2FC, highestL2FC)
        $("#slider-log2foldchange-abs").slider({
            range: "min",
            min: 0,
            max: log2foldchange_absolute,
            step: 0.001,
            value: log2foldchange_absolute,
            slide: function(event, ui) {
                $("#log2foldchange-abs").val(ui.value.toFixed(3));
            }
        });
        $("#log2foldchange-abs").val($("#slider-log2foldchange-abs").slider("value").toFixed(3));

        $("#quantitative-filters").show();
    }

    window.OMICS.draw_plots = function(omics_data, firstTime, minPval, maxPval, minL2FC, maxL2FC, minPval_neg, maxPval_neg, L2FC_abs, called_from="analysis") {
        var chartData = {}
        var log2fc, avgexpress, neglog10pvalue, pvalue, check_over, check_under, check_neither, log2fc_threshold, threshold_pvalue;
        check_over = $("#check-over").is(":checked");
        check_under = $("#check-under").is(":checked");
        check_neither = $("#check-neither").is(":checked");
        pvalue_threshold = $("#pvalue-threshold").val()
        log2fc_threshold = $("#log2foldchange-threshold").val()

        // For each group/file/TBD
        for (x of Object.keys(omics_data['data'])) {
            if (!(omics_data['data'][x] in chartData)) {
                chartData[x] = {
                    'volcano': [['Log2(FoldChange)', 'Over Expressed', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}, 'Under Expressed', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}, 'Not Significant', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}]],
                    'ma': [['Average Expression', 'Over Expressed', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}, 'Under Expressed', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}, 'Not Significant', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}]]
                };
            }

            // Create Omics info table on first pass
            if (firstTime && called_from == 'anaylsis') {
                $("#omics_table_body").html($("#omics_table_body").html()+"<tr><td class='dt-center'><input type='checkbox' class='big-checkbox'></td><td>" + x + "</td><td>" + omics_table[x] + "</td></tr>")
            }

            // For each gene probe ID
            for (y of Object.keys(omics_data['data'][x])) {
                log2fc = parseFloat(omics_data['data'][x][y][omics_data['target_name_to_id']['log2FoldChange']]);
                avgexpress = Math.log2(parseFloat(omics_data['data'][x][y][omics_data['target_name_to_id']['baseMean']]));
                pvalue = parseFloat(omics_data['data'][x][y][omics_data['target_name_to_id']['pvalue']]);
                neglog10pvalue = -Math.log10(pvalue);
                stat = parseFloat(omics_data['data'][x][y][omics_data['target_name_to_id']['stat']]);
                padj = parseFloat(omics_data['data'][x][y][omics_data['target_name_to_id']['padj']]);

                // On first pass: Determine high/low for Log2FoldChange slider
                if (firstTime) {
                    if (Object.keys(omics_data['data'][x])[0] == y && Object.keys(omics_data['data'])[0] == x) {
                        lowestL2FC = log2fc;
                        highestL2FC = log2fc;
                        lowestPVAL = pvalue;
                        highestPVAL = pvalue;
                    }
                    if (log2fc < lowestL2FC) {
                        lowestL2FC = log2fc;
                    }
                    if (log2fc > highestL2FC) {
                        highestL2FC = log2fc;
                    }
                    if (pvalue < lowestPVAL) {
                        lowestPVAL = pvalue;
                    }
                    if (pvalue > highestPVAL) {
                        highestPVAL = pvalue;
                    }
                }

                // Starter rows for each plot, consisting of headers and an invisible anchor point.
                if (chartData[x]['volcano'].length == 1) {
                	chartData[x]['volcano'].push([0, 0, 'point { fill-opacity: 0; }', '', 0, 'point { fill-opacity: 0; }', '', 0, 'point { fill-opacity: 0; }', '']);
                	chartData[x]['ma'].push([0, 0, 'point { fill-opacity: 0; }', '', 0, 'point { fill-opacity: 0; }', '', 0, 'point { fill-opacity: 0; }', '']);
                }

                // Determine filter conditions.
                if ($("#pvalue-filter1").css("display") !== "none") {
                    var pvalue_filter = (pvalue >= minPval && pvalue <= maxPval);
                } else {
                    var pvalue_filter = (neglog10pvalue >= minPval_neg && neglog10pvalue <= maxPval_neg);
                }

                if ($("#l2fc-filter1").css("display") !== "none") {
                    var l2fc_filter = (log2fc >= minL2FC && log2fc <= maxL2FC);
                } else {
                    var l2fc_filter = (log2fc >= -L2FC_abs && log2fc <= L2FC_abs);
                }

                // Add data if first pass OR all filter conditions met.
                if (firstTime || ((pvalue_filter) && (l2fc_filter))) {
                    // Threshold determination and point addition.
                	if (check_over && (log2fc >= log2fc_threshold && pvalue <= pvalue_threshold)) {
                		chartData[x]['volcano'].push([log2fc, neglog10pvalue, null, 'Probe ID: ' + y + '\n-Log10(pvalue): ' + neglog10pvalue.toFixed(3) + '\nLog2(FoldChange): ' + log2fc.toFixed(3) + '\nStat: ' + stat.toFixed(3) + '\nAdjusted P-Value: ' + padj.toFixed(3), null, null, '', null, null, '']);
                		chartData[x]['ma'].push([avgexpress, log2fc, null, 'Probe ID: ' + y + '\nLog2(FoldChange): ' + log2fc.toFixed(3) + '\nAverage Expression: ' + avgexpress.toFixed(3) + '\nStat: ' + stat.toFixed(3) + '\nAdjusted P-Value: ' + padj.toFixed(3), null, null, '', null, null, '']);
                	} else if (check_under && (log2fc <= -log2fc_threshold && pvalue <= pvalue_threshold)) {
                		chartData[x]['volcano'].push([log2fc, null, null, '', neglog10pvalue, null, 'Probe ID: ' + y + '\n-Log10(pvalue): ' + neglog10pvalue.toFixed(3) + '\nLog2(FoldChange): ' + log2fc.toFixed(3) + '\nStat: ' + stat.toFixed(3) + '\nAdjusted P-Value: ' + padj.toFixed(3), null, null, '']);
                		chartData[x]['ma'].push([avgexpress, null, null, '', log2fc, null, 'Probe ID: ' + y + '\nLog2(FoldChange): ' + log2fc.toFixed(3) + '\nAverage Expression: ' + avgexpress.toFixed(3) + '\nStat: ' + stat.toFixed(3) + '\nAdjusted P-Value: ' + padj.toFixed(3), null, null, '']);
                	} else if (check_neither && !(log2fc >= log2fc_threshold && pvalue <= pvalue_threshold) && !(log2fc <= -log2fc_threshold && pvalue <= pvalue_threshold)) {
                		chartData[x]['volcano'].push([log2fc, null, null, '', null, null, '', neglog10pvalue, null, 'Probe ID: ' + y + '\n-Log10(pvalue): ' + neglog10pvalue.toFixed(3) + '\nLog2(FoldChange): ' + log2fc.toFixed(3) + '\nStat: ' + stat.toFixed(3) + '\nAdjusted P-Value: ' + padj.toFixed(3)]);
                		chartData[x]['ma'].push([avgexpress, null, null, '', null, null, '', log2fc, null, 'Probe ID: ' + y + '\nLog2(FoldChange): ' + log2fc.toFixed(3) + '\nAverage Expression: ' + avgexpress.toFixed(3) + '\nStat: ' + stat.toFixed(3) + '\nAdjusted P-Value: ' + padj.toFixed(3)]);
                	}
                }
            }

        }

        if (firstTime) {
            createSliders();
            if (called_from == 'anaylsis') {
                $("#omics_table").DataTable({
                    order: [1, 'asc'],
                    responsive: true,
                    dom: 'B<"row">lfrtip',
                    paging: false,
                    fixedHeader: {headerOffset: 50},
                    deferRender: true,
                    columnDefs: [
                        // Try to sort on checkbox
                        {"sortable": false, "targets": 0, "width": "10%"}
                    ]
                });
            }
        }

        var volcanoData, maData, volcanoChart, maChart;

        let volcano_chart_row = $('<div>').addClass('row');
        let ma_chart_row = $('<div>').addClass('row');
        // $('#volcano-plots').append("<div class='row'>");
        // $('#ma-plots').append("<div class='row'>");
        for (const prop in chartData) {
            // console.log(prop)
            volcano_chart_row.append("<div class='col-lg-6'><div id='volcano-" + prop + "'></div></div>");
            ma_chart_row.append("<div class='col-lg-6'><div id='ma-" + prop + "'></div></div>");
        }

        $('#volcano-plots').html(volcano_chart_row);
        $('#ma-plots').append(ma_chart_row);

        for (const prop in chartData) {
            volcanoData = google.visualization.arrayToDataTable(chartData[prop]['volcano']);
            maData = google.visualization.arrayToDataTable(chartData[prop]['ma']);

            volcanoChart = new google.visualization.LineChart(document.getElementById('volcano-' + prop));
            maChart = new google.visualization.LineChart(document.getElementById('ma-' + prop));

            volcanoOptions['title'] = prop
            maOptions['title'] = prop

            volcanoChart.draw(volcanoData, volcanoOptions);
            maChart.draw(maData, maOptions);
        }

        // Stop spinner
        window.spinner.stop();
    }

    var volcanoOptions = {
        titleTextStyle: {
            fontSize: 18,
            bold: true,
            underline: true
        },
        legend: {
            position: 'none',
        },
        hAxis: {
            title: 'Log2FoldChange',
            textStyle: {
                bold: true
            },
            titleTextStyle: {
                fontSize: 14,
                bold: true,
                italic: false
            },
            minValue: -1,
            maxValue: 1,
        },
        vAxis: {
            title: '-Log10(P-Value)',
            textStyle: {
                bold: true
            },
            titleTextStyle: {
                fontSize: 14,
                bold: true,
                italic: false
            },
            // This doesn't seem to interfere with displaying negative values
            minValue: 0,
            viewWindowMode: 'explicit'
        },
        pointSize: 5,
        lineWidth: 0,
        'chartArea': {
            'width': '65%',
            'height': '65%',
            // left: 100
        },
        'height': 400,
        'width': 600,
        // Individual point tooltips, not aggregate
        focusTarget: 'datum',
        series: {
            0: { color: $("#color-over-expressed").val() },
            1: { color: $("#color-under-expressed").val() },
            2: { color: $("#color-not-significant").val() }
        }
    }

    var maOptions = {
        titleTextStyle: {
            fontSize: 18,
            bold: true,
            underline: true
        },
        legend: {
            position: 'none',
        },
        hAxis: {
            title: 'Average Expression',
            textStyle: {
                bold: true
            },
            titleTextStyle: {
                fontSize: 14,
                bold: true,
                italic: false
            },
            minValue: 0,
            scaleType: 'log'
        },
        vAxis: {
            title: 'Log2FoldChange',
            textStyle: {
                bold: true
            },
            titleTextStyle: {
                fontSize: 14,
                bold: true,
                italic: false
            },
            // This doesn't seem to interfere with displaying negative values
            minValue: -1,
            maxValue: 1,
            viewWindowMode: 'explicit'
        },
        pointSize: 5,
        lineWidth: 0,
        'chartArea': {
            'width': '65%',
            'height': '65%',
            // left: 100
        },
        'height': 400,
        'width': 600,
        // Individual point tooltips, not aggregate
        focusTarget: 'datum',
        series: {
            0: { color: $("#color-over-expressed").val() },
            1: { color: $("#color-under-expressed").val() },
            2: { color: $("#color-not-significant").val() }
        }
    }
});