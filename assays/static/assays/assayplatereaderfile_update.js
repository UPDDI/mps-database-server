$(document).ready(function () {

    // START SECTION TO SET GLOBAL MOST VARIABLES
    // set global variables
    let global_file_plate_this_file_id = 0;
    let global_file_plate_number_blank_columns = 0;
    let global_file_plate_file_delimiter = "";
    let global_file_plate_form_plate_size = 0;

    let global_file_plate_form_number_blocks = 0;
    let global_file_plate_form_number_blank_columns = 0;
    
    let global_file_iblock_delimited_start = [];
    let global_file_iblock_delimited_end = [];
    let global_file_iblock_line_start = [];
    let global_file_iblock_line_end = [];
    let global_file_iblock_data_block_metadata = [];
    let global_file_iblock_data_block = [];

    let global_file_set_delimiter = "";
    let global_file_set_plate_size = 0;
    let global_file_set_number_blocks = 0;
    let global_file_set_number_blank_columns = 0;

    let global_file_file_format_select = 0;
    let global_file_selected_plate_map_size = 0;
    let global_file_selected_plate_map_time_unit = "";
    let global_file_plate_map_changed_id = 0;

    let global_file_plate_map_changed_formset_index = 0;

    let global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
    // assuming the extra form of the formset will be last, which will be if the extra is the only formset
    let global_file_extra_formset_number = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
    
    let global_file_qc_messages = [];


    // on load, change the appearance of the overwrite sample time unit in each formset,
    // if there is a platemap else, hide the NONE (need each since calling ajax, if use for loop, problems)
    let global_file_formset_platemap_id_list = [];
    let global_file_formset_platemap_value_list = [];
    let global_file_formset_time_unit_id_list = [];
    // want to use the same ajax call for two purposes, so, set a variable to know which purpose
    let global_file_platemap_find_size_and_time_unit = 'load';

    // load the para||el plate map doc id, time unit doc id, and plate map pk id for all formsets
    for ( var idx = 0, ls = global_file_formset_count; idx < ls; idx++ ) {
        let get_this = "#id_assayplatereadermapdatafileblock_set-" + idx + "-assayplatereadermap";
        let set_this = "#id_assayplatereadermapdatafileblock_set-" + idx + "-form_selected_plate_map_time_unit";
        global_file_formset_time_unit_id_list.push(set_this);
        global_file_formset_platemap_id_list.push(get_this);
        // console.log($(get_this))
        // another get method - HANDY
        let get_pk_id = $(get_this)[0].value;
        global_file_formset_platemap_value_list.push(get_pk_id);
    }

     // END SECTION TO SET MOST GLOBAL VARIABLES

    // START SECTION FOR LOADING

    // deal with the extra formset - find which it is when there is more than the extra
    if (global_file_formset_count > 1) {
        showOverwriteSampleTimeInfo();
        global_file_plate_form_plate_size = $('#id_upload_plate_size').val();
        // when do form manual validation (clean) on existing, if there is a clean error
        // the extra formset kicks into being a valid formset and it will ADDed table during save
        // I tested a few methods for dealing with this
        // deleting did not work well when returning to edit (without form validation error)
        // instead, mark the formset for deletion by checking the delete box
        // the blocks are identified when the data_block = 999
        // remember, the formset number is 1 to ? whereas the index number for the set is 0 to ?
        for (var idx = 0, ls = global_file_formset_count; idx < ls; idx++) {
            let data_block_id = '#id_assayplatereadermapdatafileblock_set-' + idx + '-data_block';
            let my_data_block_value = $(data_block_id).val();
            if (my_data_block_value == 999) {
                let delete_block_id = '#id_assayplatereadermapdatafileblock_set-' + idx + '-DELETE';
                // console.log('delete_block_id  ',delete_block_id )
                $(delete_block_id).prop('checked', true);
                let my_formset_number = idx + 1;
                let my_formset_id = '#id_formset_' + my_formset_number;
                // console.log('my_formset_id ',my_formset_id)

                // option to hide the extra
                $(my_formset_id).addClass('hidden');

                // option to delete the formset - used for testing, save as example for later
                // deleteForm('id_formset_' + idx+1, 'assayplatereadermapdatafileblock_set');
            } else {
                // these are the existing formset that were previously saved by are not marked for deletion
                // these should not ever be cloned, so, okay to reformat them here
                // we want these to remain and display
                $('#id_assayplatereadermapdatafileblock_set-' + idx + '-assayplatereadermap').addClass('form-control');
            }
        }
        // get the unit associated with plates for previously saved formsets
        // send the list of platemap pks to the function
        // sending the list since ajax call and we need to control the order
        findSizeAndTimeUnitOfPlateSelectedInDropDown(global_file_formset_platemap_value_list);
    } else {
        // this is the condition where there are no saved blocks yet
        // hide the extra formset - it will be cloned, so, do not selectize the platemap or cloning will NOT work
       $('#id_formset_' + global_file_extra_formset_number).addClass('hidden');
    }

    function showOverwriteSampleTimeInfo() {
        $('#overwrite_sample_time_row').removeClass('hidden');
    }

    // apply styles to formsets
    // tried other ways of doing this, including css and form widget, but this worked the best
    // these fields should not be edited by the user
    let index_css = 0;
    while (index_css < global_file_formset_count) {
        // console.log(index_css)
        let element_id1 = 'id_assayplatereadermapdatafileblock_set-' + index_css + '-data_block';
        document.getElementById(element_id1).style.borderStyle = 'none';
        let element_id2 = 'id_assayplatereadermapdatafileblock_set-' + index_css + '-form_selected_plate_map_time_unit';
        document.getElementById(element_id2).style.borderStyle = 'none';
        document.getElementById(element_id1).readOnly = true;
        document.getElementById(element_id2).readOnly = true;
        index_css = index_css + 1;
    }
    // apply style, tried other ways, this worked best
    document.getElementById('id_upload_plate_size').style.borderStyle = 'none';

    // END SECTION FOR LOADING

    // START SECTION THAT SETS TOOLTIPS
    // set lists for the tooltips
    // just add in para||el if need more tooltips
    let global_file_tooltip_selector = [
          '#file_description_tooltip'
        , '#file_plate_size_tooltip'
        , '#file_file_delimiter_tooltip'
        , '#file_overwrite_sample_time_tooltip'
        , '#file_number_data_blocks_tooltip'
        , "#file_file_format_select_tooltip"
        , '#file_number_blank_columns_tooltip'
        ,
    ,];
    let global_file_tooltip_text = [
          "Description for the file (optional)."
        , "Select one if using the auto detect file block feature. Best results will come from selecting the size plate used in the plate reader."
        , "This can be set by the user or auto detected."
        , "If a value is provided, this sample time will be used for this whole data block (sample times in the selected plate map will be overwritten with this value)."
        , "The number of blocks of data in the file."
        , "Selecting a specific format will ONLY work the follow follows that format - exactly."
        , "Set the number of blank columns to the left of the data block."
        ,
    ,];
    // set the tooltips
    $.each(global_file_tooltip_selector, function (index, show_box) {
        $(show_box).next().html($(show_box).next().html() + make_escaped_tooltip(global_file_tooltip_text[index]));
    });
    // END SECTION THAT SETS TOOLTIPS

    // START - SECTION FOR CHANGES ON PAGE

    // toggle to hide/show auto detect help section
    $("#reviewButtonHelp").click(function() {
        $("#auto_detect_help_section").toggle();
    });

    $("#runQualityControl").click(function() {
        // Scroll through the blocks and send inform for each block to QC
        global_file_qc_messages = [];
        alert('in development - not working yet. When working, will show a list of the problems detected. \n');
        // loop through the above named list of error messages
    });

    // where user changes anything about a block
    // save the block number as 1 (instead of 0) so changes can be made on save to values in platemap
    // do not know which is the selected block, so find it by class change
    $(".form2-row").change(function() {
        // console.log($(this).context.id)
        let formset_id = $(this).context.id;
        let block_number = formset_id.substring(11, );
        // form_changed_something_in_block - not really using this to change what is removed/added during submit..may add later??
        let block_number_id = "#id_assayplatereadermapdatafileblock_set-" + String(block_number-1) + "-form_changed_something_in_block";
        // console.log("changed in block: ",block_number_id)
        // 1 for something changed in the block, 0 for nothing changed in the block
        $(block_number_id).val(1);
    });    

    // select dropdown for the file format to work with
    $("#id_se_file_format_select").change(function() {
        // console.log($(this))
        global_file_file_format_select = $(this).val();
        if (global_file_file_format_select > 0) {
            showOverwriteSampleTimeInfo()
        }
        let myt = $(this).text();
        // console.log("picked file format ",myt)
        // HARDCODED PLATE SIZE OPTION
        //     (0,    'Select a File Format'),
        //     (9999, 'Full Auto Detect (Some Rules Apply)'),
        //     (1, 'Softmax Pro 5.3 (Molecular Devices M5 Series)'),
        //     (2, 'Wallac EnVision Manager Version 1.12 (EnVision)'),

        // What can be set in advance? Really, nothing
        // if (global_file_file_format_select === 1 || global_file_file_format_select === 2) {
        //     // tab delimited
        //     global_file_plate_file_delimiter = 'tab';
        //     $("#id_file_delimiter").selectize()[0].selectize.setValue(global_file_plate_file_delimiter);
        //
        //     $("#set_delimiter").closest('div').removeClass('off');
        //     $("#set_delimiter").prop('checked', true);
        //     global_file_set_delimiter = $("#set_delimiter").prop('checked');
        // } else if (global_file_file_format_select === 9999) {
        //
        // } else {
        //
        // }

        // Important: this was designed with the assumption that the name of the file would contain the plate size o
        // if (myt.includes("(24)") || myt.includes("(96)") || myt.includes("(384)")) {
        //     if(myt.includes("(24)")) {
        //         global_file_plate_form_plate_size = 24;
        //     } else if (myt.includes("(96)")) {
        //         global_file_plate_form_plate_size = 96;
        //     } else if (myt.includes("(384)")) {
        //         global_file_plate_form_plate_size = 384;
        //     }
        //     // the toggle class is set in an auto created div class above the switch
        //     // get div where the class is set
        //     $("#set_plate_size").closest('div').removeClass('off');
        //     $("#set_plate_size").prop('checked', true);
        //     global_file_set_plate_size = $("#set_plate_size").prop('checked');
        //     // console.log("set ",global_file_set_plate_size)
        //     // $("#id_se_form_plate_size").selectize()[0].selectize.setValue(global_file_plate_form_plate_size);
        //
        //     // will need an auto call to the function after develop this
        //
        // } else {
        //     // the full auto detect with no plate size - make = 24 but do NOT set
        //     $("#set_plate_size").closest('div').addClass('off');
        //     $("#set_plate_size").prop('checked', false);
        //     global_file_set_plate_size = $("#set_plate_size").prop('checked');
        //     // console.log("not set ",global_file_set_plate_size)
        //     global_file_plate_form_plate_size = 24;
        //     $("#id_se_form_plate_size").selectize()[0].selectize.setValue(global_file_plate_form_plate_size);
        // }
        // $("#id_upload_plate_size").val(global_file_plate_form_plate_size);

        // make sure the size of the list is such that on an auto method is > 9000
        if (global_file_file_format_select > 9000) {
            $('.auto-detect-section').removeClass('hidden');
        } else if (global_file_file_format_select == 0) {
            //don't do anything
        } else {
            $('.auto-detect-section').addClass('hidden');
            // call the script immediately since not using full auto
            reviewPlateReaderFile();
        }
    });

    // when user selects a plate map for a block of data
    // find which block of data was changed  - by class change
    $(".get-plate-map-changed").change(function() {
        // console.log($(this))
        // this can only happen after blocks have been added and plate size for file determined
        // confirm that the plate is the same size as the one picked in the file format
        // what plate was selected and what is it's size?
        global_file_selected_plate_map_size = 0;
        global_file_selected_plate_map_time_unit = "";
        // console.log($(this).closest('select'))
        // console.log($(this).closest('select').context)
        // console.log($(this).closest('select').context.childNodes[1].id)
        // how to get the value of the pk of the thing selected - HANDY
        global_file_plate_map_changed_id = $(this).closest('select').context.childNodes[1].id;
        // console.log("my id ", global_file_plate_map_changed_id)
        // my_id = id_assayplatereadermapdatafileblock_set-0-assayplatereadermap
        let find_index = global_file_plate_map_changed_id.split("-")[1];
        global_file_plate_map_changed_formset_index = parseInt(find_index);
        // console.log($(this).text())   --- this returns the WHOLE LIST --- not what what
        //$('#id_assayplatereadermapdatafileblock_set-0-assayplatereadermap')[0].value  == 39 which what want
        let platemap_pk_list = [];
        platemap_pk_list.push(document.getElementById(global_file_plate_map_changed_id).value);
        // set this so know when call function if it is a change or load
        global_file_platemap_find_size_and_time_unit = 'change';        
        // find the plate size of the plate just selected - with the pk of key_value
        findSizeAndTimeUnitOfPlateSelectedInDropDown(platemap_pk_list)
    });

    function findSizeAndTimeUnitOfPlateSelectedInDropDown(platemap_id_list) {
        // console.log("platemap_id_list ", platemap_id_list)
        // to send in ajax call, need this - HANDY
        let platemap_id_stringify = JSON.stringify(platemap_id_list);
        global_file_selected_plate_map_size = 0;
        global_file_selected_plate_map_time_unit = "";
        // console.log(platemap_id_stringify)

        var data = {
            call: 'fetch_plate_reader_data_block_plate_map_size',
            platemap_id_stringify: platemap_id_stringify,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };

        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );

        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                window.spinner.stop();
                if (json.errors) {
                    // Display errors
                    alert(json.errors);
                }
                else {
                    let exist = true;
                    findSizeAndTimeUnitOfPlateSelectedInDropDownAndTimeUnit(json, exist);
                    // alert('' +
                    //     '\n\nPlease note that changes will not be made until you press the "Submit" button at the bottom of the page.');
                }
            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();
                alert('An unknown error has occurred. \n');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    let findSizeAndTimeUnitOfPlateSelectedInDropDownAndTimeUnit = function (json, exist) {
        let platemap_size_and_unit = json.platemap_size_and_unit;
        // console.log(global_file_platemap_find_size_and_time_unit)

        if (global_file_platemap_find_size_and_time_unit == 'change'){
            // this is an change event and there is only ONE that is changed so just need to handle ONE
            global_file_selected_plate_map_size = platemap_size_and_unit[0][('device')];
            global_file_selected_plate_map_time_unit = platemap_size_and_unit[0][('time_unit')];
            if (global_file_selected_plate_map_size == global_file_plate_form_plate_size) {
                // console.log(" global_file_selected_plate_map_size ",  global_file_selected_plate_map_size)
                // console.log("global_file_plate_map_changed_formset_index ",global_file_plate_map_changed_formset_index)
                let this_unit_id = '#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-form_selected_plate_map_time_unit';
                // console.log('this_unit_id' ,this_unit_id)
                // console.log('global_file_selected_plate_map_time_unit ',global_file_selected_plate_map_time_unit)
                // $(this_unit_id).text(global_file_selected_plate_map_time_unit);
                $(this_unit_id).val(global_file_selected_plate_map_time_unit);

                let this_data_block = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-data_block').val();
                let this_line_start = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-line_start').val();
                let this_line_end = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-line_end').val();
                let this_delimited_start = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-delimited_start').val();
                let this_delimited_end = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-delimited_end').val();

                global_file_qc_messages = [];
                doQualityCheck(this_data_block, global_file_plate_form_plate_size, this_line_start, this_line_end, this_delimited_start, this_delimited_end);
                $.each(global_file_qc_messages, function (qc_index, qc_item) {
                    alert(qc_item + ' \n');
                });
            } else {
                alert('The plate map selected for this block does not match the plate size selected with the file format (or determined using the auto detect). Select a plate map of matching size.\n');
                // invalid plate selected, clear the selection, find
                let myid_plus_option = "#" + global_file_plate_map_changed_id + " option"
                // clear a selections - HANDY
                $(myid_plus_option).removeProp('selected');
                let this_unit_id = '#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-form_selected_plate_map_time_unit';
                $(this_unit_id).val("");
            }
        } else {
            // this is an onload event and will handle the list of all the formsets
            // just get the time unit from the selected platemap if one is selected
            // use the para||el lists
            // global_file_formset_time_unit_id_list.push(set_this);
            // global_file_formset_platemap_id_list.push(get_this);

            // console.log("calling each")
            $.each(platemap_size_and_unit, function (index, item) {
                // console.log('platemap_size_and_unit d ', index)
                // console.log('platemap_size_and_unit t ', item)
                // $(global_file_formset_time_unit_id_list[index]).text(platemap_size_and_unit[index][('time_unit')]);
                $(global_file_formset_time_unit_id_list[index]).val(platemap_size_and_unit[index][('time_unit')]);
            });
        }
    };

    function doQualityCheck(this_data_block, this_plate_map_size, this_line_start, this_line_end, this_delimited_start, this_delimited_end) {
        // will come here for each block, run qc and fill a message list with errors
        // QC is here - check the plate size and the size of the selected block

        // console.log(this_data_block)
        // console.log(this_plate_map_size)
        // console.log(this_line_start)
        // console.log(this_line_end)
        // console.log(this_delimited_start)
        // console.log(this_delimited_end)

        this_data_block = parseInt(this_data_block);
        this_plate_map_size = parseInt(this_plate_map_size);
        // these come in as indexes of the file, not line numbers
        this_line_start = parseInt(this_line_start);
        this_line_end = parseInt(this_line_end);
        this_delimited_start = parseInt(this_delimited_start);
        this_delimited_end = parseInt(this_delimited_end);

        let number_columns = 1 + this_delimited_end - this_delimited_start;
        let number_rows = 1 + this_line_end - this_line_start;
        let calculated_number_wells = number_columns * number_rows;

        // console.log(number_columns)
        // console.log(number_rows)
        // console.log(this_plate_map_size)

        if (calculated_number_wells == this_plate_map_size) {
            // okay - add other QC checks later if needed
        } else {
            let this_message = 'The plate size (' + String(this_plate_map_size) + ') and block information for block ' + String(this_data_block) + ' do not match (' + String(calculated_number_wells) + ' wells). This must be corrected prior to submitting this block information.';
            global_file_qc_messages.push(this_message);
        }
    }

    $("#reviewDataButton").click(function() {
        reviewPlateReaderFile();
    });

    function reviewPlateReaderFile() {
        // this is the function to read the file and determine the blocks
        // console.log("the selected file format ", global_file_file_format_select)

        // must reset these or they keep appending with ajax calls
        global_file_iblock_delimited_start = [];
        global_file_iblock_delimited_end = [];
        global_file_iblock_line_start = [];
        global_file_iblock_line_end = [];
        global_file_iblock_data_block = [];
        global_file_iblock_data_block_metadata = [];

        // let this_file_id = parseInt(document.getElementById ("this_file_id").innerText.trim());
        try { global_file_plate_this_file_id = parseInt(document.getElementById ("this_file_id").innerText.trim());
        }
        catch(err) { global_file_plate_this_file_id = $("#this_file_id").val();
        }
        // console.log('global_file_plate_this_file_id ', global_file_plate_this_file_id)
        try { global_file_plate_file_delimiter = $("#id_file_delimiter").val();
        }
        catch(err) { global_file_plate_file_delimiter = $("#id_file_delimiter").selectize()[0].selectize.items[0];
        }
        try { global_file_plate_form_plate_size = $("#id_se_form_plate_size").val();
        }
        catch(err) { global_file_plate_form_plate_size = $("#id_se_form_plate_size").selectize()[0].selectize.items[0];
        }
        $("#id_upload_plate_size").val(global_file_plate_form_plate_size);
        try { global_file_plate_form_number_blocks = $("#id_form_number_blocks").val();
        }
        catch(err) { global_file_plate_form_number_blocks = $("#id_form_number_blocks").selectize()[0].selectize.items[0];
        }
        try { global_file_plate_form_number_blank_columns = $("#id_form_number_blank_columns").val();
        }
        catch(err) { global_file_plate_form_number_blank_columns = $("#id_form_number_blank_columns").selectize()[0].selectize.items[0];
        }
        global_file_set_delimiter = $("#set_delimiter").prop('checked');
        global_file_set_plate_size = $("#set_plate_size").prop('checked');
        global_file_set_number_blocks = $("#set_number_blocks").prop('checked');
        global_file_set_number_blank_columns = $("#set_number_blank_columns").prop('checked');

        // console.log(global_file_plate_this_file_id)
        // console.log(global_file_plate_file_delimiter)
        // console.log(global_file_plate_form_plate_size)
        // console.log(global_file_plate_form_number_blocks)
        // console.log(global_file_set_delimiter)
        // console.log(global_file_set_plate_size)
        // console.log(global_file_set_number_blocks)
        // console.log(global_file_set_number_blank_columns)

        var data = {
            call: 'fetch_review_plate_reader_data_file',
            this_file_id: global_file_plate_this_file_id,
            this_file_format_selected: global_file_file_format_select,
            file_delimiter: global_file_plate_file_delimiter,
            form_plate_size: global_file_plate_form_plate_size,
            form_number_blocks: global_file_plate_form_number_blocks,
            form_number_blank_columns: global_file_plate_form_number_blank_columns,
            set_delimiter: global_file_set_delimiter,
            set_plate_size: global_file_set_plate_size,
            set_number_blocks: global_file_set_number_blocks,
            set_number_blank_columns: global_file_set_number_blank_columns,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };

        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );

        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                window.spinner.stop();
                if (json.errors) {
                    // Display errors
                    alert(json.errors);
                }
                else {
                    let exist = true;
                    processDataFromBlockDetect(json, exist);
                    // alert('' +
                    //      '\n\nPlease note that changes will not be made until you press the "Submit" button at the bottom of the page.');
                }
            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();
                alert('An unknown error has occurred. \n');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    let processDataFromBlockDetect = function (json, exist) {
        let file_block_info = json.file_block_info;
        // console.log(file_block_info)
        // note this method if needed $("#id_device").selectize()[0].selectize.setValue(pm_device);
        let add_blocks = 0;
        // get info that is the same for all out of the first dictionary
        let calculated_number_of_blocks = file_block_info[0][('calculated_number_of_blocks')];

        if (global_file_set_plate_size == false) {
            // make the plate size show what was identified
            global_file_plate_form_plate_size = file_block_info[0]['plate_size'];
            $("#id_se_form_plate_size").selectize()[0].selectize.setValue(global_file_plate_form_plate_size);
            $("#id_upload_plate_size").val(global_file_plate_form_plate_size);
        }
        // do not need else because if the plate size is given and set, it is used

        if (global_file_set_delimiter == false) {
            // make the delimiter show what was identified
            global_file_plate_file_delimiter = file_block_info[0]['block_delimiter'];
            $("#id_file_delimiter").selectize()[0].selectize.setValue(global_file_plate_file_delimiter);
        }
        // do not need else because if the delimiter is given and set, it is used

        if (global_file_set_number_blocks == false) {
            global_file_plate_form_number_blocks = calculated_number_of_blocks;
            $("#id_form_number_blocks").val(global_file_plate_form_number_blocks);
        } else if (global_file_set_number_blocks == true && calculated_number_of_blocks == global_file_plate_form_number_blocks) {
            // pass
        } else {
            // (set_number_blocks == True && calculated_number_of_blocks != global_file_plate_form_number_blocks)
            alert('The number of blocks specified does not match the number detected. Try specifying the plate size and check to make sure the file follows the rules. If the auto reader still will not return the desired block locations, specify the number of blocks and perform auto detect, then fill in the information for each block manually.\n');
            // console.log(calculated_number_of_blocks)
            // console.log(global_file_plate_form_number_blocks)
            add_blocks = global_file_plate_form_number_blocks - calculated_number_of_blocks;
        }
        // need this global_file_plate_form_number_blocks

        if (global_file_set_number_blank_columns == false) {
            global_file_plate_number_blank_columns = file_block_info[0]['delimited_start'];
            // console.log("blank columns: ",global_file_plate_number_blank_columns)
            $("#id_form_number_blank_columns").val(global_file_plate_number_blank_columns);
        }
        // do not need else because if the number of blank columns is given and set, it is used

        // console.log(global_file_plate_this_file_id)
        // console.log(global_file_plate_file_delimiter)
        // console.log(global_file_plate_form_plate_size)
        // console.log(global_file_plate_form_number_blocks)
        // console.log(global_file_plate_form_number_blank_columns)
        // console.log(calculated_number_of_blocks)
        // console.log(global_file_set_delimiter)
        // console.log(global_file_set_plate_size)
        // console.log(global_file_set_number_blocks)
        // console.log(global_file_set_number_blank_columns)

        // fill para||el arrays for the number of blocks determined (or set) to be needed
        idx = 0;
        let data_block = idx + 1;
        $.each(file_block_info, function(index, each) {
            // console.log("each block", each)
            global_file_iblock_data_block.push(data_block);
            global_file_iblock_data_block_metadata.push(each.data_block_metadata);
            global_file_iblock_delimited_start.push(each.delimited_start);
            global_file_iblock_delimited_end.push(each.delimited_end);
            global_file_iblock_line_start.push(each.line_start);
            global_file_iblock_line_end.push(each.line_end);
            idx = idx + 1;
            data_block = data_block + 1;
        });

        if (add_blocks > 0) {
            // the user set a number of blocks greater than what was determined, so need to add place holder blocks
            for ( var idx = 0, ls = add_blocks; idx < ls; idx++ ) {
                // console.log("each block", idx)
                global_file_iblock_data_block.push(data_block);
                global_file_iblock_data_block_metadata.push(data_block_metadata);
                global_file_iblock_delimited_start.push(0);
                global_file_iblock_delimited_end.push(0);
                global_file_iblock_line_start.push(0);
                global_file_iblock_line_end.push(0);
                data_block = data_block + 1;
            }
        } else if (add_blocks == 0) {
            //    pass
        } else {
            // the user set a number of blocks less than what was determined, so need to remove some blocks
            add_blocks = add_blocks*(-1)
            for ( var idx = 0, ls = add_blocks; idx < ls; idx++ ) {
                global_file_iblock_data_block.pop();
                global_file_iblock_data_block_metadata.pop();
                global_file_iblock_delimited_start.pop();
                global_file_iblock_delimited_end.pop();
                global_file_iblock_line_start.pop();
                global_file_iblock_line_end.pop();
            }
        }

        // The para||el lists to fill the fields should now be ready, in order, and of the correct length
        // console.log(global_file_iblock_data_block)
        // console.log(global_file_iblock_data_block_metadata)
        // console.log(global_file_iblock_delimited_start)
        // console.log(global_file_iblock_delimited_end)
        // console.log(global_file_iblock_line_start)
        // console.log(global_file_iblock_line_end)

        // if this has been called, we are starting finding blocks
        // could be for first time or repeated but is prior to first submit with blocks
        // remove all formsets except the first one, so can clone it
        // note that - this only works prior to first submit - once saved, this does not work well
        global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
        while (global_file_formset_count > 1) {
            // console.log('global_file_formset_count ', global_file_formset_count)
            deleteForm('id_formset_' + global_file_formset_count, 'assayplatereadermapdatafileblock_set');
            global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
        }

        // add formsets until = number of blocks
        // idx should be number of formsets minus 1
        // will copy in the saved extra formset - global_file_extra_formset
        idx = 0;
        while (idx < global_file_plate_form_number_blocks) {
            // console.log("----------------------")
            let formset_number = idx+1;
            // console.log("idx ", idx)
            // console.log("formset_number ", formset_number)
            global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
            // console.log('global_file_formset_count pre clone ', global_file_formset_count)

            if (idx > 0) {
                // console.log($('.form2-row:last'))
                cloneMore('.form2-row:last', 'assayplatereadermapdatafileblock_set', idx);
            }
            let this_formset = '#id_formset_' + formset_number;
            $(this_formset).removeClass('hidden');

            let dblock = '#id_assayplatereadermapdatafileblock_set-' + idx + '-data_block';
            let dblockmetadata = '#id_assayplatereadermapdatafileblock_set-' + idx + '-data_block_metadata';
            let lstart = '#id_assayplatereadermapdatafileblock_set-' + idx + '-line_start';
            let lend = '#id_assayplatereadermapdatafileblock_set-' + idx + '-line_end';
            let dstart = '#id_assayplatereadermapdatafileblock_set-' + idx + '-delimited_start';
            let dend = '#id_assayplatereadermapdatafileblock_set-' + idx + '-delimited_end';
            // What comes back from the ajax call?
            $(dblock).val(global_file_iblock_data_block[idx]);
            $(dblockmetadata).val(global_file_iblock_data_block_metadata[idx]);
            // The INDEXES of the top and bottom lines, and the first and last column for each block
            // add 1 to get the line or column number
            $(lstart).val(global_file_iblock_line_start[idx]+1);
            $(lend).val(global_file_iblock_line_end[idx]+1);
            $(dstart).val(global_file_iblock_delimited_start[idx]+1);
            $(dend).val(global_file_iblock_delimited_end[idx]+1);

            global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
            // console.log('global_file_formset_count post clone ', global_file_formset_count)
            idx = idx + 1;
        }

        // Now that formsets are in use, show as form control (never turn the selectize back on, argh)
        global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
        let index_css = 0;
        while (index_css < global_file_formset_count) {
            $('#id_assayplatereadermapdatafileblock_set-' + index_css + '-assayplatereadermap').addClass('form-control selectized');
            index_css = index_css + 1;
        }
    };

    // More Functions
    // https:// simpleit.rocks/python/django/dynamic-add-form-with-add-button-in-django-modelformset-template/
    // https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0
    // function updateElementIndex(el, prefix, ndx) {
    //     var id_regex = new RegExp('(' + prefix + '-\\d+)');
    //     var replacement = prefix + '-' + ndx;
    //     if ($(el).prop("for")) $(el).prop("for", $(el).prop("for").replace(id_regex, replacement));
    //     if (el.id) el.id = el.id.replace(id_regex, replacement);
    //     if (el.name) el.name = el.name.replace(id_regex, replacement);
    // }
    function cloneMore(selector, prefix, index) {
        // console.log("function index bring in ", index)
        var newElement = $(selector).clone(true);
        var total = $('#id_' + prefix + '-TOTAL_FORMS').val();
        newElement.find(':input:not([type=button]):not([type=submit]):not([type=reset])').each(function() {
            var name = $(this).attr('name').replace('-' + (total-1) + '-', '-' + total + '-');
            var id = 'id_' + name;
            $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        });

        // An interesting thing - at one point, when dealing with selectized, tried this way
        // var id = $(this).attr('id').replace('-' + (total-1) + '-', '-' + total + '-');
        // console.log("id ", id)
        // var name = id.slice(4,);
        // $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        // The above looked like it worked, until form save, then, the cloned forms were empty.
        // I did not figure out why....keep in case run into again

        // this made the dropdown behave when copied with the formset!
        // SUPER IMPORTANT and HANDY when need to copy formsets with dropdowns - if have selectized, it is a big mess
        // turn the selectized OFF in the form init!
        // eg self.fields['assayplatereadermap'].widget.attrs.update({'class': ' no-selectize'})

        // see what this gives  $(this)[0]
        // why to find type
        // if (typeof $(this).attr('name') === 'undefined')
        // if ($(this)[0].type = 'select-one') {
        // if ($(this).hasClass("selectized")) {

        newElement.find('label').each(function() {
            var forValue = $(this).attr('for');
            if (forValue) {
              forValue = forValue.replace('-' + (total-1) + '-', '-' + total + '-');
              $(this).attr({'for': forValue});
            }
        });
        total++;
        $('#id_' + prefix + '-TOTAL_FORMS').val(total);
        // not sure need all of this, but when comment it out, error...
        $(selector).after(newElement);
        var conditionRow = $('.form-row:not(:last)');
        conditionRow.find('.btn.add-form-row')
        .removeClass('btn-success').addClass('btn-danger')
        .removeClass('add-form-row').addClass('remove-form-row')
        .html('<span class="glyphicon glyphicon-minus" aria-hidden="true"></span>');

        // console.log('newElement2')
        // console.log(newElement)
        var id = 'id_formset_' + total;
        // console.log("try id: ",id)
        $(newElement).attr({'id': id,})
        // console.log('newElement3')
        // console.log(newElement)

        return false;
    }
    //delete
    function deleteForm(id, prefix) {
        // console.log("id ",id)
        var elem = document.getElementById(id);
        elem.parentNode.removeChild(elem);

        global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
        let new_count = global_file_formset_count - 1;
        $('#id_' + prefix + '-TOTAL_FORMS').val(new_count);
        global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
        return false;
    }
    //
    // functions for the tooltips - keep
    function escapeHtml(html) {
        return $('<div>').text(html).html();
    }
    function make_escaped_tooltip(title_text) {
        let new_span = $('<div>').append($('<span>')
            .attr('data-toggle', "tooltip")
            .attr('data-title', escapeHtml(title_text))
            .addClass("glyphicon glyphicon-question-sign")
            .attr('aria-hidden', "true")
            .attr('data-placement', "bottom"));
        return new_span.html();
    }

    // START SECTION OF SPECIALS FOR EXTENDING FEATURES

    // activates Bootstrap tooltips, must be AFTER tooltips are created - keep
    $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
    // END SECTION OF SPECIALS FOR EXTENDING FEATURES

});
