$(document).ready(function () {
    var setup_data_selector = $('#id_setup_data');

    // FULL DATA
    var current_setup_data = [];

    // FOR ADD INTERFACE ONLY
    // ERRORS
    var setup_table_errors_selector = $('#setup_table_errors').find('.errorlist');

    // More selectors
    var study_setup_table_section = $('#study_setup_table_section');

    var table_errors = {}

    setup_table_errors_selector.find('li').each(function() {
        var current_text = $(this).text();
        var split_info = current_text.split('-')[0];
        var error_message = current_text.split('-').slice(1).join('-');
        table_errors[split_info] = error_message;
    });

    // FOR EDITING INTERFACE ONLY
    var form_slated_for_deletion = [];

    // ODD, NOT GOOD
    var organ_model = $('#id_organ_model');
    var protocol = $('#id_organ_model_protocol');

    var current_protocol = protocol.val();

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
        if(!current_setup[prefix]) {
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
                var current_data = $.extend(true, {}, current_setup_data[current_row_index][current_prefix][current_column_index]);

                var this_popup = $(this);

                this_popup.find('input').each(function() {
                    if ($(this).attr('name')) {
                        $(this).val(current_data[$(this).attr('name').replace(current_prefix + '_', '')]);
                    }
                });

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
                    // ACTUALLY MAKE THE CHANGE TO THE RESPECTIVE ENTITY
                    // TODO TODO TODO
                    var current_data = {};

                    $(this).find('input').each(function() {
                        if ($(this).attr('name')) {
                            current_data[$(this).attr('name').replace(current_prefix + '_', '')] = $(this).val();
                        }
                    });

                    $(this).find('select').each(function() {
                        if ($(this).attr('name')) {
                            current_data[$(this).attr('name').replace(current_prefix + '_', '') + '_id'] = $(this).val();
                        }
                    });

                    // SLOPPY
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
                    if ($(this).find('input[name="' + prefix + '_cell_sample"]')[0]) {
                        current_data['cell_sample_id'] = $(this).find('input[name="' + prefix + '_cell_sample"]').val();
                        delete current_data['cell_sample'];
                    }

                    modify_setup_data(current_prefix, current_data, current_row_index, current_column_index);

                    var html_contents = get_content_display(current_prefix, current_row_index, current_column_index, current_data, true);

                    $('a[data-edit-button="true"][data-row="' + current_row_index +'"][data-column="' + current_column_index +'"][data-prefix="' + current_prefix + '"]').parent().html(html_contents);

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
        current_dialog.removeProp('hidden');
    });

    function reset_current_setup(reset_data) {
        current_setup = {};

        // MAKE SURE ALL PREFIXES ARE PRESENT
        $.each(prefixes, function(index, prefix) {
            if(!current_setup[prefix]) {
              current_setup[prefix] = [];
            }
        });

        if (reset_data) {
            current_setup_data = [];
        }
    }

    function get_display_for_field(field_name, field_value, prefix) {
        // NOTE: SPECIAL EXCEPTION FOR CELL SAMPLES
        if (field_name === 'cell_sample') {
            // TODO VERY POORLY DONE
            // return $('#' + 'cell_sample_' + field_value).attr('data-name');
            // Global here is a little sloppy, but should always succeed
            return window.CELLS.cell_sample_id_to_label[field_value];
        }
        else {
            // Ideally, this would be cached in an object or something
            var origin = $('#id_' + prefix + '_' + field_name);

            // Get the select display if select
            if (origin.prop('tagName') === 'SELECT') {
                // Convert to integer if possible, thanks
                var possible_int = Math.floor(field_value);
                if (possible_int) {
                    return origin[0].selectize.options[possible_int].text;
                }
                else {
                    return origin[0].selectize.options[field_value].text;
                }
                // THIS IS BROKEN, FOR PRE-SELECTIZE ERA
                // return origin.find('option[value="' + field_value + '"]').text()
            }
            // Just display the thing if there is an origin
            else if (origin[0]) {
                return field_value;
            }
            // Give back null to indicate this should not be displayed
            else {
                return null;
            }
        }
    }

    // TODO NEEDS MAJOR REVISION
    function get_content_display(prefix, row_index, column_index, content, editable) {
        var html_contents = [];

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
                    var field_display = get_display_for_field(field_name, value, prefix);
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

    var number_of_columns = {
        'cell': 0,
        'compound': 0,
        'setting': 0,
    };

    // Table vars
    var study_setup_table = $('#study_setup_table');
    var study_setup_head = study_setup_table.find('thead').find('tr');
    var study_setup_body = study_setup_table.find('tbody');

    // PREVIEW
    var study_setup_table_preview = $('#study_setup_table_preview');

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

    function replace_setup_data() {
        setup_data_selector.val(JSON.stringify(current_setup_data));
    }

    function modify_setup_data(prefix, content, setup_index, object_index) {
        if (object_index) {
            current_setup_data[setup_index][prefix][object_index] = $.extend(true, {}, content);
        }
        else {
            current_setup_data[setup_index][prefix] = content;
        }

        setup_data_selector.val(JSON.stringify(current_setup_data));
    }

    function spawn_column(prefix) {
        var column_index = number_of_columns[prefix];
        // UGLY
        study_setup_head.find('.' + prefix + '_start').last().after('<th class="new_column ' + prefix + '_start' + '">' + prefix[0].toUpperCase() + prefix.slice(1) + ' ' + (column_index + 1) + create_delete_button(prefix, column_index) +'</th>');

        // ADD TO EXISTING ROWS AS EMPTY
        study_setup_body.find('tr').each(function(row_index) {
            $(this).find('.' + prefix + '_start').last().after('<td class="' + prefix + '_start' + '">' + create_edit_button(prefix, row_index, column_index) + '</td>', false);
        });

        number_of_columns[prefix] += 1;
    }

    // JUST USES DEFAULT PROTOCOL FOR NOW
    function spawn_row(setup_to_use, add_new_row) {
        if (!setup_to_use) {
            setup_to_use = current_setup;
        }

        var new_row = $('<tr>');

        var row_index = study_setup_body.find('tr').length;

        var buttons_to_add = '';
        buttons_to_add = create_clone_button(row_index) + create_delete_button('row', row_index);
        new_row.append(
            $('<td>').html(
                '<div class="no-wrap">' + buttons_to_add + '</div>'
            ).append(
                $('<strong>').text('Series ' + (row_index + 1))
            )
        );

        // SLOPPY, BAD
        // var new_td = $('<td>').html(
        //     '<div class="error-message-section error-display important-display"></div>'
        // );

        // new_row.append(
        //     new_td
        // );

        // SLOPPY
        var organ_model_input = $('#id_organ_model_full')
            .clone()
            .removeAttr('id')
            .attr('name', 'organ_model')
            .attr('data-row', row_index)
            .addClass('organ-model');

        // SLOPPY
        organ_model_input.attr('required', 'required');

        new_row.append(
            $('<td>').append(organ_model_input).append(
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

        organ_model_input.selectize();

        // SLOPPY
        var test_type_input = $('#id_test_type')
            .clone()
            .removeAttr('id')
            .attr('data-row', row_index)
            .addClass('test-type');

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

        new_row.find('.organ-model')[0].selectize.setValue(setup_to_use['organ_model_id']);
        new_row.find('.test-type').val(setup_to_use['test_type']);

        study_setup_body.append(new_row);

        if (add_new_row) {
            current_setup_data.push(
                $.extend(true, {}, setup_to_use)
            );
        }

        setup_data_selector.val(JSON.stringify(current_setup_data));
    }

    $(document).on('change', '.test-type', function() {
        modify_setup_data('test_type', $(this).val(), $(this).attr('data-row'));
    });

    $(document).on('change', '.organ-model', function() {
        modify_setup_data('organ_model_id', $(this).val(), $(this).attr('data-row'));
    });

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
        $.each(current_setup_data, function(index, current_content) {
            current_content[current_prefix].splice(current_column_index, 1);
        });

        number_of_columns[current_prefix] -= 1;

        rebuild_table();
    });

    // NOT ALLOWED IN EDIT?
    $(document).on('click', 'a[data-clone-row-button="true"]', function() {
        current_row_index = Math.floor($(this).attr('data-row'));
        spawn_row(current_setup_data[current_row_index], true);

        // MAKE SURE HIDDEN COLUMNS ARE ADHERED TO
        change_matrix_visibility();
    });

    // NOT ALLOWED IN EDIT?
    $(document).on('click', 'a[data-delete-row-button="true"]', function() {
        current_row_index = Math.floor($(this).attr('data-row'));

        // JUST FLAT OUT DELETE THE ROW
        current_setup_data.splice(current_row_index, 1);

        rebuild_table();
    });

    $(document).on('click', '.subform-delete', function() {
        current_row_index = Math.floor($(this).attr('data-row'));
        current_column_index = Math.floor($(this).attr('data-column'));
        current_prefix = $(this).attr('data-prefix');

        // DELETE THE DATA HERE
        current_setup_data[current_row_index][current_prefix][current_column_index] = {};

        rebuild_table();
    });

    $(document).on('click', '.subform-edit', function() {
        // Chaining parents this way is foolish
        $(this).parent().parent().parent().find('a[data-edit-button="true"]').trigger('click');
    });

    $('a[data-add-new-button="true"]').click(function() {
        spawn_column($(this).attr('data-prefix'));
    });

    $('#add_group_button').click(function() {
        spawn_row(null, true);
        // MAKE SURE HIDDEN COLUMNS ARE ADHERED TO
        change_matrix_visibility();
    });

    // SLOPPY: PLEASE REVISE
    // Triggers for hiding elements
    function change_matrix_visibility() {
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

    $('.visibility-checkbox').change(change_matrix_visibility);
    change_matrix_visibility();

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

        change_matrix_visibility();
    }

    $('#show_details').change(show_hide_full_details);
    show_hide_full_details();

    function set_new_protocol(is_new) {
        if (is_new) {
            // Set organ_model_id
            current_setup_data[current_setup_index]['organ_model_id'] = organ_model.val();
        }

        if (protocol.val() && protocol.val() != current_protocol || protocol.val() && !Object.keys(current_setup).length) {
            // Start SPINNING
            window.spinner.spin(
                document.getElementById("spinner")
            );

            // Swap to new protocol
            current_protocol = protocol.val();

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

                    // current_setup_data[current_setup_index] = $.extend(true, {}, json);

                    if (is_new) {
                        // MAKE SURE ALL PREFIXES ARE PRESENT
                        $.each(prefixes, function(index, prefix) {
                            if (json[prefix]) {
                                // Slow, but rare operation
                                current_setup_data[current_setup_index][prefix] = JSON.parse(JSON.stringify(json[prefix]));
                            }
                        });

                        // FORCE INITIAL TO BE CONTROL
                        // current_setup_data[current_setup_index]['test_type'] = 'control';

                        // console.log(current_setup_data);

                        rebuild_table();
                    }
                    // Contrived make preview
                    else {
                        study_setup_table_preview.empty();
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

                        study_setup_table_preview.append(new_row);
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
                rebuild_table();
            }
            else {
                study_setup_table_preview.empty();
            }
        }
    }

    function rebuild_table() {
        // GET RID OF ANYTHING IN THE TABLE
        study_setup_head.find('.new_column').remove();
        study_setup_body.empty();

        number_of_columns = {
            'cell': 0,
            'compound': 0,
            'setting': 0,
        };

        if (current_setup_data.length) {
            $.each(current_setup_data, function(index, content) {
                spawn_row(content, false);
            });
        }
        else {
            spawn_row(null, true);
        }

        replace_setup_data();

        // MAKE SURE HIDDEN COLUMNS ARE ADHERED TO
        change_matrix_visibility();

        // Show errors if necessary (ADD)
        if (Object.keys(table_errors).length) {
            $.each(table_errors, function(current_id, error) {
                var split_info = current_id.split('|');
                var prefix = split_info[0];
                var row_index = split_info[1];
                var column_index = split_info[2];
                var field = split_info[3];
                var current_bubble = $('.subform-delete[data-prefix="' + prefix +'"][data-row="' + row_index + '"][data-column="' + column_index + '"]').parent().parent();
                current_bubble.find('.error-message-section').append(empty_error_html.clone().text(field + ': ' + error));
            });
        }
    }

    // TESTING
    rebuild_table();

    var version_dialog = $('#version_dialog');
    version_dialog.dialog({
        width: 900,
        height: 500,
        open: function() {
            $.ui.dialog.prototype.options.open();
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
    version_dialog.removeProp('hidden');

    $(document).on('click', '.query-versions', function() {
        current_setup_index = $(this).attr('data-row-index');
        current_setup = current_setup_data[current_setup_index];
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

    // MATRIX HANDLING
    // START

    // Alias for the matrix selector
    var matrix_table_selector = $('#matrix_table');
    var matrix_body_selector = $('#matrix_body');

    // Alias for device selector
    var device_selector = $('#id_device');
    // Alias for representation selector
    var representation_selector = $('#id_representation');
    // Alias for number of rows/columns
    var number_of_items_selector = $('#id_number_of_items');
    var number_of_rows_selector = $('#id_number_of_rows');
    var number_of_columns_selector = $('#id_number_of_columns');

    var item_display_class = '.matrix_item-td';

    // Allows the matrix_table to have the draggable JQuery UI element
    matrix_table_selector.selectable({
        // SUBJECT TO CHANGE: WARNING!
        filter: item_display_class,
        distance: 1,
        cancel: '.btn-xs',
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

    // To highlight and un-highlight rows/columns
    function highlight_row() {
        $('#row_' + $(this).attr('data-row-to-apply')).find('td').addClass('ui-selecting');
    }

    function un_highlight_row() {
        $('#row_' + $(this).attr('data-row-to-apply')).find('td').removeClass('ui-selecting');
    }

    function highlight_column() {
        $('td[data-column-index="' + $(this).attr('data-column-to-apply') + '"]').addClass('ui-selecting');
    }

    function un_highlight_column() {
        $('td[data-column-index="' + $(this).attr('data-column-to-apply') + '"]').removeClass('ui-selecting');
    }


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

            for (var column_index=starting_index_for_matrix; column_index < number_of_columns; column_index++) {
                var item_id = item_prefix + '_' + row_index + '_' + column_index;
                var new_cell = null;

                // If this is an apply to row
                if (column_index === -1) {
                    if (row_index === -1) {
                        new_cell = $('<td>')
                            .css('width', '1px')
                            .css('white-space', 'no-wrap')
                    }
                    else {
                        new_cell = $('<td>')
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
                    new_cell = $('<td>')
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
                    new_cell = empty_item_html
                        .clone()
                        .attr('id', item_id)
                        .attr('data-row-index', row_index)
                        .attr('data-column-index', column_index)
                    ;
                }

                // Add
                current_row.append(new_cell);
            }

            matrix_body_selector.append(current_row);
        }
    };

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

            // SET DISPLAY AND VALUE HERE
        });
    }

    function programmatic_select(current_selection) {
        $('.ui-selected').not(current_selection).removeClass('ui-selected').addClass('ui-unselecting');

        current_selection.not('.ui-selected').addClass('ui-selecting');

        matrix_table_selector.selectable('refresh');

        matrix_table_selector.data('ui-selectable')._mouseStop(null);
    }

    function apply_action_to_all() {
        // $(item_display_class).addClass('ui-selected');
        programmatic_select($(item_display_class));
        matrix_add_content_to_selected();
    }

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
        // TODO

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
        }
        else if (!device_selector.val() || representation_selector.val() === 'plate') {
            device_selector.val('');
        }
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
});
