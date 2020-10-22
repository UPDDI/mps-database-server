$(document).ready(function () {
    // STUDY LIST Stuff
    // NOT REMOTELY DRY
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(reproPie);

    var studies_table = $('#studies');
    var current_table = null;

    // Cached selectors
    var studies_selector = $('#id_studies');
    var assays_selector = $('#id_assays');
    var selected_studies_table_selector = $('#selected_studies_table');

    var list_section_selector = $('#list_section');
    var form_section_selector = $('#form_section');

    // CONTRIVED
    var study_list_hint_selector = $('#study_list_hint');

    // Populate study_id_to_assay
    var study_id_to_assays = {};
    var new_studies = [];
    var initial_studies = {};

    var initial_load = true;

    // If the studies are not empty, it must be an update
    if (studies_selector.val()) {
        $.each(studies_selector.val(), function(index, value) {
            var current_checkbox = studies_table.find('.study-selector[value="' + value + '"]');
            current_checkbox.prop('checked', true);
            current_checkbox.attr('checked', 'checked');
            initial_studies[value] = true;
        });
    }

    // Hide initially
    studies_table.hide();

    // BAD: NOT DRY
    function reproPie() {
        studies_table.show();

        var pieOptions = {
            legend: 'none',
            slices: {
                0: {color: '#74ff5b'},
                1: {color: '#fcfa8d'},
                2: {color: '#ff7863'}
            },
            pieSliceText: 'none',
            pieSliceTextStyle: {
                color: 'black',
                bold: true,
                fontSize: 12
            },
            'chartArea': {'width': '90%', 'height': '90%'},
            backgroundColor: {fill: 'transparent'},
            pieSliceBorderColor: "black",
            tooltip: {
                textStyle: {
                    fontName: 'verdana', fontSize: 10
                }
            }
            // enableInteractivity: false
        };

        var number_of_rows = studies_table.find('tr').length - 1;
        var pie, pieData, pieChart;
        for (x = 0; x < number_of_rows; x++) {
            pieData = null;

            if ($("#piechart" + x)[0]) {
                pie = $("#piechart" + x).data('nums');
                if (pie !== '0|0|0' && pie) {
                    pie = pie.split("|");
                    pieData = google.visualization.arrayToDataTable([
                        ['Status', 'Count'],
                        ['Excellent', parseInt(pie[0])],
                        ['Acceptable', parseInt(pie[1])],
                        ['Poor', parseInt(pie[2])]
                    ]);
                }
                if (pieData) {
                    pieChart = new google.visualization.PieChart(document.getElementById('piechart' + x));
                    pieChart.draw(pieData, pieOptions);
                }
            }
        }

        // Hide again
        studies_table.hide();

        current_table = studies_table.DataTable({
            dom: '<Bl<"row">frptip>',
            fixedHeader: {headerOffset: 50},
            responsive: true,
            "iDisplayLength": 50,
            // Initially sort on start date (descending), not ID
            "order": [[0, "asc"], [2, "desc"]],
            "aoColumnDefs": [
                {
                    sSortDataType: "dom-checkbox",
                    targets: 0,
                    width: "10%"
                },
                {
                    "width": "10%",
                    "targets": [0]
                },
                {
                    "type": "numeric-comma",
                    "targets": [6, 7, 8, 9, 10, 11, 12]
                },
                {
                    'visible': false,
                    'targets': [5, 9, 10, 11, 12, 16, 18, 19]
                },
                {
                    'className': 'none',
                    'targets': [13]
                },
                {
                    'sortable': false,
                    'targets': [14]
                }
            ],
            drawCallback: function () {
                // Show when done (if not update)
                // Hide table if updating
                if (!studies_selector.val()) {
                    study_list_hint_selector.show('slow');
                    studies_table.show('slow');
                    initial_load = false;
                }
                if (initial_load) {
                    studies_table.show();
                    list_section_selector.hide();
                    study_list_hint_selector.show();
                }

                initial_load = false;

                // Swap positions of filter and length selection; clarify filter
                $('.dataTables_filter').css('float', 'left').prop('title', 'Separate terms with a space to search multiple fields');
                $('.dataTables_length').css('float', 'right');
                // Reposition download/print/copy
                $('.DTTT_container').css('float', 'none');
            },
        });
    }

    assays_selector.find('option').each(function() {
        var assay_id = $(this).val();
        // The text of each option contains the data we need
        // It is delimited with @~|
        // var split_name = $(this).text().split('~@|');
        var split_name = $(this).text().split(window.SIGILS.COMBINED_VALUE_SIGIL);
        var study_id = split_name[0];
        var target = split_name[1];
        var method = split_name[2];
        var unit = split_name[3];
        // Now we can make the entry
        var assay_to_add = {
            id: assay_id,
            target: target,
            method: method,
            unit: unit,
        };

        // Now we add the assay
        if (study_id_to_assays[study_id]) {
            study_id_to_assays[study_id].push(assay_to_add);
        }
        else {
            study_id_to_assays[study_id] = [assay_to_add];
        }
    });

    // Datatable for filtering assays
    var assay_filter_data_table = null;

    // Assays to deselect/select after hitting confirm
    var current_assay_filter = {};

    // To discern how to modify assays
    var current_study_id = null;

    var assay_dialog_body = $('#assay_dialog_body');
    var assay_table = $('#assay_table');

    var assay_dialog = $('#assay_dialog').dialog({
        width: 900,
        closeOnEscape: true,
        autoOpen: false,
        buttons: [
        {
            text: 'Apply',
            click: function() {
                // Select or deselect as necessary
                // TODO
                apply_assay_filter();
                $(this).dialog("close");
            }
        },
        {
            text: 'Cancel',
            click: function() {
                reset_assay_filter();
                $(this).dialog("close");
            }
        }]
    });
    assay_dialog.removeProp('hidden');

    // Maybe later
    // function reset_study_filter() {
    //     studies_selector.find('option').each(function() {
    //         if ($(this).prop('selected')) {
    //             current_study_filter[$(this).val()] = true;
    //             $('.study-selector[value="' + $(this).val() + '"]').prop('checked', true);
    //         }
    //         else {
    //             current_study_filter[$(this).val()] = false;
    //             $('.study-selector[value="' + $(this).val() + '"]').prop('checked', false);
    //         }
    //     });
    // }

    // function apply_study_filter() {
    //     $.each(current_study_filter, function(study_id, add_or_remove) {
    //         // Add/remove from m2m
    //         // (Can pass selections as an array, but this works too)
    //         var current_study_option = studies_selector.find('option[value="' + study_id + '"]');
    //         current_study_option.prop('selected', add_or_remove);
    //
    //         add_or_remove_from_study_table(current_study_option, add_or_remove);
    //     });
    // }

    function reset_assay_filter() {
        assays_selector.find('option').each(function() {
            if ($(this).prop('selected')) {
                current_assay_filter[$(this).val()] = true;
            }
            else {
                current_assay_filter[$(this).val()] = false;
            }
        });

        // Make sure that all of the assay boxes have the correct colors
        $('.assay-select-button').each(function() {
            check_assay_filter_button(Math.floor($(this).attr('data-study-id')));
        });
    }

    function check_assay_filter_button(study_id) {
        if (study_id) {
            var current_filter_button = $('.assay-select-button[data-study-id="' + study_id +'"]');
            var current_assays = study_id_to_assays[study_id];

            var study_is_affected = false;
            var study_is_empty = true;

            $.each(current_assays, function(assay_index, assay) {
                if (!current_assay_filter[assay.id]) {
                    study_is_affected = true;
                }
                else {
                    study_is_empty = false;
                }
            });

            // Study is empty
            if (study_is_empty) {
                current_filter_button.removeClass('btn-warning');
                current_filter_button.addClass('btn-danger');
            }
            // Study is partial
            else if (study_is_affected) {
                current_filter_button.addClass('btn-warning');
                current_filter_button.removeClass('btn-danger');
            }
            // Study is full
            else {
                current_filter_button.removeClass('btn-warning');
                current_filter_button.removeClass('btn-danger');
            }
        }
    }

    function apply_assay_filter() {
        $.each(current_assay_filter, function(assay_id, add_or_remove) {
            // Add/remove from m2m
            // (Can pass selections as an array, but this works too)
            var current_assay_option = assays_selector.find('option[value="' + assay_id + '"]');
            current_assay_option.prop('selected', add_or_remove);
        });

        check_assay_filter_button(current_study_id);
    }

    function add_or_remove_from_study_table(current_study_option, add_or_remove, initial) {
        var study_id = current_study_option.val();
        var current = selected_studies_table_selector.find('tr[data-study-id="' + current_study_option.val() + '"]');
        // If selected, then add to table
        if (add_or_remove && !current[0]) {
            var new_row = $('<tr>')
                .attr('data-study-id', current_study_option.val())
                .append($('<td>')
                    .text(current_study_option.text())
                )
                .append($('<td>')
                    .html('<a role="button" class="assay-select-button btn btn-primary" data-study-id="' + current_study_option.val()  + '"><span class="glyphicon glyphicon-search"></span> Select Assays</a>')
                )

            selected_studies_table_selector.append(new_row);

            // Select/de-select all associated assays by default
            if (!initial && study_id_to_assays[study_id]) {
                $.each(study_id_to_assays[study_id], function(index, value) {
                    assays_selector.find('option[value="' + value.id + '"]').prop('selected', true);
                });
            }

            // Add to new studies
            if (!initial_studies[study_id]) {
                new_studies.push(Math.floor(study_id));
            }
        }
        // If de-selected, then remove from table
        else if (!add_or_remove && current[0]) {
            current.remove();

            // Select/de-select all associated assays by default
            if (study_id_to_assays[study_id]) {
                $.each(study_id_to_assays[study_id], function(index, value) {
                    assays_selector.find('option[value="' + value.id + '"]').prop('selected', false);
                });
            }
        }
    }

    // List continue buttons
    $('#list_continue_button').click(function() {
        list_section_selector.hide();
        form_section_selector.show();

        // FORCE THE APPLICATION FOR ALL NEW STUDIES
        $.each(new_studies, function(i, study_id) {
            $.each(study_id_to_assays[study_id], function(index, assay) {
                current_assay_filter[assay.id] = true;
            });
        });

        // Apply the filter
        apply_assay_filter();

        // No longer consider new studies
        new_studies = [];

        // Force fixed header recalc
        setTimeout(function() {
            // Kill fixed header
            $('#studies').DataTable().fixedHeader.disable()
        }, 100);
    });

    // Back button
    $('#back_button').click(function() {
        list_section_selector.show();
        form_section_selector.hide();

        // Force fixed header recalc
        setTimeout(function() {
            $('#studies').DataTable().fixedHeader.enable();
        }, 100);
    });

    $(document).on('click', '.study-selector', function() {
        var current_study = studies_selector.find('option[value="' + $(this).val() + '"]').first();
        current_study.prop('selected', $(this).prop('checked'))
        add_or_remove_from_study_table(current_study, $(this).prop('checked'));
        var checkbox_index = $(this).attr('data-table-index');

        if ($(this).prop('checked')) {
            current_table.data()[
                checkbox_index
            ][0] = current_table.data()[
                checkbox_index
            ][0].replace('>', ' checked="checked">');
        }
        else {
            current_table.data()[
                checkbox_index
            ][0] = current_table.data()[
                checkbox_index
            ][0].replace(' checked="checked">', '>');
        }

        // if ($(this).prop('checked')) {
        //     current_study_filter[$(this).val()] = true;
        // }
        // else {
        //     current_study_filter[$(this).val()] = false;
        // }
    });

    // Iterate over every intial selection in studies and spawn table
    $('#id_studies > option:selected').each(function() {
        // True indicates always add
        add_or_remove_from_study_table($(this), true, true);
    });

    // Get initial study filter
    // reset_study_filter();

    // TODO dialog for selecting a set of assays (per study)
    $(document).on('click', '.assay-select-button', function() {
        current_study_id = $(this).attr('data-study-id');
        var current_assays = study_id_to_assays[current_study_id];

        // Populate the datatable
        // TODO
        // Clear current contents
        if (assay_filter_data_table) {
            assay_table.DataTable().clear();
            assay_table.DataTable().destroy();
        }

        assay_dialog_body.empty();

        var html_to_append = [];

        if (current_assays) {
            // Spawn checkboxes
            $.each(current_assays, function (index, assay) {
                var row = '<tr>';

                if (current_assay_filter[assay.id]) {
                    row += '<td width="10%" class="text-center"><input class="big-checkbox assay-selector" type="checkbox" value="' + assay.id + '" checked></td>';
                }
                else {
                    row += '<td width="10%" class="text-center"><input class="big-checkbox assay-selector" type="checkbox" value="' + assay.id + '"></td>';
                }

                // Stick the name in
                row += '<td>' + assay.target + '</td>';
                row += '<td>' + assay.method + '</td>';
                row += '<td>' + assay.unit + '</td>';

                row += '</tr>';

                html_to_append.push(row);
            });
        }
        else {
            html_to_append.push('<tr><td></td><td>No data to display.</td></tr>');
        }

        assay_dialog_body.html(html_to_append.join(''));

        // TODO BETTER SELECTOR
        assay_filter_data_table = assay_table.DataTable({
            autoWidth: false,
            destroy: true,
            dom: '<"wrapper"lfrtip>',
            deferRender: true,
            iDisplayLength: 10,
            order: [1, 'asc']
        });

        // Show the dialog
        assay_dialog.dialog('open');
    });

    // TODO NOT DRY
    // Triggers for select all
    $('#assay_filter_section_select_all').click(function() {
        assay_filter_data_table.page.len(-1).draw();

        assay_table.find('.assay-selector').each(function() {
            $(this)
                .prop('checked', false)
                .attr('checked', false)
                .trigger('click');
        });

        assay_filter_data_table.order([[1, 'asc']]);
        assay_filter_data_table.page.len(10).draw();
    });

    // Triggers for deselect all
    $('#assay_filter_section_deselect_all').click(function() {
        assay_filter_data_table.page.len(-1).draw();

        assay_table.find('.assay-selector').each(function() {
            $(this)
                .prop('checked', true)
                .attr('checked', true)
                .trigger('click');
        });

        assay_filter_data_table.order([[1, 'asc']]);
        assay_filter_data_table.page.len(10).draw();
    });

    // TODO CHECKBOX TRIGGER
    $(document).on('click', '.assay-selector', function() {
        if ($(this).prop('checked')) {
            current_assay_filter[$(this).val()] = true;
            $(this).attr('checked', true);
        }
        else {
            current_assay_filter[$(this).val()] = false;
            $(this).attr('checked', false);
        }
    });

    // Get initial assay filter
    reset_assay_filter();
});
