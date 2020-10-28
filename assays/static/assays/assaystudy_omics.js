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
    var present_groups = [];
    var hovered_groups = [];

    // Container that shows up to reveal what a group contains
    var omics_contents_hover = $('#omics_contents_hover');
    // The row to add the group data to
    var omics_contents_hover_body = $('#omics_contents_hover_body');

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

                // Make Difference Table, generate list of groups to aid in hover displays
                // Maybe I should make a way to just get the tds?
                window.GROUPS.make_difference_table();

                // GET THE PRESENT GROUPS
                // $('#difference_table_body').find('tr').each(function() {
                //     present_groups.push($(this).data('group-name'));
                // });

                // TEMPORARY
                // GET THE GROUP NAMES
                let full_series_data = JSON.parse($('#id_series_data').val());

                $.each(full_series_data.series_data, function(index, group) {
                    present_groups.push(group.name);
                });
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

    // function generate_row_html(hovered_groups) {
    //     // (these divs are contrivances)
    //     var name_row = $('<div>').append(
    //         $('#difference_table_body').find('[data-group-name="' + hovered_groups[0] + '"]').clone().append(
    //             $('#difference_table_body').find('[data-group-name="' + hovered_groups[1] + '"]').clone()
    //         )
    //     );

    //     var full_row = $('<div>');

    //     return name_row.html() + full_row.html();
    // }

    // NOT DRY
    function generate_row_html(current_groups) {
        var full_row = $('<div>');

        // SUBJECT TO CHANGE
        // Just draws from the difference table
        // Be careful with conditionals! Zero has the truthiness of *false*!
        $.each(current_groups, function(index, group_name) {
            let name_row = $('<tr>').append($('<td>').text(group_name));

            full_row.append(name_row);

            let content_row = $('<tr>');

            // NOT VERY ELEGANT
            let current_stored_tds = window.GROUPS.difference_table_displays[group_name];

            // Determine row hiding
            // NOT DRY
            let columns_to_check = [
                'model',
                'test_type',
                'cell',
                'compound',
                'setting'
            ];

            $.each(columns_to_check, function(index, key) {
                if (!window.GROUPS.hidden_columns[key]) {
                    content_row.append(
                        current_stored_tds[key].clone(),
                    )
                }
            });

            full_row.append(content_row);
        });

        return full_row.html();
    }

    $(document).on('mouseover', '.omics-groups-hover, svg > g', function() {
        hovered_groups = [];

        if ($(this).text()) {
            // THIS CAN CAUSE COLLISIONS IN THE CASE OF SUBSTRINGS
            // (ie. Group 1 and Group 12 are both matched)
            for (group in present_groups) {
                if ($(this).text().includes(present_groups[group])) {
                    hovered_groups.push(present_groups[group]);
                }
            }

            if (hovered_groups.length) {
                omics_contents_hover.show();
                // Hard value for left (TODO: Probably better to set to left of the matrix?)
                var left = $('#omics_table').position().left - 15;
                // Place slightly below current label
                var top = $(this).offset().top + 50;
                omics_contents_hover.offset({left: left, top: top});

                omics_contents_hover_body.empty();
                omics_contents_hover_body.html(
                    generate_row_html(hovered_groups)
                );
            }
        }
    });

    $(document).on('mouseout', '.omics-groups-hover, svg > g', function() {
        omics_contents_hover.hide();
    });

});
