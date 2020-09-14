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
            // Even cruder, trigger the resize after a delay
            // setTimeout(function() {
            //     $(window).trigger('resize');
            // }, 1000);

            // Let's try to remove the resize trigger
            setTimeout(function() {
                // $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
                $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
                $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
            }, 1000);
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
    // window.onresize = function() {
    //     setTimeout(function() {
    //         $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
    //         $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
    //         $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
    //     }, 250);
    // }

    // Jump to top after page change
    // CRUDE
   $(document).on('page.dt', '.dataTables_wrapper', function () {
        $('html, body').animate({
            scrollTop: $(this).offset().top - 75
        }, 500);
    });

    window.TABLES.add_new_row_to_selection_list = function(
        current_app,
        current_model,
        new_pk,
        new_name
    ) {
        if (current_model === 'CellSample') {
            var cell_sample_table = $('#cellsamples');

            // Clear the search!
            cell_sample_table.DataTable().search('').draw();

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

            // Clear the search!
            reference_table.DataTable().search('').draw();

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

    /*
    * Natural Sort algorithm for Javascript - Version 0.7 - Released under MIT license
    * Author: Jim Palmer (based on chunking idea from Dave Koelle)
    * Contributors: Mike Grier (mgrier.com), Clint Priest, Kyle Adams, guillermo
    * See: http://js-naturalsort.googlecode.com/svn/trunk/naturalSort.js
    */
    function naturalSort (a, b, html) {
        var re = /(^-?[0-9]+(\.?[0-9]*)[df]?e?[0-9]?%?$|^0x[0-9a-f]+$|[0-9]+)/gi,
            sre = /(^[ ]*|[ ]*$)/g,
            dre = /(^([\w ]+,?[\w ]+)?[\w ]+,?[\w ]+\d+:\d+(:\d+)?[\w ]?|^\d{1,4}[\/\-]\d{1,4}[\/\-]\d{1,4}|^\w+, \w+ \d+, \d{4})/,
            hre = /^0x[0-9a-f]+$/i,
            ore = /^0/,
            htmre = /(<([^>]+)>)/ig,
            // convert all to strings and trim()
            x = a.toString().replace(sre, '') || '',
            y = b.toString().replace(sre, '') || '';
            // remove html from strings if desired
            if (!html) {
                x = x.replace(htmre, '');
                y = y.replace(htmre, '');
            }
            // chunk/tokenize
        var xN = x.replace(re, '\0$1\0').replace(/\0$/,'').replace(/^\0/,'').split('\0'),
            yN = y.replace(re, '\0$1\0').replace(/\0$/,'').replace(/^\0/,'').split('\0'),
            // numeric, hex or date detection
            xD = parseInt(x.match(hre), 10) || (xN.length !== 1 && x.match(dre) && Date.parse(x)),
            yD = parseInt(y.match(hre), 10) || xD && y.match(dre) && Date.parse(y) || null;

        // first try and sort Hex codes or Dates
        if (yD) {
            if ( xD < yD ) {
                return -1;
            }
            else if ( xD > yD ) {
                return 1;
            }
        }

        // natural sorting through split numeric strings and default strings
        for(var cLoc=0, numS=Math.max(xN.length, yN.length); cLoc < numS; cLoc++) {
            // find floats not starting with '0', string or 0 if not defined (Clint Priest)
            var oFxNcL = !(xN[cLoc] || '').match(ore) && parseFloat(xN[cLoc], 10) || xN[cLoc] || 0;
            var oFyNcL = !(yN[cLoc] || '').match(ore) && parseFloat(yN[cLoc], 10) || yN[cLoc] || 0;
            // handle numeric vs string comparison - number < string - (Kyle Adams)
            if (isNaN(oFxNcL) !== isNaN(oFyNcL)) {
                return (isNaN(oFxNcL)) ? 1 : -1;
            }
            // rely on string comparison if different types - i.e. '02' < 2 != '02' < '2'
            else if (typeof oFxNcL !== typeof oFyNcL) {
                oFxNcL += '';
                oFyNcL += '';
            }
            if (oFxNcL < oFyNcL) {
                return -1;
            }
            if (oFxNcL > oFyNcL) {
                return 1;
            }
        }
        return 0;
    }

    jQuery.extend( jQuery.fn.dataTableExt.oSort, {
        "natural-asc": function ( a, b ) {
            return naturalSort(a,b,true);
        },

        "natural-desc": function ( a, b ) {
            return naturalSort(a,b,true) * -1;
        },

        "natural-nohtml-asc": function( a, b ) {
            return naturalSort(a,b,false);
        },

        "natural-nohtml-desc": function( a, b ) {
            return naturalSort(a,b,false) * -1;
        },

        "natural-ci-asc": function( a, b ) {
            a = a.toString().toLowerCase();
            b = b.toString().toLowerCase();

            return naturalSort(a,b,true);
        },

        "natural-ci-desc": function( a, b ) {
            a = a.toString().toLowerCase();
            b = b.toString().toLowerCase();

            return naturalSort(a,b,true) * -1;
        }
    } );
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
