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
            return data._aData[0].indexOf(' checked>') > -1 ? 0 : 1;
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
        }
    });

    // Indicates that floating headers need to be refreshed when a toggle-hide-button is clicked
    $(document).on('click', '.toggle-hide-button', function() {
        // Recalculate responsive and fixed headers
        setTimeout(function() {
            $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
            $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
        }, 1000);
    });

    // Fix some issues with column width on resize.
    window.onresize = function() {
        setTimeout(function() {
            $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
            // $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
            // $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
        }, 250);
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
