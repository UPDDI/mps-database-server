$(document).ready(function () {
    // STUDY LIST Stuff
    // NOT REMOTELY DRY
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(reproPie);

    var studies_table = $('#studies');

    // Cached secletors
    var studies_selector = $('#id_studies');
    var assays_selector = $('#id_assays');
    var selected_studies_table_selector = $('#selected_studies_table');

    // Populate study_id_to_assay
    var study_id_to_assays = {};

    var initial_load = true;

    // If the studies are not empty, it must be an update
    if (studies_selector.val()) {
        $.each(studies_selector.val(), function(index, value) {
            studies_table.find('.study-selector[value="' + value + '"]').prop('checked', true);
        });
    }

    // Hide initially
    studies_table.hide();

    function reproPie() {
        studies_table.show();

        var number_of_rows = $('.study').length;
        var pie, pieData, pieOptions, pieChart;
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
                    pieOptions = {
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
                    };
                }

                if (pieData) {
                    pieChart = new google.visualization.PieChart(document.getElementById('piechart' + x));
                    pieChart.draw(pieData, pieOptions);
                }
            }
        }

        // Hide again
        studies_table.hide();

        studies_table.DataTable({
            dom: 'B<"row">lfrtip',
            fixedHeader: {headerOffset: 50},
            responsive: true,
            "iDisplayLength": 50,
            // Initially sort on start date (descending), not ID
            "order": [ 2, "desc" ],
            "aoColumnDefs": [
                {
                    "bSortable": false,
                    "aTargets": [0]
                },
                {
                    "width": "10%",
                    "targets": [0]
                },
                {
                    "type": "numeric-comma",
                    "targets": [5, 6, 7, 8]
                },
                {
                    'visible': false,
                    'targets': [7, 8, 12]
                },
                {
                    'className': 'none',
                    'targets': [9]
                },
                {
                    'sortable': false,
                    'targets': [10]
                }
            ],
            drawCallback: function () {
                // Show when done (if not update)
                // Hide table if updating
                if (!studies_selector.val()) {
                    studies_table.show('slow');
                    initial_load = false;
                }
                if (initial_load) {
                    studies_table.show();
                    $('#list_section').hide();
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
        var split_name = $(this).text().split('~@|');
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

    var assay_dialog_body = $('#assay_dialog_body');
    var assay_table = $('#assay_table');

    var assay_dialog = $('#assay_dialog').dialog({
        width: 900,
        closeOnEscape: true,
        autoOpen: false,
        close: function () {
            $('body').removeClass('stop-scrolling');
        },
        open: function () {
            $('body').addClass('stop-scrolling');
        },
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
    }

    function apply_assay_filter() {
        $.each(current_assay_filter, function(assay_id, add_or_remove) {
            // Add/remove from m2m
            // (Can pass selections as an array, but this works too)
            var current_assay_option = assays_selector.find('option[value="' + assay_id + '"]');
            current_assay_option.prop('selected', add_or_remove);
        });
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
            if (!initial) {
                $.each(study_id_to_assays[study_id], function(index, value) {
                    assays_selector.find('option[value="' + value.id + '"]').prop('selected', true);
                });
            }
        }
        // If de-selected, then remove from table
        else if (!add_or_remove && current[0]) {
            current.remove();

            // Select/de-select all associated assays by default
            $.each(study_id_to_assays[study_id], function(index, value) {
                assays_selector.find('option[value="' + value.id + '"]').prop('selected', false);
            });
        }
    }

    // List continue buttons
    $('#list_continue_button').click(function() {
        $('#list_section').hide();
        $('#form_section').show();
    });

    // Back button
    $('#back_button').click(function() {
        $('#list_section').show();
        $('#form_section').hide();
    });

    $(document).on('click', '.study-selector', function() {
        var current_study = studies_selector.find('option[value="' + $(this).val() + '"]').first();
        current_study.prop('selected', $(this).prop('checked'))
        add_or_remove_from_study_table(current_study, $(this).prop('checked'));

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
        var current_study_id = $(this).attr('data-study-id');
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
        }
        else {
            current_assay_filter[$(this).val()] = false;
        }
    });

    // Get initial assay filter
    reset_assay_filter();
});
