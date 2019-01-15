// The compound report must be able to:
// 1.) Employ some method to filter desired compounds (will resemble list display with checkboxes)
// 2.) Display all of the requested compound data in the desired table
// 3.) Display D3 "Sparklines" for every assay for the given compound (TODO LOOK AT D3 TECHNIQUE)
$(document).ready(function () {
    // Object of all selected compounds
    var compounds = {};

    var width = 50;
    var height = 50;
    var x = d3.scale.linear().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);
    var line = d3.svg.line()
        // We no longer interpolate
        //.interpolate("basis")
        .x(function(d) { return x(d.time); })
        .y(function(d) { return y(d.value); });

    var selections = $('#selections');
    var MAX_SAVED_SELECTIONS = 5;

    // Open and then close dialog so it doesn't get placed in window itself
    var dialog = $('#selection_dialog');
    dialog.dialog({
        width: 825,
        height: 500,
        closeOnEscape: true,
        autoOpen: false,
        close: function() {
            $('body').removeClass('stop-scrolling');
        },
        open: function() {
            $('body').addClass('stop-scrolling');
        }
    });
    dialog.removeProp('hidden');

    // Convert ID to valid selector
    function valid_selector(id) {
        var new_id = "#" + id.replace(/(:|\.|\[|\]|,|'|\(|\))/g, "\\$1");
        // Compensate for slashes
        new_id = new_id.replace(/\//g, '\\\/');
        return new_id;
    }

    // Add method to sort by checkbox
    // (I reversed it so that ascending will place checked first)
    // $.fn.dataTable.ext.order['dom-checkbox'] = function(settings, col){
    //     return this.api().column(col, {order:'index'}).nodes().map(function(td, i){
    //         return $('input', td).prop('checked') ? 0 : 1;
    //     });
    // };

    function clear_selections(reset) {
        // Remove search terms
        $('input[type=search]').val('');
        window.TABLE.search('');
        // Uncheck all checkboxes
        checkboxes.prop('checked', false);
        // Remove all compounds
        compounds = {};

        if (reset) {
            // Return to default length (maintains previous sorting and so on)
            window.TABLE.page.len(25).draw();
        }
    }

    function save_selections() {
        var current_selections = _.keys(compounds);

        var all_selections = [];
        var current_storage = localStorage.getItem('compound_report_selections');

        if (current_storage) {
            all_selections = JSON.parse(current_storage);

            if (all_selections.length >= MAX_SAVED_SELECTIONS) {
                all_selections = all_selections.slice(1);
            }
        }
        all_selections.push(current_selections);
        all_selections = JSON.stringify(all_selections);

        localStorage.setItem('compound_report_selections', all_selections)
    }

    function display_load_dialog() {
        var current_storage = localStorage.getItem('compound_report_selections');
        if (current_storage) {
            var all_selections = JSON.parse(current_storage);

            // Clear old selections
            selections.html('');

            $.each(all_selections, function(index, selection) {
                var row = $('<tr>').addClass('table-selection')
                    .attr('data-selection-index', index);

                var compound_column = $('<td>').text(selection.join(', '));

                row.append(compound_column);
                selections.append(row);
            });
        }

        dialog.dialog('open');
        // Remove focus
        // $('.ui-dialog :button').blur();
    }

    function check_selection(value) {
        $.each(checkboxes, function(index, checkbox) {
            if (checkbox.value == value) {
                $(checkbox).prop('checked', true);
            }
        });
    }

    function load_selections(selection_index) {
        clear_selections(false);

        var current_storage = localStorage.getItem('compound_report_selections');
        var all_selections = JSON.parse(current_storage);

        var compound_selections = all_selections[selection_index];

        $.each(compound_selections, function(index, compound) {
            compounds[compound] = compound;
            check_selection(compound);
        });

        // Sort first column ascending
        window.TABLE.order([[0, 'asc']]);
        // Go back to 10 items per page
        window.TABLE.page.len(10).draw();

        dialog.dialog('close');

        // Recalculate responsive and fixed headers
        $($.fn.dataTable.tables(true)).DataTable().responsive.recalc();
        $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
    }

    function sparkline(elem_id, plot, x_domain, y_domain) {
        //console.log(x_domain);
        //console.log(y_domain);
        var data = [];
        for (var time in plot) {
            var value = +plot[time];
            var x_time = +time;
            data.push({'time':x_time, 'value':value});
        }

        // Sort by time
        data = _.sortBy(data, function(obj){ return +obj.time });

        // TODO THE X AND Y DOMAINS NEED TO SCALE TOGETHER ACROSS ASSAYS
        // FOR THE X AXIS: 0-Max(X) IF I AM NOT MISTAKEN
        // FOR THE Y AXIS: 0-100 UNLESS Y FOR THE ASSAY EXCEEDS 100
        x.domain([0, x_domain]);
        y.domain([0, y_domain]);

        d3.select(valid_selector(elem_id))
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('path')
            .datum(data)
            .attr('class', 'sparkline')
            .attr('d', line);
    }

    // AJAX call for getting data
    function get_data() {
        $.ajax({
            url: "/compounds_ajax/",
            type: "POST",
            dataType: "json",
            data: {
                call: 'fetch_compound_report',
                compounds: JSON.stringify(compounds),
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            },
            success: function (json) {
                // console.log(json);
                // Stop spinner
                window.spinner.stop();
                // Build table
                build_table(json);
            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    function build_table(data) {
        // Show graphic
        $('#graphic').prop('hidden',false);

        // Clear old (if present)
        $('#results_table').dataTable().fnDestroy();
        $('#results_body').html('');

        // Acquire domains for the plots (based on assay)
        var x_max = {};
        var y_max = {};
        for (var compound in data) {
            var all_plots = data[compound].plot;
            for (var assay in all_plots) {
                if (x_max[assay] === undefined) {
                    x_max[assay] = 0;
                    y_max[assay] = 1;
                }
                var assay_plots = all_plots[assay];
                for (var concentration in assay_plots) {
                    for (var time in assay_plots[concentration]) {
                        var value = +assay_plots[concentration][time];
                        time = +time;
                        x_max[assay] = time > x_max[assay] ? time: x_max[assay];
                        y_max[assay] = value > y_max[assay] ? value: y_max[assay];
                    }
                }
            }
        }

        for (compound in data) {
            var values = data[compound].table;
            var plot = data[compound].plot;

            var row = "<tr>";

            row += "<td><a href='/compounds/"+values['id']+"'>" + compound + "</a></td>";
            //row += "<td>" + values['Dose (xCmax)'] + "</td>";
            row += "<td>" + values['logP']  + "</td>";
            row += "<td>" + values['pk_metabolism'].replace(/\r\n/g,'<br>') + "</td>";
            row += "<td>" + values['preclinical'].replace(/\r\n/g,'<br>') + "</td>";
            row += "<td>" + values['clinical'].replace(/\r\n/g,'<br>') + "</td>";
            row += "<td>" + values['post_marketing'].replace(/\r\n/g,'<br>') + "</td>";
            row += "<td>";

            // Make the table
            row += "<table id='"+compound+"_table' class='table table-striped table-bordered inner'>";

            // Add a row for the header
            row += "<tr id='"+compound+"_header'><td></td></tr>";

            row += "</table>";
            row += "</td>";

            row += "</tr>";
            $('#results_body').append(row);

            // Sorted assays for iteration
            var sorted_assays = _.sortBy(_.keys(x_max), function(a) { return a; });

            for (var i=0; i<sorted_assays.length; i++) {
                assay = sorted_assays[i];

                var assay_max_time = values.max_time[assay] ? values.max_time[assay]:"-";
                // Tack this assay on to the header
                $(valid_selector(compound+'_header')).append($('<td>')
                    // The use of days here is contrived, actual units to be decided on later
                    .addClass('small')
                    .attr('width', 50)
                    .append('<span>'+assay+'<br>'+'(' + assay_max_time + 'd)'+'</span>'));
                if (plot[assay]) {
                    var sorted_concentrations = _.sortBy(_.keys(plot[assay]), function(a) { return parseFloat(a); });
                    // console.log(sorted_concentrations);

                    for (var j=0; j<sorted_concentrations.length; j++) {
                        concentration = sorted_concentrations[j];

                        var row_id = compound + '_' + concentration;
                        // If the concentration does not have a row, add it to the table
                        if (!$(valid_selector((row_id)))[0]) {
                            // Add the row
                            $(valid_selector(compound + '_table')).append($('<tr>')
                                .attr('id', row_id)
                                .append($('<td>')
                                    .text(concentration.replace('_', ' '))));
                        }
                        for (var x=0; x<sorted_assays.length; x++) {
                            var every_assay = sorted_assays[x];
                            // Add a cell for the assay given concentration
                            if (!$(valid_selector(compound + '_' + every_assay + '_' + concentration))[0]) {
                                $(valid_selector(row_id)).append($('<td>')
                                    .attr('id', compound + '_' + every_assay + '_' + concentration));
                            }
                        }
                    }
                }
            }

            for (var assay in plot) {
                for (var concentration in plot[assay]) {
                    sparkline(
                        compound + '_' + assay + '_' + concentration,
                        plot[assay][concentration],
                        x_max[assay],
                        y_max[assay]
                    );
                }
            }
        }

        $('#results_table').DataTable({
            dom: 'B<"row">rt',
            fixedHeader: {headerOffset: 50},
            responsive: true,
            "iDisplayLength": 100,
            // Needed to destroy old table
            "bDestroy": true,
            "order": [[ 0, "asc" ]],
            "aoColumnDefs": [
                {
                    "bSortable": false,
                    "aTargets": [6]
                }
            ]
        });

        // Swap positions of filter and length selection
        $('.dataTables_filter').css('float','left');
        // Reposition download/print/copy
        $('.DTTT_container').css('float', 'none');
    }

    // Submission
    function submit() {
        // Hide Selection html
        $('#selection').prop('hidden',true);
        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );
        get_data();
    }

    // Checks whether the submission button was clicked
    $('#submit').click(function() {
        submit();
    });

    // Tracks the clicking of checkboxes to fill compounds
    $('.checkbox').change(function() {
        var compound = this.value;
        var checkbox_index = $(this).attr('data-table-index');

        if (this.checked) {
            compounds[compound] = compound;
            window.TABLE.data()[checkbox_index][0] = window.TABLE.data()[
                checkbox_index
            ][0].replace('>', ' checked="checked">');
        }
        else {
            delete compounds[compound];
            window.TABLE.data()[checkbox_index][0] = window.TABLE.data()[
                checkbox_index
            ][0].replace(' checked="checked">', '>');
        }
    });

    $('#save_selections').click(function() {
        save_selections();
    });

    $('#load_selections').click(function() {
        display_load_dialog();
    });

    $('#clear_selections').click(function() {
        clear_selections(true);
    });

    selections.on('click', '.table-selection', function() {
        load_selections(+$(this).attr('data-selection-index'));
    });

    window.onhashchange = function() {
        if (location.hash !== '#show') {
            $('#graphic').prop('hidden', true);
            $('#selection').prop('hidden', false);
            // Hide the header for results
            $('#results_header').hide();
            // Show the header for compounds
            $('#compounds_header').show();
        }
        else {
            $('#graphic').prop('hidden', false);
            $('#selection').prop('hidden', true);
            // Show the header for results
            $('#results_header').show();
            // Hide the header for compounds
            $('#compounds_header').hide();
        }
    };

    // Make the initial data table
    window.TABLE = $('#compounds').DataTable({
        dom: 'B<"row">lfrtip',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        "order": [[ 1, "asc" ]],
        "aoColumnDefs": [
            {
                "bSortable": false,
                "aTargets": [8]
            },
            {
                "targets": [3, 9],
                "visible": false,
                "searchable": true
            },
            { "sSortDataType": "dom-checkbox", "targets": 0, "width": "10%" },
        ],
        "iDisplayLength": 25
    });

    var cells = window.TABLE.cells().nodes();
    var checkboxes = $(cells).find(':checkbox');

    // Crude way to deal with resizing from images
    setTimeout(function() {
         $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
    }, 500);
});
