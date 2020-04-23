$(document).ready(function () {
    var plate_id = Math.floor(window.location.href.split('/')[5]);

    // Crude differentiation for new plates
    if (window.location.href.split('/')[4] === 'assaystudy') {
        plate_id = '';
    }

    // TEMPORARY ->
    var series_data_selector = $('#id_series_data');
    // TEMPORARY
    // FULL DATA

    console.log(series_data_selector.val());

    var full_series_data = JSON.parse(series_data_selector.val());

    if (series_data_selector.val() === '{}') {
        full_series_data = {
            series_data: [],
            // Plates is an array, kind of ugly, but for the moment one has to search for the current plate on the plate page
            // On the other hand, might we not have another "fake schema" contrivance for matrices?
            plates: [],
            // The ID needs to be in individual chip objects, they don't exist initially (unlike plates!)
            chips: []
        };
    }

    // SERIES DATA
    var series_data = full_series_data.series_data;

    // TODO: USE THIS CONTRIVED FIELD FOR PLATES FOR NOW?
    // var matrix_item_data = full_series_data.matrix_item_data;
    // var matrix_item_data = $('#id_matrix_item_data').val();

    var matrix_item_data = null;

    console.log(plate_id);
    // Try to get the plate
    $.each(full_series_data.plates, function(index, plate) {
        if (plate.id === plate_id) {
            matrix_item_data = full_series_data.plates[index];
        }
    });
    if (!matrix_item_data) {
        full_series_data.plates.push({id: ''});
        console.log(full_series_data);
        matrix_item_data = full_series_data.plates[full_series_data.plates.length-1];
    }

    // TEMPORARY ACQUISITION OF GROUPS
    // THIS NEEDS TO BE REPLACED ASAP
    $.each(series_data, function(index) {
        var new_option = null;
        if (series_data[index].device_type === 'plate') {
            if (series_data[index].name) {
                new_option = new Option(series_data[index].name, index + 1)
            }
            else {
                new_option = new Option('Group ' + (index + 1), index + 1)
            }
            $('#id_series_selector').append(
                new_option
            );
        }
    });

    // <- END TEMPORARY

    // CRUDE AND BAD
    // If I am going to use these, they should be ALL CAPS to indicate global status
    // NOT DRY
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

    // Alias for the matrix selector
    var matrix_table_selector = $('#matrix_table');
    var matrix_body_selector = $('#matrix_body');

    // Alias for device selector
    var device_selector = $('#id_device');
    // Alias for representation selector
    // var representation_selector = $('#id_representation');
    // Alias for number of rows/columns
    // These probably are not going to be used
    // (We will just select a Device)
    var number_of_items_selector = $('#id_number_of_items');
    var number_of_rows_selector = $('#id_number_of_rows');
    var number_of_columns_selector = $('#id_number_of_columns');

    var selection_dialog_selected_items = $('#selection_dialog_selected_items');
    var series_selector = $('#id_series_selector');
    // var selection_dialog_naming_section = $('.selection_dialog_naming_section');
    // var use_chip_naming = $('#id_use_chip_naming');
    // var chip_naming = $('#id_chip_naming');

    var item_display_class = '.matrix_item-td';

    var current_selection = null;

    // To see if a selection is occurring
    var user_is_selecting = false;

    function start_selection() {
        user_is_selecting = true;
    }

    // Allows the matrix_table to have the draggable JQuery UI element
    matrix_table_selector.selectable({
        // SUBJECT TO CHANGE: WARNING!
        filter: 'td' + item_display_class,
        distance: 1,
        // Stop selection when over a th
        cancel: 'th',
        start: start_selection,
        stop: matrix_add_content_to_selected
    });

    // This function turns numbers into letters
    // Very convenient for handling things like moving from "Z" to "AA" automatically
    // Though, admittedly, the case of so many rows is somewhat unlikely
    function to_letters(num) {
        "use strict";
        var mod = num % 26,
            pow = num / 26 | 0,
            out = mod ? String.fromCharCode(64 + mod) : (--pow, 'Z');
        return pow ? to_letters(pow) + out : out;
    }

    // Decided by an checkbox option?
    // function plate_style_name_creation(append_zero) {
    //     var current_global_name = $('#id_matrix_item_name').val();
    //     var current_number_of_rows = number_of_rows_selector.val();
    //     var current_number_of_columns = number_of_columns_selector.val();

    //     var largest_row_name_length = Math.pow(current_number_of_columns, 1/10);

    //     for (var row_id=0; row_id < current_number_of_rows; row_id++) {
    //         // Please note + 1
    //         var row_name = to_letters(row_id + 1);

    //         for (var column_id=0; column_id < current_number_of_columns; column_id++) {
    //             var current_item_id = item_prefix + '_' + row_id + '_' + column_id;

    //             var column_name = column_id + 1 + '';
    //             if (append_zero) {
    //                 while (column_name.length < largest_row_name_length) {
    //                     column_name = '0' + column_name;
    //                 }
    //             }

    //             var value = current_global_name + row_name + column_name;

    //             // TODO TODO TODO PERFORM THE ACTUAL APPLICATION TO THE FORMS
    //             // TODO TODO TODO PERFORM THE ACTUAL APPLICATION TO THE FORMS
    //             // Set display
    //             var item_display = $('#'+ current_item_id);
    //             item_display.find('.matrix_item-name').html(value);
    //             // Set form
    //             $('#id_' + item_prefix + '-' + item_display.attr(item_form_index_attribute) + '-name').val(value);
    //         }
    //     }
    // }

    // This function gets the initial dimensions of the matrix
    // Please see the corresponding AJAX call as necessary
    // TODO PLEASE ADD CHECKS TO SEE IF EXISTING DATA FALLS OUTSIDE NEW BOUNDS
    // TODO PLEASE NOTE THAT THIS GETS RUN A MILLION TIMES DO TO HOW TRIGGERS ARE SET UP
    // TODO MAKE A VARIABLE TO SEE WHETHER DATA WAS ALREADY ACQUIRED
    var get_matrix_dimensions = function() {
        var current_device = device_selector.val();

        var current_number_of_rows = number_of_rows_selector.val();
        var current_number_of_columns = number_of_columns_selector.val();

        if (current_device) {
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_device_dimensions',
                    // The device may be needed to specify the dimensions
                    device_id: current_device,
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                success: function (json) {
                    number_of_rows_selector.val(json.number_of_rows);
                    number_of_columns_selector.val(json.number_of_columns);
                    build_matrix(
                        json.number_of_rows,
                        json.number_of_columns
                    );
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }

        if (current_number_of_rows > 200) {
            alert('Number of rows exceeds limit.');
            number_of_rows_selector.val(200);
            current_number_of_rows = 200;
        }

        if (current_number_of_columns > 200) {
            alert('Number of columns exceeds limit.');
            current_number_of_columns.val(200);
            current_number_of_columns = 200;
        }

        if (!current_device && current_number_of_rows && current_number_of_columns) {
            build_matrix(
                current_number_of_rows,
                current_number_of_columns
            );

            // initial_number_of_rows = current_number_of_rows;
            // initial_number_of_columns = current_number_of_columns;
        }

        // Set number of items if not already set
        if (number_of_items_selector.val() !== current_number_of_rows * current_number_of_columns) {
            number_of_items_selector.val(current_number_of_rows * current_number_of_columns);
        }
    };

    // To highlight and un-highlight rows/columns
    function highlight_row() {
        $('#row_' + $(this).attr('data-row-to-apply')).find('td').addClass('bg-warning');
    }

    function un_highlight_row() {
        $('#row_' + $(this).attr('data-row-to-apply')).find('td').removeClass('bg-warning');
    }

    function highlight_column() {
        $('td[data-column-index="' + $(this).attr('data-column-to-apply') + '"]').addClass('bg-warning');
    }

    function un_highlight_column() {
        $('td[data-column-index="' + $(this).attr('data-column-to-apply') + '"]').removeClass('bg-warning');
    }

    // Set label for selection (the label is just the current group)
    function set_label(current_label, group) {
        current_label.find('.matrix-item-hover')
            .removeClass('label-warning')
            .addClass('label-primary')
            .text(group);
    }

    function unset_label(current_label) {
        current_label.find('.matrix-item-hover')
            .removeClass('label-primary')
            .addClass('label-warning')
            .text('X');

        // Removes the name of the chip as well
        current_label.find('.matrix_item-name').text('');
    }

    // Makes the initial matrix
    // TODO PURGE CELLS WHEN SHRINKING
    function build_matrix(number_of_rows, number_of_columns) {
        matrix_body_selector.empty();

        // ONLY DISPLAY APPLY ROW/COLUMN BUTTONS IF THIS IS ADD/UPDATE
        var starting_index_for_matrix = $('#floating-submit-row')[0] ? -1 : 0;

        // Check to see if new forms will be generated
        for (var row_index=starting_index_for_matrix; row_index < number_of_rows; row_index++) {
            var row_id = 'row_' + row_index;
            var current_row = $('<tr>')
                .attr('id', row_id);

            for (var column_index=starting_index_for_matrix; column_index < number_of_columns; column_index++) {
                var item_id = item_prefix + '_' + row_index + '_' + column_index;
                var new_cell = null;

                // If this is an apply to row
                if (column_index === -1) {
                    if (row_index === -1) {
                        new_cell = $('<th>')
                            .css('width', '1px')
                            .css('white-space', 'no-wrap')
                    }
                    else {
                        new_cell = $('<th>')
                            .addClass('text-center')
                            // Note: CRUDE
                            .css('vertical-align', 'middle')
                            .css('width', '1px')
                            .css('white-space', 'no-wrap')
                            .append(
                                $('<a>')
                                    .html(to_letters(row_index + 1))
                                    .attr('data-row-to-apply', row_index)
                                    .addClass('btn btn-sm btn-primary')
                                    .click(apply_action_to_row)
                                    .mouseover(highlight_row)
                                    .mouseout(un_highlight_row)
                            );
                    }
                }
                // If this is an apply to column
                else if (row_index === -1) {
                    new_cell = $('<th>')
                        .addClass('text-center')
                        .attr('data-column-index', column_index)
                        .append(
                            $('<a>')
                                .html(column_index + 1)
                                .attr('data-column-to-apply', column_index)
                                .addClass('btn btn-sm btn-primary')
                                .click(apply_action_to_column)
                                .mouseover(highlight_column)
                                .mouseout(un_highlight_column)
                        );
                }
                // If this is for actual contents
                else {
                    var current_name = to_letters(row_index + 1) +(column_index + 1);
                    var row_column = row_index + '_' + column_index;
                    new_cell = empty_item_html
                        .clone()
                        .attr('id', item_id)
                        .attr('data-row-index', row_index)
                        .attr('data-column-index', column_index)
                        .attr('data-row-column', row_column)
                        .attr('data-well-name', current_name);

                    if (matrix_item_data[row_column]) {
                        // new_cell.find('.matrix-item-hover')
                        //     .removeClass('label-warning')
                        //     .addClass('label-primary')
                        //     .text(matrix_item_data[current_name].group);
                        set_label(new_cell, matrix_item_data[row_column].group);

                        // Add the name
                        new_cell.find('.matrix_item-name').text(matrix_item_data[row_column].name);
                    }
                }

                // Add
                current_row.append(new_cell);
            }

            matrix_body_selector.append(current_row);
        }
    };

    // function chip_style_name_incrementer() {
    //     // var original_name = $('#id_matrix_item_name').val();

    //     var original_name = $('#id_chip_naming').val();
    //     var split_name = original_name.split(/(\d+)/).filter(Boolean);

    //     var numeric_index = original_name.length - 1;
    //     // Increment the first number encountered
    //     while (!$.isNumeric(split_name[numeric_index]) && numeric_index >= 0) {
    //         numeric_index -= 1;
    //     }

    //     if (numeric_index === -1) {
    //         numeric_index = original_name.length;
    //     }

    //     var first_half = split_name.slice(0, numeric_index).join('');
    //     var second_half = split_name.slice(numeric_index + 1).join('');
    //     var initial_value = Math.floor(split_name[numeric_index]);

    //     if (isNaN(initial_value)) {
    //         initial_value = 1;
    //     }

    //     // Skipped keeps track of how many items were skipped (recalculates the name this way)
    //     var skipped = 0;

    //     // Iterate over all selected
    //     current_selection.each(function(index) {
    //         // Note that this accounts for skips
    //         var incremented_value = index + initial_value - skipped;
    //         incremented_value += '';

    //         while (first_half.length + second_half.length + incremented_value.length < original_name.length) {
    //             incremented_value = '0' + incremented_value;
    //         }

    //         var value = first_half + incremented_value + second_half;

    //         // SET DISPLAY AND VALUE HERE
    //         // TODO
    //         // Conditional is to ignore empty items, every item needs a series before it is considered
    //         if (matrix_item_data[$(this).attr('data-row-column')]) {
    //             // Set the name
    //             matrix_item_data[$(this).attr('data-row-column')].name = value;
    //             // Set the name label
    //             $(this).find('.matrix_item-name').text(value);
    //         }
    //         // Increment skipped if this items doesn't have a series
    //         else {
    //             skipped += 1;
    //         }
    //     });
    // }

    function programmatic_select(current_selection) {
        $('.ui-selected').not(current_selection).removeClass('ui-selected').addClass('ui-unselecting');

        current_selection.not('.ui-selected').addClass('ui-selecting');

        matrix_table_selector.selectable('refresh');

        matrix_table_selector.data('ui-selectable')._mouseStop(null);
    }

    // We PROBABLY won't want to apply to everything
    // function apply_action_to_all() {
    //     // $(item_display_class).addClass('ui-selected');
    //     programmatic_select($(item_display_class));
    //     matrix_add_content_to_selected();
    // }

    function apply_action_to_row() {
        // Remove ui-selected class manually
        $(item_display_class).removeClass('ui-selected');
        // Get the column index
        var row_index = $(this).attr('data-row-to-apply');
        // Add the ui-selected class to the column
        // $(item_display_class + '[data-row-index="' + row_index + '"]').addClass('ui-selected');
        programmatic_select($($(item_display_class + '[data-row-index="' + row_index + '"]')));
        // Make the call
        matrix_add_content_to_selected();
    }

    function apply_action_to_column() {
        // Remove ui-selected class manually
        $(item_display_class).removeClass('ui-selected');
        // Get the column index
        var column_index = $(this).attr('data-column-to-apply');
        // Add the ui-selected class to the column
        // $(item_display_class + '[data-column-index="' + column_index + '"]').addClass('ui-selected');
        programmatic_select($(item_display_class + '[data-column-index="' + column_index + '"]'));
        // Make the call
        matrix_add_content_to_selected();
    }

    function matrix_add_content_to_selected() {
        // Indicate selection has concluded
        user_is_selecting = false;

        // TODO: OPEN THE DIALOG
        selection_dialog.dialog('open');

        // Remove ui-selected class manually
        $(item_display_class).removeClass('ui-selected');
    }

    // Matrix Listeners
    // BE CAREFUL! THIS IS SUBJECT TO CHANGE!
    // function check_representation() {
    //     var current_representation = representation_selector.val();

    //     // Hide all matrix sections
    //     $('.matrix-section').hide('fast');

    //     if (current_representation === 'chips') {
    //         $('#matrix_dimensions_section').show();
    //         if (device_selector.val()) {
    //             // number_of_rows_selector.val(0);
    //             // number_of_columns_selector.val(0);
    //             // number_of_items_selector.val(0);
    //             device_selector.val('').change();
    //         }

    //         // SPECIAL OPERATION
    //         $('#id_matrix_item_device').parent().parent().show();

    //         // SPECIAL OPERATION: SHOW NAMES
    //         $('.matrix_item-name_section').show();
    //     }
    //     else if (current_representation === 'plate') {
    //         $('#matrix_device_and_model_section').show();
    //         // TODO FORCE SETUP DEVICE TO MATCH
    //         // SPECIAL OPERATION
    //         $('#id_matrix_item_device').parent().parent().hide();

    //         // SPECIAL OPERATION: HIDE NAMES
    //         $('.matrix_item-name_section').hide();

    //         // UNCHECK USE CHIP NAMES
    //         // use_chip_naming.prop('checked', false);
    //     }
    // }

    // // Attach trigger and run initially
    // representation_selector.change(check_representation);
    // check_representation();

    // Deal with device changing and change dimensions as necessary
    function check_matrix_device() {
        if (device_selector.val()) {
            get_matrix_dimensions();
        }
        // else if (!device_selector.val() || representation_selector.val() === 'plate') {
        //     device_selector.val('');
        // }
    }

    device_selector.change(check_matrix_device);
    check_matrix_device();

    number_of_rows_selector.change(function() {
        get_matrix_dimensions();
    });

    number_of_columns_selector.change(function() {
        get_matrix_dimensions();
    });

    number_of_items_selector.change(function() {
        var number_of_items = Math.floor(number_of_items_selector.val());
        var first_estimate = Math.floor(Math.sqrt(number_of_items));

        var number_of_rows = first_estimate;
        var number_of_columns = first_estimate;

        var additional_columns = 0;

        while (Math.pow(first_estimate, 2) + additional_columns * number_of_rows < number_of_items) {
            additional_columns += 1;
        }

        // Make sure even splits are always possible
        if (
            number_of_items % 2 === 0 &&
            number_of_items !== number_of_rows * (number_of_columns + additional_columns)
        ) {
            number_of_rows = 2;
            number_of_columns = number_of_items / 2;
            additional_columns = 0;
        }

        if (
            number_of_items % 2 !== 0 &&
            number_of_items !== number_of_rows * (number_of_columns + additional_columns)
        ) {
            number_of_rows = 1;
            number_of_columns = number_of_items;
            additional_columns = 0;
        }

        number_of_rows_selector.val(number_of_rows);
        number_of_columns_selector.val(number_of_columns + additional_columns);

        get_matrix_dimensions();
    });

    get_matrix_dimensions();

    // NEW THINGS FROM NOW ON

    function delete_selected() {
        current_selection.each(function() {
            delete matrix_item_data[$(this).attr('data-row-column')];

            unset_label($(this));
        });

        // TO BE REVISED
        // replace_series_data();
        series_data_selector.val(JSON.stringify(full_series_data));
    }

    function apply_to_selected() {
        // var current_representation = representation_selector.val();
        if (series_selector.val()) {
            current_selection.each(function() {
                // Make new object if necessary for current item
                if (!matrix_item_data[$(this).attr('data-row-column')]) {
                    matrix_item_data[$(this).attr('data-row-column')] = {};
                }

                var current_matrix_item_data = matrix_item_data[$(this).attr('data-row-column')];

                current_matrix_item_data.series = series_selector.val();

                // TODO: SET GROUP WITH RESPECT TO INCREMENT TODO
                // TODO
                current_matrix_item_data.group = series_selector.val();

                set_label($(this), series_selector.val());

                // TODO: SET NAME
                // Be careful setting to magic string
                // Should the plate also fill the name label, even if it is not used?
                // if (current_representation !== 'chips') {
                //     // TODO PLATE NAMING
                //     // FOR THE MOMENT, JUST SETS TO THE DEFAULT NO APPENDED ZEROES
                //     current_matrix_item_data.name = $(this).attr('data-well-name');
                // }
                // TODO PLATE NAMING
                // FOR THE MOMENT, JUST SETS TO THE DEFAULT NO APPENDED ZEROES
                current_matrix_item_data.name = $(this).attr('data-well-name');
            });
        }

        // If the representation is a chips, use the initial
        // if (current_representation === 'chips' && use_chip_naming.prop('checked')) {
        //     // Sets the chip names
        //     chip_style_name_incrementer();
        // }

        // TO BE REVISED:
        // replace_series_data();
        series_data_selector.val(JSON.stringify(full_series_data));
    }

    // Selection dialog
    var selection_dialog = $('#selection_dialog');
    selection_dialog.dialog({
        width: 900,
        height: 500,
        open: function() {
            $.ui.dialog.prototype.options.open();
            // BAD
            setTimeout(function() {
                // Blur all
                $('.ui-dialog').find('input, select, button').blur();
            }, 150);

            current_selection = $('.ui-selected');

            // Discern what will be applied to
            var first_selection = current_selection.first();
            var last_selection = current_selection.last();
            selection_dialog_selected_items.text(first_selection.attr('data-well-name') + ' -> ' + last_selection.attr('data-well-name'));

            // Set series selector to nothing
            series_selector.val('').trigger('change');

            // Disable the accept button until a series is selected
            $('#selection_dialog_accept').prop('disabled', 'disabled');

            // SHOULD THE USE CHIP NAMING BE UNCHECKED EVERY TIME?
            // Set the initial name to the first item or nothing
            // if (matrix_item_data[first_selection.attr('data-row-column')] && matrix_item_data[first_selection.attr('data-row-column')].name) {
            //     chip_naming.val(matrix_item_data[first_selection.attr('data-row-column')].name);
            // }
            // else {
            //     chip_naming.val('');
            // }

            // Only display initial name if this is for chips
            // if (representation_selector.val() === 'chips') {
            //     selection_dialog_naming_section.show();

            //     // Allow just changing the name
            //     if (use_chip_naming.prop('checked')) {
            //         $('#selection_dialog_accept').prop('disabled', false);
            //     }
            // }
            // else {
            //     selection_dialog_naming_section.hide();
            // }
        },
        buttons: [
        {
            text: 'Delete',
            class: 'btn-danger',
            click: function() {
                // Apply TODO XXX
                delete_selected();

                $(this).dialog('close');
            }
        },
        {
            text: 'Apply',
            id: 'selection_dialog_accept',
            click: function() {
                // Apply TODO XXX
                apply_to_selected();

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
    selection_dialog.removeProp('hidden');

    // Checking and unchecking will disable the increment and type
    // use_compound_concentration_increment.change(function() {
    //     var is_checked = $(this).prop('checked');

    //     // Enable/disable increment inputs as necessary
    //     compound_compound_increment.prop('disabled', !is_checked);
    //     compound_compound_increment_type.prop('disabled', !is_checked);
    //     compound_concentration_increment_direction.prop('disabled', !is_checked);

    //     // PLEASE NOTE: ALSO SET THE INCREMENT TO NOTHING IF NOT ACTIVE
    //     if (!is_checked) {
    //         compound_compound_increment.val('');
    //     }
    // }).trigger('change');

    // Check to see if chip naming style should be used
    // use_chip_naming.change(function() {
    //     if ($(this).prop('checked') && representation_selector.val() === 'chips') {
    //         // Allow apply
    //         $('#selection_dialog_accept').prop('disabled', false);
    //     }
    //     // If this is for chips and there is no series and use_chip_naming is off
    //     else if (representation_selector.val() === 'chips' && !series_selector.val()) {
    //         // Disable apply
    //         $('#selection_dialog_accept').prop('disabled', true);
    //     }
    //     // Enable/disable chip_naming
    //     chip_naming.prop('disabled', !$(this).prop('checked'));
    // }).trigger('change');

    // Disable and enable apply based on whether there is a series
    series_selector.change(function() {
        if ($(this).val()) {
            $('#selection_dialog_accept').prop('disabled', false);
        }
        // else if (representation_selector.val() !== 'chips' && !use_chip_naming.prop('checked')) {
        //     $('#selection_dialog_accept').prop('disabled', true);
        // }
        else {
            $('#selection_dialog_accept').prop('disabled', true);
        }
    });

    // Container that shows up to reveal what a group contains
    var matrix_contents_hover = $('#matrix_contents_hover');
    // The row to add the group data to
    var matrix_contents_hover_body = $('#matrix_contents_hover_body');

    // For the hover preview of the data
    // TODO NEED current_group for dilution etc.
    function generate_row_clone_html(current_well_name, current_series, current_group) {
        // (This divs are contrivances)
        var name_row = $('<div>').append(
            $('<tr>').append(
                $('<td>').text(current_well_name)
            )
        );

        var full_row = $('<div>').append(
            $('tr[data-series="' + current_series + '"]').clone()
        );

        // Axe the first column
        full_row.find('td').first().remove();

        // Replace selects with their values
        var current_selects = full_row.find('select');
        current_selects.each(function() {
            var current_text = $(this).find('option[value="' + $(this).val() + '"]').text();
            var current_parent = $(this).parent();

            current_parent.html(current_text);
        });

        // TODO: NEED TO REVISE COMPOUND DISPLAYS FOR DILUTION

        // Kill buttons (this isn't for editing, just showing the data)
        full_row.find('.btn').remove();

        return name_row.html() + full_row.html();
    }

    // Hover event for matrix contents
    // TODO NEED TO DEAL WITH INCREMENTING COMPOUNDS
    // ie. NEED TO DIFFERENTIATE GROUP AND SERIES
    $(document).on('mouseover', '.matrix-item-hover', function() {
        // Current group of the item
        var current_group = null;
        var current_series = null;
        var current_data = matrix_item_data[$(this).parent().attr('data-row-column')];

        if (current_data && current_data.group) {
            current_group = current_data.group;
            current_series = current_data.series;
        }

        // Only show if the user is not selecting
        // Note that empty wells just show the name of the well
        if (!user_is_selecting) {
            matrix_contents_hover.show();
            // var left = $(this).offset().left - 10;
            // Hard value for left (TODO: Probably better to set to left of the matrix?)
            var left = $('#fluid-content').position().left + 30;
            // Place slightly below current label
            var top = $(this).offset().top + 50;
            matrix_contents_hover.offset({left: left, top: top});

            matrix_contents_hover_body.empty();
            matrix_contents_hover_body.html(
                generate_row_clone_html($(this).parent().attr('data-well-name'), current_series, current_group)
            );
        }
    });

    $(document).on('mouseout', '.matrix-item-hover', function() {
        matrix_contents_hover.hide();
    });
});
