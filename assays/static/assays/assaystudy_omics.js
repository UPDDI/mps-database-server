$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages': ['corechart']});
    google.charts.load('visualization', '1', {'packages': ['imagechart']});
    // Set the callback
    google.charts.setOnLoadCallback(fetchOmicsData);

    // FILE-SCOPE VARIABLES
    var study_id = Math.floor(window.location.href.split('/')[5]);

    var omics_data, omics_metadata;
    var lowestL2FC, highestL2FC, lowestPVAL, highestPVAL;

    var cohen_tooltip = "Cohen's D is the mean difference divided by the square root of the pooled variance.";

    $('#pam-cohen-d').next().html($('#pam-cohen-d').next().html() + make_escaped_tooltip(cohen_tooltip));

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

    $(".filter-input").change(function() {
        $("#slider-range-log2foldchange").slider("option", "values", [$("#log2foldchange-low").val(), $("#log2foldchange-high").val()])
        $("#slider-range-pvalue").slider("option", "values", [$("#pvalue-low").val(), $("#pvalue-high").val()])
    })

    $("#apply-filters").click(function() {
        window.spinner.spin(
            document.getElementById("spinner")
        );
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
        drawPlots(JSON.parse(JSON.stringify(omics_data)), false, $("#slider-range-pvalue").slider("option", "values")[0], $("#slider-range-pvalue").slider("option", "values")[1], $("#slider-range-log2foldchange").slider("option", "values")[0], $("#slider-range-log2foldchange").slider("option", "values")[1]);
    })

    function createSliders() {
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
        $("#quantitative-filters").show();
    }

    function fetchOmicsData(){
        window.spinner.spin(
            document.getElementById("spinner")
        );

        $.ajax(
            "/assays_ajax/",
            {
                data: {
                    call: 'fetch_omics_data',
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                    study_id: study_id,
                },
                type: 'POST',
            }
        )
        .success(function(data) {
            console.log("DATA", data)

            omics_data = data['data']
            omics_target_name_to_id = data['target_name_to_id']
            omics_file_id_to_name = data['file_id_to_name']
            if (!('error' in data)) {
                drawPlots(JSON.parse(JSON.stringify(omics_data)), true, 1, 0, 1, 0);
            } else {
                console.log(data['error']);
                // Stop spinner
                window.spinner.stop();
            }

        })
        .fail(function(xhr, errmsg, err) {
            // Stop spinner
            window.spinner.stop();

            alert('An error has occurred, please try different selections.');
            console.log(xhr.status + ": " + xhr.responseText);
        });
    }

    function drawPlots(data, firstTime, minPval, maxPval, minL2FC, maxL2FC) {
        var chartData = {}
        var log2fc, avgexpress, neglog10pvalue, pvalue, check_over, check_under, check_neither, threshold_log2fc, threshold_pvalue;
        check_over = $("#check-over").is(":checked");
        check_under = $("#check-under").is(":checked");
        check_neither = $("#check-neither").is(":checked");
        pvalue_threshold = $("#pvalue-threshold").val()
        log2fc_threshold = $("#log2foldchange-threshold").val()

        for (x of Object.keys(data)) {
            if (!(data[x] in chartData)) {
                chartData[x] = {
                    'volcano': [['Log2FoldChange', 'Over Expressed', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}, 'Under Expressed', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}, 'Not Significant', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}]],
                    'ma': [['Average Expression', 'Over Expressed', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}, 'Under Expressed', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}, 'Not Significant', {'type': 'string', 'role': 'style'}, {'type': 'string', 'role': 'tooltip'}]]
                };
            }

            for (y of Object.keys(data[x])) {
                log2fc = parseFloat(data[x][y][omics_target_name_to_id['log2FoldChange']]);
                avgexpress = Math.log2(parseFloat(data[x][y][omics_target_name_to_id['baseMean']]));
                pvalue = parseFloat(data[x][y][omics_target_name_to_id['pvalue']]);
                neglog10pvalue = -Math.log10(pvalue);

                // On first pass: Determine high/low for Log2FoldChange slider
                if (firstTime) {
                    if (Object.keys(data[x])[0] == y && Object.keys(data)[0] == x) {
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

                // Add data if first pass OR all filter conditions met
                if (firstTime || ((log2fc >= minL2FC && log2fc <= maxL2FC) && (pvalue >= minPval && pvalue <= maxPval))) {
                	if (check_over && (log2fc >= Math.log2(log2fc_threshold) && pvalue <= pvalue_threshold)) {
                		chartData[x]['volcano'].push([log2fc, neglog10pvalue, null, 'TEST', null, null, '', null, null, '']);
                		chartData[x]['ma'].push([avgexpress, log2fc, null, '', null, null, '', null, null, '']);
                	} else if (check_under && (log2fc <= -Math.log2(log2fc_threshold) && pvalue <= pvalue_threshold)) {
                		chartData[x]['volcano'].push([log2fc, null, null, '', neglog10pvalue, null, 'TEST', null, null, '']);
                		chartData[x]['ma'].push([avgexpress, null, null, '', log2fc, null, '', null, null, '']);
                	} else if (check_neither && !(log2fc >= Math.log2(log2fc_threshold) && pvalue <= pvalue_threshold) && !(log2fc <= -Math.log2(log2fc_threshold) && pvalue <= pvalue_threshold)) {
                		chartData[x]['volcano'].push([log2fc, null, null, '', null, null, '', neglog10pvalue, null, 'TEST']);
                		chartData[x]['ma'].push([avgexpress, null, null, '', null, null, '', log2fc, null, '']);
                	}
                }
            }

        }

        if (firstTime) {
            createSliders();
        }

        // console.log(chartData)

        var volcanoData, maData, volcanoChart, maChart;
        var counter = 0;

        $('#volcano-plots').append("<div class='row'>");
        $('#ma-plots').append("<div class='row'>");
        for (const prop in chartData) {
            console.log(prop)
            $('#volcano-plots').append("<div class='col-lg-6'><div id='volcano-" + prop + "'></div></div>");
            $('#ma-plots').append("<div class='col-lg-6'><div id='ma-" + prop + "'></div></div>");
            counter++;

            volcanoData = google.visualization.arrayToDataTable(chartData[prop]['volcano']);
            maData = google.visualization.arrayToDataTable(chartData[prop]['ma']);

            volcanoChart = new google.visualization.LineChart(document.getElementById('volcano-' + prop));
            maChart = new google.visualization.LineChart(document.getElementById('ma-' + prop));

            volcanoOptions['title'] = 'Volcano ' + prop
            maOptions['title'] = 'MA ' + prop

            volcanoChart.draw(volcanoData, volcanoOptions);
            maChart.draw(maData, maOptions);
        }
        $('#volcano-plots').append("</div>");
        $('#ma-plots').append("</div>");

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
