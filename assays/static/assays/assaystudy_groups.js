// TODO WE ARE NOW CALLING THEM GROUPS AGAIN, I GUESS
// TODO: WHY ARE WE GOING BACK AND FORTH BETWEEN INT AND STING FOR INDICES???????
// A SERIOUS STYLISTIC DEFICIENCY IS THAT FILE SCOPE VARIABLES ARE NOT CLEARLY INDICATED, THE LIKELIHOOD OF COLLISIONS ARE THEREFORE QUITE HIGH
$(document).ready(function () {
    // TEMPORARY
    var series_data_selector = $('#id_series_data');

    // FULL DATA
    // TEMPORARY
    var full_series_data = JSON.parse(series_data_selector.val());

    if (series_data_selector.val() === '{}') {
        full_series_data = {
            series_data: [],
            // Plates is an array, kind of ugly, but for the moment one has to search for the current plate on the plate page
            plates: {},
            // The ID needs to be in individual chip objects, they don't exist initially (unlike plates!)
            chips: []
        };
    }

    // TODO WE NEED TO SPLIT OUT MATRIX ITEM DATA
    var chips = full_series_data.chips;

    // SERIES DATA
    var series_data = full_series_data.series_data;
    // var matrix_item_data = full_series_data.matrix_item_data;

    // ERRORS
    var setup_table_errors_selector = $('#setup_table_errors').find('.errorlist');

    var table_errors = {};

    setup_table_errors_selector.find('li').each(function() {
        var current_text = $(this).text();
        var split_info = current_text.split('-')[0];
        var error_message = current_text.split('-').slice(1).join('-');
        table_errors[split_info] = error_message;
    });

    // ODD, NOT GOOD
    var organ_model = $('#id_organ_model');
    var protocol = $('#id_organ_model_protocol');

    var organ_model_full = $('#id_organ_model_full');
    var organ_model_protocol_full = $('#id_organ_model_protocol_full');

    // var current_protocol = protocol.val();

    window.organ_model = organ_model;
    window.organ_model_protocol = protocol;

    // CRUDE AND BAD
    // If I am going to use these, they should be ALL CAPS to indicate global status
    var item_prefix = 'matrix_item';
    var cell_prefix = 'cell';
    var setting_prefix = 'setting';
    var compound_prefix = 'compound';

    // The different components of a setup
    var prefixes = [
        'cell',
        'compound',
        'setting',
    ];

    var time_prefixes = [
        'addition_time',
        'duration'
    ];

    // DATA FOR THE VERSION
    var current_setup = {};

    // CRUDE
    // MAKE SURE ALL PREFIXES ARE PRESENT
    $.each(prefixes, function(index, prefix) {
        if (!current_setup[prefix]) {
          current_setup[prefix] = [];
        }
    });

    // SOMEWHAT TASTELESS USE OF VARIABLES TO TRACK WHAT IS BEING EDITED
    var current_prefix = '';
    var current_setup_index = 0;
    var current_row_index = null;
    var current_column_index = null;

    // DISPLAYS
    // JS ACCEPTS STRING LITERALS IN OBJECT INITIALIZATION
    var empty_html = {};
    var empty_item_html = $('#empty_matrix_item_html').children();
    var empty_compound_html = $('#empty_compound_html');
    var empty_cell_html = $('#empty_cell_html');
    var empty_setting_html = $('#empty_setting_html');
    var empty_error_html = $('#empty_error_html').children();
    empty_html[item_prefix] = empty_item_html;
    empty_html[compound_prefix] = empty_compound_html;
    empty_html[cell_prefix] = empty_cell_html;
    empty_html[setting_prefix] = empty_setting_html;

    // Specific to compounds, this checkbox will indicate whether to use the increment
    // var use_compound_concentration_increment = $('#id_use_compound_concentration_increment');
    // var compound_compound_increment = $('#id_compound_compound_increment');
    // var compound_compound_increment_type = $('#id_compound_compound_increment_type');
    // var compound_concentration_increment_direction = $('#id_compound_concentration_increment_direction');

    // var selection_dialog_selected_items = $('#selection_dialog_selected_items');
    // var series_selector = $('#id_series_selector');
    // var selection_dialog_naming_section = $('.selection_dialog_naming_section');
    // var use_chip_naming = $('#id_use_incremental_well_naming');
    // var chip_naming = $('#id_incremental_well_naming');

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
            // current_page -= 1;
            rebuild_table(false, current_page - 1);
        }
    });

    pagination_next_button_selector.click(function() {
        if (!$(this).hasClass('disabled') && current_page < number_of_pages) {
            // current_page += 1;
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

            // CRUDE: DO NOT INCLUDE MATRIX ITEM
            if (current_name === 'matrix_item') {
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

    // Resets the data for the current_setup
    function reset_current_setup(reset_data) {
        current_setup = {};

        // MAKE SURE ALL PREFIXES ARE PRESENT
        $.each(prefixes, function(index, prefix) {
            if(!current_setup[prefix]) {
              current_setup[prefix] = [];
            }
        });

        if (reset_data) {
            series_data = [];
        }
    }

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
    var number_of_columns = {
        'cell': 0,
        'compound': 0,
        'setting': 0,
    };

    // Table vars
    var study_setup_table = $('#study_setup_table');
    var study_setup_head = study_setup_table.find('thead').find('tr');
    var study_setup_body = study_setup_table.find('tbody');

    // Not a very clear name: refers to table shown for MPS Model Versions
    // PREVIEW
    var series_table_preview = $('#series_table_preview');

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

    function create_clone_button(index) {
        // Change clone button to read "Copy"
        // return '<a data-clone-row-button="true" data-row="' + index + '" role="button" class="btn btn-info"><span class="glyphicon glyphicon-duplicate"></span></a>';
        return '<a data-clone-row-button="true" data-row="' + index + '" role="button" class="btn btn-info">Copy</a>';
    }

    // Swaps out the data we are saving to the form
    // TODO TODO TODO XXX REVISE TO USE ALL_DATA
    function replace_series_data() {
        series_data_selector.val(JSON.stringify(full_series_data));
    }

    // TODO REVISE FOR TRUE ID
    // NOTE: Interestingly, the way add works right now, one will NEVER be able to "add back" a group they inadvertently deleted
    // Is this a problem?
    // Obviously it would be an issue if there was data, someone (for whatever reason) decreased the item number, increased it again, and then saved. How often would this occur? It is difficult to say.
    function add_chip(setup_index) {
        chips.push({
            'name': chips.length + 1,
            'group_index': Math.floor(setup_index)
        });
    }

    // TODO REVISE FOR TRUE ID
    // TODO BE CAREFUL HERE
    function remove_chip(setup_index) {
        $.each(chips, function(index, chip) {
            // NOTE: group_index is just an index for the moment
            // We also need access to the id, ideally
            // TODO TODO TODO SHOULD BE MORE CAREFUL ABOUT STRING TO INTEGER COMPARISONS
            if (chip.group_index == setup_index) {
                // If the chip exists, we need to mark it for deletion
                if (chip.id && !chip.deleted) {
                    full_series_data['chips'][index]['deleted'] = true;
                    // Break after removal
                    return false;
                }
                // If the chip doesn't exist yet, just kill it
                else if (!chip.id) {
                    chips.splice(index, 1);
                    // Break after removal
                    return false;
                }
            }
        });
    }

    function modify_chip_data(number_of_chips, setup_index) {
        var current_number_of_chips = 0;

        $.each(chips, function(index, chip) {
            // NOTE: group_index is just an index for the moment
            // We also need access to the id, ideally
            // NOTE: DO NOT COUNT DELETED CHIPS
            if (chip.group_index == setup_index && !chip.deleted) {
                current_number_of_chips += 1;
            }
        });

        while (current_number_of_chips > number_of_chips) {
            remove_chip(setup_index);
            current_number_of_chips -= 1;
        }

        while (current_number_of_chips < number_of_chips) {
            add_chip(setup_index);
            current_number_of_chips += 1;
        }

        replace_series_data();
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

    // JUST USES DEFAULT PROTOCOL FOR NOW
    function spawn_row(setup_to_use, add_new_row, is_clone, row_index) {
        // TODO: SHOULD REMOVE, WHOLE CONCEPT OF current_setup NEEDS TO BE REVISED
        if (!setup_to_use) {
            setup_to_use = {
                'cell': [],
                'compound': [],
                'setting': []
            };
        }

        var new_row = $('<tr>');

        // NOPE! NEED TO PASS THE INDEX!
        // var row_index = study_setup_body.find('tr').length;

        new_row.attr('data-series', row_index + 1);

        var buttons_to_add = '';
        buttons_to_add = create_clone_button(row_index) + create_delete_button('row', row_index);
        new_row.append(
            $('<td>').html(
                '<div class="no-wrap">' + buttons_to_add + '</div>'
            ).append(
                $('<strong>').text('Group ' + (row_index + 1))
            )
        );

        // SLOPPY, BAD
        // var new_td = $('<td>').html(
        //     '<div class="error-message-section error-display important-display"></div>'
        // );

        // new_row.append(
        //     new_td
        // );

        // Let's just have text instead, saves space among other things
        // SLOPPY
        // var organ_model_input = $('#id_organ_model_full')
        //     .clone()
        //     .removeAttr('id')
        //     .attr('name', 'organ_model')
        //     .attr('data-row', row_index)
        //     .addClass('organ-model');

        // SLOPPY
        // organ_model_input.attr('required', 'required');

        var organ_model_input = $('<div>')
            .append($('<div>')
                .attr('data-row', row_index)
                .addClass('organ-model')
            ).append($('<div>')
                .attr('data-row', row_index)
                .addClass('organ-model-protocol')
            )

        new_row.append(
            $('<td>').append(
                // CRUDE!
                $('<div>').addClass('error-message-section error-display important-display')
            ).append(organ_model_input).append(
                $('<div>')
                .append(
                    $('<span>').addClass(
                        'btn btn-primary btn-block glyphicon glyphicon-search query-versions'
                    ).attr(
                        'data-row-index', row_index
                    )
                )
            )
        );

        var type_display = $('<div>')
            .attr('data-row', row_index);

        if (setup_to_use['device_type']) {
            type_display.html(
                setup_to_use['device_type'][0].toUpperCase() + setup_to_use['device_type'].substr(1).toLowerCase()
            );
        }

        new_row.append(
            $('<td>').append(type_display)
        );

        var name_input = $('#id_group_name')
            .clone()
            .removeAttr('id')
            .addClass('group-name required')
            .attr('data-row', row_index);

        // SLOPPY: MAKE REQUIRED FOR NOW
        name_input.attr('required', 'required')

        new_row.append(
            $('<td>').append(name_input)
        );

        // organ_model_input.selectize();

        // TODO: ONLY SHOW FOR CHIPS
        // TODO: MAKE FUNCTIONAL
        var number_of_items_input = $('#id_number_of_items')
                .clone()
                .removeAttr('id')
                .addClass('number-of-items required')
                .attr('data-row', row_index);

        // SLOPPY: MAKE REQUIRED FOR NOW
        number_of_items_input.attr('required', 'required')

        new_row.append(
            $('<td>').append(number_of_items_input)
        );

        // SLOPPY
        var test_type_input = $('#id_test_type')
            .clone()
            .removeAttr('id')
            .attr('data-row', row_index)
            .addClass('test-type')
            // Contrived: prevent from getting smashed
            .css('min-width', 100);

        // SLOPPY
        test_type_input.attr('required', 'required');

        new_row.append(
            $('<td>').append(test_type_input)
        );

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

        // new_row.find('.organ-model')[0].selectize.setValue(setup_to_use['organ_model_id']);

        // Set the organ model and protocol
        // IF NO ORGAN MODEL: ASK FOR ONE!
        if (!setup_to_use['organ_model_id']) {
            new_row.find('.organ-model')
            .text(
                'Please click the magnifying glass to select an MPS Model'
            ).addClass(
                'text-danger'
            );
        }
        else {
            new_row.find('.organ-model').text(
                organ_model_full.find('option[value="' + setup_to_use['organ_model_id'] + '"]').text()
            ).removeClass(
                'text-danger'
            );
            if (setup_to_use['organ_model_protocol_id']) {
                new_row.find('.organ-model-protocol').text(
                    'Version: ' +
                    organ_model_protocol_full.find('option[value="' + setup_to_use['organ_model_protocol_id'] + '"]').text()
                );
            }
        }

        if (setup_to_use['device_type'] === 'plate') {
            new_row.find('.number-of-items')
                .val(0)
                .attr('disabled', 'disabled')
                .attr('title', 'Apply to Wells in the Plate Tab')
        }
        else {
            new_row.find('.number-of-items')
                .val(setup_to_use['number_of_items'])
                .removeAttr('disabled');
        }

        new_row.find('.group-name').val(setup_to_use['name']);
        new_row.find('.test-type').val(setup_to_use['test_type']);

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

            // Crude way to make sure the chips get generated
            new_row.find('.number-of-items').trigger('change');
        }
        else if (setup_to_use['device_type'] === 'plate') {
            new_row.find('.number-of-items').trigger('change');
        }

        // Srikeout if delete
        if (setup_to_use.deleted) {
            new_row.addClass('strikethrough');
        }

        // NO! CAN'T DO THIS! TOO EXPENSIVE!
        // replace_series_data();

        // Add group to selectors
        // series_selector.append(new Option('Group ' + (row_index + 1), row_index + 1));
    }

    $(document).on('change', '.test-type', function() {
        // CRUDE SOLUTION FOR IDIOSYNCRATIC BEHAVIOR: INVESTIGATE ASAP
        $('option[value="' + this.value + '"]', this)
            .attr('selected', true).siblings()
            .removeAttr('selected')
        modify_series_data('test_type', $(this).val(), $(this).attr('data-row'));

        // Overkill
        // rebuild_table();
        window.GROUPS.make_difference_table();
    });

    $(document).on('change', '.number-of-items', function() {
        modify_series_data('number_of_items', $(this).val(), $(this).attr('data-row'));

        modify_chip_data($(this).val(), $(this).attr('data-row'));

        // Overkill
        // rebuild_table();
        window.GROUPS.make_difference_table();
    });

    $(document).on('change', '.group-name', function() {
        modify_series_data('name', $(this).val(), $(this).attr('data-row'));

        // Overkill
        // rebuild_table();
        window.GROUPS.make_difference_table();
    });

    // $(document).on('change', '.organ-model', function() {
    //     modify_series_data('organ_model_id', $(this).val(), $(this).attr('data-row'));
    // });

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

        // MAKE SURE HIDDEN COLUMNS ARE ADHERED TO
        // change_table_visibility();

        // TODO TODO TODO
        // TODO LAZY

        // SKIP TO LAST PAGE
        let new_current_page = Math.ceil(series_data.length / display_length) - 1;

        rebuild_table(true, new_current_page);
    });

    // NOT ALLOWED IN EDIT?
    $(document).on('click', 'a[data-delete-row-button="true"]', function() {
        current_row_index = Math.floor($(this).attr('data-row'));

        // A somewhat odd way to kill the chips
        // Set the number of items to zero and trigger it
        // We *PROBABLY* can get away with this
        // Cascade will kill chips when it gets deleted anyway

        // Well, we don't really want this, it is hard to undo...
        // $('.number-of-items[data-row="' + $(this).attr('data-row') + '"]').val(0).trigger('change');

        // TODO: WE NEED TO DEAL WITH THE CONSEQUENCES OF DELETION!
        // Iterate over matrix_item and reset the current series
        // var all_keys = Object.keys(matrix_item_data);
        // $.each(all_keys, function(index, item_row_column) {
        //     var contents = matrix_item_data[item_row_column];
        //     // Delete if this is associated with the series to be removed
        //     if (contents.series - 1 === current_row_index) {
        //         delete matrix_item_data[item_row_column];

        //         // Unset the label
        //         unset_label($(item_display_class + '[data-row-column="' + item_row_column + '"]'));
        //     }
        //     // Decrement if this comes after the series to be removed
        //     else if (contents.series - 1 > current_row_index) {
        //         contents.series = contents.series - 1;

        //         // Reset the label
        //         set_label($(item_display_class + '[data-row-column="' + item_row_column + '"]'), contents.series);
        //     }
        // });

        // JUST FLAT OUT DELETE THE ROW
        // BUT WAIT! MAKE SURE THERE ISN'T A GROUP YET!
        // TODO TODO TODO: NOTE: BUT WAIT!!!! ONLY DO THIS IF IT DOESN'T ALREADY EXIST!
        // We would know this because it has an id (unless something goofy is happening)
        if (series_data[current_row_index].id === undefined) {
            // DELETE THE DATA HERE
            series_data.splice(current_row_index, 1);
        }
        else {
            // TODO STRIKE IT OUT!
            // Uh, why use data-series as index + 1?
            var current_row = $('tr[data-series="' + (current_row_index + 1) + '"]');

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
        // MAKE SURE HIDDEN COLUMNS ARE ADHERED TO
        // change_table_visibility();

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

    function get_device_type(is_new) {
        if (organ_model.val()) {
            // Get the organ_model type
            // Start SPINNING
            window.spinner.spin(
                document.getElementById("spinner")
            );
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_organ_model_type',
                    organ_model_id: organ_model.val(),
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                },
                success: function (json) {
                    // Stop spinner
                    window.spinner.stop();

                    series_data[current_setup_index]['device_type'] = json;

                    get_protocol(is_new);
                },
                error: function (xhr, errmsg, err) {
                    // Stop spinner
                    window.spinner.stop();

                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
        else {
            get_protocol(is_new);
        }
    }

    function get_protocol(is_new) {
        if (is_new) {
            // Set organ_model_id
            series_data[current_setup_index]['organ_model_id'] = organ_model.val();
            series_data[current_setup_index]['organ_model_protocol_id'] = protocol.val();
        }

        // if (protocol.val() && protocol.val() != current_protocol || protocol.val() && !Object.keys(current_setup).length) {
        if (protocol.val()) {
            // Start SPINNING
            window.spinner.spin(
                document.getElementById("spinner")
            );

            // Swap to new protocol
            // current_protocol = protocol.val();

            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_organ_model_protocol_setup',
                    organ_model_protocol_id: protocol.val(),
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                },
                success: function (json) {
                    // Stop spinner
                    window.spinner.stop();

                    // series_data[current_setup_index] = $.extend(true, {}, json);

                    if (is_new) {
                        // MAKE SURE ALL PREFIXES ARE PRESENT
                        $.each(prefixes, function(index, prefix) {
                            if (json[prefix]) {
                                // Slow, but rare operation
                                series_data[current_setup_index][prefix] = JSON.parse(JSON.stringify(json[prefix]));
                            }
                        });

                        // FORCE INITIAL TO BE CONTROL
                        // series_data[current_setup_index]['test_type'] = 'control';

                        // console.log(series_data);

                        rebuild_table(true, current_page);
                    }
                    // Contrived make preview
                    else {
                        series_table_preview.empty();
                        var new_row = $('<tr>');

                        $.each(json, function(prefix, content_set) {
                            for (var i=0; i < content_set.length; i++) {
                                var html_contents = get_content_display(prefix, 0, i, content_set[i], false);

                                new_row.append(
                                    $('<td>')
                                        .html(html_contents)
                                );
                            }
                        });

                        series_table_preview.append(new_row);
                    }
                },
                error: function (xhr, errmsg, err) {
                    // Stop spinner
                    window.spinner.stop();

                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
        else if (!protocol.val()) {
            if (is_new) {
                reset_current_setup();
                rebuild_table(true, current_page);
            }
            else {
                series_table_preview.empty();
            }
        }
    }

    function set_new_protocol(is_new) {
        get_device_type(is_new);
    }

    // Crude, make the start index file scope
    let start_index = 0;

    function rebuild_table(data_change, new_current_page) {
        // GET RID OF ANYTHING IN THE TABLE
        study_setup_head.find('.new_column').remove();
        study_setup_body.empty();

        number_of_columns = {
            'cell': 0,
            'compound': 0,
            'setting': 0,
        };

        let page_change = false;
        if (new_current_page !== current_page) {
            page_change = true;
        }

        current_page = new_current_page;

        // console.log(series_data);
        // console.log('REBUILD', 'PAGE: ', current_page, 'START: ', current_page * display_length, 'DATA CHANGE: ', data_change);

        if (series_data.length) {
            // $.each(series_data, function(index, content) {
            //     spawn_row(content, false);
            // });
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

    var version_dialog = $('#version_dialog');
    version_dialog.dialog({
        width: 900,
        height: 500,
        open: function() {
            $.ui.dialog.prototype.options.open();

            // Set the organ model and organ model protocol to current
            if (current_setup['organ_model_id']) {
                organ_model[0].selectize.setValue(current_setup['organ_model_id']);
                organ_model.trigger('change');

                // RACE CONDITION (need to wait until dropdown is populated)
                // NOTE: Not how one should handle race conditions (TODO REVISE)
                setTimeout(function() {
                    if (current_setup['organ_model_protocol_id']) {
                        protocol[0].selectize.setValue(current_setup['organ_model_protocol_id']);
                        protocol.trigger('change');
                    }
                }, 150);
            }
            else {
                organ_model[0].selectize.setValue('');
                organ_model.trigger('change');
            }

            // BAD
            setTimeout(function() {
                // Blur all
                $('.ui-dialog').find('input, select, button').blur();
            }, 150);
        },
        buttons: [
        {
            text: 'Apply',
            click: function() {
                // Get the version data and apply to row
                set_new_protocol(true);

                $(this).dialog('close');
            }
        },
        {
            text: 'Cancel',
            click: function() {
               $(this).dialog('close');
            }
        }]
    });
    version_dialog.removeProp('hidden');

    $(document).on('click', '.query-versions', function() {
        current_setup_index = $(this).attr('data-row-index');
        current_setup = series_data[current_setup_index];
        version_dialog.dialog('open');
    });

    // Handling Device flow
    // Make sure global var exists before continuing
    if (window.get_organ_models) {
        organ_model.change(function() {
            // Get and display correct protocol options
            // Asynchronous
            window.get_protocols(organ_model.val());
        }).trigger('change');

        protocol.change(function() {
            set_new_protocol(false);
        });
    }
});
