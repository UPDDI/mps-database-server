$(document).ready(function() {

    let global_plate_map_index_tooltip = "After a study has been setup in the database matrix items (i.e. chips) have been added to the study, assay plate maps can be create here. Making an assay plate map is the first step in using the assay plate reader upload and calibration feature. Step 2) After the plate map is made, add a data file and identify data blocks and assign them to a plate map. Step 3) Return here and select Edit to process and export data.";
    $('#plate_map_index_tooltip').next().html($('#plate_map_index_tooltip').next().html() + make_escaped_tooltip(global_plate_map_index_tooltip));

    // to format the table - keep
    $('#assayplatereadermaps').DataTable({
        "iDisplayLength": 25,
        "sDom": '<B<"row">lfrtip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[2, "asc"]],
    });

    // Activates Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});

    function escapeHtml(html) {
        return $('<div>').text(html).html();
    }

    function make_escaped_tooltip(title_text) {
        let new_span = $('<div>').append($('<span>')
            .attr('data-toggle', "tooltip")
            .attr('data-title', escapeHtml(title_text))
            .addClass("glyphicon glyphicon-question-sign")
            .attr('aria-hidden', "true")
            .attr('data-placement', "bottom"));
        return new_span.html();
    }

});
