$(document).ready(function() {
    const button_grid = $('#button_grid');

    let current_row_iteration = 0;
    let total_tables = $('.disease-dialog').length;
    let current_row = null;

    $('.disease-dialog').each(function() {
        // Make into a dialog
        $(this).dialog({
            width: $('#content').width(),
        });
        $(this).removeProp('hidden');

        // Make a button to push
        // let new_button = $('<button>')
        //     .text($(this).attr('data-type'))
        //     .addClass('open-dialog')
        //     .attr('data-dialog-id', $(this).attr('id'))

        // button_grid.append(new_button);

        // if (!current_row || current_row_iteration > 3 ) {
        //     current_row = $('<div>').addClass('row');
        //     current_row_iteration = 0;
        //     button_grid.append(current_row);
        // }

        let new_panel_grid = $('<div>')
            .addClass('panel panel-default col-md-4');

        let new_panel_body = $('<div>')
            .addClass('panel-body')
            .append(
                $('<span>')
                    .text($(this).attr('data-type'))
                    .css('font-size', '24px')
                    .css('margin-right', '12px')
            );
        let new_button = $('<button>')
            .addClass('open-dialog btn btn-primary')
            .attr('data-dialog-id', $(this).attr('data-type'))
            .css('margin-top', '-5px')
            .html('<span class="glyphicon glyphicon-fullscreen"></span>');

        // current_row.append(new_panel_grid);
        new_panel_body.append(new_button);
        new_panel_grid.append(new_panel_body);

        button_grid.append(new_panel_grid);

        current_row_iteration += 1;
    });

    // while (current_row && current_row_iteration != 3) {
    //     current_row.append(
    //         $('<div>').addClass('col-md-4')
    //     );
    //     current_row_iteration += 1;
    // }

    $('.open-dialog').click(function() {
        $('.disease-dialog[data-type="' + $(this).attr('data-dialog-id') + '"]').dialog('open');
    });

    // Highlight the current page
    // BE CAREFUL!
    $('a:contains("'+ $('#page_header').attr('data-page-name') + '")').addClass('btn-primary');
});
