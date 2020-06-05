$(document).ready(function () {
    // START SECTION TO SET GLOBAL MOST VARIABLES
    // set global variables
    let global_check_load = $("#check_load").html().trim();
    if (global_check_load === 'review') {
        // HANDY - to make everything on a page read only
        $('.selectized').each(function() { this.selectize.disable() });
        $(':input').attr('disabled', 'disabled')
    }

    let global_counter_to_check_loopA = 0;
    let global_counter_to_check_loopB = 0;

    let global_file_plate_this_file_id = 0;
    
    let global_file_setting_box_delimiter = "";
    let global_file_setting_box_form_plate_size = 0;
    let global_file_setting_box_form_number_blocks = 0;
    let global_file_setting_box_form_number_blank_columns = 0;
    let global_file_setting_box_form_number_blank_rows = 0;
    
    let global_file_iblock_delimited_start = [];
    let global_file_iblock_delimited_end = [];
    let global_file_iblock_line_start = [];
    let global_file_iblock_line_end = [];
    let global_file_iblock_data_block_metadata = [];
    let global_file_iblock_data_block = [];
    let global_file_iblock_file_list = [[]];

    let global_file_set_delimiter = false;
    let global_file_set_plate_size = false;
    let global_file_set_number_blocks = false;
    let global_file_set_number_blank_columns = false;
    let global_file_set_number_blank_rows = false;
    let global_file_set_format = false;

    let global_file_file_format_select = 0;

    let global_file_selected_a_plate_map_with_this_size = 0;
    let global_file_selected_a_plate_map_with_number_lines_by_plate_size = 0;
    let global_file_selected_a_plate_map_with_number_columns_by_plate_size = 0;
    let global_file_selected_a_plate_map_with_this_time_unit = "";
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
        let set_this = "#id_assayplatereadermapdatafileblock_set-" + idx + "-form_selected_plate_map_time_unit";
        global_file_formset_time_unit_id_list.push(set_this);

        let get_this = "#id_assayplatereadermapdatafileblock_set-" + idx + "-assayplatereadermap";
        global_file_formset_platemap_id_list.push(get_this);

        let get_pk_id = 0;
        // another get method - HANDY - but doesn't work if turned to .value form field
        get_pk_id = $(get_this)[0].value;
        global_file_formset_platemap_value_list.push(get_pk_id);
    }

    // set a default different than in the forms.py as per PI request - but do it here so easy to change again in future
    // keep in mind it is not on the web page if the page is not editable
    global_file_file_format_select = 1;
    try {
        $("#id_se_file_format_select").selectize()[0].selectize.setValue(global_file_file_format_select);
        setTheSetFieldsBasedOnSelectedFileFormat();
    } catch (err) {}

     // END SECTION TO SET MOST GLOBAL VARIABLES

    // START SECTION FOR LOADING

    // deal with the extra formset - find which it is when there is more than the extra
    if (global_file_formset_count > 1) {
        showOverwriteSampleTimeInfo();
        showPlateSizeForFile();
        showQCForFile();
        setPlateSizeParameters();

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

        // load the file into the memory variable for use in displaying plate maps on reload of submitted
        reviewPlateReaderFileOnLoad();
    } else {
        // this is the condition where there are no saved blocks yet
        // hide the extra formset - it will be cloned, so, do not selectize the platemap or cloning will NOT work
       $('#id_formset_' + global_file_extra_formset_number).addClass('hidden');
    }

    function setPlateSizeParameters() {
        // plate size is stored in the file model, so,
        // just get the lines columns the HARDCODED way...
        global_file_setting_box_form_plate_size = $('#id_upload_plate_size').val();
        if (global_file_setting_box_form_plate_size == 24) {
            global_file_selected_a_plate_map_with_number_lines_by_plate_size = 4;
            global_file_selected_a_plate_map_with_number_columns_by_plate_size = 6;
        } else if (global_file_setting_box_form_plate_size == 96) {
            global_file_selected_a_plate_map_with_number_lines_by_plate_size = 8;
            global_file_selected_a_plate_map_with_number_columns_by_plate_size = 12;
        } else {
            // form_plate_size = 384
            global_file_selected_a_plate_map_with_number_lines_by_plate_size = 16;
            global_file_selected_a_plate_map_with_number_columns_by_plate_size = 24;
        }

        $("#plate_number_columns").text(global_file_selected_a_plate_map_with_number_columns_by_plate_size);
        $("#plate_number_lines").text(global_file_selected_a_plate_map_with_number_lines_by_plate_size);
    }

    function adjustEndingLineOrColumnOrReloadingPage(adjust_or_reload, this_element, line_or_delimited) {
        let this_form_row = this_element.closest(".form2-row");
        // console.log(this_form_row)
        let formset_id = this_form_row[0].id;
        // console.log(formset_id)
        let block_number = formset_id.substring(11,);
        let fidx = block_number - 1;
        // console.log(fidx)

        let dstart = $('#id_assayplatereadermapdatafileblock_set-' + fidx + '-delimited_start').val();
        let lstart = $('#id_assayplatereadermapdatafileblock_set-' + fidx + '-line_start').val();

        if (dstart < 1 || lstart < 1) {
            let mymessage = "Please enter a integer > 0."
             alert(mymessage + ' \n');
        } else {

            let dend = $('#id_assayplatereadermapdatafileblock_set-' + fidx + '-delimited_end').val();
            let lend = $('#id_assayplatereadermapdatafileblock_set-' + fidx + '-line_end').val();

            // when edit the start line or the start column, auto change the end line and/or end column based on plate size
            if (line_or_delimited == "delimited") {
                dend = '#id_assayplatereadermapdatafileblock_set-' + fidx + '-delimited_end';
                $(dend).val(parseInt(dstart) + parseInt(global_file_selected_a_plate_map_with_number_columns_by_plate_size) - 1);
                dend = $('#id_assayplatereadermapdatafileblock_set-' + fidx + '-delimited_end').val();
            } else {
                lend = '#id_assayplatereadermapdatafileblock_set-' + fidx + '-line_end';
                $(lend).val(parseInt(lstart) + parseInt(global_file_selected_a_plate_map_with_number_lines_by_plate_size) - 1);
                lend = $('#id_assayplatereadermapdatafileblock_set-' + fidx + '-line_end').val();
            }

            makeOrRemakePlateMapTable(
                "update",
                block_number,
                lstart - 1,
                lend - 1,
                dstart - 1,
                dend - 1);

        }
    }

    function showOverwriteSampleTimeInfo() {
        $('#overwrite_sample_time_row').removeClass('hidden');
    }

    function showPlateSizeForFile() {
        $('#plate_size_in_well').removeClass('hidden');
    }

    function showQCForFile() {
        $('#go_qc_section').removeClass('hidden');
    }

    // changed back to toggle button..not using right now
    // function showVerboseSettingsSection() {
    //     // make sure the size of the list is such that on an auto method is > 9000
    //     // console.log(global_file_file_format_select)
    //     if (global_file_file_format_select > 9000) {
    //         $('#auto_detect_settings_section').removeClass('hidden');
    //     // } else if (global_file_file_format_select == 0) {
    //     //     //don't do anything
    //     } else {
    //         $('#auto_detect_settings_section').addClass('hidden');
    //         // call the script immediately since not using full auto - changed this
    //         // reviewPlateReaderFileOnClick();
    //     }
    // }

    function setTheSetFieldsBasedOnSelectedFileFormat() {
        // NEW FORMATS - edit here
        // choices = (
        // (0, 'COMPUTER BEST GUESS - No format selected'),
        // (1, 'Softmax Pro 5.3 Molecular Devices M5 - requested by UPDDI Director of Operations'),
        // (96, 'One 96 plate (8 lines by 12 columns) starting at line 1 column 1 (CSV) - requested by Larry V.'),
        // (384, 'One 384 plate (16 lines by 24 columns) starting at line 1 column 1 (CSV) - requested by Larry V.'),
        // (2, 'Wallac EnVision Manager Version 1.12 (EnVision)'),
        // (9999, 'USER CUSTOMIZED by Presetting Format Information (for advanced users)'),
        // )

        let send_this_message = "No additional knowledge about this format is embedded in the block detection algorithm.";

        switch(parseInt(global_file_file_format_select)) {
            case 0:
                // best guesses, nothing gets set
                $("#set_format").closest('div').addClass('off');
                $("#set_delimiter").closest('div').addClass('off');
                $("#set_plate_size").closest('div').addClass('off');
                $("#set_number_blocks").closest('div').addClass('off');
                $("#set_number_blank_columns").closest('div').addClass('off');
                $("#set_number_blank_rows").closest('div').addClass('off');
                break;
            case 1:
                // do we want to set for this case
                $("#set_format").closest('div').removeClass('off');
                $("#set_delimiter").closest('div').removeClass('off');
                $("#set_plate_size").closest('div').addClass('off');
                $("#set_number_blocks").closest('div').addClass('off');
                $("#set_number_blank_columns").closest('div').addClass('off');
                $("#set_number_blank_rows").closest('div').addClass('off');

                // when setting, use this value, comment out if not using
                global_file_setting_box_delimiter = "tab";
                global_file_setting_box_form_plate_size = 96;
                // global_file_setting_box_form_number_blocks = 0;
                global_file_setting_box_form_number_blank_columns = 3;
                global_file_setting_box_form_number_blank_rows = 4;

                send_this_message = "This file format has knowledge of where to look in the file for: the plate size, the header information and content, and the metadata embedded in the block detection algorithm.";
                break;
            case 10:
                // do we want to set for this case
                $("#set_format").closest('div').addClass('off');
                $("#set_delimiter").closest('div').addClass('off');
                $("#set_plate_size").closest('div').addClass('off');
                $("#set_number_blocks").closest('div').removeClass('off');
                $("#set_number_blank_columns").closest('div').removeClass('off');
                $("#set_number_blank_rows").closest('div').removeClass('off');

                // when setting, use this value, comment out if not using
                global_file_setting_box_delimiter = "comma";
                global_file_setting_box_form_plate_size = 96;
                global_file_setting_box_form_number_blocks = 1;
                global_file_setting_box_form_number_blank_columns = 1;
                global_file_setting_box_form_number_blank_rows = 1;
                break;
            case 9999:
                // do we want to set for this case
                global_file_set_format = $("#set_format").prop('checked');
                $("#set_format").closest('div').addClass('off');
                $("#set_delimiter").closest('div').addClass('off');
                $("#set_plate_size").closest('div').addClass('off');
                $("#set_number_blocks").closest('div').addClass('off');
                $("#set_number_blank_columns").closest('div').addClass('off');
                $("#set_number_blank_rows").closest('div').addClass('off');

                // force the settings ON if they are OFF
                // JSCSS
                let mystyle = $('#auto_detect_settings_section').css('display');
                // console.log("mystyle: ", mystyle)
                if (mystyle == "none") {
                    $("#auto_detect_settings_section").toggle();
                }
                break;
            default:
            // no changes to what is set
        }
        // load all the set buttons for true/false
        if ($("#set_format").closest('div').hasClass('off')) {
            // console.log('1')
            global_file_set_format = false;
        } else {
            global_file_set_format = true;
        }
        if ($("#set_delimiter").closest('div').hasClass('off')) {
            // console.log('2')
            global_file_set_delimiter = false;
        } else {
            global_file_set_delimiter = true;
        }
        if ($("#set_plate_size").closest('div').hasClass('off')) {
            // console.log('3')
            global_file_set_plate_size = false;
        } else {
            global_file_set_plate_size = true;
        }
        if ($("#set_number_blocks").closest('div').hasClass('off')) {
            // console.log('4')
            global_file_set_number_blocks = false;
        } else {
            global_file_set_number_blocks = true;
        }
        if ($("#set_number_blank_columns").closest('div').hasClass('off')) {
            // console.log('5')
            global_file_set_number_blank_columns = false;
        } else {
            global_file_set_number_blank_columns = true;
        }
        if ($("#set_number_blank_rows").closest('div').hasClass('off')) {
            // console.log('6')
            global_file_set_number_blank_rows = false;
        } else {
            global_file_set_number_blank_rows = true;
        }

        try {
            // put what is in memory into the setting box - only on html page if still editable
            $("#id_file_delimiter").selectize()[0].selectize.setValue(global_file_setting_box_delimiter);
            $("#id_se_form_plate_size").selectize()[0].selectize.setValue(global_file_setting_box_form_plate_size);
            $("#id_form_number_blocks").val(global_file_setting_box_form_number_blocks);
            $("#id_form_number_blank_columns").val(global_file_setting_box_form_number_blank_columns);
            $("#id_form_number_blank_rows").val(global_file_setting_box_form_number_blank_rows);
        } catch (err) {}

        document.getElementById('format_selected_annotation').innerHTML = send_this_message;
    }

    // apply styles/formatting to formsets - JSCSS
    // tried other ways of doing this, including css and form widget,
    // but this worked the best/easiest
    let index_css = 0;
    while (index_css < global_file_formset_count) {
        // console.log(index_css)
        // I tried moving this stuff into a class, but it did not work as anticipated
        let element_id1 = 'id_assayplatereadermapdatafileblock_set-' + index_css + '-data_block';
        document.getElementById(element_id1).style.borderStyle = 'none';
        document.getElementById(element_id1).readOnly = true;
        let element_id2 = 'id_assayplatereadermapdatafileblock_set-' + index_css + '-form_selected_plate_map_time_unit';
        document.getElementById(element_id2).style.borderStyle = 'none';
        document.getElementById(element_id2).readOnly = true;
        document.getElementById(element_id2).style.backgroundColor = 'transparent';
        let element_id3 = 'id_assayplatereadermapdatafileblock_set-' + index_css + '-line_end';
        document.getElementById(element_id3).style.borderStyle = 'none';
        document.getElementById(element_id3).style.backgroundColor = 'lightgrey';
        let element_id4 = 'id_assayplatereadermapdatafileblock_set-' + index_css + '-delimited_end';
        document.getElementById(element_id4).style.borderStyle = 'none';
        document.getElementById(element_id4).style.backgroundColor = 'lightgrey';
        index_css = index_css + 1;
    }
    // apply style, tried other ways, this worked best
    try {document.getElementById('id_upload_plate_size').style.borderStyle = 'none';}
    catch (err) {}

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
        , '#file_number_blank_rows_tooltip'
        , '#file_use_format_specific_info_tooltip',
        ,
    ,];
    let global_file_tooltip_text = [
          "Description for the file is optional, but can be helpful if there are many files in the study."
        , "If the plate size is known, set this to On and select the size plate used in the plate reader."
        , "If the delimiter is known, set this to On and select the correct delimiter."
        , "If a value is provided, this sample time will be used for this whole data block (sample times in the selected assay plate map will be overwritten with this value)."
        , "The number of blocks of data in the file. If this is set to On, this number of data blocks will be avaiable for editing."
        , "Selecting a specific format will yield the best results IF the file follows that format - exactly."
        , "Set the number of blank columns to the left of the data block. Use 123 to look for column headers of 1, 2, 3 etc. throughout the file. It is always assumed that a data block starts the line below headers of 1, 2, 3 etc. and, when using 123, all ~blank/~end line tags are ignored."
        , "Set the number of header rows above of the data block. If 123 is used for the number of blank columns, it will also be used to find the first set of data blocks and the number provided here will be ignored, even if set On."
        , "Some formats have additional information embedded in the block detection algorithm. If set to On, this information is used in detecting data blocks."
        ,
    ,];
    // set the tooltips
    $.each(global_file_tooltip_selector, function (index, show_box) {
        $(show_box).next().html($(show_box).next().html() + make_escaped_tooltip(global_file_tooltip_text[index]));
    });
    // END SECTION THAT SETS TOOLTIPS

    // START - SECTION FOR CHANGES ON PAGE

    // toggle to hide/show auto detect help section
    // $("#reviewButtonHelp").click(function() {
    //     $("#auto_detect_help_section").toggle();
    // });
    $("#reviewSettings").click(function() {
        $("#auto_detect_settings_section").toggle();
    });
    $("#reviewTips").click(function() {
        $("#auto_detect_tips_section").toggle();
    });

    // this button is currently hidden, if needed, add it back
    // but on 20200207, put QC on the changing of the start line and start column number and QC was already on the plate map selection
    $("#runQualityControl").click(function() {
        // Scroll through the blocks and send inform for each block to QC
        global_file_qc_messages = [];
        idx = 0;
        // console.log("global_file_setting_box_form_number_blocks ",global_file_setting_box_form_number_blocks)
        while (idx < global_file_setting_box_form_number_blocks) {
            let this_plate_map       = $('#id_assayplatereadermapdatafileblock_set-' + idx + '-assayplatereadermap').val();
            let this_data_block      = $('#id_assayplatereadermapdatafileblock_set-' + idx + '-data_block').val();
            let this_block_metadata  = $('#id_assayplatereadermapdatafileblock_set-' + idx + '-data_block_metadata').val();
            let this_line_start      = $('#id_assayplatereadermapdatafileblock_set-' + idx + '-line_start').val();
            let this_line_end        = $('#id_assayplatereadermapdatafileblock_set-' + idx + '-line_end').val();
            let this_delimited_start = $('#id_assayplatereadermapdatafileblock_set-' + idx + '-delimited_start').val();
            let this_delimited_end   = $('#id_assayplatereadermapdatafileblock_set-' + idx + '-delimited_end').val();
            doQualityCheck(this_plate_map, this_data_block, global_file_setting_box_form_plate_size, this_line_start, this_line_end, this_delimited_start, this_delimited_end);
            $.each(global_file_qc_messages, function (qc_index, qc_item) {
                alert(qc_item + ' \n');
            });
            idx = idx + 1;
        }
    });

    $(".start-delimited-number").change(function() {
        adjustEndingLineOrColumnOrReloadingPage('change', $(this), 'delimited');
    });
    $(".start-line-number").change(function() {
        adjustEndingLineOrColumnOrReloadingPage('change', $(this), 'line');
    });

    $(".end-delimited-number").change(function() {
        alert('You should not change this. You are likely going to get errors unless you change the start. \n');
    });
    $(".end-line-number").change(function() {
        alert('You should not change this. You are likely going to get errors unless you change the start. \n');
    });

    // $(".start-delimited-number").mouseout(function() {
    //     adjustEndingLineOrColumnOrReloadingPage('change', $(this), 'delimited');
    // });
    // $(".start-line-number").mouseout(function() {
    //     adjustEndingLineOrColumnOrReloadingPage('change', $(this), 'line');
    // });

    // where user changes anything about a block
    // save the block number as 1 (instead of 0) so changes can be made on save to values in platemap
    // do not know which is the selected block, so find it by class change
    $(".form2-row").change(function() {
        // console.log($(this))
        // console.log($(this).context)
        // console.log($(this).context.id)
        let formset_id = $(this).context.id;

        let block_number = formset_id.substring(11, );
        let fidx = block_number-1;
        // console.log(fidx)

        // form_changed_something_in_block - not really using this to change what is removed/added during submit..may add later??
        let block_number_id = "#id_assayplatereadermapdatafileblock_set-" + fidx + "-form_changed_something_in_block";
        // console.log("changed in block: ",block_number_id)
        // 1 for something changed in the block, 0 for nothing changed in the block
        $(block_number_id).val(1);

    });    

    // select dropdown for the file format to work with
    $("#id_se_file_format_select").change(function() {
        global_file_file_format_select = $(this).val();
        // showVerboseSettingsSection();
        setTheSetFieldsBasedOnSelectedFileFormat();
    });

    $("#set_plate_size").closest('div').change(function() {

        if ($("#id_se_file_format_select").val() == 1) {
            if ($("#set_format").closest('div').hasClass('off')) {
                //skip
            } else {
                if ($("set_plate_size").closest('div').hasClass('off')) {
                    //skip
                } else {
                    // both on, tried to use both on but did not evaluate
                    alert('This cannot be set if the Use File Specific Info is set and the Softmax Pro is selected as the File Format. \n');
                    $("#set_plate_size").closest('div').addClass('off');
                }
            }

        }
    });

    $("#set_format").closest('div').change(function() {
        // console.log("bo1 ",$("#set_format").closest('div').hasClass('on'))
        // console.log("bo2 ",$("#set_plate_size").closest('div').hasClass('on'))
        // console.log("val ",$("#id_se_file_format_select").val())

        if ($("#id_se_file_format_select").val() == 1) {
            $("#set_plate_size").closest('div').addClass('off');
        }
    });

    //not sure need this...check after find root of other problem
    // $("#id_se_form_plate_size").change(function() {
    //     setPlateSizeParameters;
    // });

    // when user selects a plate map for a block of data
    // find which block of data was changed  - by class change
    $(".get-plate-map-changed").change(function() {
        // console.log($(this))
        // this can only happen after blocks have been added and plate size for file determined
        // confirm that the plate is the same size as the one picked in the file format
        // what plate was selected and what is it's size?
        global_file_selected_a_plate_map_with_this_size = 0;
        global_file_selected_a_plate_map_with_this_time_unit = "";
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
        global_file_selected_a_plate_map_with_this_size = 0;
        global_file_selected_a_plate_map_with_this_time_unit = "";
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
            global_file_selected_a_plate_map_with_this_size = platemap_size_and_unit[0][('device')];
            global_file_selected_a_plate_map_with_this_time_unit = platemap_size_and_unit[0][('time_unit')];
            if (global_file_selected_a_plate_map_with_this_size == global_file_setting_box_form_plate_size) {
                // console.log(" global_file_selected_a_plate_map_with_this_size ",  global_file_selected_a_plate_map_with_this_size)
                // console.log("global_file_plate_map_changed_formset_index ",global_file_plate_map_changed_formset_index)
                let this_unit_id = '#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-form_selected_plate_map_time_unit';
                // console.log('this_unit_id' ,this_unit_id)
                // console.log('global_file_selected_a_plate_map_with_this_time_unit ',global_file_selected_a_plate_map_with_this_time_unit)
                // $(this_unit_id).text(global_file_selected_a_plate_map_with_this_time_unit);
                $(this_unit_id).val(global_file_selected_a_plate_map_with_this_time_unit);

                let this_plate_map  = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-assayplatereadermap').val();
                let this_data_block = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-data_block').val();
                let this_line_start = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-line_start').val();
                let this_line_end = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-line_end').val();
                let this_delimited_start = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-delimited_start').val();
                let this_delimited_end = $('#id_assayplatereadermapdatafileblock_set-' + global_file_plate_map_changed_formset_index + '-delimited_end').val();

                // this is run when plate map is selected - we will reuse the list, but empty it first
                global_file_qc_messages = [];
                doQualityCheck(this_plate_map, this_data_block, global_file_setting_box_form_plate_size, this_line_start, this_line_end, this_delimited_start, this_delimited_end);
                $.each(global_file_qc_messages, function (qc_index, qc_item) {
                    alert(qc_item + ' \n');
                });
            } else {
                alert('The assay plate map selected for this block does not match the plate size selected with the file format (or determined using the auto detect). Select an assay plate map of matching size.\n');
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

    function doQualityCheck(the_plate_map, this_data_block, this_plate_map_size, this_line_start, this_line_end, this_delimited_start, this_delimited_end) {
        // will come here for each block when plate map is selected, run qc and fill a message list with errors
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
        showOverwriteSampleTimeInfo();
        showPlateSizeForFile();
        showQCForFile();
        reviewPlateReaderFileOnClick();
    });

    function reviewPlateReaderFileOnClick() {
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
        try { global_file_setting_box_delimiter = $("#id_file_delimiter").val();
        }
        catch(err) { global_file_setting_box_delimiter = $("#id_file_delimiter").selectize()[0].selectize.items[0];
        }
        try { global_file_setting_box_form_plate_size = $("#id_se_form_plate_size").val();
        }
        catch(err) { global_file_setting_box_form_plate_size = $("#id_se_form_plate_size").selectize()[0].selectize.items[0];
        }
        $("#id_upload_plate_size").val(global_file_setting_box_form_plate_size);
        try { global_file_setting_box_form_number_blocks = $("#id_form_number_blocks").val();
        }
        catch(err) { global_file_setting_box_form_number_blocks = $("#id_form_number_blocks").selectize()[0].selectize.items[0];
        }
        try { global_file_setting_box_form_number_blank_columns = $("#id_form_number_blank_columns").val();
        }
        catch(err) { global_file_setting_box_form_number_blank_columns = $("#id_form_number_blank_columns").selectize()[0].selectize.items[0];
        }
        try { global_file_setting_box_form_number_blank_rows = $("#id_form_number_blank_rows").val();
        }
        catch(err) { global_file_setting_box_form_number_blank_rows = $("#id_form_number_blank_rows").selectize()[0].selectize.items[0];
        }

        // check all the set buttons for true/false
        if ($("#set_format").closest('div').hasClass('off')) {
            global_file_set_format = false;
        } else {
            global_file_set_format = true;
        }
        if ($("#set_delimiter").closest('div').hasClass('off')) {
            global_file_set_delimiter = false;
        } else {
            global_file_set_delimiter = true;
        }
        if ($("#set_plate_size").closest('div').hasClass('off')) {
            global_file_set_plate_size = false;
        } else {
            global_file_set_plate_size = true;
        }
        if ($("#set_number_blocks").closest('div').hasClass('off')) {
            global_file_set_number_blocks = false;
        } else {
            global_file_set_number_blocks = true;
        }
        if ($("#set_number_blank_columns").closest('div').hasClass('off')) {
            global_file_set_number_blank_columns = false;
        } else {
            global_file_set_number_blank_columns = true;
        }
        if ($("#set_number_blank_rows").closest('div').hasClass('off')) {
            global_file_set_number_blank_rows = false;
        } else {
            global_file_set_number_blank_rows = true;
        }

        // console.log(global_file_plate_this_file_id)
        // console.log(global_file_setting_box_delimiter)
        // console.log(global_file_setting_box_form_plate_size)
        // console.log(global_file_setting_box_form_number_blocks)
        // console.log(global_file_set_format)
        // console.log(global_file_set_delimiter)
        // console.log(global_file_set_plate_size)
        // console.log(global_file_set_number_blocks)
        // console.log(global_file_set_number_blank_columns)
        // console.log(global_file_set_number_blank_rows)

        var data = {
            call: 'fetch_review_plate_reader_data_file_with_block_info',
            this_file_id: global_file_plate_this_file_id,
            this_file_format_selected: global_file_file_format_select,
            file_delimiter: global_file_setting_box_delimiter,
            form_plate_size: global_file_setting_box_form_plate_size,
            form_number_blocks: global_file_setting_box_form_number_blocks,
            form_number_blank_columns: global_file_setting_box_form_number_blank_columns,
            form_number_blank_rows: global_file_setting_box_form_number_blank_rows,
            set_delimiter: global_file_set_delimiter,
            set_format: global_file_set_format,
            set_plate_size: global_file_set_plate_size,
            set_number_blocks: global_file_set_number_blocks,
            set_number_blank_columns: global_file_set_number_blank_columns,
            set_number_blank_rows: global_file_set_number_blank_rows,
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
                alert('An unknown error has occurred. Try a different file format. \n');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    let processDataFromBlockDetect = function (json, exist) {
        let file_block_info = json.file_block_info;
        global_file_iblock_file_list = json.file_list;

        // console.log(file_block_info)
        // note this method if needed $("#id_device").selectize()[0].selectize.setValue(pm_device);
        let add_blocks = 0;
        let calculated_number_of_blocks = 0;
        // get info that is the same for all out of the first dictionary
        try {
            calculated_number_of_blocks = file_block_info[0][('calculated_number_of_blocks')];
        } catch (err) {
            calculated_number_of_blocks = 0;
            alert('Error SCK0001-AJAX CALL RETURNED EMPTY has occurred. Notify a database administrator that you have received this error \n');
        }

        if (global_file_set_plate_size == false) {
            // make the plate size show what was identified
            // HANDY to update a selectize selection
            global_file_setting_box_form_plate_size = file_block_info[0]['plate_size'];
            $("#id_se_form_plate_size").selectize()[0].selectize.setValue(global_file_setting_box_form_plate_size);
            $("#id_upload_plate_size").val(global_file_setting_box_form_plate_size);

            global_file_selected_a_plate_map_with_number_lines_by_plate_size = file_block_info[0]['plate_lines'];
            global_file_selected_a_plate_map_with_number_columns_by_plate_size = file_block_info[0]['plate_columns'];
            // console.log(global_file_selected_a_plate_map_with_number_lines_by_plate_size)
            // console.log(global_file_selected_a_plate_map_with_number_columns_by_plate_size)
            $("#plate_number_columns").text(global_file_selected_a_plate_map_with_number_columns_by_plate_size);
            $("#plate_number_lines").text(global_file_selected_a_plate_map_with_number_lines_by_plate_size);
        }
        // do not need else because if the plate size is given and set, it is used

        if (global_file_set_delimiter == false) {
            // make the delimiter show what was identified
            global_file_setting_box_delimiter = file_block_info[0]['block_delimiter'];
            $("#id_file_delimiter").selectize()[0].selectize.setValue(global_file_setting_box_delimiter);
        }
        // do not need else because if the delimiter is given and set, it is used
        // console.log("calculated_number_of_blocks: ",calculated_number_of_blocks)
        // console.log("global_file_set_number_blocks2: ",global_file_set_number_blocks)

        if (global_file_set_number_blocks == false) {
            global_file_setting_box_form_number_blocks = calculated_number_of_blocks;
            $("#id_form_number_blocks").val(global_file_setting_box_form_number_blocks);
        } else if (global_file_set_number_blocks == true && calculated_number_of_blocks == global_file_setting_box_form_number_blocks) {
            // pass
        } else {
            // (set_number_blocks == True && calculated_number_of_blocks != global_file_setting_box_form_number_blocks)
            let mymessage = "The number of blocks specified does not match the number detected." ;
            mymessage = mymessage + " The set number of blocks will be used.";
            mymessage = mymessage + " Try setting the plate size and/or some of the other settings";
            mymessage = mymessage + " to get better performance from the block detect algorithm or";
            mymessage = mymessage + " manually edit the block information as needed. \n";
            alert(mymessage);
            // console.log(calculated_number_of_blocks)
            // console.log(global_file_setting_box_form_number_blocks)
            add_blocks = global_file_setting_box_form_number_blocks - calculated_number_of_blocks;
        }
        // need this global_file_setting_box_form_number_blocks

        if (global_file_set_number_blank_columns == false) {
            global_file_setting_box_form_number_blank_columns = file_block_info[0]['number_blank_columns'];
            $("#id_form_number_blank_columns").val(global_file_setting_box_form_number_blank_columns);
        }
        // do not need else because if the number of blank columns is given and set, it is used
        if (global_file_set_number_blank_rows == false) {
            global_file_setting_box_form_number_blank_rows = file_block_info[0]['number_blank_rows'];
            $("#id_form_number_blank_rows").val(global_file_setting_box_form_number_blank_rows);
        }
        // console.log(global_file_plate_this_file_id)
        // console.log(global_file_setting_box_delimiter)
        // console.log(global_file_setting_box_form_plate_size)
        // console.log(global_file_setting_box_form_number_blocks)
        // console.log(global_file_setting_box_form_number_blank_columns)
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
                global_file_iblock_data_block_metadata.push(0);
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
        while (idx < global_file_setting_box_form_number_blocks) {
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
            let this_dblock = global_file_iblock_data_block[idx];
            let this_dblockmetadata = global_file_iblock_data_block_metadata[idx];
            let this_lstart = global_file_iblock_line_start[idx]+1;
            let this_lend = global_file_iblock_line_end[idx]+1;
            let this_dstart = global_file_iblock_delimited_start[idx]+1;
            let this_dend = global_file_iblock_delimited_end[idx]+1;

            $(dblock).val(this_dblock);
            $(dblockmetadata).val(this_dblockmetadata);
            // The INDEXES of the top and bottom lines, and the first and last column for each block
            // add 1 to get the line or column number
            $(lstart).val(this_lstart);
            $(lend).val(this_lend);
            $(dstart).val(this_dstart);
            $(dend).val(this_dend);

            global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
            // console.log('global_file_formset_count post clone ', global_file_formset_count)

            // global_counter_to_check_loopB = global_counter_to_check_loopB + 1;
            // console.log("global_counter_to_check_loopB ",global_counter_to_check_loopB)

            makeOrRemakePlateMapTable(
                "create",
                this_dblock,
                this_lstart - 1,
                this_lend - 1,
                this_dstart - 1,
                this_dend - 1);

            idx = idx + 1;
        }

        // Now that formsets are in use, show as form control (never turn the selectize back on, argh)
        // JSCSS
        global_file_formset_count = $('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val();
        let index_css = 0;
        while (index_css < global_file_formset_count) {
            $('#id_assayplatereadermapdatafileblock_set-' + index_css + '-assayplatereadermap').addClass('form-control selectized');
            index_css = index_css + 1;
        }
    };


    function reviewPlateReaderFileOnLoad() {
        // this is the function to read the file on load

        // let this_file_id = parseInt(document.getElementById ("this_file_id").innerText.trim());
        try { global_file_plate_this_file_id = parseInt(document.getElementById ("this_file_id").innerText.trim());
        }
        catch(err) { global_file_plate_this_file_id = $("#this_file_id").val();
        }

        global_file_setting_box_delimiter = $("#id_readonly_file_delimiter").text().trim();
        // if (global_file_setting_box_delimiter.length < 1) {
        //     global_file_setting_box_delimiter = $("#id_readonly_file_delimiter").value;
        // }

        // console.log("setting data")
        // console.log("this_file_id: ",global_file_plate_this_file_id)
        // console.log("file_delimiter: ",global_file_setting_box_delimiter)
        var data = {
            call: 'fetch_review_plate_reader_data_file_only',
            this_file_id: global_file_plate_this_file_id,
            file_delimiter: global_file_setting_box_delimiter,
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
                    processDataLoadFileListOnLoad(json, exist);
                    // alert('' +
                    //      '\n\nPlease note that changes will not be made until you press the "Submit" button at the bottom of the page.');
                }
            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();
                alert('Notify the developer that the error FILE_LOAD_AJAX_DATA_ERROR. \n');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    let processDataLoadFileListOnLoad = function (json, exist) {
        global_file_iblock_file_list = json.file_list;
        //console.log(global_file_iblock_file_list)

        // do it here or will get race errors
        for (var fidx = 1, fidxds = global_file_formset_count; fidx < fidxds; fidx++) {
            block_number = fidx;
            let formset_fields = fidx-1;
            let dstart = $('#id_assayplatereadermapdatafileblock_set-' + formset_fields + '-delimited_start').val();
            let lstart = $('#id_assayplatereadermapdatafileblock_set-' + formset_fields + '-line_start').val();
            let dend = $('#id_assayplatereadermapdatafileblock_set-' + formset_fields + '-delimited_end').val();
            let lend = $('#id_assayplatereadermapdatafileblock_set-' + formset_fields + '-line_end').val();

            // console.log("block_number ", block_number)
            // console.log(dstart)

            makeOrRemakePlateMapTable(
                "update",
                block_number,
                lstart - 1,
                lend - 1,
                dstart - 1,
                dend - 1);
        }
    };

    // More Functions
    // make a table for each block and update when requested
    function makeOrRemakePlateMapTable(
        create_or_update,
        this_dblock,
        i_lstart,
        i_lend,
        i_dstart,
        i_dend)
        {
        setPlateSizeParameters();

        // console.log("this_dblock ", this_dblock)
        // console.log("i_lstart ",i_lstart)
        // console.log("i_lend ",i_lend)
        // console.log("i_dstart ",i_dstart)
        // console.log("i_dend ",i_dend)
        //
        // console.log("create_or_update ", create_or_update)
        // console.log(global_file_setting_box_form_plate_size)
        //
        // console.log(global_file_iblock_file_list[4])
        // console.log(global_file_iblock_file_list[4].line_list)

        let table_column_number = i_dend-i_dstart+1;
        let column_width = parseInt(100/global_file_selected_a_plate_map_with_number_columns_by_plate_size).toString() + "%";
        // console.log("column_width ", column_width)
        let this_table_name = '#plate_table_' + this_dblock;

        try {
            var elem = document.querySelector(this_table_name);
            elem.parentNode.removeChild(elem);
            // $(this_table_name).empty();
        } catch (err) {}


        let this_table = document.createElement("table");
        $(this_table).attr('id', 'plate_table_' + this_dblock);
        $(this_table).addClass('plate-map-file-table');

        // for each row
        let tbody = document.createElement("tbody");
        // $(tbody).addClass('plate-map-file-table');
        let ret_block_raw_value = "0";

        // console.log("how many formsets ",$('#id_assayplatereadermapdatafileblock_set-TOTAL_FORMS').val())
        let continue_if_true = 'true';
        try {
            let my_line_list = global_file_iblock_file_list[0].line_list;
        } catch (err) {
            continue_if_true = 'false';
            alert('Notify the developer that the error FILE_LOAD_AJAX_DATA_ERROR_EMPTY_LIST. \n');
        }

        if (continue_if_true == 'true') {
            for (var ridx = i_lstart, rls = i_lend; ridx <= rls; ridx++) {
                // console.log("ridx: ", ridx)
                // console.log("global_file_iblock_file_list[ridx]")
                // console.log(global_file_iblock_file_list[ridx])

                let my_line_list = [];
                try {
                    my_line_list = global_file_iblock_file_list[ridx].line_list;

                } catch (err) {
                    continue_if_true = 'false';
                    alert('The requested block is out of bounds of the file. Try setting the plate size. If that does not work, set the bounds manually for block ' + this_dblock + ' or try another file format. \n');
                    break;
                }

                if (continue_if_true == "true") {
                    let trbodyrow = document.createElement("tr");
                    // while in a row, go through each column
                    for (var cidx = i_dstart, cls = i_dend; cidx <= cls; cidx++) {
                        // console.log("cidx: ", cidx)
                        // make parts of the table body
                        let td = document.createElement("td");
                        $(td).addClass('plate-map-file-table-cell');
                        if (table_column_number > 13) {
                            $(td).addClass('plate-map-file-font-percent-small');
                        } else if (table_column_number > 7) {
                            $(td).addClass('plate-map-file-font-percent-medium');
                        } else {
                            $(td).addClass('plate-map-file-font-percent-large');
                        }

                        $(td).attr('width', column_width);
                        ret_block_raw_value = "-";
                        //console.log("my_line_list ",my_line_list)
                        try {
                            if (my_line_list[cidx].trim().length > 0) {
                                ret_block_raw_value = my_line_list[cidx];
                            } else {
                                ret_block_raw_value = "-";
                            }
                        } catch (err) {
                        }

                        //console.log("ret_block_raw_value ", ret_block_raw_value)
                        td.appendChild(document.createTextNode(ret_block_raw_value));
                        trbodyrow.appendChild(td);
                    }
                    tbody.appendChild(trbodyrow);
                    this_table.appendChild(tbody);
                }
            }

            let this_dom_el = '#id_formset_' + this_dblock;
            var elem = document.querySelector(this_dom_el);
            var one_div = elem.querySelector('.place-table-in-this-div');

            one_div.appendChild(this_table);
        }
    }

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

        // the formset was being copied WITH the table, so, had to remove before add new later
        let this_dom_el = '#' + id;
        var elem = document.querySelector(this_dom_el);
        var one_div = elem.querySelector('.place-table-in-this-div');
        // console.log(one_div)

        var children = one_div.children;
        for (var i = 0; i < children.length; i++) {
            var tableChild = children[i];
            // console.log(tableChild)
            tableChild.parentNode.removeChild(tableChild);
        }

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

