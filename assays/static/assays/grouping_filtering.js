// Contains functions for grouping and filtering data

// Global variable for grouping
window.GROUPING = {
    // Refresh wrapper runs refresh_function under certain criteria
    refresh_wrapper: function(manual_refresh) {
        if (!window.GROUPING.refresh_function) {
            console.log('Error refreshing');
        }
        else {
            if (manual_refresh || !document.getElementById("id_manually_refresh").checked) {
                window.GROUPING.refresh_function();
            }
        }
    },
    // Starts null
    refresh_function: null,
    // Starts null
    full_post_filter: null,
    // Starts empty
    current_post_filter: {},
    // Starts null
    set_grouping_filtering: null,
    get_grouping_filtering: null,
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

    var post_filter_spawn_selector = $('.post-filter-spawn');

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

    var toggle_sidebar_button = $('.toggle_sidebar_button');

    // Contrived: Show the toggle sidebar button
    toggle_sidebar_button.removeClass('hidden');

    // Gray out filters with nothing in them
    window.GROUPING.set_grouping_filtering = function(new_post_filter) {
        if (window.GROUPING.full_post_filter === null) {
            window.GROUPING.full_post_filter = JSON.parse(JSON.stringify(new_post_filter));
            window.GROUPING.current_post_filter = JSON.parse(JSON.stringify(new_post_filter));

            post_filter_spawn_selector.each(function() {
                // Current parent model
                current_parent_model = $(this).attr('data-parent-model');
                // Current filter
                current_filter = $(this).attr('data-filter-relation');

                // PLEASE NOTE: TECHNICALLY SHOULD BE PROP
                if (!new_post_filter || !new_post_filter[current_parent_model] || !new_post_filter[current_parent_model][current_filter] || new_post_filter[current_parent_model][current_filter].length < 2) {
                    $(this).attr('disabled', 'disabled');
                    $(this).removeClass('btn-info');
                }
                else {
                    $(this).removeAttr('disabled');
                    $(this).addClass('btn-info');
                }
            });
        }
    }

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
            close: function () {
                // Purge the buffer
                filter_buffer = {};
                $.ui.dialog.prototype.options.close();
            },
            buttons: [
            {
                text: 'Apply',
                click: function() {
                    window.GROUPING.current_post_filter[current_parent_model][current_filter] = $.extend(true, {}, filter_buffer);
                    filter_buffer = {};

                    // Refresh on apply
                    window.GROUPING.refresh_wrapper();

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
    post_filter_spawn_selector.click(function() {
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
            filter_buffer = $.extend(true, {}, current_post_filter_data);

            // Clear current contents
            if (filter_data_table) {
                filter_table.DataTable().clear();
                filter_table.DataTable().destroy();

                // KILL ALL LINGERING HEADERS
                $('.fixedHeader-locked').remove()
            }

            filter_body.empty();

            var html_to_append = [];

            if (full_post_filter_data) {
                // Spawn checkboxes
                var index = 0;
                $.each(full_post_filter_data, function (obj_val, obj_name) {
                    var row = '<tr>';

                    if (current_post_filter_data[obj_val]) {
                        row += '<td><input data-table-index="' + index + '" data-obj-name="' + obj_name + '" class="big-checkbox post-filter-checkbox" type="checkbox" value="' + obj_val + '" checked="checked"></td>';
                    }
                    else {
                        row += '<td><input data-table-index="' + index + '" data-obj-name="' + obj_name + '" class="big-checkbox post-filter-checkbox" type="checkbox" value="' + obj_val + '"></td>';
                    }

                    if (obj_name) {
                        obj_name += '';
                        obj_name = obj_name.replace('~@|', ' ')
                    }

                    // WARNING: NAIVE REPLACE
                    row += '<td>' + obj_name + '</td>';

                    row += '</tr>';

                    html_to_append.push(row);

                    index++;
                });
            }
            else {
                html_to_append.push('<tr><td></td><td>No data to display.</td></tr>');
            }

            filter_body.html(html_to_append.join(''));

            filter_data_table = filter_table.DataTable({
                destroy: true,
                dom: '<"wrapper"lfrtip>',
                deferRender: true,
                iDisplayLength: 10,
                order: [1, 'asc'],
                columnDefs: [
                    // Treat the group column as if it were just the number
                    { "sSortDataType": "dom-checkbox", "targets": 0, "width": "10%" },
                    { "className": "dt-center", "targets": 0}
                ]
            });

            filter_popup.dialog('open');
        }
    });

    // Add a check to datatables data to make sorting work properly (and ensure no missing checks)
    function modify_checkbox(checkbox, add_or_remove) {
        if (current_parent_model && current_filter) {
            var checkbox_index = $(checkbox).attr('data-table-index');

            // Visibly make checked
            $(checkbox).prop('checked', add_or_remove);

            if (add_or_remove) {
                $(checkbox).attr('checked', 'checked');

                filter_data_table.data()[
                    checkbox_index
                ][0] = filter_data_table.data()[
                    checkbox_index
                ][0].replace('>', ' checked="checked">');

                filter_buffer[$(checkbox).val()] = $(checkbox).attr('data-obj-name');
            }
            else {
                $(checkbox).removeAttr('checked');

                filter_data_table.data()[
                    checkbox_index
                ][0] = filter_data_table.data()[
                    checkbox_index
                ][0].replace(' checked="checked">', '>');

                delete filter_buffer[$(checkbox).val()];
            }
        }
    }

    // Triggers for select all
    $('#filter_section_select_all').click(function() {
        filter_data_table.page.len(-1).draw();

        filter_table.find('.post-filter-checkbox').each(function() {
            // $(this)
            //     .prop('checked', false)
            //     .removeAttr('checked')
            //     .trigger('click');
            modify_checkbox(this, true);
        });

        filter_data_table.order([[1, 'asc']]);
        filter_data_table.page.len(10).draw();
    });

    // Triggers for deselect all
    $('#filter_section_deselect_all').click(function() {
        filter_data_table.page.len(-1).draw();

        filter_table.find('.post-filter-checkbox').each(function() {
            // $(this)
            //     .prop('checked', true)
            //     .attr('checked', 'checked')
            //     .trigger('click');
            modify_checkbox(this, false);
        });

        filter_data_table.order([[1, 'asc']]);
        filter_data_table.page.len(10).draw();
    });

    // TODO CHECKBOX TRIGGER
    $(document).on('click', '.post-filter-checkbox', function() {
        if (current_parent_model && current_filter) {
            // if ($(this).prop('checked')) {
            //     filter_buffer[$(this).val()] = $(this).attr('data-obj-name');
            // }
            // else {
            //     delete filter_buffer[$(this).val()];
            // }
            modify_checkbox(this, $(this).prop('checked'));
        }
    });

    $('#refresh_plots').click(function() {
        window.GROUPING.refresh_function();
    });

    toggle_sidebar_button.click(function() {
         $('#sidebar').toggleClass('active');
         $('#page').toggleClass('pushed');
    });

    $(window).resize(function() {
        if ($(window).width() > 768) {
             $('#page').addClass('pushed');
             $('#sidebar').addClass('active');
        }
        else {
            $('#page').removeClass('pushed');
            $('#sidebar').removeClass('active');
        }

        // Adjust datatables
        setTimeout(function() {
            $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
        }, 250);
    });

    if($(window).width() > 768) {
        $('#page').addClass('pushed');
        $('#sidebar').addClass('active');

        setTimeout(function() {
            $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
        }, 250);
    }

    // EXPERIMENTAL
    // IF THERE IS A SIDEBAR, GET RID OF CONTAINER CLASS IN BREADCRUMBS AND FOOTER
    $('#content').removeClass('container').addClass('fluid-container');
    $('#footer').removeClass('container').addClass('fluid-container');
});
