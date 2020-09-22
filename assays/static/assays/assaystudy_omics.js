//GLOBAL-SCOPE
window.OMICS = {
    chart_visiblity: null
};

$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages': ['corechart']});
    google.charts.load('visualization', '1', {'packages': ['imagechart']});
    // Set the callback
    google.charts.setOnLoadCallback(fetchOmicsData);

    // FILE-SCOPE VARIABLES
    var study_id = Math.floor(window.location.href.split('/')[5]);

    var get_params, visible_charts = {};

    function fetchOmicsData(){
        window.spinner.spin(
            document.getElementById("spinner")
        );

        $.ajax(
            "/assays_ajax/",
            {
                data: {
                    call: 'fetch_omics_data_for_visualization',
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                    study_id: study_id,
                },
                type: 'POST',
            }
        )
        .success(function(data) {
            // console.log("DATA", data)

            if (!('error' in data)) {
                window.OMICS.omics_data = JSON.parse(JSON.stringify(data))
                window.OMICS.draw_plots(window.OMICS.omics_data, true, 0, 0, 0, 0, 0, 0, 0);
                for (var chart in data['table']) {
                    visible_charts[data['table'][chart][1]] = true;
                }
            } else {
                console.log(data['error']);
                // Stop spinner
                window.spinner.stop();
            }

        })
        .fail(function(xhr, errmsg, err) {
            // Stop spinner
            window.spinner.stop();

            alert('An error has occurred, failed to retrieve omics data.');
            console.log(xhr.status + ": " + xhr.responseText);
        });
    }

    // On checkbox click, toggle relevant chart.
    // Dynamically generated content does not work with a typical JQuery selector in some cases, hence this.
    $(document).on('click', '.big-checkbox', function() {
        $("#ma-"+$(this).data("checkbox-id")).parent().toggle();
        $("#volcano-"+$(this).data("checkbox-id")).parent().toggle();
        if (this.checked) {
            visible_charts[$(this).data("checkbox-id")] = true;
        } else {
            visible_charts[$(this).data("checkbox-id")] = false;
        }
        window.OMICS.chart_visiblity = visible_charts
    });

    $("#download-filtered-data").click(function(e) {
        e.preventDefault()

        get_params = {
            "negative_log10_pvalue": $("#pvalue-filter1").css("display") !== "none",
            "absolute_log2_foldchange": $("#l2fc-filter2").css("display") !== "none",
            "over_expressed": $("#check-over").is(":checked"),
            "under_expressed": $("#check-under").is(":checked"),
            "neither_expressed": $("#check-neither").is(":checked"),
            "threshold_pvalue": $("#pvalue-threshold").val(),
            "threshold_log2_foldchange": $("#log2foldchange-threshold").val(),
            "min_pvalue": parseFloat($("#slider-range-pvalue").slider("option", "values")[0]).toFixed(3),
            "max_pvalue": parseFloat($("#slider-range-pvalue").slider("option", "values")[1]).toFixed(3),
            "min_negative_log10_pvalue": parseFloat($("#slider-range-pvalue-neg").slider("option", "values")[0]).toFixed(3),
            "max_negative_log10_pvalue": parseFloat($("#slider-range-pvalue-neg").slider("option", "values")[1]).toFixed(3),
            "min_log2_foldchange": parseFloat($("#slider-range-log2foldchange").slider("option", "values")[0]).toFixed(3),
            "max_log2_foldchange": parseFloat($("#slider-range-log2foldchange").slider("option", "values")[1]).toFixed(3),
            "abs_log2_foldchange": parseFloat($("#slider-log2foldchange-abs").slider("option", "value")).toFixed(3),
            "visible_charts": Object.keys(visible_charts).filter(function(key) { return visible_charts[key]}).join("+")
        }

        window.open(window.location.href + "download/?" + $.param(get_params), "_blank")
    });
});
