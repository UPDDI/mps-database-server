$(document).ready(function() {
    var filters = {
        'organ_models': {},
        'groups': {},
        'compounds': {},
        'targets': {}
    };

    // see if there are filters from GET parameters
    var get_filters = decodeURIComponent(window.location.search.split('?filters=')[1]);
    if (get_filters && get_filters !== 'undefined') {
        filters = JSON.parse(get_filters);
    }

    var first_run = true;

    var ordered_filters = [
        'organ_models',
        'groups',
        'targets',
        'compounds'
    ];

    var filter_empty_messages = {
        'organ_models': 'Please Select at Least One MPS Model.',
        'groups': 'Please Select at Least One MPS User Group.',
        'targets': 'Please Select at Least One Target.',
        'compounds': 'Please Select at Least One Compound.'
    };

    var submit_buttons_selector = $('.submit-button');

    var number_of_points_selector = $('#number_of_points');
    var number_of_points_container_selector = $('#number_of_points_container');
    var make_more_selections_message_selector = $('#make_more_selections_message');

    var treatment_group_table = $('#treatment_group_table');

    function refresh_filters(parent_filter) {
        number_of_points_container_selector.removeClass('text-success text-danger');
        number_of_points_container_selector.addClass('text-warning');
        number_of_points_selector.html('Calculating, Please Wait');

        // Disable all checkboxes
        // $('.filter-checkbox').attr('disabled', 'disabled');
        $('.filter-table').addClass('gray-out');

        // Change the hrefs to include the filters
        submit_buttons_selector.each(function() {
            var current_download_href = $(this).attr('href');
            var initial_href = current_download_href.split('?')[0];
            var get_for_href = 'filters=' + JSON.stringify(filters);
            $(this).attr('href', initial_href + '?' + get_for_href);
        });

        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: {
                call: 'fetch_pre_submission_filters',
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                filters: JSON.stringify(filters)
            },
            success: function (json) {
                number_of_points_selector.html(json.number_of_points);
                if (json.number_of_points > 0) {
                    number_of_points_container_selector.removeClass('text-warning text-danger');
                    number_of_points_container_selector.addClass('text-success');
                    submit_buttons_selector.removeAttr('disabled');
                }
                else {
                    number_of_points_container_selector.removeClass('text-warning text-success');
                    number_of_points_container_selector.addClass('text-danger');
                    submit_buttons_selector.attr('disabled', 'disabled');
                }

                // Test if this is an "initial" query
                // if (_.isEmpty(json.filters.groups)) {
                //     make_more_selections_message_selector.show();
                //     submit_buttons_selector.attr('disabled', 'disabled');
                // }
                // else {
                //     make_more_selections_message_selector.hide();
                // }

                // Hide initially
                make_more_selections_message_selector.hide();

                $.each(ordered_filters, function (index, filter) {
                    if (_.isEmpty(filters[filter])) {
                        make_more_selections_message_selector.html(filter_empty_messages[filter]);
                        make_more_selections_message_selector.show();
                        submit_buttons_selector.attr('disabled', 'disabled');
                        return false;
                    }
                });

                $.each(json.filters, function (filter, contents) {
                    // Do not refresh current
                    if (filter === parent_filter) {
                        return true;
                    }

                    // Do not refresh MPS Model if you don't have to
                    // Crude, obviously
                    if (filter === 'organ_models' && !first_run && _.keys(filters['organ_models']).length) {
                        return true;
                    }

                    var current_table = $('#filter_' + filter);
                    var current_body = current_table.find('tbody');

                    current_table.DataTable().clear();
                    current_table.DataTable().destroy();
                    current_body.empty();

                    var initial_filter = filters[filter];
                    var current_filter = {};

                    var rows_to_add = [];
                    $.each(contents, function (index, content) {
                        var content_id = content[0];
                        var content_name = content[1];
                        var checkbox = '<input class="big-checkbox filter-checkbox" data-table-index="' + index + '" data-filter="' + filter + '" type="checkbox" value="' + content_id + '">';
                        if (initial_filter[content_id]) {
                            current_filter[content_id] = true;
                            checkbox = '<input class="big-checkbox filter-checkbox" data-table-index="' + index + '" data-filter="' + filter + '" type="checkbox" value="' + content_id + '" checked="checked">';
                        }

                        rows_to_add.push(
                            '<tr>' +
                            '<td>' + checkbox + '</td>' +
                            '<td>' + content_name + '</td>' +
                            '</tr>'
                        )
                    });

                    // Swap to new filter
                    filters[filter] = current_filter;

                    current_body.html(rows_to_add.join(''));

                    // var table_ordering = [[1, 'asc']];
                    // if (_.keys(current_filter).length) {
                    //     table_ordering = [[0, "asc"], [1, 'asc']];
                    // }

                    current_table.DataTable({
                        // Cuts out extra unneeded pieces in the table
                        dom: 'lfrtip',
                        // Scratch the fixedHeader
                        // fixedHeader: {headerOffset: 50},
                        // order: table_ordering,
                        order: [1, 'asc'],
                        // Needed to destroy old table
                        bDestroy: true,
                        columnDefs: [
                            // Treat the group column as if it were just the number
                            { "sSortDataType": "dom-checkbox", "targets": 0, "width": "10%" },
                            { "className": "dt-center", "targets": 0}
                        ]
                    });
                });

                // TODO NOT DRY
                // Swap positions of filter and length selection; clarify filter
                $('.dataTables_filter').css('float', 'left').prop('title', 'Separate terms with a space to search multiple fields');
                $('.dataTables_length').css('float', 'right');

                // Recalculate fixed headers
                // $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();

                // Enable buttons
                $('.filter-table').removeClass('gray-out');

                first_run = false;
            },
            error: function (xhr, errmsg, err) {
                number_of_points_container_selector.removeClass('text-warning text-success');
                number_of_points_container_selector.addClass('text-danger');
                number_of_points_selector.html('An Error has Occurred');

                // Enable boxes
                // $('.filter-checkbox').removeAttr('disabled');
                $('.filter-table').removeClass('gray-out');

                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    // Add a check to datatables data to make sorting work properly (and ensure no missing checks)
    function modify_checkbox(current_table, checkbox, add_or_remove, data_filter) {
        var checkbox_index = $(checkbox).attr('data-table-index');
        var checkbox_data_filter = $(checkbox).attr('data-filter');

        if (add_or_remove) {
            $(checkbox).attr('checked', 'checked');

            current_table.data()[
                checkbox_index
            ][0] = current_table.data()[
                checkbox_index
            ][0].replace('>', ' checked="checked">');


            if (data_filter) {
                data_filter[checkbox_data_filter][checkbox.value] = true;
            }
        }
        else {
            $(checkbox).removeAttr('checked');

            current_table.data()[
                checkbox_index
            ][0] = current_table.data()[
                checkbox_index
            ][0].replace(' checked="checked">', '>');

            if (data_filter) {
                delete data_filter[checkbox_data_filter][checkbox.value];
            }
        }
    }

    // Triggers for select all
    $('.filter-select-all').click(function() {
        var current_table = $(this).attr('data-target-id');
        current_table = $('#' + current_table);
        current_data_table = current_table.DataTable();

        current_data_table.page.len(-1).draw();

        // Recalculate fixed headers
        $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();

        current_table.find('.filter-checkbox').each(function() {
            modify_checkbox(current_data_table, this, true, filters);
        });

        current_data_table.order([[1, 'asc']]);
        current_data_table.page.len(10).draw();

        // Recalculate fixed headers
        $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();

        refresh_filters(current_table.attr('data-filter'));
    });

    // Triggers for deselect all
    $('.filter-deselect-all').click(function() {
        var current_table = $(this).attr('data-target-id');
        current_table = $('#' + current_table);
        current_data_table = current_table.DataTable();

        current_data_table.page.len(-1).draw();

        // Recalculate fixed headers
        $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();

        current_table.find('.filter-checkbox').each(function() {
            modify_checkbox(current_data_table, this, false, filters);
        });

        current_data_table.order([[1, 'asc']]);
        current_data_table.page.len(10).draw();

        // Recalculate fixed headers
        $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();

        refresh_filters(current_table.attr('data-filter'));
    });

    $(document).on('change', '.filter-checkbox', function() {
        var current_table = $(this).parent().parent().parent().parent().DataTable();

        modify_checkbox(current_table, this, $(this).prop('checked'), filters);
        refresh_filters($(this).attr('data-filter'));
    });

    refresh_filters();
});
