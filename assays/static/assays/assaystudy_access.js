$(document).ready(function() {
    let add_all_buttons = $('[data-horizontal-filter-action="all_right"]');
    let add_buttons = $('[data-horizontal-filter-action="current_right"]');
    let remove_all_buttons = $('[data-horizontal-filter-action="all_left"]');
    let remove_buttons = $('[data-horizontal-filter-action="current_left"]');

    function populate_selection_boxes(field_id) {
        let unselected = $('#id_left_' + field_id);
        let selected =$('#id_right_' + field_id);

        unselected.empty();
        selected.empty();

        $('#id_' + field_id).find('option').each(function() {
            var clone = $(this).clone().prop('selected', false);
            if ($(this).prop('selected')) {
                selected.append(clone);
            }
            else {
                unselected.append(clone);
            }
        });
    }

    // Not optimal
    add_all_buttons.click(function() {
        $('#id_' + $(this).attr('data-field')).find('option').prop('selected', true);
        populate_selection_boxes($(this).attr('data-field'));
    });

    remove_all_buttons.click(function() {
        $('#id_' + $(this).attr('data-field')).prop('selected', false);
        populate_selection_boxes($(this).attr('data-field'));
    });

    add_buttons.click(function() {
        let parent_field = $('#id_' + $(this).attr('data-field'));
        $('#id_left_' + $(this).attr('data-field')).find('option:selected').each(function() {
            parent_field.find('option[value="' + this.value + '"]').prop('selected', true);
        });

        populate_selection_boxes($(this).attr('data-field'));
    });

    remove_buttons.click(function() {
        let parent_field = $('#id_' + $(this).attr('data-field'));
        $('#id_left_' + $(this).attr('data-field')).find('option:selected').each(function() {
            parent_field.find('option[value="' + this.value + '"]').prop('selected', false);
        });

        populate_selection_boxes($(this).attr('data-field'));
    });

    // CRUDE
    add_all_buttons.each(function() {
        populate_selection_boxes($(this).attr('data-field'));
    });

    // var access_groups_selector = $('#id_access_groups');
    // var hidden_from = $('#id_hidden_from');
    // var visible_to = $('#id_visible_to');

    // var access_group_section = $('#access_group_section');

    // var restricted_selector = $('#id_restricted');
    // var restricted_radio = $('#id_restricted_radio');
    // var unrestricted_radio = $('#id_unrestricted_radio');

    // var access_group_buttons = $('#access_group_buttons');
    // var add_all_button= $('#id_all_right');
    // var add_button = $('#id_right');
    // var remove_all_button = $('#id_all_left');
    // var remove_button = $('#id_left');

    // function populate_selection_boxes() {
    //     hidden_from.empty();
    //     visible_to.empty();

    //     access_groups_selector.find('option').each(function() {
    //         var clone = $(this).clone().prop('selected', false);
    //         if ($(this).prop('selected')) {
    //             visible_to.append(clone);
    //         }
    //         else {
    //             hidden_from.append(clone);
    //         }
    //     });
    // }

    // add_all_button.click(function() {
    //     access_groups_selector.find('option').prop('selected', true);
    //     populate_selection_boxes();
    // });

    // remove_all_button.click(function() {
    //     access_groups_selector.find('option').prop('selected', false);
    //     populate_selection_boxes();
    // });

    // add_button.click(function() {
    //     hidden_from.find('option:selected').each(function() {
    //         access_groups_selector.find('option[value="' + this.value + '"]').prop('selected', true);
    //     });

    //     populate_selection_boxes();
    // });

    // remove_button.click(function() {
    //     visible_to.find('option:selected').each(function() {
    //         access_groups_selector.find('option[value="' + this.value + '"]').prop('selected', false);
    //     });

    //     populate_selection_boxes();
    // });

    // populate_selection_boxes();

    // if (restricted_selector.prop('checked')) {
    //     restricted_radio.prop('checked', true);
    //     access_group_section.show('fast');
    //     // $('select').prop('disabled', false);
    //     // access_group_buttons.css('visibility', 'visible');
    // }
    // else {
    //     unrestricted_radio.prop('checked', true);
    //     access_group_section.hide('fast');
    //     // $('select').prop('disabled', true);
    //     // access_group_buttons.css('visibility', 'hidden');
    // }

    // restricted_radio.click(function() {
    //     restricted_selector.prop('checked', true);
    //     access_group_section.show('fast');
    //     // $('select').prop('disabled', false);
    //     // access_group_buttons.css('visibility', 'visible');
    // });

    // unrestricted_radio.click(function() {
    //     restricted_selector.prop('checked', false);
    //     access_group_section.hide('fast');
    //     // $('select').prop('disabled', true);
    //     // access_group_buttons.css('visibility', 'hidden');
    // });
});
