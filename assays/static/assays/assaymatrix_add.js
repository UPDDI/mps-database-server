// Functions for displaying Assay Matrices
// TODO WE MAY WANT THIS IN MULTIPLE LOCATIONS, BUT AT THE MOMENT I AM ASSUMING ADD ONLY
// TODO THIS FILE IS A MESS
$(document).ready(function () {
    // TODO TODO TODO IN THE FUTURE FILE-SCOPE VARIABLES SHOULD BE IN ALL-CAPS
    // The matrix's ID
    var matrix_id = Math.floor(window.location.href.split('/')[5]);

    // Alias for the matrix selector
    var matrix_table_selector = $('#matrix_table');
    var matrix_body_selector = $('#matrix_body');

    window.device = $('#id_matrix_item_device');
    window.organ_model = $('#id_matrix_item_organ_model');
    window.organ_model_protocol = $('#id_matrix_item_organ_model_protocol');

    // Contrived, but useful:
    // Will make a clone of the organ_model and organ_model_protocol dropdowns for display
    var full_organ_model = $('#id_matrix_item_full_organ_model');
    var full_organ_model_protocol = $('#id_matrix_item_full_organ_model_protocol');

    var item_display_class = '.matrix_item-td';

    // Allows the matrix_table to have the draggable JQuery UI element
    matrix_table_selector.selectable({
        // SUBJECT TO CHANGE: WARNING!
        filter: item_display_class,
        distance: 1,
        cancel: '.btn-xs',
        stop: matrix_add_content_to_selected
    });

    // Page selector (MAY OR MAY NOT BE USED)
    var page_selector = $('#page');

    // Alias for device selector
    var device_selector = $('#id_device');

    // Alias for action selector
    var action_selector = $('#id_action');

    // Alias for representation selector
    var representation_selector = $('#id_representation');

    // Alias for number of rows/columns
    var number_of_items_selector = $('#id_number_of_items');
    var number_of_rows_selector = $('#id_number_of_rows');
    var number_of_columns_selector = $('#id_number_of_columns');

    // Not currently used, may be helpful in future
    // var initial_number_of_rows = 0;
    // var initial_number_of_columns = 0;

    // CRUDE AND BAD
    // If I am going to use these, they should be ALL CAPS to indicate global status
    var item_prefix = 'matrix_item';
    var cell_prefix = 'cell';
    var setting_prefix = 'setting';
    var compound_prefix = 'compound';

    var item_form_index_attribute = 'data-form-index';
    var item_subform_index_attribute = 'data-subform-index';
    var item_id_attribute = 'data-matrix_item-id';

    var prefixes = [
        item_prefix,
        cell_prefix,
        setting_prefix,
        compound_prefix
    ];

    var empty_item_html = $('#empty_matrix_item_html').children();
    var empty_compound_html = $('#empty_compound_html').children();
    var empty_cell_html = $('#empty_cell_html').children();
    var empty_setting_html = $('#empty_setting_html').children();

    // JS ACCEPTS STRING LITERALS IN OBJECT INITIALIZATION
    var empty_html = {};
    empty_html[item_prefix] = empty_item_html;
    empty_html[compound_prefix] = empty_compound_html;
    empty_html[cell_prefix] = empty_cell_html;
    empty_html[setting_prefix] = empty_setting_html;

    // All but matrix item should be static here
    // var item_final_index = $('#id_' + item_prefix + '-TOTAL_FORMS').val() - 1;
    var item_final_index = $('.' + item_prefix).length - 1;
    var cell_final_index = $('.' + cell_prefix).length - 1;
    var setting_final_index = $('.' + setting_prefix).length - 1;
    var compound_final_index = $('.' + compound_prefix).length - 1;

    // Due to extra=1 (A SETTING WHICH SHOULD NOT CHANGE) there will always be an empty example at the end
    // I can use these to make new forms as necessary
    var empty_item_form = $('#' + item_prefix + '-' + item_final_index).html();
    var empty_setting_form = $('#' + setting_prefix + '-' + setting_final_index).html();
    var empty_cell_form = $('#' + cell_prefix + '-' + cell_final_index).html();
    var empty_compound_form = $('#' + compound_prefix + '-' + compound_final_index).html();

    var empty_forms = {};
    empty_forms[item_prefix] = empty_item_form;
    empty_forms[compound_prefix] = empty_compound_form;
    empty_forms[cell_prefix] = empty_cell_form;
    empty_forms[setting_prefix] = empty_setting_form;

    var final_indexes = {};
    final_indexes[item_prefix] = item_final_index;
    final_indexes[compound_prefix] = compound_final_index;
    final_indexes[cell_prefix] = cell_final_index;
    final_indexes[setting_prefix] = setting_final_index;

    // For converting between times
    var time_conversions = {
        'day': 1440.0,
        'hour': 60.0,
        'minute': 1.0
    };

    // For using incrementers
    // TODO TODO SUBJECT TO CHANGE
    var incrementers = {
        'concentration': {
            'increment': $('#id_compound_concentration_increment'),
            'type': $('#id_compound_concentration_increment_type'),
            'direction': $('#id_compound_concentration_increment_direction')
        }
    };

    function add_form(prefix, form) {
        var formset = $('#' + prefix);
        formset.append(form);
        $('#id_' + prefix + '-TOTAL_FORMS').val($('.' + prefix).length);
    }

    // Takes a prefix and an Object of {field_name: value} to spit out a form
    function generate_form(prefix, values_to_inject) {
        // TODO TODO TODO
        // Can't cache this, need to check every call!
        var number_of_forms = $('.' + prefix).length;
        var regex_to_replace_old_index = new RegExp("\-" + final_indexes[prefix] + "\-", 'g');

        var new_html = empty_forms[prefix].replace(regex_to_replace_old_index,'-' + number_of_forms + '-');
        var new_form = $('<div>')
            .html(new_html)
            .attr('id', prefix + '-' + number_of_forms)
            .addClass(prefix);

        // TODO TODO TODO ITEM FORMS NEED TO HAVE ROW AND COLUMN INDICES
        if (values_to_inject) {
            $.each(values_to_inject, function(field, value) {
                new_form.find('input[name$="' + field + '"]').val(value);
                // TODO NAIVE: Also set the attribute (val sets a property)
                new_form.find('input[name$="' + field + '"]').attr('value', value);
            });
        }

        return new_form;
    }

    // DEPRECATED
    // WILL PROBABLY JUST HANDLE THIS IN PYTHON
    function get_split_time(time_in_minutes) {
        var times = {
            'day': 0,
            'hour': 0,
            'minute': 0
        };

        var time_in_minutes_remaining = time_in_minutes;
        $.each(time_conversions, function(time_unit, conversion) {
            var initial_time_for_current_field = Math.floor(time_in_minutes_remaining / conversion);
            if (initial_time_for_current_field) {
                times[time_unit] = initial_time_for_current_field;
                time_in_minutes_remaining -= initial_time_for_current_field * conversion;
            }
        });

        // Add fractions of minutes if necessary
        if (time_in_minutes_remaining) {
            times['minute'] += time_in_minutes_remaining
        }

        return times
    }

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

    function plate_style_name_creation(append_zero) {
        var current_global_name = $('#id_matrix_item_name').val();
        var current_number_of_rows = number_of_rows_selector.val();
        var current_number_of_columns = number_of_columns_selector.val();

        var largest_row_name_length = Math.pow(current_number_of_columns, 1/10);

        for (var row_id=0; row_id < current_number_of_rows; row_id++) {
            // Please note + 1
            var row_name = to_letters(row_id + 1);

            for (var column_id=0; column_id < current_number_of_columns; column_id++) {
                var current_item_id = item_prefix + '_' + row_id + '_' + column_id;

                var column_name = column_id + 1 + '';
                if (append_zero) {
                    while (column_name.length < largest_row_name_length) {
                        column_name = '0' + column_name;
                    }
                }

                var value = current_global_name + row_name + column_name;

                // TODO TODO TODO PERFORM THE ACTUAL APPLICATION TO THE FORMS
                // TODO TODO TODO PERFORM THE ACTUAL APPLICATION TO THE FORMS
                // Set display
                var item_display = $('#'+ current_item_id);
                item_display.find('.matrix_item-name').html(value);
                // Set form
                $('#id_' + item_prefix + '-' + item_display.attr(item_form_index_attribute) + '-name').val(value);
            }
        }
    }

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
                    build_initial_matrix(
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
            build_initial_matrix(
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

    // Makes the initial matrix
    // TODO PURGE CELLS WHEN SHRINKING
    var build_initial_matrix = function(number_of_rows, number_of_columns) {
        matrix_body_selector.empty();

        // ONLY DISPLAY APPLY ROW/COLUMN BUTTONS IF THIS IS ADD/UPDATE
        var starting_index_for_matrix = $('#floating-submit-row')[0] ? -1 : 0;

        // Check to see if new forms will be generated
        for (var row_index=starting_index_for_matrix; row_index < number_of_rows; row_index++) {
            var row_id = 'row_' + row_index;
            var current_row = $('<tr>')
                .attr('id', row_id);

            var all_matching_for_row_value = $('.' + item_prefix).has('input[name$="-row_index"][value="' + row_index + '"]');

            for (var column_index=starting_index_for_matrix; column_index < number_of_columns; column_index++) {
                var item_id = item_prefix + '_' + row_index + '_' + column_index;
                var new_cell = null;

                // If this is an apply to row
                if (column_index === -1) {
                    if (row_index === -1) {
                        new_cell = $('<td>')
                    }
                    else {
                        new_cell = $('<td>')
                            .addClass('text-center')
                            // Note: CRUDE
                            .css('vertical-align', 'middle')
                            .append(
                                $('<a>')
                                    .html('Apply to Row')
                                    .attr('data-row-to-apply', row_index)
                                    .addClass('btn btn-sm btn-primary')
                                    .click(apply_action_to_row)
                            );
                    }
                }
                // If this is an apply to column
                else if (row_index === -1) {
                    new_cell = $('<td>')
                        .addClass('text-center')
                        .append(
                            $('<a>')
                                .html('Apply to Column')
                                .attr('data-column-to-apply', column_index)
                                .addClass('btn btn-sm btn-primary')
                                .click(apply_action_to_column)
                        );
                }
                // If this is for actual contents
                else {
                    new_cell = empty_item_html
                        .clone()
                        .attr('id', item_id)
                        .attr('data-row-index', row_index)
                        .attr('data-column-index', column_index)
                    ;

                    // If the form does not exist, then add it!
                    if (!all_matching_for_row_value.has('input[name$="-column_index"][value="' + column_index + '"]')[0]) {
                        var new_form = generate_form(
                            item_prefix, {'row_index': row_index, 'column_index': column_index}
                        );
                        // Get number of forms and add as attribute to the display
                        // A little inefficient, but relatively safe
                        var number_of_forms = $('.' + item_prefix).length;
                        new_cell.attr(item_form_index_attribute, number_of_forms);

                        add_form(item_prefix, new_form);
                    }
                }

                // Add
                current_row.append(new_cell);
            }

            matrix_body_selector.append(current_row);
        }

        // Don't run this if the forms are all new anyway
        // TODO TODO TODO
        refresh_all_contents_from_forms();
    };

    function get_field_name(field) {
        // To get the field name in question, I can split away everything before the terminal -
        if (field.attr('name')) {
            var field_name = field.attr('name').split('-');
            return field_name[field_name.length-1];
        }
        else {
            return false;
        }
    }

    function get_display_for_field(field, field_name, prefix) {
        // If the value of the field is null, don't bother!
        if (!field.val()) {
            return null;
        }

        // NOTE: SPECIAL EXCEPTION FOR CELL SAMPLES
        if (field_name === 'cell_sample') {
            // TODO VERY POORLY DONE
            // return $('#' + 'cell_sample_' + field.val()).attr('name');
            // Global here is a little sloppy, but should always succeed
            return window.CELLS.cell_sample_id_to_label[field.val()];
        }
        // SPECIAL EXCEPTION FOR ORGAN MODELS
        else if (field_name === 'organ_model') {
            return full_organ_model.find('option[value="' + field.val() + '"]').text();
        }
        // SPECIAL EXCEPTION FOR ORGAN MODEL PROTOCOLS
        else if (field_name === 'organ_model_protocol') {
            return full_organ_model_protocol.find('option[value="' + field.val() + '"]').text();
        }
        else {
            // Ideally, this would be cached in an object or something
            var origin = $('#id_' + prefix + '_' + field_name);

            // Get the select display if select
            if (origin.prop('tagName') === 'SELECT') {
                // Convert to integer if possible, thanks
                var possible_int = Math.floor(field.val());
                // console.log(possible_int);
                if (possible_int) {
                    // console.log(origin[0].selectize.options[possible_int].text);
                    return origin[0].selectize.options[possible_int].text;
                }
                else {
                    // console.log(origin[0].selectize.options[field.val()].text);
                    return origin[0].selectize.options[field.val()].text;
                }
                // THIS IS BROKEN, FOR PRE-SELECTIZE ERA
                // return origin.find('option[value="' + field.val() + '"]').text()
            }
            // Just display the thing if there is an origin
            else if (origin[0]) {
                return field.val();
            }
            // Give back null to indicate this should not be displayed
            else {
                return null;
            }
        }
    }

    // This function finds where to put the new display data
    function get_display_from_item_form(form) {
        var row_index = form.find('input[name$="row_index"]').val();
        var column_index = form.find('input[name$="column_index"]').val();
        return $('#' + item_prefix + '_' + row_index + '_' + column_index);
    }

    function get_display_id_from_subform(subform) {
        var parent_item_id = subform.find('input[name$="matrix_item"]').val();
        var parent_form = $('.' + item_prefix + '> input[name$="-id"][value="' + parent_item_id + '"]').parent();
        return get_display_from_item_form(parent_form);
    }

    // TODO REVISE
    function refresh_all_contents_from_forms() {
        // I probably can get away with purging the marked entries
        $('.matrix_item-setup_set_section').empty();

        var errors_exist = false;
        // Iterate over all prefixes
        $.each(prefixes, function(index, prefix) {
            // Iterate over all forms
            $('.' + prefix).each(function(form_index) {
                var display = null;
                var new_subdisplay = null;
                // Get the display to add to here TODO TODO TODO
                if (prefix === item_prefix) {
                    display = get_display_from_item_form($(this));
                    // var current_item_index = $(this).attr('id').split('-');
                    // TODO TODO TODO I NEED TO THINK ABOUT THE CONSEQUENCES OF THIS
                    // display.attr(item_form_index_attribute, current_item_index[current_item_index.length - 1]);
                    display.attr(item_form_index_attribute, form_index);
                    var current_id = $(this).find('input[name$="-id"]').val();
                    display.attr(item_id_attribute, current_id);
                    if (current_id) {
                        // BE CAREFUL WITH THIS SORT OF STUFF
                        display.find('.matrix_item-name')
                            .removeAttr('disabled')
                            .attr('href', '/assays/assaymatrixitem/' + current_id);
                    }
                    else {
                        display.find('.matrix_item-name').attr('disabled', '');
                        // display.find('.form-delete').hide();
                    }
                }
                // Generate a subdisplay if this is not item TODO TODO TODO
                // Add the subdisplay to the display
                else {
                    // console.log($(this));
                    display = get_display_id_from_subform($(this));
                    new_subdisplay = empty_html[prefix].clone();
                    new_subdisplay.attr(item_subform_index_attribute, form_index);
                    // Probably superfluous
                    new_subdisplay.attr(item_form_index_attribute, display.attr(item_form_index_attribute));
                }

                // List of errors to add in a ul at the top of a display
                var errors = [];

                // Iterate over all fields
                // Out of convenience, I can iterate over every child
                $(this).find(':input').each(function(input_index) {
                    // I will need to think about invalid fields
                    var field_name = get_field_name($(this));
                    var field_display = get_display_for_field($(this), field_name, prefix);
                    if (!new_subdisplay) {
                        display.find('.' + prefix + '-' + field_name).html(field_display);
                    }
                    else {
                        new_subdisplay.find('.' + prefix + '-' + field_name).html(field_display);
                    }

                    var possible_errors = [];
                    if (!input_index) {
                        possible_errors = $(this).prev().prev().find('li');
                        $.each(possible_errors, function() {
                            errors.push($(this).text());
                        });
                    }
                    else {
                        possible_errors = $(this).prev().find('li');
                        $.each(possible_errors, function() {
                            errors.push(field_name + ': ' + $(this).text());
                        });
                    }
                });

                // Hide deletes for forms without names
                if (!$(this).find('input[name$="-name"]').val()) {
                    display.find('.form-delete').hide();
                }
                else {
                    display.find('.form-delete').show();
                }

                var errors_display = null;
                var errors_list = null;

                var item_was_marked_deleted = $(this).find('input[name$="DELETE"]').prop('checked');

                if (errors.length > 0 && !item_was_marked_deleted) {
                    errors_display = $('#empty_error_html').children().clone();
                    errors_list = $('<ul>');
                    $.each(errors, function(index, error_message) {
                        errors_list.append($('<li>').text(error_message));
                    });
                    errors_display.html(errors_list);
                    errors_exist = true;
                }
                else if (item_was_marked_deleted) {
                    display.addClass('strikethrough');
                }

                if (new_subdisplay) {
                    // If this subform is to be deleted
                    // TODO NOT DRY
                    var delete_input = $('#id_' + prefix + '-' + new_subdisplay.attr(item_subform_index_attribute) + '-DELETE');
                    var checked_value = delete_input.prop('checked');

                    if (checked_value || item_was_marked_deleted) {
                        new_subdisplay.addClass('strikethrough');
                    }
                    else {
                        new_subdisplay.removeClass('strikethrough');
                    }

                    display.find('.matrix_item-' + prefix).append(new_subdisplay);
                    if (errors_display) {
                        new_subdisplay.find('.error-message-section').html(errors_display);
                    }
                }
                else if (errors_display) {
                    display.find('.error-message-section').html(errors_display);
                }
            });
        });

        // NOTE: Special operation! Hide device if one is selected
        if (device_selector.val()) {
            $('.matrix_item-device').hide();
        }
        else {
            $('.matrix_item-device').show();
        }

        // NOTE: Show all displays if there are errors
        if (errors_exist) {
            $('.visibility-checkbox').prop('checked', true);
            // Be sure to show "Show Errors" as well
            $('#show_errors').parent().parent().show();
            change_matrix_visibility();
        }
    }

    function chip_style_name_incrementer() {
        var original_name = $('#id_matrix_item_name').val();
        var split_name = original_name.split(/(\d+)/).filter(Boolean);

        var numeric_index = original_name.length - 1;
        // Increment the first number encountered
        while (!$.isNumeric(split_name[numeric_index]) && numeric_index >= 0) {
            numeric_index -= 1;
        }

        if (numeric_index === -1) {
            numeric_index = original_name.length;
        }

        var first_half = split_name.slice(0, numeric_index).join('');
        var second_half = split_name.slice(numeric_index + 1).join('');
        var initial_value = Math.floor(split_name[numeric_index]);

        if (isNaN(initial_value)) {
            initial_value = 1;
        }

        // Iterate over all selected
        $('.ui-selected').each(function(index) {
            var current_item_id = this.id;

            var incremented_value = index + initial_value;
            incremented_value += '';

            while (first_half.length + second_half.length + incremented_value.length < original_name.length) {
                incremented_value = '0' + incremented_value;
            }

            var value = first_half + incremented_value + second_half;

            // Set display
            $(this).find('.matrix_item-name').html(value);
            // Set form
            $('#id_' + item_prefix + '-' + $(this).attr(item_form_index_attribute) + '-name').val(value);
        });

        // Semi-superfluous (refreshes things like delete button)
        refresh_all_contents_from_forms();
    }

    function default_incrementer(
            current_value,
            increment_key,
            index,
            number_of_items
    ) {
        var increment = incrementers[increment_key]['increment'].val();
        var increment_direction = incrementers[increment_key]['direction'].val();
        var increment_type = incrementers[increment_key]['type'].val();

        if (increment_direction === 'rlu') {
            index = number_of_items - 1 - index;
        }

        var new_value = current_value;
        var result = null;

        // Add
        if (increment_type === '+') {
            result = new_value + (index * increment);
            if (result >= 0) {
                new_value = result;
            }
            else {
                new_value = 0;
            }
        }

        // Divide
        else if(increment_type === '/') {
            result = new_value / Math.pow(increment, index);
            if (isFinite(result) && result >= 0) {
                new_value = result;
            }
            else {
                new_value = 0;
            }
        }

        // Subtract
        else if(increment_type === '-') {
            result = new_value - (index * increment);
            if (result >= 0) {
                new_value = result;
            }
            else {
                new_value = 0;
            }
        }

        // Multiply
        else {
            result = new_value * Math.pow(increment, index);
            if (result >= 0) {
                new_value = result;
            }
            else {
                new_value = 0;
            }
        }

        return new_value;
    }

    function get_field_from_control(prefix, control) {
        // console.log(prefix, control);
        return control.attr('name').replace(prefix + '_', '');
    }

    // TODO TODO TODO BE POSITIVE THAT SUBFORMS ARE NOT ADDED TO ITEMS THAT DON'T EXIST YET
    function add_subform(prefix)  {
        var current_fields = $('.matrix_item-section:visible').find('select, input, textarea').not('[id$="-selectized"]');

        var number_of_items = $('.ui-selected').length;

        $('.ui-selected').each(function(index) {
            var current_item_id = $(this).attr(item_id_attribute);
            if (current_item_id) {
                var new_form = generate_form(prefix);

                // TODO PERHAPS THIS SHOULD BE IN values_to_inject ARG, but doesn't matter too much, would need to accomodate incrementer anyway
                current_fields.each(function(field_index) {
                    var field_name = get_field_from_control(prefix, $(this));
                    var current_value = $(this).val();
                    // I BELIEVE I AM SAFE IN ASSUMING THAT ALL MY FORMS WILL JUST HAVE INPUT, NO SELECT OR WHATEVER
                    if (incrementers[field_name]) {
                        current_value = default_incrementer(current_value, field_name, index, number_of_items);
                    }
                    new_form.find('input[name$="' + field_name + '"]').val(current_value);
                });

                new_form.find('input[name$="matrix_item"]').val(current_item_id);

                add_form(prefix, new_form.clone());
            }
        });

        refresh_all_contents_from_forms();
    }

    // SUBJECT TO CHANGE
    function add_to_item() {
        var current_fields = $('.matrix_item-section:visible').find('select, input, textarea').not('[id$="-selectized"]');

        var number_of_items = $('.ui-selected').length;

        $('.ui-selected').each(function(index) {
            var current_form = $('#' + item_prefix + '-' + $(this).attr(item_form_index_attribute));
            // console.log(current_form);

            // TODO PERHAPS THIS SHOULD BE IN values_to_inject ARG, but doesn't matter too much, would need to accomodate incrementer anyway
            current_fields.each(function(field_index) {
                var field_name = get_field_from_control(item_prefix, $(this));
                var current_value = $(this).val();
                // I BELIEVE I AM SAFE IN ASSUMING THAT ALL MY FORMS WILL JUST HAVE INPUT, NO SELECT OR WHATEVER
                if (incrementers[field_name]) {
                    current_value = default_incrementer(current_value, field_name, index, number_of_items);
                }

                var form_field_to_add_to = current_form.find('input[name$="' + field_name + '"]');

                if (!form_field_to_add_to[0]) {
                    form_field_to_add_to = current_form.find('select[name$="' + field_name + '"]');
                }

                // DO NOT ADD TO FORMS THAT ARE MISSING THEIR NAME!
                // ONLY IGNORE IF field_name IS NAME
                if (field_name == 'name' || current_form.find('input[name$="name"]').val()) {
                    form_field_to_add_to.val(current_value);
                }
            });
        });

        refresh_all_contents_from_forms();
    }

    function mark_subform_deleted(delete_button) {
        var current_parent = delete_button.parent().parent();
        var prefix = current_parent.attr('data-prefix');
        var delete_input = $('#id_' + prefix + '-' + current_parent.attr(item_subform_index_attribute) + '-DELETE');
        var checked_value = !delete_input.prop('checked');

        if (checked_value) {
            current_parent.addClass('strikethrough');
        }
        else {
            current_parent.removeClass('strikethrough');
        }

        delete_input.prop('checked', function(i, val) {return !val;});
    }

    function mark_form_deleted(delete_button) {
        // TODO TODO TODO SUBJECT TO CHANGE
        var current_parent = delete_button.parent().parent().parent();
        var current_prefix = current_parent.attr('data-prefix');
        var delete_input = $('#id_' + current_prefix + '-' + current_parent.attr(item_form_index_attribute) + '-DELETE');

        var checked_value = !delete_input.prop('checked');

        if (checked_value) {
            current_parent.addClass('strikethrough');
        }
        else {
            current_parent.removeClass('strikethrough');
        }

        delete_input.prop('checked', function(i, val) {return !val;});

        // TODO MAY BE PROBLEMMATIC IN CERTAIN CIRCUMSTANCES
        // Requires testing
        current_parent.find('.subform-delete').trigger('click');
        current_parent.find('.subform-delete').attr('disabled', checked_value);
    }

    function delete_items() {
        var delete_option = $('#id_delete_option').val();

        // If delete all
        if (delete_option === 'all') {
            $('.ui-selected').not('.strikethrough').find('.form-delete').trigger('click');
        }
        // Otherwise find the matching subforms and delete them
        else {
            $('.ui-selected').not('.strikethrough')
                .find('.matrix_item-' + delete_option)
                .find('.subform-delete')
                .trigger('click');
        }
    }

    // TODO TODO TODO TENTATIVE
    function clear_fields() {
        $('.ui-selected').each(function(index) {
            var current_id = $(this).find('input[name$="-id"]').val();
            if (!current_id) {
                var current_form = $('#' + item_prefix + '-' + $(this).attr(item_form_index_attribute));
                // console.log(current_form);

                current_form.find('input').val('');
                current_form.find('select').val('');
            }
        });

        refresh_all_contents_from_forms();
    }

    function apply_action_to_all() {
        $(item_display_class).addClass('ui-selected');
        matrix_add_content_to_selected();
    }

    function apply_action_to_row() {
        // Remove ui-selected class manually
        $(item_display_class).removeClass('ui-selected');
        // Get the column index
        var row_index = $(this).attr('data-row-to-apply');
        // Add the ui-selected class to the column
        $(item_display_class + '[data-row-index="' + row_index + '"]').addClass('ui-selected');
        // Make the call
        matrix_add_content_to_selected();
    }

    function apply_action_to_column() {
        // Remove ui-selected class manually
        $(item_display_class).removeClass('ui-selected');
        // Get the column index
        var column_index = $(this).attr('data-column-to-apply');
        // Add the ui-selected class to the column
        $(item_display_class + '[data-column-index="' + column_index + '"]').addClass('ui-selected');
        // Make the call
        matrix_add_content_to_selected();
    }

    function matrix_add_content_to_selected() {
        var current_action = action_selector.val();

        if (current_action === 'add_name') {
            // Default action for add name is to use chip style
            chip_style_name_incrementer();
        }
        else if (current_action === 'add_cells') {
            // add_cell_form(current_fields);
            add_subform(cell_prefix);
        }
        else if (current_action === 'add_settings') {
            add_subform(setting_prefix);
        }
        else if (current_action === 'add_compounds') {
            add_subform(compound_prefix);
        }
        else if (current_action === 'delete') {
            delete_items();
        }
        // TODO TODO TODO TENTATIVE
        // else if (current_action === 'clear') {
        //     clear_fields();
        // }
        // Default for most actions
        else {
            add_to_item();
        }

        // Remove ui-selected class manually
        $(item_display_class).removeClass('ui-selected');
    }

    // Matrix Listeners
    // BE CAREFUL! THIS IS SUBJECT TO CHANGE!
    function check_representation() {
        var current_representation = representation_selector.val();

        // Hide all matrix sections
        $('.matrix-section').hide('fast');

        if (current_representation === 'chips') {
            $('#matrix_dimensions_section').show();
            if (device_selector.val()) {
                // number_of_rows_selector.val(0);
                // number_of_columns_selector.val(0);
                // number_of_items_selector.val(0);
                device_selector.val('').change();
            }

            // SPECIAL OPERATION
            $('#id_matrix_item_device').parent().parent().show();
        }
        else if (current_representation === 'plate') {
            $('#matrix_device_and_model_section').show();
            // TODO FORCE SETUP DEVICE TO MATCH
            // SPECIAL OPERATION
            $('#id_matrix_item_device').parent().parent().hide();
        }
    }

    representation_selector.change(check_representation);
    check_representation();

    function check_matrix_device() {
        if (device_selector.val()) {
            get_matrix_dimensions();

            if (representation_selector.val() === 'plate') {
                // window.device.val(device_selector.val()).trigger('change');
                window.get_organ_models(device_selector.val());
            }
        }
        else if (!window.device.val() || representation_selector.val() === 'plate') {
            window.device.val('');
            window.get_organ_models('');
        }
    }

    device_selector.change(check_matrix_device);
    check_matrix_device();

    // TODO TODO TODO RESTORE LATER
    // if (device_selector.val()) {
    //     device_selector.trigger('change');
    // }

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

        number_of_rows_selector.val(number_of_rows);
        number_of_columns_selector.val(number_of_columns + additional_columns);

        get_matrix_dimensions();
    });

    // TODO TODO TODO RESTORE LATER
    // if (number_of_items_selector.val() && !device_selector.val()) {
    //     number_of_items_selector.trigger('change');
    // }

    function check_action() {
        $('.matrix_item-section').hide('fast');
        var current_section = action_selector.val();
        $('.' + current_section + '_section').show('fast');
        if (current_section) {
            $('#apply_action_to_all').show();
        }
        else {
            $('#apply_action_to_all').hide();
        }

        // Check visibility boxes as necessary
        if (current_section === 'add_settings') {
            $('#show_settings').prop('checked', true).trigger('change');
        }
        else if (current_section === 'add_compounds') {
            $('#show_compounds').prop('checked', true).trigger('change');
        }
        else if (current_section === 'add_cells') {
            $('#show_cells').prop('checked', true).trigger('change');
        }
        else if (current_section.indexOf('add_') > -1) {
            $('#show_matrix_items').prop('checked', true).trigger('change');
        }
    }
    action_selector.change(check_action);

    // Initially check action
    check_action();

    // Testing SUBJECT TO CHANGE
    $('#apply_plate_names_zero').click(function() {
       plate_style_name_creation(true);
    });

    $('#apply_plate_names_no_zero').click(function() {
       plate_style_name_creation(false);
    });

    // Triggers for subform-delete
    matrix_body_selector.on('click', '.subform-delete', function() {
        mark_subform_deleted($(this));
    });

    // Triggers for form-delete
    matrix_body_selector.on('click', '.form-delete', function() {
        mark_form_deleted($(this));
    });

    // Trigger for apply all
    $('#apply_action_to_all').click(function() {
        apply_action_to_all();
    });

    // TODO TODO TODO TESTING
    if (!device_selector.val()) {
        get_matrix_dimensions();
    }

    // Handling Device flow
    window.device.change(function() {
        // Get organ models
        window.get_organ_models(device.val());
    });

    window.get_organ_models(device.val());

    window.organ_model.change(function() {
        // Get and display correct protocol options
        window.get_protocols(window.organ_model.val());
    });

    window.get_protocols(window.organ_model.val());

    window.organ_model_protocol.change(function() {
        window.display_protocol(window.organ_model_protocol.val());
    });

    window.display_protocol(window.organ_model_protocol.val());

    // Hide all
    function hide_all_sections() {
        $('.visibility-checkbox').each(function() {
            var class_to_hide = $(this).attr('value');
                $(class_to_hide).hide();
        });
    }

    // Triggers for hiding elements
    function change_matrix_visibility() {
        $('.visibility-checkbox').each(function() {
            var class_to_hide = $(this).attr('value');
            if ($(this).prop('checked')) {
                $(class_to_hide).show();
            }
            else {
                $(class_to_hide).hide();
            }
        });
    }

    $('.visibility-checkbox').change(change_matrix_visibility);
    change_matrix_visibility();

    // On shift press hide all for dragging
    $(document).keydown(function (e) {
        if (e.keyCode === 16) {
            hide_all_sections();
        }
    });

    $(document).keyup(function (e) {
        if (e.keyCode === 16) {
            change_matrix_visibility();
        }
    });

    // Special operations for pre-submission
    $('form').submit(function() {
        // Iterate over every Matrix Item form
        // EXCEEDINGLY NAIVE, PLEASE REVISE
        $('.' + item_prefix).each(function(form_index) {
            // Removed the notion of shadow deleting "empty" items
            var empty = true;

            var current_name = $(this).find('input[name$="-name"]').val();
            if (current_name) {
                $(this).find('input:not(:checkbox)').each(function(input_index) {
                    if($(this).val()) {
                        if(
                            $(this).attr('name').indexOf('_index') === -1 &&
                            $(this).attr('name').indexOf('-name') === -1 &&
                            $(this).attr('name').indexOf('-matrix') === -1 &&
                            $(this).attr('name').indexOf('-test_type') === -1 &&
                            $(this).attr('name').indexOf('-setup_date') === -1 &&
                            (!device_selector.val() || $(this).attr('name').indexOf('-device') === -1)
                        ) {
                            empty = false;
                            return false;
                        }
                    }
                });
            }
            // Mark for deletion if empty
            // Items without names should always be removed
            if (empty) {
                $(this).find('input[name$="DELETE"]').prop('checked', true);
            }
            // Items with names must have device
            // Only apply global device when plate representation is selected
            // Otherwise make sure has device
            if (current_name && representation_selector.val() === 'plate') {
                $(this).find('input[name$="device"]').val(device_selector.val());
            }
        });
    });

    // Charting business
    // Load core chart package
    // Only bother if charts exist
    var charts = $('#charts');

    if (charts[0]) {
        google.charts.load('current', {'packages':['corechart']});
        // Set the callback
        google.charts.setOnLoadCallback(get_readouts);

        // Name for the charts for binding events etc
        var charts_name = 'charts';

        window.GROUPING.refresh_function = get_readouts;

        function get_readouts() {
            var data = {
                // TODO TODO TODO CHANGE CALL
                call: 'fetch_data_points',
                matrix: matrix_id,
                criteria: JSON.stringify(window.GROUPING.get_grouping_filtering()),
                post_filter: JSON.stringify(window.GROUPING.current_post_filter),
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            };

            var options = window.CHARTS.prepare_chart_options(charts_name);

            data = $.extend(data, options);

            // Show spinner
            window.spinner.spin(
                document.getElementById("spinner")
            );

            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: data,
                success: function (json) {
                    // Stop spinner
                    window.spinner.stop();

                    window.CHARTS.prepare_side_by_side_charts(json, charts_name);
                    window.CHARTS.make_charts(json, charts_name);

                    // Recalculate responsive and fixed headers
                    $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
                    $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
                },
                error: function (xhr, errmsg, err) {
                    // Stop spinner
                    window.spinner.stop();

                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }

        // Setup triggers
        $('#' + charts_name + 'chart_options').find('input').change(function() {
            get_readouts();
        });
    }
});
