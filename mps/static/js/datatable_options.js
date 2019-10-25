// CRUDE SOLUTION
// Contrary to the idea that this is only for options
window.TABLES = {
    add_new_row_to_selection_list: null
};

// Add method to sort by checkbox
// (I reversed it so that ascending will place checked first)
$(document).ready(function () {
    // $.fn.dataTable.ext.order['dom-checkbox'] = function (settings, col) {
    //     return this.api().column(col, {order: 'index'}).nodes().map(function (td, i) {
    //         return $('input', td).prop('checked') ? 0 : 1;
    //     });
    // };

    $.fn.dataTable.ext.order['dom-checkbox'] = function(settings, col) {
        return settings.aoData.map(function(data, index) {
            return data._aData[0].indexOf(' checked="checked">') > -1 ? 0 : 1;
        });
    };

    $.fn.dataTable.ext.order['time-in-minutes'] = function (settings, col) {
        return this.api().column(col, {order: 'index'}).nodes().map(function (td, i) {
            return parseFloat($('.time_in_minutes', td).val());
        });
    };

    // Define numeric comma sorting
    $.extend($.fn.dataTableExt.oSort, {
        "numeric-comma-pre": function (a) {
            var x = a.replace(/,/g, '');
            return parseFloat(x);
        },

        "numeric-comma-asc": function (a, b) {
            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
        },

        "numeric-comma-desc": function (a, b) {
            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
        }
    });

    // Define brute numeric sort
    $.extend($.fn.dataTableExt.oSort, {
        "brute-numeric-pre": function (a) {
            var x = a.replace(/\D/g, '');
            return parseFloat(x);
        },

        "brute-numeric-asc": function (a, b) {
            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
        },

        "brute-numeric-desc": function (a, b) {
            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
        }
    });

    // Defines the options for the print, copy, and save as buttons
    $.extend(true, $.fn.dataTable.defaults, {
        buttons: [
            'copy', 'csv', 'print', 'colvis'
        ],
        autoWidth: false,
        // swfPath: '/static/swf/flashExport.swf'
        // Default draw callback
        drawCallback: function () {
            if ($(this).table) {
                // Show when done
                $(this).table().container().show('slow');
            }
            // For defer render
            else {
                $(this).show('slow');
            }
            // Swap positions of filter and length selection; clarify filter
            $('.dataTables_filter').css('float', 'left').prop('title', 'Separate terms with a space to search multiple fields');
            $('.dataTables_length').css('float', 'right');
            // Reposition download/print/copy
            $('.DTTT_container').css('float', 'none');

            // Activates Bootstrap tooltips
            $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});

            // CRUDE!
            // Trigger resize
            $(window).trigger('resize');
        }
    });

    // Indicates that floating headers need to be refreshed when a toggle-hide-button is clicked
    $(document).on('click', '.toggle-hide-button, .toggle_sidebar_button', function() {
        // Recalculate responsive and fixed headers
        setTimeout(function() {
            // $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
            $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
        }, 1000);
    });

    // Fix some issues with column width on resize.
    // BAD
    window.onresize = function() {
        setTimeout(function() {
            $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
            $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
            $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
        }, 250);
    }

    window.TABLES.add_new_row_to_selection_list = function(
        current_app,
        current_model,
        new_pk,
        new_name
    ) {
        if (current_model === 'CellSample') {
            var cell_sample_table = $('#cellsamples');

            var new_row = cell_sample_table
                .find('tbody')
                .find('tr')
                .first()
                .clone()
                .addClass('success');

            var split_name = new_name.split(window.SIGILS.COMBINED_VALUE_SIGIL);

            // CRUDE
            new_row.find('.cellsample-selector').attr('data-cell-sample-id', new_pk).attr('data-name', split_name[6]);
            new_row.find('td').eq(1).text(new_pk);
            new_row.find('td').eq(2).text(split_name[0]);
            new_row.find('td').eq(3).text(split_name[1]);
            new_row.find('td').eq(4).text(split_name[2]);
            new_row.find('td').eq(5).text(split_name[3]);
            new_row.find('td').eq(6).text(split_name[4]);
            new_row.find('td').eq(7).text(split_name[5]);

            // Acquire the label
            window.CELLS.cell_sample_id_to_label[new_pk] = split_name[6];

            cell_sample_table.DataTable().row.add(new_row).draw();
        }
        // If reference
        else if (current_model === 'AssayReference') {
            var split_name = new_name.split(window.SIGILS.COMBINED_VALUE_SIGIL);
            var authors = split_name[0];
            var title = split_name[1];
            // SLOPPY
            var pmid = split_name[2];

            var reference_table = $('#reference_table');

            var new_row = reference_table
                .find('tbody')
                .find('tr')
                .first()
                .clone()
                .addClass('success');
            new_row.find('button').attr('data-reference-id', new_pk);
            new_row.find('td[data-reference-field="id"]').text(new_pk);
            new_row.find('td[data-reference-field="pubmed_id"]').text(pmid);
            new_row.find('td[data-reference-field="title"]').text(title);
            new_row.find('td[data-reference-field="authors"]').text(authors);

            reference_table.DataTable().row.add(new_row).draw();
        }
    }
});
// $.fn.dataTable.TableTools.defaults.aButtons = [
//     {
//         "sExtends": "copy",
//         "sButtonText": "Copy to Clipboard",
//         "mColumns": "sortable",
//         "bFooter": false
//     },
//     {
//         "sExtends": "csv",
//         "sButtonText": "Save as CSV",
//         "mColumns": "sortable",
//         "bFooter": false
//     },
//     {
//         "sExtends": "print",
//         "sButtonText": "Print"
//         // Unfortunately it seems columns can not be removed from print in this way
//         //"mColumns": "sortable"
//     }
// ];
// $.fn.dataTable.TableTools.defaults.sSwfPath = '/static/swf/copy_csv_xls.swf';
