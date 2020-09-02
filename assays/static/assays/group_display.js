// TODO: Things like prefixes should be listed here to avoid repetition!
// Perhaps even selectors for things we know shouldn't change
// (Also should think of a better scheme for dependency injection)
// TODO: VERY SLOW FOR LARGE TABLES FOR A NUMBER OF REASONS
window.GROUPS = {
    make_difference_table: null,
    make_group_preview: null,
    difference_table_displays: {},
    // Indicates the hidden columns via object
    hidden_columns: {},
    get_display_for_field: null,
    convert_to_numeric_view: {
        value: true,
        density: true,
        concentration: true,
    },
};

$(document).ready(function () {
    // The different components of a setup
    var prefixes = [
        'cell',
        'compound',
        'setting',
    ];

    // For other things to compare
    var non_prefix_comparisons = [
        'organ_model_id',
        'organ_model_protocol_id',
        'test_type',
    ];

    // Array of values to convert to have commas etc.
    // var convert_to_numeric_view = {
    //     value: true,
    //     density: true,
    //     concentration: true,
    // };

    // TEMPORARY
    var series_data_selector = $('#id_series_data');

    // We need a variable to store the data that would go into a difference table
    // Tricky thing is, is this variable or isn't it?
    // We could have templates similar to the group displays...
    // Would they be controlled the same way? ie. would "Show Full Details" affect them?
    // Another complication is that we need displays that are mandatory (the compound and the units etc.) but sometimes the divergence may not be in these mandatory fields! For instance, the addition location could be divergent
    // People will be unhappy if small divergences, like the addition location, are not made clear, but the displays would be unintelligible without the mandatory sections (compound, cell sample, etc.)
    // Having a by field difference is possible, it just gets messy

    // For the moment, we will make some number of templates in the component_displays include and use those for the difference table
    // After all, there are instances where the stringification of cells will be the same but the samples in-and-of-themselves are different (one would only know easily because we have access to the ID)

    // For the moment, the difference table content is stored as an array
    // Each index is a group
    // Each group's data is likewise an array, each index being a column
    // var difference_table_content = [];

    // This may be a good file to make these shared?
    // Prefixes
    // If I am going to use these, they should be ALL CAPS to indicate global status
    var item_prefix = 'matrix_item';
    var cell_prefix = 'cell';
    var setting_prefix = 'setting';
    var compound_prefix = 'compound';

    // DISPLAYS
    // JS ACCEPTS STRING LITERALS IN OBJECT INITIALIZATION
    var empty_difference_html = {};
    var empty_item_difference_html = $('#empty_matrix_item_difference_html').children();
    var empty_compound_difference_html = $('#empty_compound_difference_html');
    var empty_cell_difference_html = $('#empty_cell_difference_html');
    var empty_setting_difference_html = $('#empty_setting_difference_html');
    empty_difference_html[item_prefix] = empty_item_difference_html;
    empty_difference_html[compound_prefix] = empty_compound_difference_html;
    empty_difference_html[cell_prefix] = empty_cell_difference_html;
    empty_difference_html[setting_prefix] = empty_setting_difference_html;

    // Clumsy selectors (need these to get names from ids)
    var test_type = $('#id_test_type');
    var organ_model_full = $('#id_organ_model_full');
    var organ_model_protocol_full = $('#id_organ_model_protocol_full');

    // WERE WE INTERESTED IN DISPLAYING THE DATA AS SEPARATE COLUMNS
    // We would also need to keep track of the number of columns of each prefix
    // Of course, this can diverge from the columns of the group table
    // We would determine this from the max diverges for each prefix
    // var number_of_columns = {
    //     'cell': 0,
    //     'compound': 0,
    //     'setting': 0,
    // };

    // Get a proper stringification of a group
    // TODO: REVISE
    // As an array
    // function stringify_group_contents(contents) {
    //     var stringification = [];

    //     for (var i=0;  i < contents.length; i++) {
    //         stringification[i] = JSON.stringify(contents[i]);
    //     }

    //     // We need to do this to deal with on-the-fly difference tables
    //     // Should just do a default string sort?
    //     stringification.sort();

    //     return stringification;
    // }

    // NOT DRY
    window.GROUPS.get_display_for_field = function(field_name, field_value, prefix) {
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
                    if (origin[0].selectize.options[field_value]) {
                        return origin[0].selectize.options[field_value].text;
                    }
                    // If the current selection is blank, return the empty string
                    else {
                        return '';
                    }
                }
                // THIS IS BROKEN, FOR PRE-SELECTIZE ERA
                // return origin.find('option[value="' + field_value + '"]').text()
            }
            else if (window.GROUPS.convert_to_numeric_view[field_name]) {
                var parsed_as_float = parseFloat(field_value);
                if (field_name !== 'value' || parsed_as_float) {
                    return parsed_as_float.toLocaleString();
                }
                else if (field_name === 'value') {
                    return field_value;
                }
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

    // Alias
    var get_display_for_field = window.GROUPS.get_display_for_field;

    // I could include iteration here rather than in the other loop
    // TODO NEEDS MAJOR REVISION
    function get_difference_display(prefix, content) {
        var html_contents = [];

        // Clone the empty_html for a starting point
        var new_display = empty_difference_html[prefix].clone();

        if (content && Object.keys(content).length) {
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
        // else {
        //     // Push empty otherwise?
        //     html_contents.push('');
        // }

        html_contents = html_contents.join('');

        return html_contents;
    }

    // Proposed alternative
    // This uses just a strict short hand
    // The consequence is that if a parameter like addition time diverges, one wouldn't know until they looked at the popup or the group table
    function get_shorthand_display(prefix, content) {

            // Just start with an empty div
            // var html_contents = $('<div>');
            var text_to_use = '';

            // Clone the empty_html for a starting point
            // var new_display = empty_difference_html[prefix].clone();

            if (content && Object.keys(content).length) {
                // Different handling per prefix
                if (prefix === 'cell') {
                    // MAKES ASSUMPTIONS ABOUT CELL SAMPLE FORMAT
                    // SPlit on paren to get origin and cell type (crude)
                    text_to_use = $.trim(get_display_for_field('cell_sample', content['cell_sample_id'], prefix).split('(')[0]);
                }
                else if (prefix === 'compound') {
                    text_to_use = $.trim(
                        [
                            get_display_for_field('compound', content['compound_id'], prefix),
                            get_display_for_field('concentration', content['concentration'], prefix),
                            get_display_for_field('concentration_unit', content['concentration_unit_id'], prefix)
                        ].join(' ')
                    );
                }
                else if (prefix === 'setting') {
                    text_to_use = $.trim(
                        [
                            get_display_for_field('setting', content['setting_id'], prefix),
                            get_display_for_field('value', content['value'], prefix),
                            get_display_for_field('unit', content['unit_id'], prefix)
                        ].join(' ')
                    );
                }

                text_to_use += ';';

                // html_contents.text(text_to_use + ';');
            }
            // else {
            //     // Push empty otherwise?
            //     html_contents.push('');
            // }

        // return html_contents[0].outerHTML;
        return text_to_use;
    }

    function stringify_group_contents(contents) {
        var stringification = {};

        // console.log(contents);

        if (!contents) {
            return stringification;
        }

        for (var i=0;  i < contents.length; i++) {
            // TODO  NOTE: This assumes nothing goofy about how the object gets populated!
            stringification[JSON.stringify(contents[i])] = i;
        }

        return stringification;
    }

    function get_text_display_for_field(field_name, value, prefix) {
        // I will need to think about invalid fields
        var field_name = field_name.replace('_id', '');
        if ((field_name !== 'addition_time' && field_name !== 'duration')) {
            return get_display_for_field(field_name, value, prefix);
        }
        // NOTE THIS ONLY HAPPENS WHEN IT IS NEEDED IN ADD PAGE
        else {
            var split_time = window.SPLIT_TIME.get_split_time(
                value
            );

            // $.each(split_time, function(time_name, time_value) {
            //     new_display.find('.' + prefix + '-' + field_name + '_' + time_name).html(time_value);
            // });

            // CRUDE
            // Should use double digits?
            return 'D ' + split_time['day'] + ' H ' + split_time['hour'] + ' M ' + split_time['minute'];
        }
    }

    function populate_popup_tables(relevant_group_data) {
        // For every prefix
        $.each(prefixes, function(prefix_index, prefix) {
            // The popup table in question
            var current_popup_table = $('#' + prefix + '_full_contents_popup_table');
            // The head
            var current_head = current_popup_table.find('thead');
            // The body
            var current_body = current_popup_table.find('tbody');

            // Run through the header to get the fields we need to compare and their order
            // The field points to a boolean that is false if it finds any divergences in the field
            var current_fields = [];

            // Get all of the fields from the table header (a little tricky, but makes sure we keep order)
            current_head.find('th').each(function() {
                if ($(this).attr('data-field')) {
                    current_fields.push($(this).attr('data-field'));
                }
            });

            // Clear the body
            current_body.empty();

            $.each(relevant_group_data, function(index, group) {
                var new_row = $('<tr>').append(
                    $('<td>').text(group['name'])
                );

                $.each(current_fields, function(field_index, current_field) {
                    var new_td = $('<td>');

                    if (group[prefix][0]) {
                        // Crude: determine if all the same
                        var all_the_same = true;
                        var value_to_compare = group[prefix][0][current_field];

                        // NOTE: We can't compare the first value if the first value is empty (eg. someone deleted "Cell 1")
                        // As a result, we need to find the first populated and SKIP all totally empty columns
                        $.each(group[prefix], function(content_index, content) {
                            if (content) {
                                value_to_compare = content[current_field];
                            }
                        });

                        $.each(group[prefix], function(content_index, content) {
                            // Don't bother with empties
                            if (Object.keys(content).length > 0 && content[current_field] !== value_to_compare) {
                                all_the_same = false;
                                // Break
                                return false;
                            }
                        });

                        if (all_the_same) {
                            new_td.append(
                                $('<div>').text(
                                    // Note added semicolon
                                    get_text_display_for_field(current_field, value_to_compare, prefix)
                                )
                            );
                        }
                        else {
                            $.each(group[prefix], function(content_index, content) {
                                // Don't bother with empties
                                if (Object.keys(content).length > 0) {
                                    new_td.append(
                                        $('<div>').text(
                                            // Note added semicolon
                                            get_text_display_for_field(current_field, content[current_field], prefix) + ';'
                                        )
                                    );
                                }
                            });
                        }
                    }

                    new_row.append(new_td);
                });

                current_body.append(new_row);
            });
        });
    }

    // Make the "difference table"
    // This determines whether any of the cells, compounds, or settings of the groups differ and shows a table depicting as much
    // NOTE: Depends on a particular element for table
    // NOTE: Depends on a particular input for data (contrived JSON)
    window.GROUPS.make_difference_table = function(restrict_to, organ_model_id) {
        // console.log("DIFFERENCE TABLE START");

        // We needs to know whether or not to show a column for a particular prefix
        var diverging_prefixes = {
            'cell': false,
            'compound': false,
            'setting': false,
            // These are called 'non_prefixes' above, should resolve naming convention
            'organ_model_id': false,
            'organ_model_protocol_id': false,
            'test_type': false,
        };

        // CONTRIVED FOR NOW: REPLACE WITH CACHED SELECTOR
        $('#difference_table').find('tbody').empty();

        // FULL DATA
        // TEMPORARY
        var full_series_data = JSON.parse(series_data_selector.val());
        var relevant_group_data = full_series_data.series_data;

        // For plate and chip difference tables we need to trim to the particular interface
        if (restrict_to) {
            relevant_group_data = [];
            $.each(JSON.parse(series_data_selector.val()).series_data, function(index, group) {
                if (group['device_type'] === restrict_to) {
                    // CHECK ORGAN MODEL IF NECESSARY
                    if (organ_model_id && group['organ_model_id'] == organ_model_id) {
                        relevant_group_data.push(group);
                    }
                    else if (!organ_model_id) {
                        relevant_group_data.push(group);
                    }
                }
            });
        }

        // Make the popup tables
        populate_popup_tables(relevant_group_data);

        var diverging_contents = [];

        // Stringify the groups
        // Doing so during comparison is a waste of time
        var stringified_groups = [];

        $.each(relevant_group_data, function(index, group) {
            var current_stringification = {};
            $.each(prefixes, function(prefix_index, prefix) {
                // console.log(prefix, group[prefix]);
                current_stringification[prefix] = stringify_group_contents(group[prefix]);
            });

            stringified_groups.push(current_stringification);
        });

        // Basically, we want to determine if a given component (as derived from its stringification) is NOT present in any of the other groups
        // This means we iterate over every group and break when we find it is NOT present and mark it as being included in the difference table

        // Iterate over every group
        $.each(stringified_groups, function(group_1_index, group_1) {
            diverging_contents.push({});
            var current_divergence = diverging_contents[group_1_index];

            // Special exceptions for model, version, and type
            // Perhaps more later
            $.each(non_prefix_comparisons, function(non_prefix_index, non_prefix_comparison) {
                $.each(relevant_group_data, function(group_2_index, group_2) {
                    if (relevant_group_data[group_1_index][non_prefix_comparison] !== relevant_group_data[group_2_index][non_prefix_comparison]) {
                        diverging_prefixes[non_prefix_comparison] = true;
                    }
                });
            });

            // Iterate over every prefix
            $.each(prefixes, function(prefix_index, prefix) {
                current_divergence[prefix] = {};
                // Iterate over every group (ideally not the same group, but the comparison shouldn't take too long)
                $.each(stringified_groups, function(group_2_index, group_2) {
                    $.each(group_1[prefix], function(current_content, current_index) {
                        if (group_2[prefix][current_content] === undefined) {
                            current_divergence[prefix][current_index] = true;

                            diverging_prefixes[prefix] = true;
                        }
                    });
                });
            });
        });

        // console.log(diverging_contents);
        // console.log(diverging_prefixes);

        // TODO TODO TODO
        // Generate the difference table
        $.each(diverging_contents, function(index, current_content) {
            var stored_tds = {};

            var name_td = $('<td>').html(relevant_group_data[index]['name']);

            var mps_model_td = $('<td>');

            if (diverging_prefixes['organ_model_id']) {
                mps_model_td.append(
                    $('<div>').text(organ_model_full.find('option[value="' + relevant_group_data[index]['organ_model_id'] + '"]').text())
                )
            }

            // TERRIBLE FOR LARGE TABLES!
            if (diverging_prefixes['organ_model_protocol_id'] && relevant_group_data[index]['organ_model_protocol_id']) {
                $('<div>').text('Version: ' + organ_model_protocol_full.find('option[value="' + relevant_group_data[index]['organ_model_protocol_id'] + '"]').text()).appendTo(mps_model_td);
            }

            var test_type_td = $('<td>');

            if (diverging_prefixes['test_type']) {
                test_type_td.html(
                    test_type.find('option[value="' + relevant_group_data[index]['test_type'] + '"]').text()
                )
            }

            var current_row = $('<tr>')
            .attr('data-group-name', relevant_group_data[index]['name'])
            .append(
                // Name
                name_td,
                // MPS Model (and version)
                mps_model_td,
                // Test type
                test_type_td,
            );

            stored_tds = {
                model: mps_model_td,
                test_type: test_type_td
            };

            $.each(prefixes, function(prefix_index, prefix) {
                var content_indices = current_content[prefix];
                var current_column = $('<td>');
                if (Object.keys(content_indices).length > 0) {
                    // Har har
                    $.each(content_indices, function(content_index) {
                        current_column.append(
                            // $('<div>').html(
                                // get_difference_display(
                                //     prefix,
                                //     relevant_group_data[index][prefix][content_index]
                                // )
                            // )
                            $('<div>').text(
                                get_shorthand_display(
                                    prefix,
                                    relevant_group_data[index][prefix][content_index]
                                )
                            )
                        );
                    });
                }

                current_row.append(current_column);

                stored_tds[prefix] = current_column.clone();
            });

            // CONTRIVED FOR NOW: REPLACE WITH CACHED SELECTOR
            $('#difference_table').find('tbody').append(current_row);

            // ASSUMES UNIQUE NAMES
            window.GROUPS.difference_table_displays[relevant_group_data[index]['name']] = stored_tds;
        });

        // Show all initially
        $('#difference_table td, #difference_table th').show();
        window.GROUPS.hidden_columns = {};

        // Determine what to hide
        // TODO: Subject to revision
        // Crude and explicit for the moment
        if (!diverging_prefixes['organ_model_id'] && !diverging_prefixes['organ_model_protocol_id']) {
            $('#difference_table td:nth-child(2), #difference_table th:nth-child(2)').hide();
            window.GROUPS.hidden_columns['model'] = true;
        }
        if (!diverging_prefixes['test_type']) {
            $('#difference_table td:nth-child(3), #difference_table th:nth-child(3)').hide();
            window.GROUPS.hidden_columns['test_type'] = true;
        }
        if (!diverging_prefixes['cell']) {
            $('#difference_table td:nth-child(4), #difference_table th:nth-child(4)').hide();
            window.GROUPS.hidden_columns['cell'] = true;
        }
        if (!diverging_prefixes['compound']) {
            $('#difference_table td:nth-child(5), #difference_table th:nth-child(5)').hide();
            window.GROUPS.hidden_columns['compound'] = true;
        }
        if (!diverging_prefixes['setting']) {
            $('#difference_table td:nth-child(6), #difference_table th:nth-child(6)').hide();
            window.GROUPS.hidden_columns['setting'] = true;
        }
    };

    $.each(prefixes, function(index, prefix) {
        // Make all of the popups
        var current_dialog = $('#' + prefix + '_full_contents_popup');
        current_dialog.dialog({
            width: $(document).width(),
            height: 500,
            buttons: [
                {
                    text: 'Close',
                    click: function() {
                       $(this).dialog('close');
                    }
                }
            ]
        });
        current_dialog.removeProp('hidden');

        // Triggers for spawning the popups
        $('#spawn_' + prefix + '_full_contents_popup').click(function() {
            $('#' + prefix + '_full_contents_popup').dialog('open');
        });
    });
});
