$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages': ['corechart']});
    google.charts.load('visualization', '1', {'packages': ['imagechart']});
    // Set the callback
    google.charts.setOnLoadCallback(fetchOmicsData);

    // FILE-SCOPE VARIABLES
    var study_id = Math.floor(window.location.href.split('/')[5]);

    var omics_data, omics_metadata;
    var lowestL2FC, highestL2FC = 0;

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
        $("#volcano-plots").toggle(500);
        $("#ma-plots").toggle(500);
    });

    $("#apply-filters").click(function() {
        drawPlots(JSON.parse(JSON.stringify(omics_data)), false, $("#slider-range-pvalue").slider("option", "values")[0], $("#slider-range-pvalue").slider("option", "values")[1], $("#slider-range-log2foldchange").slider("option", "values")[0], $("#slider-range-log2foldchange").slider("option", "values")[1]);
    })

    function createSliders() {
        $("#slider-range-pvalue").slider({
            range: true,
            min: 0,
            max: 1.01,
            step: 0.01,
            values: [0, 1],
            slide: function(event, ui) {
                $("#pvalue").val(ui.values[0].toFixed(2) + " - " + ui.values[1].toFixed(2));
            }
        });
        $("#pvalue").val($("#slider-range-pvalue").slider("values", 0).toFixed(2) + " - " + $("#slider-range-pvalue").slider("values", 1).toFixed(2));
        $("#slider-range-log2foldchange").slider({
            range: true,
            min: lowestL2FC,
            max: highestL2FC,
            step: 0.01,
            values: [lowestL2FC, highestL2FC],
            slide: function(event, ui) {
                $("#log2foldchange").val(ui.values[0].toFixed(2) + " - " + ui.values[1].toFixed(2));
            }
        });
        $("#log2foldchange").val($("#slider-range-log2foldchange").slider("values", 0).toFixed(2) + " - " + $("#slider-range-log2foldchange").slider("values", 1).toFixed(2));
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
            // // Stop spinner
            // window.spinner.stop();

            omics_data = data['datafile']
            omics_metadata = data['metadatafile']

            drawPlots(JSON.parse(JSON.stringify(omics_data)), true, 1, 0, 1, 0);
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
        var type;

        for (var x=1; x<data.length; x++) {
            if (!(data[x][6] in chartData)) {
                chartData[data[x][6]] = {
                    'volcano': [['Log2FoldChange', 'Over Expressed', {'type': 'string', 'role': 'style'}, 'Under Expressed', {'type': 'string', 'role': 'style'}, 'General', {'type': 'string', 'role': 'style'}]],
                    'ma': [['Average Expression', 'Over Expressed', {'type': 'string', 'role': 'style'}, 'Under Expressed', {'type': 'string', 'role': 'style'}, 'General', {'type': 'string', 'role': 'style'}]]
                };
            }

            // On first pass: Determine high/low for Log2FoldChange slider
            if (firstTime) {
                if (x == 1) {
                    lowestL2FC = parseFloat(data[x][1]);
                    highestL2FC = parseFloat(data[x][1]);
                }
                if (parseFloat(data[x][1]) < lowestL2FC) {
                    lowestL2FC = parseFloat(data[x][1]);
                }
                if (parseFloat(data[x][1]) > highestL2FC) {
                    highestL2FC = parseFloat(data[x][1]);
                }
                createSliders();
            }

            if (chartData[data[x][6]]['volcano'].length == 1) {
                chartData[data[x][6]]['volcano'].push([0, 0, 'point { fill-opacity: 0; }', 0, 'point { fill-opacity: 0; }', 0, 'point { fill-opacity: 0; }']);
                chartData[data[x][6]]['ma'].push([0, 0, 'point { fill-opacity: 0; }', 0, 'point { fill-opacity: 0; }', 0, 'point { fill-opacity: 0; }']);
            }

            // Add data if first pass OR all filter conditions met
            if (firstTime || ((parseFloat(data[x][1]) >= minL2FC && parseFloat(data[x][1]) <= maxL2FC) && (parseFloat(data[x][4]) >= minPval && parseFloat(data[x][4]) <= maxPval))) {
                if (parseFloat(data[x][1]) >= Math.log2(1.5) && parseFloat(data[x][4]) <= 0.05) {
                    chartData[data[x][6]]['volcano'].push([parseFloat(data[x][1]), -Math.log10(parseFloat(data[x][4])), null, null, null, null, null]);
                    chartData[data[x][6]]['ma'].push([Math.log2(parseFloat(data[x][0])), parseFloat(data[x][1]), null, null, null, null, null]);
                } else if (parseFloat(data[x][1]) <= -Math.log2(1.5) && parseFloat(data[x][4]) <= 0.05) {
                    chartData[data[x][6]]['volcano'].push([parseFloat(data[x][1]), null, null, -Math.log10(parseFloat(data[x][4])), null, null, null,]);
                    chartData[data[x][6]]['ma'].push([Math.log2(parseFloat(data[x][0])), null, null, parseFloat(data[x][1]), null, null, null,]);
                } else {
                    chartData[data[x][6]]['volcano'].push([parseFloat(data[x][1]), null, null, null, null, -Math.log10(parseFloat(data[x][4])), null]);
                    chartData[data[x][6]]['ma'].push([Math.log2(parseFloat(data[x][0])), null, null, null, null, parseFloat(data[x][1]), null]);
                }
            }
        }

        var volcanoData, maData, volcanoChart, maChart;
        var counter = 0;

        $('#volcano-plots').append("<div class='row'>");
        $('#ma-plots').append("<div class='row'>");
        for (const prop in chartData) {
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
            title: 'Legend',
            position: 'none',
            maxLines: 5,
            textStyle: {
                // fontSize: 8,
                bold: true
            }
        },
        hAxis: {
            // Begins empty
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
            // scaleType: 'mirrorLog'
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
            0: { color: '#e2431e' },
            1: { color: '#1c91c0' },
            2: { color: '#333333' }
        }
    }

    var maOptions = {
        titleTextStyle: {
            fontSize: 18,
            bold: true,
            underline: true
        },
        legend: {
            title: 'Legend',
            position: 'none',
            maxLines: 5,
            textStyle: {
                bold: true
            }
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
            0: { color: '#e2431e' },
            1: { color: '#1c91c0' },
            2: { color: '#333333' }
        }
    }
});
