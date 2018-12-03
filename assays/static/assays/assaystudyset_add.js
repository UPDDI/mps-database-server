$(document).ready(function () {
    // Cached secletors
    var studies_selector = $('#id_studies');
    var assays_selector = $('#id_assays');
    var selected_studies_table_selector = $('#selected_studies_table');

    // Populate study_id_to_assay
    var study_id_to_assays = {};

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

    // TODO dialog for selecting a study
    var study_id_selector = $('#study_id_selector');

    var current_study_filter = {};

    // Open and then close dialog so it doesn't get placed in window itself
    var study_dialog = $('#study_dialog');
    study_dialog.dialog({
        width: 900,
        closeOnEscape: true,
        autoOpen: false,
        buttons: [
            {
                text: 'Apply',
                click: function() {
                    // Select or deselect as necessary
                    apply_study_filter();
                    reset_assay_filter();
                    // TODO
                    $(this).dialog("close");
                }
            },
            {
                text: 'Close',
                click: function() {
                    reset_study_filter();
                    $(this).dialog("close");
                }
            }
        ],
        // Probably should have these as defaults somewhere...
        close: function() {
            $('body').removeClass('stop-scrolling');
        },
        open: function() {
            $('body').addClass('stop-scrolling');
            // Remove focus
            $(this).focus();
        }
    });
    study_dialog.removeProp('hidden');

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

    function reset_study_filter() {
        studies_selector.find('option').each(function() {
            if ($(this).prop('selected')) {
                current_study_filter[$(this).val()] = true;
                $('.study-selector[value="' + $(this).val() + '"]').prop('checked', true);
            }
            else {
                current_study_filter[$(this).val()] = false;
                $('.study-selector[value="' + $(this).val() + '"]').prop('checked', false);
            }
        });
    }

    function apply_study_filter() {
        $.each(current_study_filter, function(study_id, add_or_remove) {
            // Add/remove from m2m
            // (Can pass selections as an array, but this works too)
            var current_study_option = studies_selector.find('option[value="' + study_id + '"]');
            current_study_option.prop('selected', add_or_remove);

            add_or_remove_from_study_table(current_study_option, add_or_remove);
        });
    }

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

    $('#select_studies_button').click(function() {
        study_dialog.dialog('open');
    });

    $(document).on('click', '.study-selector', function() {
        if ($(this).prop('checked')) {
            current_study_filter[$(this).val()] = true;
        }
        else {
            current_study_filter[$(this).val()] = false;
        }
    });

    // Iterate over every intial selection in studies and spawn table
    $('#id_studies > option:selected').each(function() {
        // True indicates always add
        add_or_remove_from_study_table($(this), true, true);
    });

    // Get initial study filter
    reset_study_filter();

    $('#study_data_table').DataTable({
        "iDisplayLength": -1,
        // Initially sort on receipt date
        "order": [ 1, "desc" ],
        // If one wants to display top and bottom
        "sDom": '<"wrapper"fti>'
    });

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
