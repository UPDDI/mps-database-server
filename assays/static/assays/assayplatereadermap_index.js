$(document).ready(function() {

    let global_plate_map_index_tooltip = "Included in a plate map -  the location on the plate and concentrations of standards, the location on the plate of blanks, and the location on the plate of samples. In cases where effluent was collected and put into an assay plate, that sample time is not considered part of the plate map, it is considered part of the plate reader data file.";
    $('#plate_map_index_tooltip').next().html($('#plate_map_index_tooltip').next().html() + make_escaped_tooltip(global_plate_map_index_tooltip));

    //to format the table - keep
    $('#assayplatereadermaps').DataTable({
        "iDisplayLength": 25,
        "sDom": '<B<"row">lfrtip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[2, "asc"]],
    });

    // keep for now in case add back the second table (group by table)
    // $('#reduce_distinct_base_name').DataTable({
    //     "iDisplayLength": 25,
    //     "sDom": '<B<"row">lfrtip>',
    //     fixedHeader: {headerOffset: 50},
    //     responsive: true,
    //     "order": [[2, "asc"]],
    // });

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
