// TODO WE ARE NOW CALLING THEM GROUPS AGAIN, I GUESS
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
            plates: [],
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

    function make_row(index, chip) {
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

        new_row.append(
            index_td,
            name_td,
            group_td
        );

        // Set values
        new_row.find('.name').val(chip['name']);

        new_row.find('.group').val(chip['group_id']);;
        // new_row.find('.group')[0].selectize.setValue(chip['group']);

        chips_table_body.append(new_row);
    }

    function build_chip_table() {
        $.each(chips, function(index, chip) {
            make_row(index, chip);
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
        series_data[chips[$(this).attr('data-index')]['group_id']]['number_of_items'] -= 1;

        // Modify the chip group
        chips[$(this).attr('data-index')]['group_id'] = $(this).val();
        replace_series_data();
    });
});
