$(document).ready(function() {

    let global_plate_file_index_tooltip = "After a study has been setup in the database (and chips added to the study), and an assay plate map has been created and saved, a file can be upload and associated to a plate map. Uploading a data file and associated its data to a plate map is the second step in using the assay plate reader upload and calibration feature.";
    $('#plate_file_index_tooltip').next().html($('#plate_file_index_tooltip').next().html() + make_escaped_tooltip(global_plate_file_index_tooltip));

    //to format the table - keep
    $('#assayplatereaderfiles').DataTable({
        "iDisplayLength": 25,
        "sDom": '<B<"row">lfrtip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[2, "asc"]],
    });

    // activates Bootstrap tooltips, must be AFTER tooltips are created - keep
    $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});

    // tool tip functions
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
