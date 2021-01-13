// This script adds previews for images
$(document).ready(function () {
    var model_image = $('#id_model_image');
    var image_display = $('#image_display');
    var current_display = $('#current_display');

    // Change cell_image preview as necessary
    model_image.change(function() {
        IMAGES.display_image(model_image, image_display, current_display);
    });

    // CRUDE: Ideally, we would make edit tables such as this re-usable
    // TEMPORARY
    const series_data_selector = $('#id_series_data');

    // FULL DATA
    // TEMPORARY
    let full_series_data = JSON.parse(series_data_selector.val());

    if (series_data_selector.val() === '{}') {
        full_series_data = {
            series_data: []
        };
    }

    // SERIES DATA
    let series_data = full_series_data.series_data;

    // ERRORS
    const setup_table_errors_selector = $('#setup_table_errors').find('.errorlist');

    let table_errors = {};

    setup_table_errors_selector.find('li').each(function() {
        let current_text = $(this).text();
        let split_info = current_text.split('-')[0];
        let error_message = current_text.split('-').slice(1).join('-');
        table_errors[split_info] = error_message;
    });

    // CRUDE AND BAD
    // If I am going to use these, they should be ALL CAPS to indicate global status
    const cell_prefix = 'cell';
    const setting_prefix = 'setting';

    // The different components of a setup
    const prefixes = [
        'cell',
        'setting',
    ];

    const time_prefixes = [
        'addition_time',
        'duration'
    ];

    // DATA FOR THE VERSION
    let current_setup = {};

    // CRUDE
    // MAKE SURE ALL PREFIXES ARE PRESENT
    $.each(prefixes, function(index, prefix) {
        if (!current_setup[prefix]) {
          current_setup[prefix] = [];
        }
    });

    // SOMEWHAT TASTELESS USE OF VARIABLES TO TRACK WHAT IS BEING EDITED
    let current_prefix = '';
    let current_row_index = null;
    let current_column_index = null;

    // DISPLAYS
    // JS ACCEPTS STRING LITERALS IN OBJECT INITIALIZATION
    let empty_html = {};
    const empty_cell_html = $('#empty_cell_html');
    const empty_setting_html = $('#empty_setting_html');
    const empty_error_html = $('#empty_error_html').children();

    empty_html[cell_prefix] = empty_cell_html;
    empty_html[setting_prefix] = empty_setting_html;

    // TRICKY: We need to paginate the groups, otherwise the DOM will detonate
    let current_page = 0;
    let number_of_pages = 1;

    const group_table_display_length = $('#id_group_table_length');
    let display_length = parseInt(group_table_display_length.val());

    // PUT TRIGGER IN A BETTER SPOT
    // NOTE THAT THIS IS NOT TRIGGERED INITIALLY (DO NOT WANT TO REDRAW SUPERFLUOUSLY)
    group_table_display_length.change(function() {
        display_length = parseInt(group_table_display_length.val());
        // GO BACK TO THE FIRST PAGE
        rebuild_table(false, 0);
    });

    // Selector clarity
    const pagination_previous_button_selector = $('.group-table-previous');
    const pagination_next_button_selector = $('.group-table-next');
    const pagination_current_page_selector = $('.group-table-current');

    // TODO TODO TODO: WE NEED TO GENERATE THE PAGINATOR(S) BEFORE THE TABLE
    // TODO TODO TODO: Obviously we need to know the number of pages etc.
    function revise_paginator_text() {
        number_of_pages = Math.ceil(series_data.length / display_length);

        if (number_of_pages === 0) {
            number_of_pages = 1;
        }

        pagination_current_page_selector.text(
            'Page ' + (current_page + 1) + ' of ' + number_of_pages
        );

        if (current_page === 0) {
            pagination_previous_button_selector.addClass('disabled');
        }
        else {
            pagination_previous_button_selector.removeClass('disabled');
        }

        if (current_page === (number_of_pages - 1)) {
            pagination_next_button_selector.addClass('disabled');
        }
        else {
            pagination_next_button_selector.removeClass('disabled');
        }
    }

    // CRUDE: TRIGGERS FOR NEXT AND PREVIOUS
    // PROBABLY A GOOD IDEA TO MOVE AND REVISE
    // TODO TODO TODO
    pagination_previous_button_selector.click(function() {
        if (!$(this).hasClass('disabled') && current_page > 0) {
            rebuild_table(false, current_page - 1);
        }
    });

    pagination_next_button_selector.click(function() {
        if (!$(this).hasClass('disabled') && current_page < number_of_pages) {
            rebuild_table(false, current_page + 1);
        }
    });

    // Default values
    var default_values = {};
    $.each(prefixes, function(prefix_index, prefix) {
        default_values[prefix] = {};
        var last_index = $('.' + prefix).length - 1;

        $('#' + prefix + '-' + last_index).find(':input:not(:checkbox)').each(function() {
            var split_name = $(this).attr('name').split('-');
            var current_name = split_name[split_name.length - 1];

            // CRUDE: DO NOT INCLUDE VERSION
            if (current_name === 'organ_model_version') {
                return true;
            }

            default_values[prefix][current_name] = $(this).val();
        });
    });

    function dialog_box_values_valid(this_popup, prefix) {
        // Contrived: TODO TODO TODO
        return true;
    }

    function apply_dialog_box_values(this_popup, prefix) {
        // ACTUALLY MAKE THE CHANGE TO THE RESPECTIVE ENTITY
        // TODO TODO TODO
        var current_data = {};

        // Apply the values from the inputs
        this_popup.find('input').each(function() {
            if ($(this).attr('name')) {
                current_data[$(this).attr('name').replace(current_prefix + '_', '')] = $(this).val();
            }
        });

        // Apply the values from the selects
        this_popup.find('select').each(function() {
            if ($(this).attr('name')) {
                current_data[$(this).attr('name').replace(current_prefix + '_', '') + '_id'] = $(this).val();
            }
        });

        // SLOPPY
        // DEAL WITH SPLIT TIMES
        $.each(time_prefixes, function(index, current_time_prefix) {
            if (current_data[current_time_prefix + '_minute'] !== undefined) {
                current_data[current_time_prefix] = window.SPLIT_TIME.get_minutes(
                        current_data[current_time_prefix + '_day'],
                        current_data[current_time_prefix + '_hour'],
                        current_data[current_time_prefix + '_minute']
                );
                $.each(window.SPLIT_TIME.time_conversions, function(key, value) {
                    delete current_data[current_time_prefix + '_' + key];
                });
            }
        });

        // Special exception for cell_sample
        if (this_popup.find('input[name="' + prefix + '_cell_sample"]')[0]) {
            current_data['cell_sample_id'] = this_popup.find('input[name="' + prefix + '_cell_sample"]').val();
            delete current_data['cell_sample'];
        }

        // Modify the setup data
        modify_series_data(current_prefix, current_data, current_row_index, current_column_index);

        // Get the display for the current content
        var html_contents = get_content_display(current_prefix, current_row_index, current_column_index, current_data, true);

        // Apply the content
        $('a[data-edit-button="true"][data-row="' + current_row_index +'"][data-column="' + current_column_index +'"][data-prefix="' + current_prefix + '"]').parent().html(html_contents);

        // Overkill
        // rebuild_table();
        window.GROUPS.make_difference_table();

        this_popup.dialog('close');
    }

    // CREATE DIALOGS
    $.each(prefixes, function(index, prefix) {
        var current_dialog = $('#' + prefix + '_dialog');
        current_dialog.dialog({
            width: 825,
            open: function() {
                $.ui.dialog.prototype.options.open();
                // BAD
                setTimeout(function() {
                    // Blur all
                    $('.ui-dialog').find('input, select, button').blur();
                }, 150);

                // Populate the fields
                var current_data = $.extend(true, {}, series_data[current_row_index][current_prefix][current_column_index]);

                var this_popup = $(this);

                // Apply current data to popup inputs
                this_popup.find('input').each(function() {
                    if ($(this).attr('name')) {
                        $(this).val(current_data[$(this).attr('name').replace(current_prefix + '_', '')]);
                    }
                });

                // Apply current data to selects
                this_popup.find('select').each(function() {
                    if ($(this).attr('name')) {
                        this.selectize.setValue(current_data[$(this).attr('name').replace(current_prefix + '_', '') + '_id']);
                    }
                });

                // TODO SPECIAL EXCEPTION FOR CELL SAMPLE
                this_popup.find('input[name="' + prefix + '_cell_sample"]').val(
                    current_data['cell_sample_id']
                );

                if (current_data['cell_sample_id']) {
                    // this_popup.find('#id_cell_sample_label').text($('#cell_sample_' + current_data['cell_sample_id']).attr('data-name'));
                    this_popup.find('#id_cell_sample_label').text(window.CELLS.cell_sample_id_to_label[current_data['cell_sample_id']]);
                }
                else {
                    this_popup.find('#id_cell_sample_label').text('');
                }

                // TODO, ANOTHER BARBARIC EXCEPTION (not the best way to handle defaults...)
                // TODO PLEASE REVISE
                if (this_popup.find('#id_cell_biosensor')[0] && !current_data['biosensor_id']) {
                    this_popup.find('#id_cell_biosensor')[0].selectize.setValue(
                        2
                    );
                }

                // TODO SPECIAL EXCEPTION FOR TIMES
                $.each(time_prefixes, function(index, current_time_prefix) {
                    var split_time = window.SPLIT_TIME.get_split_time(
                        current_data[current_time_prefix]
                    );

                    $.each(split_time, function(time_name, time_value) {
                        this_popup.find('input[name="' + prefix + '_' + current_time_prefix + '_' + time_name + '"]').val(time_value);
                    });
                });
            },
            buttons: [
            {
                text: 'Apply',
                click: function() {
                    // CHECK IF VALID!
                    // ONLY PROCESS IF TRUE
                    if (dialog_box_values_valid($(this), prefix)) {
                        // Pass this popup to apply_values
                        apply_dialog_box_values($(this), prefix);
                    }
                }
            },
            {
                text: 'Cancel',
                click: function() {
                   $(this).dialog('close');
                }
            }]
        });
        current_dialog.removeProp('hidden');
    });

    // TODO NEEDS MAJOR REVISION
    function get_content_display(prefix, row_index, column_index, content, editable) {
        var html_contents = [];

        // Clone the empty_html for a starting point
        var new_display = empty_html[prefix].clone();

        // KILL EDIT FOR PREVIEW
        if (!editable)
        {
            new_display.find('.subform-delete').remove();
            new_display.find('.subform-edit').remove();
        }

        // Delete button
        if (editable) {
            new_display.find('.subform-delete').attr('data-prefix', prefix).attr('data-row', row_index).attr('data-column', column_index);
        }

        if (content && Object.keys(content).length) {
            if (editable) {
                // Hide 'edit' button
                html_contents.push(create_edit_button(prefix, row_index, column_index, true));
            }

            $.each(content, function(key, value) {
                // html_contents.push(key + ': ' + value);
                // I will need to think about invalid fields
                var field_name = key.replace('_id', '');
                if ((field_name !== 'addition_time' && field_name !== 'duration')) {
                    var field_display = window.GROUPS.get_display_for_field(field_name, value, prefix);
                    new_display.find('.' + prefix + '-' + field_name).html(field_display);
                }
                // NOTE THIS ONLY HAPPENS WHEN IT IS NEEDED IN ADD PAGE
                else {
                    var split_time = window.SPLIT_TIME.get_split_time(
                        value
                    );

                    $.each(split_time, function(time_name, time_value) {
                        new_display.find('.' + prefix + '-' + key + '_' + time_name).html(time_value);
                    });
                }
            });

            html_contents.push(new_display.html());
        }
        else {
            // Show 'edit' button
            html_contents.push(create_edit_button(prefix, row_index, column_index, false));
        }

        html_contents = html_contents.join('<br>');

        return html_contents;
    }

    // To discern how many columns are needed for the table display
    // Obviously, the largest number of columns found for any series
    let number_of_columns = {
        'cell': 0,
        'setting': 0,
    };

    // Table vars
    const study_setup_table = $('#study_setup_table');
    const study_setup_head = study_setup_table.find('thead').find('tr');
    const study_setup_body = study_setup_table.find('tbody');

    // MISNOMER, NOW MORE OF AN ADD BUTTON
    function create_edit_button(prefix, row_index, column_index, hidden) {
        // Sloppy
        if (hidden) {
            return '<a data-edit-button="true" data-row="' + row_index + '" data-prefix="' + prefix + '" data-column="' + column_index + '" role="button" class="btn btn-success collapse">Add</a>';
        }
        else {
            return '<a data-edit-button="true" data-row="' + row_index + '" data-prefix="' + prefix + '" data-column="' + column_index + '" role="button" class="btn btn-success">Add</a>';
        }
    }

    function create_delete_button(prefix, index) {
        if (prefix === 'row') {
            return '<a data-delete-row-button="true" data-row="' + index + '" role="button" class="btn btn-danger" style="margin-left: 5px;"><span class="glyphicon glyphicon-remove"></span></a>';
        }
        // NOTE UNFORTUNATE INLINE STYLE
        else {
            return '<a data-delete-column-button="true" data-column="' + index + '" data-prefix="' + prefix + '" role="button" class="btn btn-danger" style="margin-left: 5px;"><span class="glyphicon glyphicon-remove"></span></a>';
        }
    }

    // Swaps out the data we are saving to the form
    // TODO TODO TODO XXX REVISE TO USE ALL_DATA
    function replace_series_data() {
        series_data_selector.val(JSON.stringify(full_series_data));
    }

    // Modify the setup data for the given contents
    function modify_series_data(prefix, content, setup_index, object_index) {
        if (object_index) {
            series_data[setup_index][prefix][object_index] = $.extend(true, {}, content);
        }
        else {
            series_data[setup_index][prefix] = content;
        }

        replace_series_data();
    }

    function spawn_column(prefix) {
        var column_index = number_of_columns[prefix];
        // UGLY
        // Finds the correct place to put a new button
        study_setup_head.find('.' + prefix + '_start').last().after('<th class="new_column ' + prefix + '_start' + '">' + prefix[0].toUpperCase() + prefix.slice(1) + ' ' + (column_index + 1) + create_delete_button(prefix, column_index) +'</th>');

        // ADD TO EXISTING ROWS AS EMPTY
        study_setup_body.find('tr').each(function(row_index) {
            let offset_row_index = row_index + start_index;
            $(this).find('.' + prefix + '_start').last().after('<td class="' + prefix + '_start' + '">' + create_edit_button(prefix, offset_row_index, column_index) + '</td>', false);
        });

        // Increment columns for this prefix
        number_of_columns[prefix] += 1;
    }

    // We probably don't want cloning? Maybe. Not sure how it would work?
    function spawn_row(setup_to_use, add_new_row, is_clone, row_index) {
        // TODO: SHOULD REMOVE, WHOLE CONCEPT OF current_setup NEEDS TO BE REVISED
        if (!setup_to_use) {
            setup_to_use = {
                'cell': [],
                'setting': []
            };
        }

        var new_row = $('<tr>');

        new_row.attr('data-series', row_index + 1);

        // Make sure this works
        // Excess selectors, but shouldn't be a big deal
        let protocol_name = setup_to_use.name;

        if (!protocol_name) {
            protocol_name = $('#id_organmodelprotocol_set-' + row_index + '-name').val();

            // EXCESSIVE, BUT WORKS I THINK
            setup_to_use.name = protocol_name;

            new_row.append(
                $('<td>')
                    .addClass('text-success')
                    .text(protocol_name)
            );
        }
        // STILL WANT IT GREEN IN THIS CASE
        else if (!setup_to_use.id) {
            new_row.append(
                $('<td>')
                    .addClass('text-success')
                    .text(protocol_name)
            );
        }
        else {
            new_row.append(
                $('<td>').text(protocol_name)
            );
        }

        $.each(prefixes, function(index, prefix) {
            var content_set = setup_to_use[prefix];
            if (!content_set.length) {
                if (!number_of_columns[prefix]) {
                    new_row.append(
                        $('<td>')
                            .attr('hidden', 'hidden')
                            .addClass(prefix + '_start')
                    );
                }
                else {
                    for (var i=0; i < number_of_columns[prefix]; i++) {
                        new_row.append(
                            $('<td>')
                                .html(create_edit_button(prefix, row_index, i), false)
                                .addClass(prefix + '_start')
                        );
                    }
                }
            }
            else {
                while (number_of_columns[prefix] < content_set.length) {
                    spawn_column(prefix);
                }

                for (var i=0; i < number_of_columns[prefix]; i++) {
                    var html_contents = get_content_display(prefix, row_index, i, content_set[i], true);

                    new_row.append(
                        $('<td>')
                            .html(html_contents)
                            .addClass(prefix + '_start')
                    );
                }
            }
        });

        study_setup_body.append(new_row);

        if (add_new_row) {
            var new_series_data = $.extend(true, {}, setup_to_use);

            // GET RID OF THE GROUP ID WHEN THIS IS A NEW ROW
            if (is_clone) {
                delete new_series_data['id'];
            }

            series_data.push(
                new_series_data
            );
        }

        // Srikeout if delete
        // Can be done, just need to be careful!
        if (setup_to_use.deleted) {
            new_row.addClass('strikethrough');
        }
    }

    $(document).on('click', 'a[data-edit-button="true"]', function() {
        current_prefix = $(this).attr('data-prefix');
        current_row_index = $(this).attr('data-row');
        current_column_index = $(this).attr('data-column');
        $('#' + $(this).attr('data-prefix') + '_dialog').dialog('open');
    });

    $(document).on('click', 'a[data-delete-column-button="true"]', function() {
        current_prefix = $(this).attr('data-prefix');
        current_column_index = $(this).attr('data-column');

        // DELETE EVERY COLUMN FOR THIS PREFIX THEN REBUILD
        $.each(series_data, function(index, current_content) {
            current_content[current_prefix].splice(current_column_index, 1);
        });

        number_of_columns[current_prefix] -= 1;

        rebuild_table(true, current_page);
    });

    // NOT ALLOWED IN EDIT?
    $(document).on('click', 'a[data-clone-row-button="true"]', function() {
        current_row_index = Math.floor($(this).attr('data-row'));
        // SLOPPY
        spawn_row(series_data[current_row_index], true, true, series_data.length);

        // TODO TODO TODO
        // TODO LAZY

        // SKIP TO LAST PAGE
        let new_current_page = Math.ceil(series_data.length / display_length) - 1;

        rebuild_table(true, new_current_page);
    });

    // NOT ALLOWED IN EDIT?
    $(document).on('click', 'a[data-delete-row-button="true"]', function() {
        current_row_index = Math.floor($(this).attr('data-row'));

        // JUST FLAT OUT DELETE THE ROW
        // BUT WAIT! MAKE SURE THERE ISN'T A GROUP YET!
        // TODO TODO TODO: NOTE: BUT WAIT!!!! ONLY DO THIS IF IT DOESN'T ALREADY EXIST!
        // We would know this because it has an id (unless something goofy is happening)
        if (series_data[current_row_index].id === undefined) {
            // DELETE THE DATA HERE
            series_data.splice(current_row_index, 1);
        }
        else {
            // Can't strikethrough here, is overwritten after rebuild
            // Un-delete
            if (series_data[current_row_index].deleted) {
                delete series_data[current_row_index].deleted;
            }
            // Delete
            else {
                series_data[current_row_index].deleted = true;
            }
        }

        // If this is the last page and there is only one entry
        // TODO TODO TODO
        if (series_data[current_row_index] === undefined) {
            if (current_page > (Math.ceil((series_data.length) / display_length)) - 1) {
                pagination_previous_button_selector.first().trigger('click');
            }
        }

        rebuild_table(true, current_page);
    });

    $(document).on('click', '.subform-delete', function() {
        current_row_index = Math.floor($(this).attr('data-row'));
        current_column_index = Math.floor($(this).attr('data-column'));
        current_prefix = $(this).attr('data-prefix');

        // DELETE THE DATA HERE
        // TODO TODO TODO: NOTE: BUT WAIT!!!! ONLY DO THIS IF IT DOESN'T ALREADY EXIST!
        // We would know this because it has an id (unless something goofy is happening)
        if (series_data[current_row_index][current_prefix][current_column_index].id === undefined) {
            series_data[current_row_index][current_prefix][current_column_index] = {};
        }
        else {
            // TODO: STRIKEOUT!
        }

        rebuild_table(true, current_page);
    });

    $(document).on('click', '.subform-edit', function() {
        // Chaining parents this way is foolish
        $(this).parent().parent().parent().find('a[data-edit-button="true"]').trigger('click');
    });

    $('a[data-add-new-button="true"]').click(function() {
        spawn_column($(this).attr('data-prefix'));
    });

    $('#add_series_button').click(function() {
        // SLOPPY
        spawn_row(null, true, false, series_data.length);

        // SKIP TO LAST PAGE
        let new_current_page = Math.ceil(series_data.length / display_length) - 1;

        // TODO LAZY
        rebuild_table(true, new_current_page);
    });

    // SLOPPY: PLEASE REVISE
    // Triggers for hiding elements
    function change_table_visibility() {
        $('.visibility-checkbox').each(function() {
            var class_to_hide = $(this).attr('value') + ':not([hidden])';
            if ($(this).prop('checked')) {
                $(class_to_hide).show();
            }
            else {
                $(class_to_hide).hide();
            }
        });
    }

    $('.visibility-checkbox').change(change_table_visibility);
    change_table_visibility();

    // Show details
    function show_hide_full_details() {
        var current_value_show_details = $('#show_details').prop('checked');

        // Hide all contents of "bubbles"
        // Bad selector
        $.each(prefixes, function(prefix_index, prefix) {
            $('.' + prefix + '-display').children().hide();
        });

        // If checked, unhide all
        if (current_value_show_details) {
            // Bad selector
            $.each(prefixes, function(prefix_index, prefix) {
                $('.' + prefix + '-display').children().show();
            });
        }
        // Otherwise, just unhide the first line of the "bubble"
        else {
            $('.important-display').show();
        }

        change_table_visibility();
    }

    $('#show_details').change(show_hide_full_details);
    show_hide_full_details();

    // Crude, make the start index file scope
    let start_index = 0;

    function rebuild_table(data_change, new_current_page) {
        // GET RID OF ANYTHING IN THE TABLE
        study_setup_head.find('.new_column').remove();
        study_setup_body.empty();

        number_of_columns = {
            'cell': 0,
            // 'compound': 0,
            'setting': 0,
        };

        let page_change = false;
        if (new_current_page !== current_page) {
            page_change = true;
        }

        current_page = new_current_page;

        if (series_data.length) {
            start_index = current_page * display_length;
            for (let index=0; index < display_length; index++) {
                let row_index = index + start_index;
                if (series_data[start_index + index]) {
                    spawn_row(series_data[start_index + index], false, false, row_index);
                }
            }
        }
        else {
            spawn_row(null, true, false, 0);
        }

        if (data_change) {
            replace_series_data();
        }
        // SLOPPY: If this is just a pagination, snap to the top
        if (page_change) {
            $('html, body').animate({
                scrollTop: $('#study_setup_table').offset().top - 175
            }, 500);
        }

        // MAKE SURE HIDDEN COLUMNS ARE ADHERED TO
        change_table_visibility();

        // Change the paginator text etc.
        revise_paginator_text();

        // Show errors if necessary
        if (Object.keys(table_errors).length) {
            $.each(table_errors, function(current_id, error) {
                var split_info = current_id.split('|');
                var prefix = split_info[0];
                var row_index = split_info[1];
                var column_index = split_info[2];
                var field = split_info[3];

                let current_errors_section = null;

                // Special exception for groups
                // Not really used as of yet
                if (prefix === 'group') {
                    current_errors_section = $('tr[data-series="' + (parseInt(row_index)+1) + '"]').find('.error-message-section').first();
                }
                else {
                    current_errors_section = $('.subform-delete[data-prefix="' + prefix +'"][data-row="' + row_index + '"][data-column="' + column_index + '"]').parent().parent().find('.error-message-section');
                }

                current_errors_section.append(empty_error_html.clone().text(field + ': ' + error));
            });
        }

        // Also remake the difference table
        // TODO: ONLY DO THIS IF IT IS NECESSARY!
        // IE this isn't just a page change
        if (data_change) {
            window.GROUPS.make_difference_table();
        }
    }

    // TESTING
    rebuild_table(true, current_page);

    // SPECIAL TRIGGERS FOR PROTOCOLS
    // PLEASE NOTE: regex selectors are not efficient
    // This selector is for all protocol names
    $(document).on('change', 'textarea[id$=-name]', function() {
        // If we need to change the page (null otherwise)
        let new_current_page = current_page;

        // Iterate over all the protocol names
        $('textarea[id$=-name]').each(function(index) {
            // If there is a name, check if there is a corresponding row in the edit table and change it
            if ($(this).val() && study_setup_body.find('tr').eq(index)[0]) {
                // Sloppy
                modify_series_data('name', $(this).val(), index);
            }
            // If there is not a name, add a new protocol
            else if ($(this).val()) {
                // SLOPPY
                spawn_row(null, true, false, series_data.length);
                // MAKE SURE HIDDEN COLUMNS ARE ADHERED TO
                // change_table_visibility();

                // SKIP TO LAST PAGE
                new_current_page = Math.ceil(series_data.length / display_length) - 1;
            }
        });

        // TODO LAZY
        rebuild_table(true, new_current_page);
    });

    // REVISE
    // TODO: We also would want a trigger to get rid of deleted protocols
    // TERRIBLE SELECTOR
    $(document).on('click', 'input[name^="organmodelprotocol_set-"][name$="-DELETE"]', function() {
        // Crude way to get the index
        let current_row_index = parseInt($(this).attr('name').split('-')[1]);

        // Only kill entries without ids
        if (series_data[current_row_index].id === undefined) {
            // DELETE THE DATA HERE
            series_data.splice(current_row_index, 1);
        }

        // If this is the last page and there is only one entry
        if (series_data[current_row_index] === undefined) {
            if (current_page > (Math.ceil((series_data.length) / display_length)) - 1) {
                pagination_previous_button_selector.first().trigger('click');
            }
        }

        rebuild_table(true, current_page);
    });
});
