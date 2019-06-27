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
                // Sloppy, make sure get params are up-to-date
                // NOT ALWAYS RELEVANT
                // window.GROUPING.generate_get_params();

                // Call the refresh function specified
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
    // INDICATES THE ORDER OF FILTERS FOR PROCESSING
    ordered_filters: [
        'organ_models',
        'groups',
        'targets',
        'compounds'
    ],
    full_get_parameters: '',
    filters: null,
    // Probably doesn't need to be global
    group_criteria: null,
    post_filter: null,
    filters_param: '',
    group_criteria_param: '',
    post_filter_param: '',
};

// Naive encapsulation
$(document).ready(function () {
    // Current base model
    var current_parent_model = null;
    // Current filter
    var current_filter = null;
    var full_post_filter_data = [];

    var current_filter_selector = null;
    var current_filter_index = null;

    var current_post_filter_data = [];

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

    // Process GET params
    window.GROUPING.process_get_params = function() {
        // Process filters
        // Only needs to be returned
        var raw_filters = $.urlParam('f');
        if ($.urlParam('f')) {
            window.GROUPING.filters_param = 'f=' + $.urlParam('f');
        }
        if (raw_filters) {
            // Default all empty
            window.GROUPING.filters = {
                'organ_models': {},
                'groups': {},
                'compounds': {},
                'targets': {}
            };

            raw_filters = raw_filters.split('+');

            $.each(window.GROUPING.ordered_filters, function(index, current_filter) {
                $.each(raw_filters[index].split(','), function(id_index, current_id) {
                    if (!window.GROUPING.filters[current_filter]) {
                        window.GROUPING.filters[current_filter] = {};
                    }
                    window.GROUPING.filters[current_filter][current_id] = 'true';
                });
            });
        }

        // TODO
        // Process criteria
        // Must be accessible before AJAX call
        var raw_criteria = $.urlParam('c');
        if ($.urlParam('c')) {
            window.GROUPING.group_criteria_param = 'c=' + $.urlParam('c');
        }
        if (raw_criteria) {
            var current_criteria = raw_criteria.split('');

            // Check all matching criteria
            window.GROUPING.group_criteria = {};

            grouping_checkbox_selector.each(function(index, current_checkbox) {
                if (current_criteria[index] && current_criteria[index] === '1') {
                    if (!window.GROUPING.group_criteria[$(this).attr('data-group-relation')]) {
                        window.GROUPING.group_criteria[$(this).attr('data-group-relation')] = [];
                    }
                    window.GROUPING.group_criteria[$(this).attr('data-group-relation')].push(
                        $(this).attr('data-group')
                    );
                }

                // Check or uncheck as necessary
                $(this).prop('checked', current_criteria[index] === '1');
            });
        }
        // Sloppy acquisition
        else if (!window.GROUPING.group_criteria) {
            window.GROUPING.modify_group_criteria_param();
        }

        // TODO
        // Process post_filter
        // Must be accessible before AJAX call
        var raw_post_filter = $.urlParam('p');
        if ($.urlParam('p')) {
            window.GROUPING.post_filter_param = 'p=' + $.urlParam('p');
        }
        if (raw_post_filter && window.GROUPING.full_post_filter) {
            var current_post_filter = raw_post_filter.split('+');

            // For every post-filter in order of where it appears in the page
            post_filter_spawn_selector.each(function(index) {
                var current_filter_values = current_post_filter[index].split(',');

                if (current_filter_values && current_filter_values[0]) {
                    // Spawn
                    $(this).trigger('click');

                    // Uncheck all (but do not provoke a refresh)
                    $('#filter_section_deselect_all').trigger('click');

                    // Unwrap
                    filter_data_table.page.len(-1).draw();

                    // Iterate over every value in this section and check
                    $.each(current_filter_values, function(filter_index, current_value) {
                        var current_checkbox = $('input[data-table-index="' + current_value + '"]:visible')[0];
                        if (current_checkbox) {
                            // Modify the matching checkbox to be marked
                            modify_checkbox(current_checkbox, true);
                        }
                    });

                    // Apply
                    apply_filter_and_swap_buffers(false);

                    // Close
                    filter_popup.dialog('close');
                }
            });
        }

        window.GROUPING.refresh_get_params();
    };

    window.GROUPING.refresh_get_params = function() {
        var parms = [
            window.GROUPING.filters_param,
            window.GROUPING.group_criteria_param,
            window.GROUPING.post_filter_param
        ];

        var strings_to_use = [];

        $.each(parms, function(index, param) {
            if (param.split('=')[1] && param.split('=')[1] !== 'null') {
                strings_to_use.push(param);
            }
        });

        window.GROUPING.full_get_parameters = '?' + strings_to_use.join('&');

        // Change the hrefs to include the filters
        $('.submit-button').each(function() {
            var current_download_href = $(this).attr('href');
            var initial_href = current_download_href.split('?')[0];
            $(this).attr('href', initial_href + window.GROUPING.full_get_parameters);
        });
    };

    window.GROUPING.modify_post_filter_param = function() {
        // NAIVE BUT EXPEDIENT
        // For every post-filter in order of where it appears in the page
        // STUPID, WHY USE THE DOM
        if (!window.GROUPING.post_filter_param) {
            var default_params = [];

            for (var i=0; i < post_filter_spawn_selector.length; i++) {
                default_params.push('+');
            }

            window.GROUPING.post_filter_param = 'p=' + default_params.join('+');
        }

        var post_filter_strings = window.GROUPING.post_filter_param.split('=')[1].split('+');

        var current_post_filter = [];

        // Unwrap
        filter_data_table.page.len(-1).draw();

        if ($('.post-filter-checkbox:visible:checked').length != $('.post-filter-checkbox:visible').length) {
            // Iterate over every visible, checked checkbox and add its index
            $.each($('.post-filter-checkbox:visible:checked'), function(filter_index, current_value) {
                // Add to current
                current_post_filter.push($(this).attr('data-table-index'));
            });
        }

        // Close
        filter_popup.dialog('close');

        // Add to main
        post_filter_strings[current_filter_index] = current_post_filter.join(',');

        window.GROUPING.post_filter_param = 'p=' + post_filter_strings.join('+');

        window.GROUPING.refresh_get_params();
    };

    window.GROUPING.modify_group_criteria_param = function() {
        // BAD, DUMB
        // window.GROUPING.get_grouping_filtering();

        // NAIVE AND NOT DRY
        var criteria_string = [];

        window.GROUPING.group_criteria = {};

        grouping_checkbox_selector.each(function(index, current_checkbox) {
            if (this.checked) {
                criteria_string.push('1');
                if (!window.GROUPING.group_criteria[$(this).attr('data-group-relation')]) {
                    window.GROUPING.group_criteria[$(this).attr('data-group-relation')] = [];
                }
                window.GROUPING.group_criteria[$(this).attr('data-group-relation')].push(
                    $(this).attr('data-group')
                );
            }
            else {
                criteria_string.push('0');
            }
        });

        window.GROUPING.group_criteria_param = 'c=' + criteria_string.join('');

        window.GROUPING.refresh_get_params();
    };

    window.GROUPING.modify_filters_param = function() {
        // DESTROY POST FILTER
        window.GROUPING.post_filter_param = '';
        window.GROUPING.post_filter = {};

        if (window.GROUPING.filters && Object.keys(window.GROUPING.filters).length) {
            var filter_string = [];
            $.each(window.GROUPING.ordered_filters, function(index, current_filter) {
                var curent_filter_string = [];
                $.each(window.GROUPING.filters[current_filter], function(current_id, present) {
                    if (present) {
                        curent_filter_string.push(current_id);
                    }
                });
                filter_string.push(curent_filter_string.join(','));
            });

            window.GROUPING.filters_param = 'f=' + filter_string.join('+');
        }

        window.GROUPING.refresh_get_params();
    };

    // Generate GET params
    // TODO REPLACE WITH SPECIFIC REFRESHES TO AVOID LARGE REFRESH
    window.GROUPING.generate_get_params = function() {
        var string_to_append = [];

        if (window.GROUPING.filters && Object.keys(window.GROUPING.filters).length) {
            var filter_string = [];
            $.each(window.GROUPING.ordered_filters, function(index, current_filter) {
                var curent_filter_string = [];
                $.each(window.GROUPING.filters[current_filter], function(current_id, present) {
                    if (present) {
                        curent_filter_string.push(current_id);
                    }
                });
                filter_string.push(curent_filter_string.join(','));
            });

            window.GROUPING.filters_param = 'f=' + filter_string.join('+');

            string_to_append.push(window.GROUPING.filters_param);
        }

        // TODO
        if (window.GROUPING.filters && Object.keys(window.GROUPING.group_criteria).length) {
            var criteria_string = [];

            grouping_checkbox_selector.each(function(index, current_checkbox) {
                if (this.checked) {
                    criteria_string.push('1');
                }
                else {
                    criteria_string.push('0');
                }
            });

            window.GROUPING.group_criteria_param = 'c=' + criteria_string.join('');

            string_to_append.push(window.GROUPING.group_criteria_param);
        }
        else if ($.urlParam('c')) {
            window.GROUPING.group_criteria_param = 'c=' + $.urlParam('c');

            string_to_append.push(window.GROUPING.group_criteria_param);
        }

        // TODO
        if (window.GROUPING.current_post_filter && Object.keys(window.GROUPING.current_post_filter).length) {
            var post_filter_string = [];

            // For every post-filter in order of where it appears in the page
            // STUPID, WHY USE THE DOM
            post_filter_spawn_selector.each(function(index) {
                var current_post_filter = [];
                // Spawn
                $(this).trigger('click');

                // Unwrap
                filter_data_table.page.len(-1).draw();

                if ($('.post-filter-checkbox:visible:checked').length != $('.post-filter-checkbox:visible').length) {
                    // Iterate over every visible, checked checkbox and add its index
                    $.each($('.post-filter-checkbox:visible:checked'), function(filter_index, current_value) {
                        // Add to current
                        current_post_filter.push($(this).attr('data-table-index'));
                    });
                }

                // Close
                filter_popup.dialog('close');

                // Add to main
                post_filter_string.push(current_post_filter.join(','));
            });

            window.GROUPING.post_filter_param = 'p=' + post_filter_string.join('+');

            string_to_append.push(window.GROUPING.post_filter_param);
        }

        window.GROUPING.full_get_parameters = '?' + string_to_append.join('&');

        // Change the hrefs to include the filters
        $('.submit-button').each(function() {
            var current_download_href = $(this).attr('href');
            var initial_href = current_download_href.split('?')[0];
            $(this).attr('href', initial_href + window.GROUPING.full_get_parameters);
        });
    };

    // TODO PLEASE MAKE THIS NOT CONTRIVED SOON
    var filter_popup = $('#filter_popup');
    var filter_table = filter_popup.find('table');
    var filter_data_table = null;
    var filter_body = filter_table.find('tbody');

    var filter_buffer = {};

    // var filter_popup_header = filter_popup.find('h5');

    function apply_filter_and_swap_buffers(modify) {
        window.GROUPING.current_post_filter[current_parent_model][current_filter] = $.extend(true, {}, filter_buffer);
        filter_buffer = {};

        // Change color if necessary
        var current_filter_button = $('button[data-parent-model="'+ current_parent_model + '"][data-filter-relation="' + current_filter + '"]');

        if (Object.keys(window.GROUPING.current_post_filter[current_parent_model][current_filter]).length !== Object.keys(window.GROUPING.full_post_filter[current_parent_model][current_filter]).length) {
            current_filter_button.addClass('btn-warning');
        }
        else {
            current_filter_button.removeClass('btn-warning');
        }

        // Modify the filter
        if (modify) {
            window.GROUPING.modify_post_filter_param();
        }
    }

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
                    apply_filter_and_swap_buffers(true);

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

        current_filter_selector = $(this);
        current_filter_index = $('#sidebar').find('.post-filter-spawn').index(this);

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
                $('.fixedHeader-locked').remove();
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
                        // obj_name = obj_name.replace('~@|', ' ');
                        obj_name = obj_name.replace(window.SIGILS.COMBINED_VALUE_SIGIL, ' ');
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

    // Trigger change of grouping
    grouping_checkbox_selector.change(function() {
        window.GROUPING.modify_group_criteria_param();
        window.GROUPING.refresh_wrapper();
    });

    // $(window).resize(function() {
        // if ($(window).width() > 768) {
        //      $('#page').addClass('pushed');
        //      $('#sidebar').addClass('active');
        // }
        // else {
        //     $('#page').removeClass('pushed');
        //     $('#sidebar').removeClass('active');
        // }

        // Adjust datatables
    //     setTimeout(function() {
    //         $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
    //     }, 250);
    // });

    if ($(window).width() > 768) {
        $('#page').addClass('pushed');
        $('#sidebar').addClass('active');

        setTimeout(function() {
            $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
        }, 250);
    }
    else {
        $('#autocollapse').width($(window).width());
    }

    // ON LOAD, PROCESS THE GET PARAMS AND APPLY TO ALL SUBMIT BUTTONS
    // TOO DANGEROUS TO PUT HERE, NEED IN RESPECTIVE FUNCTIONS TO AVOID RACE CONDITION
    // window.GROUPING.process_get_params();
    // window.GROUPING.generate_get_params();

    // EXPERIMENTAL
    // IF THERE IS A SIDEBAR, GET RID OF CONTAINER CLASS IN BREADCRUMBS AND FOOTER
    $('#content').removeClass('container').addClass('fluid-container');
    $('#footer').removeClass('container').addClass('fluid-container');
});
