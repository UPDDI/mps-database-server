$(document).ready(function () {
    var group_selector = $('#id_group');
    var center_name_selector = $('#center_name');
    var image_selector = $('#id_image');
    var image_display_selector = $('#image_display');
    var current_image_display_selector = $('#current_display');

    function get_center_id() {
        if (group_selector.val()) {
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_center_id',
                    id: group_selector.val(),
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                success: function (json) {
                    center_name_selector.html(json.name + ' (' + json.center_id + ')');
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
        else {
            center_name_selector.html('');
        }
    }

    // Need to have condition for adding vs. changing data
    get_center_id();

    // Needs an AJAX call to get centerID
    group_selector.change(function (evt) {
        get_center_id();
    });

    // Change image preview as necessary
    image_selector.change(function() {
        IMAGES.display_image(image_selector, image_display_selector, current_image_display_selector);
    });

    // AJAX to get Category, Target, Method associations
    var category_to_targets = {};
    var target_to_methods = {};

    // Avoid magic strings like this
    var assay_table_inline_string = 'assaystudyassay_set';
    var study_assay_table = $('#assaystudyassay_set-group');

    // Uhh...
    var default_dropdown = [{'value': "", 'text': '---------'}];

    function apply_filters_to_all_rows() {
        // THE NUMBER OF ROWS CAN CHANGE
        study_assay_table.find('.inline').each(function(index) {
            apply_category_to_row(index);
        });
    }

    // NOT VERY DRY
    function apply_category_to_row(current_row_id) {
        var current_category = $('#id_' + assay_table_inline_string + '-' + current_row_id + '-category');
        var current_category_id = current_category.val();

        var current_target = $('#id_' + assay_table_inline_string + '-' + current_row_id + '-target');
        var current_target_id = current_target.val();

        var possible_targets = category_to_targets[current_category_id];
        current_target[0].selectize.clear();
        current_target[0].selectize.clearOptions();
        if (possible_targets) {
            current_target[0].selectize.addOption(possible_targets);
            if (current_target_id) {
                current_target[0].selectize.setValue(current_target_id);
            }
        }
        else {
            current_target[0].selectize.addOption(default_dropdown);
        }

        apply_target_to_row(current_row_id, current_target_id);
    }

    function apply_target_to_row(current_row_id, current_target_id) {
        var current_method = $('#id_' + assay_table_inline_string + '-' + current_row_id + '-method');
        var current_method_id = current_method.val();

        var possible_methods = target_to_methods[current_target_id];
        current_method[0].selectize.clear();
        current_method[0].selectize.clearOptions();
        if (possible_methods) {
            current_method[0].selectize.addOption(possible_methods);
            if (current_method_id) {
                current_method[0].selectize.setValue(current_method_id);
            }
        }
        else {
            current_method[0].selectize.addOption(default_dropdown);
        }
    }

    $.ajax({
        url: "/assays_ajax/",
        type: "POST",
        dataType: "json",
        data: {
            call: 'fetch_assay_associations',
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        },
    })
    .done(function (json) {
        category_to_targets = json.category_to_targets;
        target_to_methods = json.target_to_methods;

        apply_filters_to_all_rows();
    })
    .fail(function (xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText);
    });

    // MAKE SURE ALL INLINES FOR ASSAYS ARE SELECTED AND NOTHING ELSE, PLEASE
    // IDEALLY WOULD NOT TRIGGER ON UNIT CHANGE
    $(document).on('change', '.inline select[name$="-category"]', function() {
        var current_row_id = $(this).parent().parent().attr('id').split('-')[1];
        apply_category_to_row(current_row_id);
    });

    $(document).on('change', '.inline select[name$="-target"]', function() {
        var current_row_id = $(this).parent().parent().attr('id').split('-')[1];

        apply_target_to_row(current_row_id, $(this).val());
    });

    // BAD TRIGGER
    $('#add_button-assaystudyassay_set').click(function() {
        apply_filters_to_all_rows();
    });
});
