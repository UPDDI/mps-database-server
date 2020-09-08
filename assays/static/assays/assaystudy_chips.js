// TODO WE ARE NOW CALLING THEM GROUPS AGAIN, I GUESS
$(document).ready(function () {
    // Make the difference table
    window.GROUPS.make_difference_table('chip');
    // NOTE THAT THIS IS RESTRICTED TO CHIPS
    // window.GROUPS.make_difference_table('chip');

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

    console.log(full_series_data);

    // TODO WE NEED TO SPLIT OUT MATRIX ITEM DATA
    var chips = full_series_data.chips;

    // SERIES DATA
    var series_data = full_series_data.series_data;

    var chips_table = $('#chips_table');
    var chips_table_body = chips_table.find('tbody');

    var chip_name_reference = $('#id_chip_name');
    var chip_group_reference = $('#id_chip_group');

    // CONTRIVED: GET VALID GROUPS
    // TEMPORARY ACQUISITION OF GROUPS
    // THIS NEEDS TO BE REPLACED ASAP
    $.each(series_data, function(index) {
        var new_option = null;
        if (series_data[index].device_type === 'chip') {
            if (series_data[index].name) {
                new_option = new Option(series_data[index].name, index)
            }
            else {
                new_option = new Option('Group ' + (index + 1), index)
            }
            chip_group_reference.append(
                new_option
            );
        }
    });

    // Swaps out the data we are saving to the form
    // TODO TODO TODO XXX REVISE TO USE ALL_DATA
    function replace_series_data() {
        series_data_selector.val(JSON.stringify(full_series_data));
    }

    // Needed for renaming chips with the popups
    // Modified version from Matrix Add
    function get_incremented_name(index, initial_value, first_half, second_half, original_name) {
        var incremented_value = index + initial_value;
        incremented_value += '';

        while (first_half.length + second_half.length + incremented_value.length < original_name.length) {
            incremented_value = '0' + incremented_value;
        }

        var value = first_half + incremented_value + second_half;

        return value;
    }

    function chip_style_name_incrementer(original_name, example_section, apply, group) {
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

        // When we want to apply
        if (apply) {
            // Iterate over all chips
            // If there is a group, passed, then use it for comparison
            // Note that "true_index" is necessary for by group
            var true_index = 0;
            $.each(chips, function(index, chip) {
                // Check the group if necessary
                // Using group_index may be dangerous??
                // (It is probably fine, but an ID is maybe more specific)
                if (!group || (group && chip['group_index'] == group)) {
                    var current_name = get_incremented_name(true_index, initial_value, first_half, second_half, original_name);

                    // Change the data
                    chip['name'] = current_name;

                    true_index++;
                }
            });

            // NEED TO RESET THE INPUT FIELD
            replace_series_data();

            // Just rebuild the table
            // I *could* just change the input, but this is easier
            build_chip_table();
        }
        // Otherwise, we just change the example
        // NOTE: this would occur from a change trigger on the respective input field
        else {
            var example_strings = [];

            // We have to count the number of chips, I guess
            // A little clumsy, but you know
            var number_of_chips = 0;
            $.each(chips, function(index, chip) {
                // Check the group if necessary
                // Using group_index may be dangerous??
                // (It is probably fine, but an ID is maybe more specific)
                if (!group || (group && chip['group_index'] == group)) {
                    number_of_chips++;
                }
            });

            // Three examples for the moment
            var terminate_point = 3;

            if (terminate_point > number_of_chips) {
                terminate_point = number_of_chips;
            }

            for(var i=0; i < terminate_point; i++) {
                example_strings.push(
                    get_incremented_name(i, initial_value, first_half, second_half, original_name)
                );
            }

            // If the termination is larger, then use it in the example
            if (number_of_chips - 1 > 2) {
                example_strings.push(
                    '... ' + get_incremented_name(number_of_chips - 1, initial_value, first_half, second_half, original_name)
                );
            }

            example_section.text(
                example_strings.join(', ')
            );
        }
    }

    // Make the naming popups
    var rename_chips_sequentially_popup = $('#rename_chips_sequentially_popup');
    rename_chips_sequentially_popup.dialog({
        width: 1000,
        height: 250,
        modal: true,
        buttons: [
        {
            text: 'Apply',
            click: function() {
                // TODO APPLY THE NAMES
                chip_style_name_incrementer($('#id_rename_chips_sequentially').val(), $('#rename_chips_sequentially_example'), true);

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
    rename_chips_sequentially_popup.removeProp('hidden');

    // Populate a table for by group naming?
    // For the moment, instead, I will populate a dropdown
    var group_to_rename = $('#id_group_to_rename');
    chip_group_reference.find('option').each(function() {
        group_to_rename.append(
            $(this).clone()
        );
    });

    var rename_chips_by_group_popup = $('#rename_chips_by_group_popup');
    rename_chips_by_group_popup.dialog({
        width: 1000,
        height: 300,
        modal: true,
        buttons: [
        {
            text: 'Apply',
            click: function() {
                // TODO APPLY THE NAMES
                // BE SURE TO APPLY THE GROUP
                // *THEORETICALLY* there will always be a group
                chip_style_name_incrementer($('#id_rename_chips_by_group').val(), $('#rename_chips_by_group_example'), true, $('#id_group_to_rename').val());

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
    rename_chips_by_group_popup.removeProp('hidden');

    function make_row(index, chip) {
        // Previously just used the index
        // var current_stored_tds = window.GROUPS.difference_table_displays[chip['group_index']];

        var current_group_name = series_data[Math.floor(chip['group_index'])].name;

        // ASSUMES UNIQUE NAMES
        var current_stored_tds = window.GROUPS.difference_table_displays[current_group_name];

        // console.log(index, chip);
        // console.log(window.GROUPS.difference_table_displays);

        var new_row = $('<tr>');

        var index_td = $('<td>').html(index + 1);
        var name_td = $('<td>').append(
            chip_name_reference
                .clone()
                .removeAttr('id')
                .addClass('name')
                .attr('data-index', index)
        );
        var group_td = $('<td>').append(
            chip_group_reference
                .clone()
                .removeAttr('id')
                .addClass('group')
                .attr('data-index', index)
        );

        // TODO: DIFFERENCE TABLE STUFF
        var model_td = current_stored_tds['model'].clone();
        var test_type_td = current_stored_tds['test_type'].clone();
        var cell_td = current_stored_tds['cell'].clone();
        var compound_td = current_stored_tds['compound'].clone();
        var setting_td = current_stored_tds['setting'].clone();

        new_row.append(
            index_td,
            name_td,
            group_td,
            model_td,
            test_type_td,
            cell_td,
            compound_td,
            setting_td
        );

        // Set values
        new_row.find('.name').val(chip['name']);

        new_row.find('.group').val(chip['group_index']);;
        // new_row.find('.group')[0].selectize.setValue(chip['group']);

        chips_table_body.append(new_row);
    }

    function build_chip_table() {
        chips_table_body.empty();

        $.each(chips, function(index, chip) {
            make_row(index, chip);
        });

        // Determine row hiding
        var columns_to_check = [
            'model',
            'test_type',
            'cell',
            'compound',
            'setting'
        ];

        $.each(columns_to_check, function(index, key) {
            if (window.GROUPS.hidden_columns[key]) {
                // Be careful with magic strings!
                // (And magic numbers for the index offset)
                $('#chips_table td:nth-child(' + (index + 4) + '), #chips_table th:nth-child(' + (index + 4) + ')').hide();
            }
        });
    }

    build_chip_table();

    $(document).on('change', '.name', function() {
        // Modify the chip name
        chips[$(this).attr('data-index')]['name'] = $(this).val();
        replace_series_data();
    });

    $(document).on('change', '.group', function() {
        // Add to new group
        series_data[$(this).val()]['number_of_items'] += 1;
        // Remove from old TODO: SUBJECT TO CHANGE
        series_data[chips[$(this).attr('data-index')]['group_index']]['number_of_items'] -= 1;

        // Modify the chip group
        chips[$(this).attr('data-index')]['group_index'] = $(this).val();

        // MODIFY THE ID BECAUSE THAT IS THE IMPORTANT ONE
        chips[$(this).attr('data-index')]['group_id'] = parseInt(series_data[$(this).val()].id);

        replace_series_data();

        // Rebuild the table
        build_chip_table();
    });

    // Simple triggers for difference popups
    $('#spawn_cell_full_contents_popup_duplicate').click(function() {
        $('#spawn_cell_full_contents_popup').trigger('click');
    });

    $('#spawn_compound_full_contents_popup_duplicate').click(function() {
        $('#spawn_compound_full_contents_popup').trigger('click');
    });

    $('#spawn_setting_full_contents_popup_duplicate').click(function() {
        $('#spawn_setting_full_contents_popup').trigger('click');
    });

    // Triggers for naming popups
    $('#rename_chips_sequentially_button').click(function() {
        rename_chips_sequentially_popup.dialog('open');
    });

    $('#rename_chips_by_group_button').click(function() {
        rename_chips_by_group_popup.dialog('open');
    });

    // Triggers for example names
    // Triggers immediately in case of stored form values
    // Input is maybe an excessive trigger? Means no click away though...
    $('#id_rename_chips_sequentially').on('input', function() {
        // Group is irrelevant here
        chip_style_name_incrementer($('#id_rename_chips_sequentially').val(), $('#rename_chips_sequentially_example'), false);
    }).trigger('input');

    $('#id_rename_chips_by_group').on('input', function() {
        // NOTE: Doesn't do anything with the group just yet
        // TODO SHOW A WARNING IF THE GROUP IS EMPTY
        chip_style_name_incrementer($('#id_rename_chips_by_group').val(), $('#rename_chips_by_group_example'), false, $('#id_group_to_rename').val());
    }).trigger('input');

    // NEED THIS FOR CHANGING THE GROUP: CHANGES THE PREVIEW IN POPUP FOR GROUPS
    $('#id_group_to_rename').on('change', function() {
        // NOTE: Doesn't do anything with the group just yet
        // TODO SHOW A WARNING IF THE GROUP IS EMPTY
        chip_style_name_incrementer($('#id_rename_chips_by_group').val(), $('#rename_chips_by_group_example'), false, $(this).val());
    }).trigger('change');
});
