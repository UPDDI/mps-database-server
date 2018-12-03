// Contains functions for grouping and filtering data

// Global variable for grouping
window.GROUPING = {
    // Starts null
    refresh_function: null,
    // Starts null
    full_post_filter: null,
    // Starts empty
    current_post_filter: {}
};

// Naive encapsulation
$(document).ready(function () {
    // Current base model
    var current_parent_model = null;
    // Current filter
    var current_filter = null;
    var full_post_filter_data = [];

    var current_post_filter_data = [];

    // Probably doesn't need to be global
    window.GROUPING.group_criteria = {};
    var grouping_checkbox_selector = $('.grouping-checkbox');

    // Iterate over matching placeholders and add correct icons
    var treatment_icon = $('<span>')
        .addClass('glyphicon glyphicon-folder-open')
        .attr('title', 'This parameter contributes to the definition of a Treatment Group.');

    var color_icon = $('<span>')
        .addClass('glyphicon glyphicon-tint')
        .attr('title', 'This parameter contributes to chart Colors.');

    var trellis_icon = $('<span>')
        .addClass('glyphicon glyphicon-th-large')
        .attr('title', 'This parameter contributes to Trellising.');

    $('[data-group-type="treatment"]').each(function() {
        $(this).append(treatment_icon.clone());
    });
    $('[data-group-type="color"]').each(function() {
        $(this).append(color_icon.clone());
    });
    $('[data-group-type="trellis"]').each(function() {
        $(this).append(trellis_icon.clone());
    });

    // Semi-arbitrary at the moment
    window.GROUPING.get_grouping_filtering = function() {
        // THIS IS A CRUDE WAY TO TEST THE GROUPING
        // Reset the criteria
        window.GROUPING.group_criteria = {};
        grouping_checkbox_selector.each(function() {
            if (this.checked) {
                if (!window.GROUPING.group_criteria[$(this).attr('data-group-relation')]) {
                    window.GROUPING.group_criteria[$(this).attr('data-group-relation')] = [];
                }
                window.GROUPING.group_criteria[$(this).attr('data-group-relation')].push(
                    $(this).attr('data-group')
                );
            }
        });

        return window.GROUPING.group_criteria;
    };

    // TODO PLEASE MAKE THIS NOT CONTRIVED SOON
    var filter_popup = $('#filter_popup');
    var filter_table = filter_popup.find('table');
    var filter_data_table = null;
    var filter_body = filter_table.find('tbody');

    var filter_buffer = {};

    // var filter_popup_header = filter_popup.find('h5');

    if (filter_popup) {
        filter_popup.dialog({
            width: 825,
            closeOnEscape: true,
            autoOpen: false,
            close: function () {
                // Purge the buffer
                filter_buffer = {};
                $('body').removeClass('stop-scrolling');
            },
            open: function () {
                $('body').addClass('stop-scrolling');
            },
            buttons: [
            {
                text: 'Apply',
                click: function() {
                    window.GROUPING.current_post_filter[current_parent_model][current_filter] = $.extend({}, filter_buffer);
                    filter_buffer = {};
                    $(this).dialog("close");
                }
            },
            {
                text: 'Cancel',
                click: function() {
                   $(this).dialog("close");
                }
            }]
        });
        filter_popup.removeProp('hidden');
    }

    var filter_popup_title = filter_popup.parent().find("span.ui-dialog-title");

    // Triggers for spawning filters
    // TODO REVISE THIS TERRIBLE SELECTOR
    $('.post-filter-spawn').click(function() {
        // Parent row
        var current_title = $(this).parent().parent().find('td').eq(2).html();

        // Current parent model
        current_parent_model = $(this).attr('data-parent-model');
        // Current filter
        current_filter = $(this).attr('data-filter-relation');

        // Set title and header
        filter_popup_title.html(current_title);
        // filter_popup_header.html(current_filter);

        if (window.GROUPING.full_post_filter && window.GROUPING.full_post_filter[current_parent_model]) {
            full_post_filter_data = window.GROUPING.full_post_filter[current_parent_model][current_filter];
            current_post_filter_data = window.GROUPING.current_post_filter[current_parent_model][current_filter];

            // Initially set buffer to current
            filter_buffer = $.extend({}, current_post_filter_data);

            // Clear current contents
            if (filter_data_table) {
                filter_table.DataTable().clear();
                filter_table.DataTable().destroy();
            }

            filter_body.empty();

            var html_to_append = [];

            if (full_post_filter_data) {
                // Spawn checkboxes
                $.each(full_post_filter_data, function (obj_val, obj_name) {
                    var row = '<tr>';

                    if (current_post_filter_data[obj_val]) {
                        row += '<td width="10%" class="text-center"><input data-obj-name="' + obj_name + '" class="big-checkbox post-filter-checkbox" type="checkbox" value="' + obj_val + '" checked></td>';
                    }
                    else {
                        row += '<td width="10%" class="text-center"><input data-obj-name="' + obj_name + '" class="big-checkbox post-filter-checkbox" type="checkbox" value="' + obj_val + '"></td>';
                    }

                    if (obj_name) {
                        obj_name += '';
                        obj_name = obj_name.replace('~@|', ' ')
                    }

                    // WARNING: NAIVE REPLACE
                    row += '<td>' + obj_name + '</td>';

                    row += '</tr>';

                    html_to_append.push(row);
                });
            }
            else {
                html_to_append.push('<tr><td></td><td>No data to display.</td></tr>');
            }

            filter_body.html(html_to_append.join(''));

            filter_data_table = filter_table.DataTable({
                autoWidth: false,
                destroy: true,
                dom: '<"wrapper"lfrtip>',
                deferRender: true,
                iDisplayLength: 10,
                order: [1, 'asc']
            });

            filter_popup.dialog('open');
        }
    });

    // Triggers for select all
    $('#filter_section_select_all').click(function() {
        filter_data_table.page.len(-1).draw();

        filter_table.find('.post-filter-checkbox').each(function() {
            $(this)
                .prop('checked', false)
                .attr('checked', false)
                .trigger('click');
        });

        filter_data_table.order([[1, 'asc']]);
        filter_data_table.page.len(10).draw();
    });

    // Triggers for deselect all
    $('#filter_section_deselect_all').click(function() {
        filter_data_table.page.len(-1).draw();

        filter_table.find('.post-filter-checkbox').each(function() {
            $(this)
                .prop('checked', true)
                .attr('checked', true)
                .trigger('click');
        });

        filter_data_table.order([[1, 'asc']]);
        filter_data_table.page.len(10).draw();
    });

    // TODO CHECKBOX TRIGGER
    $(document).on('click', '.post-filter-checkbox', function() {
        if (current_parent_model && current_filter) {
            if ($(this).prop('checked')) {
                filter_buffer[$(this).val()] = $(this).attr('data-obj-name');
            }
            else {
                delete filter_buffer[$(this).val()];
            }
        }
    });

    $('#refresh_plots').click(function() {
        if (!window.GROUPING.refresh_function) {
            console.log('Error refreshing');
        }
        else {
            window.GROUPING.refresh_function();
        }
    });
});
