$(document).ready(function () {
    
    // START do on load

    //show the validation stuff
    $('#form_errors').show();

    // there will only be upload and review, not add (add is a special case of update handled by the forms.py!)
    let page_omic_metadata_check_load = $('#check_load').html().trim();

    // indy sample stuff
    var sample_metadata_table_id = 'sample_metadata_table';

    // make sure to update this as needed (to match what comes from utils.py)
    var indy_row_label = 'Sample Label'

    var indy_list_of_dicts_of_table_rows = JSON.parse($('#id_indy_list_of_dicts_of_table_rows').val());
    var indy_list_of_column_labels = JSON.parse($('#id_indy_list_of_column_labels').val());
    var indy_list_of_column_labels_show_hide = JSON.parse($('#id_indy_list_of_column_labels_show_hide').val());
    var indy_matrix_item_list = JSON.parse($('#id_indy_matrix_item_list').val());
    var indy_matrix_item_name_to_pk_dict = JSON.parse($('#id_indy_matrix_item_name_to_pk_dict').val());
    var indy_list_columns_hide = [];
    var indy_list_time_units_to_include_initially = JSON.parse($('#id_indy_list_time_units_to_include_initially').val());
    var indy_dict_time_units_to_table_column = JSON.parse($('#id_indy_dict_time_units_to_table_column').val());
    var indy_add_or_update = JSON.parse($('#id_indy_add_or_update').val());

    var indy_input_box_in_out_compare = '';

    findTheTimeUnitsThatShouldBeInTheTableAndAsDefault();
    var page_radio_time_unit = $("input[type='radio'][name='radio_time_unit']:checked").val();
    var current_sample_pattern = 'clt';

    // Prepare and build the table on load
    // the current one
    var metadata_lod = indy_list_of_dicts_of_table_rows;
    //for holding versions to allow for undo and redo
    var metadata_lod_cum = [];
    metadata_lod_cum.push(JSON.parse(JSON.stringify(metadata_lod)));
    // version number aka current index - is the current one (should be 1, 2, 3, 4, or 5 after first population)
    var metadata_lod_last_index = 0;
    //the table info that is highlighted
    var metadata_highlighted = [];
    var list_of_row_indexs_with_one_or_more_highlighted = [];
    var list_of_fields_for_replacing_that_are_highlighted = [];
    var special_tracking = {};

    // just working variables, but want in different subs, so just declare here
    var current_pk = 0;
    var current_val = '';
    var page_paste_cell_irow = null;
    var page_paste_cell_icol = null;

    var indy_table_order = [];
    var indy_table_column_defs = [{bSortable: false, targets: [5 ,]},
        {'targets': indy_list_columns_hide, 'visible': false,},
    ];
    // indy_table_column_defs = [{bSortable: false, targets: [1,]}];
        // { 'width': '20%' },
        // { width: 200, targets: 0 }
        // {'targets': [0], 'visible': true,},
        // {'targets': [1], 'visible': true,},
        // {responsivePriority: 1, targets: 0},
        // {responsivePriority: 2, targets: 1},

    // make a cross reference to the html dom name of the content box
    // make a cross reference to the html of the content box
    // note: the column header is an attribute of the cells in the indy table
    // and the key of these to dicts is the column header
    // e.g. col-label='Chip or Well Name'
    var icol_to_html_outer = {};
    var icol_to_html_element = {};
    // Note that these keys are hardcoded to columns headers or metadata labels
    // todo check these for new ones...not sure they are correct
    icol_to_html_outer['Chip/Well Name'] = 'h_indy_matrix_item';
    icol_to_html_element['Chip/Well Name'] = 'matrix_item_name';
    icol_to_html_outer['Sample Location'] = 'h_indy_sample_location';
    icol_to_html_element['Sample Location'] = 'sample_location_name';
    icol_to_html_outer['Sample Time (Day)'] = 'h_indy_time_day';
    icol_to_html_element['Sample Time (Day)'] = 'time_day';
    icol_to_html_outer['Sample Time (Hour)'] = 'h_indy_time_hour';
    icol_to_html_element['Sample Time (Hour)'] = 'time_hour';
    icol_to_html_outer['Sample Time (Minute)'] = 'h_indy_time_minute';
    icol_to_html_element['Sample Time (Minute)'] = 'time_minute';

    if (page_omic_metadata_check_load === 'review') {
        // HANDY - to make everything on a page read only (for review page)
        $('.selectized').each(function() { this.selectize.disable() });
        $(':input').attr('disabled', 'disabled');
    }

    // has a default in html page
    var page_radio_duplicate_value = $("input[type='radio'][name='radio_change_duplicate_increment']:checked").val();
    var page_drag_action = $("input[type='radio'][name='radio_change_drag_action']:checked").val();

    //set the visibility based on default form selections (as set in the html)
    radioDuplicateVisibility();
    radioActionVisibility();
    radioTimeVisibility();
    goBuildSampleMetadataTable();
    postBuildSampleMetadataTable();
    reapplyTheHighlightingToTheIndyTable();
    
    // END do on load

    // START clicks and changes section EXCEPT 4 actions
    
    $(document).on('click', '#clearHighlightingButton', function() {
        $('.special-selected1').removeClass('special-selected1');
        whatIsCurrentlyHighlightedInTheIndyTable();
    });

    $(document).on('click', '#highlightAllSampleLabelsButton', function() {
        $('.special-label-td').addClass('special-selected1');
        $('.no-edit1').removeClass('special-selected1');
        whatIsCurrentlyHighlightedInTheIndyTable();
    });

    $("input[type='radio'][name='radio_change_duplicate_increment']").click(function () {
        page_radio_duplicate_value = $(this).val();
        radioDuplicateVisibility();
    });

    $("input[type='radio'][name='radio_change_drag_action']").click(function () {
        page_drag_action = $(this).val();
        radioActionVisibility();
    });

    $("input[type='radio'][name='radio_time_unit']").click(function () {
        page_radio_time_unit = $(this).val();
        radioTimeVisibility();

        // get the column number from the unit just changed to
        let obj = indy_dict_time_units_to_table_column;
        let num_in_list = obj[page_radio_time_unit];
        // if it is in the list to hide in the table, remove it
        const index = indy_list_columns_hide.indexOf(num_in_list);
        if (index > -1) {
          indy_list_columns_hide.splice(index, 1);
        }
        // there is not change to the actually data, so, not need to update the metadata_lod or form field
        goBuildSampleMetadataTable();
        postBuildSampleMetadataTable();
        reapplyTheHighlightingToTheIndyTable();
    });

    // need on change events for chip id and for sample location so can populate the corresponding dom element
    // could have just used a memory variable, but having the text and pk in a dom element made picking a general process for all!
    // note in html file, search ~pk_tracking_note~
    $(document).on('change', '#id_indy_matrix_item', function() {
        var thisText = $('#id_indy_matrix_item').children('option:selected').text();
        var thisValue = $('#id_indy_matrix_item').children('option:selected').val();
        document.getElementById('matrix_item_name').innerHTML = thisText;
        document.getElementById('matrix_item_pk').innerHTML = thisValue;
    });

    $(document).on('change', '#id_indy_sample_location', function() {
        var thisText = $('#id_indy_sample_location').children('option:selected').text();
        var thisValue = $('#id_indy_sample_location').children('option:selected').val();
        document.getElementById('sample_location_name').innerHTML = thisText;
        document.getElementById('sample_location_pk').innerHTML = thisValue;
    });

    // when the user changes a sample label using the input instead of a pattern
    // they would need to do this for replicates to change them
    $(document).on('focusin', '.special-label', function (e) {
        let what_cell_changed = $(this);
        indy_input_box_in_out_compare = what_cell_changed.val();
    });

    $(document).on('focusout', '.special-label', function (e) {
        let what_cell_changed = $(this);
        if (indy_input_box_in_out_compare == what_cell_changed.val()) {
            // user went in and out but made no change
        } else {
            let this_row_index = what_cell_changed.attr("row-index");
            let this_col_index = what_cell_changed.attr("col-index");
            //this assumes all the columns are included in the table - BE CAREFUL with that
            metadata_lod[this_row_index - 1][indy_row_label] = what_cell_changed.val();
            // update the form variable
            $('#id_indy_list_of_dicts_of_table_rows').val(JSON.stringify(metadata_lod));
            metadata_lod_cum.push(JSON.parse(JSON.stringify(metadata_lod)));
            metadata_lod_last_index = metadata_lod_cum.length - 1;
            checkUndoRedoButtonVisibility();
            // NO NEED to redraw the table
        }
    });

    $(document).on('click', '#undoIndyButton', function() {
        indyClickedToUndoRedoChangeToTable('undo');
    });
    
    $(document).on('click', '#redoIndyButton', function() {
        indyClickedToUndoRedoChangeToTable('redo');
    });

    // just need the pattern so know how to populate when highlighted and clicked
    $(document).on('change', '#id_indy_sample_label_options', function() {
        current_sample_pattern = $(this).val();
    });

    // END clicks and changes section EXCEPT 4 actions

    // START - Functions EXCEPT 4 actions

    // maybe add some cleaning of the master list if it gets too big
    function indyClickedToUndoRedoChangeToTable(which_do) {
        var current_length_list = metadata_lod_cum.length;
        // undo goes toward the 0 index, redo towards the length of the index
        // the buttons should only be visible if the undo/redo is possible, but check before add/subtract
        if (which_do === 'undo') {
            if (metadata_lod_last_index > 0) {
                metadata_lod_last_index = metadata_lod_last_index - 1;
            } else {
                alert('No undo storage at the current time')
            }
        } else {
            // which_do === 'redo'
            if (metadata_lod_last_index < current_length_list-1) {
                metadata_lod_last_index = metadata_lod_last_index + 1;
            } else {
                alert('No redo storage at the current time')
            }
        }
        // must change the current one to match with what undid or redid
        metadata_lod = JSON.parse(JSON.stringify(metadata_lod_cum[metadata_lod_last_index]));
        // update the form variable
        $('#id_indy_list_of_dicts_of_table_rows').val(JSON.stringify(metadata_lod));

        checkUndoRedoButtonVisibility();
        goBuildSampleMetadataTable();
        postBuildSampleMetadataTable();
        // reapplyTheHighlightingToTheIndyTable(); - this is really hard to get right after undo or redo, so do not do it
    }

    function checkUndoRedoButtonVisibility() {
        var current_length_list = metadata_lod_cum.length;
        // should a button (undo or redo) show after whatever change brought you here
        if (metadata_lod_last_index > 0) {
            // yes, can undo another time
            $('#undoIndyButton').show();
        } else {
            $('#undoIndyButton').hide();
        }

        if (metadata_lod_last_index < current_length_list-1) {
            // yes, can undo another time
            $('#redoIndyButton').show();
        } else {
            $('#redoIndyButton').hide();
        }
    }

    function radioDuplicateVisibility() {
        $('.increment-section').hide();
        if (page_radio_duplicate_value === 'increment') {
            $('.increment-section').show();
        }
    }

    function radioActionVisibility() {
        $('.empty-section').hide();
        $('.pastes-section').hide();
        $('.delete-section').hide();
        $('.replace-section').hide();

        if (page_drag_action === 'pastes') {
            $('.pastes-section').show();
        } else if (page_drag_action === 'empty') {
            $('.empty-section').show();
        } else if (page_drag_action === 'delete') {
            $('.delete-section').show();
        } else if (page_drag_action === 'replace') {
            $('.replace-section').show();
        }
    }

    function radioTimeVisibility() {
        $('#h_indy_time_day').hide();
        $('#h_indy_time_hour').hide();
        $('#h_indy_time_minute').hide();

        if (page_radio_time_unit === 'day') {
            $('#h_indy_time_day').show();
            $('#sample_time_label').text('Sample Time (Day)');
        } else if (page_radio_time_unit === 'hour') {
            $('#h_indy_time_hour').show();
            $('#sample_time_label').text('Sample Time (Hour)');
        } else if (page_radio_time_unit === 'minute') {
            $('#h_indy_time_minute').show();
            $('#sample_time_label').text('Sample Time (Minute)');
        } else {
            $('#sample_time_label').text('?');
        }
    }

    /**
     * When this page opens, there is a list sent back that has units that should be displayed in the table
     * and a dictionary with the unit and the column number in the table this pushing both to the utils.py
    */
    function findTheTimeUnitsThatShouldBeInTheTableAndAsDefault() {
        // set default unit based on what IS in the units initially from utils.py
        $('#radio_minute').prop('checked', true);
        if (indy_list_time_units_to_include_initially.indexOf('day') > -1) {
            $('#radio_day').prop('checked', true);
        } else if (indy_list_time_units_to_include_initially.indexOf('hour') > -1) {
            $('#radio_hour').prop('checked', true);
        }
        page_radio_time_unit = $("input[type='radio'][name='radio_time_unit']:checked").val();

        let obj = indy_dict_time_units_to_table_column;
        Object.keys(obj).forEach(function(key) {
           // console.log(key + " " + obj[key]);
           if (indy_list_time_units_to_include_initially.indexOf(key) < 0) {
                indy_list_columns_hide.push(obj[key])
           }
        });
    }

    function reapplyTheHighlightingToTheIndyTable() {
        var tirow = null;
        var ticol = null;
        var thisElementList = null;
        for (let index = 0; index < metadata_highlighted.length; index++) {
            tirow = metadata_highlighted[index]['metadata_highlighted_tirow'];
            ticol = metadata_highlighted[index]['metadata_highlighted_ticol'];
            thisElementList = $('td[col-index*="' + ticol + '"][row-index*="' + tirow + '"]');
            thisElementList.addClass('special-selected1');
        }
    }

    // this is called when drag across the metadata table
    function selectableDragOnSampleMetadataTable() {
        $('.ui-selected').each(function() {
            if ($(this).hasClass('special-selected1')) {
                $(this).removeClass('special-selected1');
            } else {
                let this_col_label = $(this).attr("col-label");
                //Watch this if rename headers - HARDCODE
                if (page_drag_action==='replace' && this_col_label.indexOf('Time') >= 0) {
                    if (
                        page_radio_time_unit === 'day' && this_col_label.indexOf('ay') >= 0 ||
                        page_radio_time_unit === 'hour' && this_col_label.indexOf('our') >= 0 ||
                        page_radio_time_unit === 'minute' && this_col_label.indexOf('inute') >= 0
                    ) {
                        $(this).addClass('special-selected1');
                    } // else, do not highlight because this unit is not the one selected in the replace content section
                } else {
                    $(this).addClass('special-selected1');
                }
            }
            $(this).removeClass('ui-selected');
        });
        // remove highlighting for the no edits
        $('.no-edit1').removeClass('special-selected1');
        // keep this updated, so can turn the fields in the replace content section yellow with every change
        whatIsCurrentlyHighlightedInTheIndyTable();
    }

    function whatIsCurrentlyHighlightedInTheIndyTable() {
        // Made a test to see what is considered highlighted vrs visible
        // Found that, only what is highlighted and visible is changed
        // $(sample_metadata_table_id).DataTable().rows( { filter: 'applied' } ).every( function () {
        //     var row = this.data();
        //     console.log("###row ", row)
        // });

        metadata_highlighted = [];
        list_of_fields_for_replacing_that_are_highlighted = [];
        let index = 0;
        $('.special-selected1').each(function() {
            var dict_highlighted_indy_metadata = {};
            var imetadata_highlighted_tirow = $(this).attr('row-index');
            var imetadata_highlighted_ticol = $(this).attr('col-index');
            var imetadata_highlighted_tlcol = $(this).attr('col-label');
            var imetadata_highlighted_content = null;

            // since this goes through all the columns, they could be different types
            // try different ways of pulling the content, and
            // keep in mind that the content could actually be null
            try {
                imetadata_highlighted_content = $(this).val();
            } catch {
                 imetadata_highlighted_content = '';
            }
            if (!imetadata_highlighted_content) {
                try {
                    imetadata_highlighted_content = $(this).text();
                } catch {
                    imetadata_highlighted_content = '';
                }
            }
            if (!imetadata_highlighted_content) {
                try {
                    imetadata_highlighted_content = $(this).innerHTML.trim();
                } catch {
                    imetadata_highlighted_content = '';
                }
            }
            if (imetadata_highlighted_content.length === 0) {
                imetadata_highlighted_content = $(this).text();
            }
            if (imetadata_highlighted_content.length === 0) {
                try {
                    imetadata_highlighted_content = $(this).innerHTML.trim();
                } catch {
                    imetadata_highlighted_content = '';
                }
            }

            //at this point, should have
            // console.log("###index ",index)
            // console.log("row i ",imetadata_highlighted_tirow)
            // console.log("col i ",imetadata_highlighted_ticol)
            // console.log("col l ",imetadata_highlighted_tlcol)
            // console.log("content ",imetadata_highlighted_content)

            //store in a dictionary
            dict_highlighted_indy_metadata['metadata_highlighted_tirow'] = imetadata_highlighted_tirow;
            if (list_of_row_indexs_with_one_or_more_highlighted.indexOf(imetadata_highlighted_tirow) >= 0) {
                //already in list
            } else {
                list_of_row_indexs_with_one_or_more_highlighted.push(imetadata_highlighted_tirow);
            }          
            
            dict_highlighted_indy_metadata['metadata_highlighted_ticol'] = imetadata_highlighted_ticol;
            dict_highlighted_indy_metadata['metadata_highlighted_tlcol'] = imetadata_highlighted_tlcol;
            dict_highlighted_indy_metadata['metadata_highlighted_content'] = imetadata_highlighted_content;
            //put in a list of dictionaries of what is highlighted
            metadata_highlighted.push(dict_highlighted_indy_metadata);
            list_of_fields_for_replacing_that_are_highlighted.push(imetadata_highlighted_tlcol);
            index = index + 1;
        });
        // a special check to turn replace content boxes yellow if one or more is highlighted in the table
        // e.g. if the user has highlighted one or more chips, turn chip/well name in the replace content yellow
        $('#h_indy_sample_location').removeClass('required');
        $('#h_indy_matrix_item').removeClass('required');
        $('#h_indy_sample_time').removeClass('required');
        $('#h_indy_time_day').removeClass('required');
        $('#h_indy_time_hour').removeClass('required');
        $('#h_indy_time_minute').removeClass('required');
        $('#h_indy_sample_name_options').removeClass('required');

        $.each(list_of_fields_for_replacing_that_are_highlighted, function (index, e) {
            if (e.indexOf('ocation') >= 0) {
                $('#h_indy_sample_location').addClass('required');
            } else if (e.indexOf('hip') >= 0) {
                $('#h_indy_matrix_item').addClass('required');
            } else if (e.indexOf('ime (D') >= 0) {
                $('#h_indy_sample_time').addClass('required');
            } else if (e.indexOf('ime (H') >= 0) {
                $('#h_indy_sample_time').addClass('required');
            } else if (e.indexOf('ime (M') >= 0) {
                $('#h_indy_sample_time').addClass('required');
            } else if (e.indexOf('abel') >= 0) {
                $('#h_indy_sample_name_options').addClass('required');
            }
        });

        // need for replace and pastes to keep track of last seen during the replace/pastes
        // costs a little extra to put here, but will always be ready
        // note that, this is a dictionary for each column header, with an index
        special_tracking = {};
        $.each(indy_list_of_column_labels, function (index, icol) {
            special_tracking[icol+'_store_value'] = '';
            special_tracking[icol+'_store_index'] = -1;
        });
    }

    function goBuildSampleMetadataTable() {
        // if there were errors and the user did something to change the table, hide the errors
        $('#form_errors').hide();

        var table = $('#' + sample_metadata_table_id).DataTable();
        var searchTerm = table.search();

        // build a table
        // set to the table div
        var elem = document.getElementById('div_for_' + sample_metadata_table_id);
        //remove an existing table
        if (elem.childNodes[0]) {
            elem.removeChild(elem.childNodes[0]);
        }

        var myTableDiv = document.getElementById('div_for_' + sample_metadata_table_id);
        var myTable = document.createElement('TABLE');
        $(myTable).attr('id', sample_metadata_table_id);
        $(myTable).attr('cellspacing', '0');
        $(myTable).attr('width', '100%');
        $(myTable).addClass('display table table-striped table-hover');

        var tableHead = document.createElement('THEAD');

        var tr = document.createElement('TR');
        var rowcounter = 0;
        $(tr).attr('row-index', rowcounter);
        var colcounter = 0;

        $.each(indy_list_of_column_labels, function (i_index, colLabel) {
            // include in table or not: 1 is for include
            if (indy_list_of_column_labels_show_hide[i_index] === 1) {
                var th = document.createElement('TH');
                $(th).attr('col-index', colcounter);
                $(th).attr('row-index', rowcounter);
                $(th).attr('col-label', colLabel);
                th.appendChild(document.createTextNode(colLabel));
                tr.appendChild(th);
                colcounter = colcounter + 1;
            }
            // else, do not put in the table and do not increment the header counter
        });
        rowcounter = rowcounter + 1;

        tableHead.appendChild(tr);

        myTable.appendChild(tableHead);
        var tableBody = document.createElement('TBODY');

        colcounter = 0;
        let myCellContent = '';
        $.each(metadata_lod, function (i_index, row) {
            var tr = document.createElement('TR');
            $(tr).attr('row-index', rowcounter);
            tableBody.appendChild(tr);

            colcounter = 0;
            let myCellContent = '';

            $.each(indy_list_of_column_labels, function (i_index, colLabel) {
                myCellContent = row[colLabel];

                // include in table or not - 1 is for include
                if (indy_list_of_column_labels_show_hide[i_index] === 1) {
                    var td = document.createElement('TD');
                    $(td).attr('col-index', colcounter);
                    $(td).attr('row-index', rowcounter);
                    $(td).attr('col-label', colLabel);

                    if (colLabel === indy_row_label) {
                        if (row['Data Attached'] === 'y') {
                            // column HARDCODE (utilys.py)
                            // if the sample label (hence the pk if in at least one row of the data point table)
                            // do not allow the sample label to be changed
                            td.appendChild(document.createTextNode(myCellContent));
                            $(td).attr('class', 'no-edit1');
                        } else {
                            let this_me = '<input type="text" ';
                            this_me = this_me + 'class="special-label" '
                            this_me = this_me + 'id="sample_row_' + rowcounter
                            this_me = this_me + '" name="' + colLabel + '" value="' + myCellContent
                            this_me = this_me + '" col-index="' + colcounter + '" row-index="' + rowcounter + '">';
                            $(td).html(this_me);
                            $(td).attr('class', 'special-label-td');
                        }
                    } else {
                        td.appendChild(document.createTextNode(myCellContent));
                    }
                    tr.appendChild(td);
                    colcounter = colcounter + 1;
                }
            });
            rowcounter = rowcounter + 1;

        });

        myTable.appendChild(tableBody);
        myTableDiv.appendChild(myTable);

        // so not as to get mixed up with the unit options, change visibility at the last minute
        if (indy_add_or_update === 'add') {
            //HARDCODE column number for that Data Attached/Used indicator
            indy_list_columns_hide.push(6);
        }

        // When I did not have the var before the variable name, the table headers acted all kinds of crazy
        var sampleDataTable = $('#' + sample_metadata_table_id).removeAttr('width').DataTable({
            // 'iDisplayLength': 100,
            paging: false,
            'sDom': '<B<"row">lfrtip>',
            //do not do the fixed header here...only want for two of the tables
            //https://datatables.net/forums/discussion/30879/removing-fixedheader-from-a-table
            //https://datatables.net/forums/discussion/33860/destroying-a-fixed-header
            fixedHeader: {headerOffset: 50},
            // responsive: true,
            'order': indy_table_order,
            'columnDefs': indy_table_column_defs,
            // fixedColumns: true
            'autoWidth': true
        });

        // HANDY each row of datatable
        // Do not need but keep for reference
        // https://stackoverflow.com/questions/29077902/how-to-loop-through-all-rows-in-datatables-jquery
        // sampleDataTable.rows().every(function () {
        //     this.data()
        //     // is a list, with the first one being the tags and such
        //     console.log("this row ",this.data());
        //     console.log("this row ",this.data()[0]);
        //     // the tags and such look like a long string, so, to find an attribute, must be creative
        //     // below is HANDY for looping through, and getting a value.by name, but we do not need that here
        //     var data = this.data();
        //     data.forEach(function (value, index) {
        //         // if (value.isActive)
        //         // {
        //          console.log('value ',value);
        //
        //          // console.log(value.UserName);
        //         // }
        //     })
        // });

        //reference $('#glossary_table_filter :input').val(searchTerm).trigger('input');
        //reference $('#glossary_table_filter :input').val(null).trigger('input');
        $('#' + sample_metadata_table_id + '_filter :input').val(searchTerm).trigger('input');
        return myTable;
    }

    function postBuildSampleMetadataTable() {
        // allows table to be selectable, must be AFTER table is created - keep
        $('#' + sample_metadata_table_id).selectable({
            filter: 'td',
            distance: 15,
            stop: selectableDragOnSampleMetadataTable
        });
    }

    // END - Functions EXCEPT 4 actions

    // START - the clicks for the 4 actions

    $(document).on('click', '#replaceInTableButton', function() {
        functionForAll4Actions('replace');
    });
    
    $(document).on('click', '#emptyInTableButton', function() {
       functionForAll4Actions('empty');
    });
    
    $(document).on('click', '#deleteInTableButton', function() {
        functionForAll4Actions('delete');
    });
    
    $(document).on('click', '#pastesInTableButton', function() {
        functionForAll4Actions('pastes');
    });

    // END - the clicks for the 4 actions

    // START - the 4 actions functions

    function functionForAll4Actions(which_button) {
        // the highlighting should be up to date, but, it will not hurt to run it as a double check
        whatIsCurrentlyHighlightedInTheIndyTable();
        
        // page_drag_action is replace, empty, delete, or pastes
        // page_radio_duplicate_value is duplicate or increment (users will need to sort to do bottom up)        
        // when delete or paste, doing whole row, so need the row index list: list_of_row_indexs_with_one_or_more_highlighted

        if (which_button === 'delete') {
            subFunctionForAddOrDeleteRows('delete');
        } else if (which_button === 'pastes') {
            subFunctionForAddOrDeleteRows('pastes');
        } else if (which_button === 'replace') {
            subFunctionForReplaceOrEmptyContent('replace');
        } else {
            subFunctionForReplaceOrEmptyContent('empty');
        }

        // update the form variable
        $('#id_indy_list_of_dicts_of_table_rows').val(JSON.stringify(metadata_lod));
        metadata_lod_cum.push(JSON.parse(JSON.stringify(metadata_lod)));
        metadata_lod_last_index = metadata_lod_cum.length - 1;
        checkUndoRedoButtonVisibility();
        goBuildSampleMetadataTable();
        postBuildSampleMetadataTable();

        if (which_button === 'delete') {
            // highlighting deleted rows makes not sense.....
        } else {
            // todo - if want this, make it work right
            // reapplyTheHighlightingToTheIndyTable();
        }
    }

    function subFunctionForAddOrDeleteRows(pastes_or_delete) {
        // sort the list of rows descending so that removal will preserve the correct lower indices
        var desc_index = list_of_row_indexs_with_one_or_more_highlighted.sort(function(a, b){return b-a});

        $.each(desc_index, function (index, each_row) {
            //each_row is in the table, since there is a header row, subtract one to get row in metadata_lod
            var metadata_lod_row = each_row-1;

            if (pastes_or_delete === 'delete') {
                if (metadata_lod[metadata_lod_row]['Data Attached'] == 'no') {
                    metadata_lod.splice(metadata_lod_row, 1);
                }
            } else {
                // a pastes row
                metadata_lod.push(metadata_lod[metadata_lod_row]);
                metadata_lod[metadata_lod_row]['sample_metadata_pk'] = '';
            }
        });
    }

    function subFunctionForReplaceOrEmptyContent(replace_or_empty) {
        // go through each highlighted and make changes to metadata_lod as needed

        // find content of the replacement fields
        if (replace_or_empty === 'replace') {
            special_tracking['Sample Time (Day)_store_value'] = $('#time_day').val();
            special_tracking['Sample Time (Day)_store_index'] = 1;

            special_tracking['Sample Time (Hour)_store_value'] = $('#time_hour').val();
            special_tracking['Sample Time (Hour)_store_index'] = 1;

            special_tracking['Sample Time (Minute)_store_value'] = $('#time_minute').val();
            special_tracking['Sample Time (Minute)_store_index'] = 1;

            special_tracking['Sample Location_store_value'] = $('#sample_location_name').text();
            special_tracking['sample_location_pk_store_value'] = $('#sample_location_pk').text();

            special_tracking['Chip/Well Name_store_value'] = $('#matrix_item_name').text();
            special_tracking['Chip/Well Name_store_index'] = 1;
            special_tracking['matrix_item_pk_store_value'] = $('#matrix_item_pk').text();
            special_tracking['matrix_item_pk_store_index'] = indy_matrix_item_list.indexOf($('#matrix_item_name').text());
        }
        console.log(special_tracking)

        let current_sample_label = '';
        let index_sample_counter = 1;

        for (var higlighted_cell_index = 0; higlighted_cell_index < metadata_highlighted.length; higlighted_cell_index++) {
            // what is the row and column number of the attribute of the highlighted cell in the table
            var tirow = metadata_highlighted[higlighted_cell_index]['metadata_highlighted_tirow'];
            var ticol = metadata_highlighted[higlighted_cell_index]['metadata_highlighted_ticol'];
            var tlcol = metadata_highlighted[higlighted_cell_index]['metadata_highlighted_tlcol'];

            console.log("tlcol ",tlcol)

            // what row of the metadata_lod is being changed?             
            var ticol_in_metadata_lod = ticol;
            var tirow_in_metadata_lod = tirow - 1;

            if (replace_or_empty === 'empty') {
                if (tlcol === 'Sample Label') {
                    if (metadata_lod[metadata_lod_row]['Data Attached'] == 'no') {
                         metadata_lod[tirow_in_metadata_lod][tlcol] = '';
                    }
                } else {
                    metadata_lod[tirow_in_metadata_lod][tlcol] = '';
                }
            } else {
                // replace

                // HARDCODE alert
                if (tlcol === 'Sample Label') {
                    // choices HARDCODED in forms.py
                    // sample_option_choices = (
                    // ('clt', 'Chip/Well - Location - Time'),
                    // ('sn1', 'Sample-1 to Sample-99999 etc'),
                    // ('sn2', 'Sample-01 to Sample-99'),
                    // ('sn3', 'Sample-001 to Sample-999'),

                    if (current_sample_pattern === 'clt') {
                        // Sample label should always be after the updates to the other metadata because of the order of the columns in the table
                        // if the order changes, this will break, and will need to redesign!!!!
                        current_sample_label = metadata_lod[tirow_in_metadata_lod]['Chip/Well Name']
                            + '-' + metadata_lod[tirow_in_metadata_lod]['Sample Location']
                            + '-D' + metadata_lod[tirow_in_metadata_lod]['Sample Time (Day)']
                            + ':H' + metadata_lod[tirow_in_metadata_lod]['Sample Time (Hour)']
                            + ':M' + metadata_lod[tirow_in_metadata_lod]['Sample Time (Minute)'];
                    } else if (current_sample_pattern === 'sn1') {
                        current_sample_label = 'Sample-' + index_sample_counter;
                    } else if (current_sample_pattern === 'sn2') {
                        if (index_sample_counter < 10) {
                            current_sample_label = 'Sample-0' + index_sample_counter;
                        } else {
                            current_sample_label = 'Sample-' + index_sample_counter;
                        }
                    } else {
                        // sn3
                        if (index_sample_counter < 10) {
                            current_sample_label = 'Sample-00' + index_sample_counter;
                        } else if (index_sample_counter < 100) {
                            current_sample_label = 'Sample-00' + index_sample_counter;
                        } else {
                            current_sample_label = 'Sample-' + index_sample_counter;
                        }
                    }
                    index_sample_counter = index_sample_counter + 1;
                }

                // when replace, sample location can ONLY be duplicate!
                // HARDCODE alert
                if (tlcol === 'Sample Location') {
                    // only replace if given a new one
                    if (special_tracking['Sample Location_store_value'].length > 0) {
                        metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking['Sample Location_store_value'];
                        metadata_lod[tirow_in_metadata_lod]['sample_location_pk'] = special_tracking['sample_location_pk_store_value'];
                    }
                } else if (tlcol === 'Sample Label') {
                    if (metadata_lod[tirow_in_metadata_lod]['Data Attached'] == 'no') {
                        // note that, if the Sample Label is locked (Data Attached), should not have been allowed to be highlighted - but checked in case
                        metadata_lod[tirow_in_metadata_lod][tlcol] = current_sample_label;
                    }
                } else {
                    // Status - we are replace with the fields that can be duplicate or increment
                    if (page_radio_duplicate_value === 'duplicate') {
                        if (tlcol === 'Sample Time (Day)') {
                            if (special_tracking[tlcol+'_store_value'].length > 0) {
                                metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking[tlcol+'_store_value'];
                            }
                        } else if (tlcol === 'Sample Time (Hour)') {
                            if (special_tracking[tlcol+'_store_value'].length > 0) {
                                metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking[tlcol+'_store_value'];
                            }
                        } else if (tlcol === 'Sample Time (Minute)') {
                            if (special_tracking[tlcol+'_store_value'].length > 0) {
                                metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking[tlcol+'_store_value'];
                            }
                        } else if (tlcol === 'Chip/Well Name') {
                            if (special_tracking[tlcol+'_store_value'].length > 0) {
                                metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking[tlcol+'_store_value'];
                                metadata_lod[tirow_in_metadata_lod]['matrix_item_pk'] = special_tracking['matrix_item_pk_store_value'];
                            }
                        }
                    } else {
                        // increment - make the change then set up the next one
                        // note: the first one (acts as duplicate)
                        if (tlcol === 'Sample Time (Day)') {
                            if (special_tracking[tlcol+'_store_value'].length > 0) {
                                metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking[tlcol+'_store_value'];
                                let numval = parseFloat(special_tracking[tlcol+'_store_value'])+ parseFloat($('#increment_value').val());
                                special_tracking[tlcol+'_store_value'] = numval.toString();
                                special_tracking[tlcol+'_store_index'] = special_tracking[tlcol + '_index'] + 1;
                            }
                        } else if (tlcol === 'Sample Time (Hour)') {
                            if (special_tracking[tlcol+'_store_value'].length > 0) {
                                metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking[tlcol+'_store_value'];
                                let numval = parseFloat(special_tracking[tlcol+'_store_value'])+ parseFloat($('#increment_value').val());
                                special_tracking[tlcol+'_store_value'] = numval.toString();
                                special_tracking[tlcol+'_store_index'] = special_tracking[tlcol + '_index'] + 1;
                            }
                        } else if (tlcol === 'Sample Time (Minute)') {
                            if (special_tracking[tlcol+'_store_value'].length > 0) {
                                metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking[tlcol+'_store_value'];
                                let numval = parseFloat(special_tracking[tlcol+'_store_value'])+ parseFloat($('#increment_value').val());
                                special_tracking[tlcol+'_store_value'] = numval.toString();
                                special_tracking[tlcol+'_store_index'] = special_tracking[tlcol + '_index'] + 1;
                            }
                        } else if (tlcol === 'Chip/Well Name') {
                            if (special_tracking[tlcol+'_store_value'].length > 0) {
                                metadata_lod[tirow_in_metadata_lod][tlcol] = special_tracking[tlcol+'_store_value'];
                                metadata_lod[tirow_in_metadata_lod]['matrix_item_pk'] = special_tracking['matrix_item_pk_store_value'];

                                // what is the index of the current matrix item name in alphabetical list of names?
                                var index_in_indy_matrix_item_list = indy_matrix_item_list.indexOf(metadata_lod[tirow_in_metadata_lod][tlcol]);
                                // what is the index of the new (skip index by increment)
                                var new_index = index_in_indy_matrix_item_list + parseInt($('#increment_value').val());
                                // is the new index in the list, or too high a number?
                                if (index_in_indy_matrix_item_list >= 0 && new_index < indy_matrix_item_list.length) {
                                    // what is the new matrix item name? and the new pk
                                    let new_matrix_item_name = indy_matrix_item_list[new_index];
                                    let new_matrix_item_pk = indy_matrix_item_name_to_pk_dict[new_matrix_item_name];

                                    special_tracking['Chip/Well Name_store_value'] = new_matrix_item_name;
                                    special_tracking['Chip/Well Name_store_index'] = special_tracking[tlcol + '_index'] + 1;
                                    special_tracking['matrix_item_pk_store_value'] = new_matrix_item_pk;
                                    special_tracking['matrix_item_pk_store_index'] = indy_matrix_item_list.indexOf(new_matrix_item_name);

                                } else {
                                    // no more left in index, just use the current one, do not need to change anything else
                                    special_tracking[tlcol+'_store_index'] = special_tracking[tlcol + '_index'] + 1;
                                }
                            }
                        }
                    }
                }
            }
            console.log(special_tracking)
        }
    }

    // END - the 4 actions functions

});
