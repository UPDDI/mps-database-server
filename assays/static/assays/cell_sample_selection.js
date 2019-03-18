// This script was made to prevent redundant code in setup pages

// For passing data
window.CELLS = {
    cell_sample_id_to_label: {}
};
$(document).ready(function () {
    // var cell_sample_search = $('#id_cell_sample_search');
    // var cell_sample_search = $('.open-cell-sample-dialog');
    // var cell_sample_id_selector = cell_sample_search.parent().find('input[readonly=readonly]');
    // Defaults for matrix (irrelevant in matrix item)
    var cell_sample_id_selector = $('#id_cell_sample');
    var cell_sample_label_selector = $('#id_cell_sample_label');
    var cellsamples_selector = $('#cellsamples');

    // Populate cell_sampel_id_to_label
    cellsamples_selector.find('button').each(function() {
        var current_sample_id = $(this).attr('data-cell-sample-id');
        var current_label = $(this).attr('name');
        window.CELLS.cell_sample_id_to_label[current_sample_id] = current_label;
    });

    // Open and then close dialog so it doesn't get placed in window itself
    var dialog = $('#dialog');
    dialog.dialog({
        width: 900,
        height: 500,
        closeOnEscape: true,
        autoOpen: false,
        close: function() {
            $('body').removeClass('stop-scrolling');
        },
        open: function() {
            $('body').addClass('stop-scrolling');
        }
    });
    dialog.removeProp('hidden');

    cellsamples_selector.DataTable({
        "iDisplayLength": -1,
        // Initially sort on receipt date
        "order": [ 1, "desc" ],
        // If one wants to display top and bottom
        "sDom": '<"wrapper"fti>'
    });

    // Move filter to left
    $('.dataTables_filter').css('float', 'left');

    $(document).on('click', '.open-cell-sample-dialog', function() {
        dialog.dialog('open');
        // Get the proper selectors
        cell_sample_id_selector = $(this).parent().find('input[readonly=readonly]');
        cell_sample_label_selector = $(this).parent().find('.small');
        // Remove focus
        // $('.ui-dialog :button').blur();
    });

    $(document).on('click', '.cellsample-selector', function() {
        var cell_sample_id = $(this).attr('data-cell-sample-id');
        cell_sample_id_selector.val(cell_sample_id);
        var cell_sample_name = this.attributes["name"].value;
        cell_sample_label_selector.text(cell_sample_name);
        $('#dialog').dialog('close');
    });

    // Display all labels(irrelevant in matrix)
    $('.cell-sample-id-field').each(function() {
        // Get label
        var current_parent = $(this).parent().parent().parent().parent().parent();
        current_parent.find('label').text($('#cell_sample_' + $(this).val()).attr('name'));
        // Turn density into scientific notation
        // TODO SUBJECT TO CHANGE
        var current_density = current_parent.find('input[name$="-density"]');
        var current_number = Number(current_density.val());
        if (current_number && current_number > 9999) {
            // TODO TODO TODO THIS DOES NOT WORK IN FIREFIX
            current_density.val(current_number.toExponential());
        }
    });
});
