$(document).ready(function () {
    // START SECTION TO SET GLOBAL VARIABLES
    // set global variables
    let global_plate_check_page_call = $("#check_load").html().trim()
    // console.log("-",global_plate_check_page_call,"-")
    let global_plate_check_number_run = 1;
    let global_plate_matrix_item_text = "-";
    let global_plate_matrix_item = 0;
    let global_plate_well_use = "empty";
    let global_plate_location_text = "-";
    let global_plate_location = 0;
    let global_plate_size = 0;
    let global_plate_increment_operation = 'divide';
    let global_plate_change_method = 'copy';
    let global_plate_increment_direction = 'left-left';
    let global_plate_data_packed = [];
    let global_plate_when_called_checkboxes = "set_to_defaults";
    let global_plate_start_map = 'a_plate';
    let global_plate_imatrix_item_id = [];
    let global_plate_imatrix_item_name = [];
    let global_plate_imatrix_item_row_index = [];
    let global_plate_imatrix_item_column_index = [];
    let global_plate_imatrix_item_row_column_index = [];
    let global_plate_iplatemap_dictionary = {};
    let global_plate_study_id = parseInt(document.getElementById ("this_study_id").innerText.trim());
    // set global variables that could cause errors (no form defaults)
    let global_plate_number_file_block_sets = 0;
    try { global_plate_number_file_block_sets = document.getElementById("id_form_number_file_block_combos").value;
    } catch(err) { }
    let global_plate_block_index = 0;
    let global_plate_block_pk = 0;
    let global_plate_block_plate_index_list_matches = [];
    let global_plate_block_time_matches = [];
    let global_plate_block_raw_value_matches = [];
    if (global_plate_number_file_block_sets > 0) {
        findValueSet("existing_load");
    }
    let global_plate_standard_value = 0;
    try { global_plate_standard_value = document.getElementById('id_form_number_standard_value').value;
    } catch(err) { }
    let global_plate_increment_value = 1;
    try { global_plate_increment_value = document.getElementById('id_form_number_increment_value').value;
    } catch(err) { }
    let global_plate_time_value = 0;
    try { global_plate_time_value = document.getElementById('id_form_number_time').value;
    } catch(err) { }
    let global_plate_default_time_value = 0;
    try { global_plate_default_time_value = document.getElementById('id_form_number_default_time').value;
    } catch(err) { }
    let global_plate_dilution_factor = 1;
    try { global_plate_dilution_factor = document.getElementById('id_form_number_dilution_factor').value;
    } catch(err) { }
    let global_plate_collection_volume = 0;
    try { global_plate_collection_volume = document.getElementById('id_form_number_collection_volume').value;
    } catch(err) { }
    let global_plate_collection_time = 0;
    try { global_plate_collection_time = document.getElementById('id_form_number_collection_time').value;
    } catch(err) { }
    // lists to use to show/hide content in plate map based on the fancy check boxes
    // NOTE: this uses two parallel lists - the MUST be correctly parallel!
    let global_plate_show_hide_fancy_checkbox_selector = [
        '#show_matrix_item',
        '#show_time',
        '#show_default_time',
        '#show_location',
        '#show_standard_value',
        '#show_well_use',
        '#show_label',
        '#show_compound',
        '#show_cell',
        '#show_setting',
        '#show_dilution_factor',
        '#show_collection_volume',
        '#show_collection_time',
        '#show_block_raw_value',
    ];
    let global_plate_show_hide_fancy_checkbox_class = [
        '.plate-cells-matrix-item',
        '.plate-cells-time',
        '.plate-cells-default-time',
        '.plate-cells-location',
        '.plate-cells-standard-value',
        '.plate-cells-well-use',
        '.plate-cells-label',
        '.plate-cells-compound',
        '.plate-cells-cell',
        '.plate-cells-setting',
        '.plate-cells-dilution-factor',
        '.plate-cells-collection-volume',
        '.plate-cells-collection-time',
        '.plate-cells-block-raw-value',
    ];

    // make the para||el lists of the matrix id, compound, cell, setting setup info
    // instead of sending from back end and needing a doc id for each
    let global_plate_isetup_matrix_item_id = [];
    let global_plate_isetup_compound = [];
    let global_plate_isetup_cell = [];
    let global_plate_isetup_setting = [];
    // get the setup information for the matrix items in this study
    populateMatrixItemSetupInfo();

    // when load page get the copy of an empty item formset and an empty value formset (the "extra" in the forms.py)
    // in this feature, I am working with inlines - to see another option, see the assay plate file update feature
    let global_plate_first_item_form = $('#formset').find('.inline').first()[0].outerHTML;
    let global_plate_first_value_form = $('#value_formset').find('.inline').first()[0].outerHTML;
    // END SECTION TO SET GLOBAL VARIABLES

    // START SECTION FOR LOADING
    // don't worry about the extra formset in the update or view page since it won't be populated or saved
    // but, when on add page, after copied to global variable, delete the extra formset so it is not saved during submit
    if ($('#formset').find('.inline').length === 1 && global_plate_check_page_call === 'add') {
        $('#formset').find('.inline').first().remove();
    }
    if ($('#value_formset').find('.inline').length === 1 && global_plate_check_page_call === 'add') {
        $('#value_formset').find('.inline').first().remove();
    }
    // NOTE: when added the following code here, made 2x forms, so moved it back to the loop
    // $('#id_assayplatereadermapitem_set-TOTAL_FORMS').val(global_plate_size);
    //}).trigger('change');

    // when loading, what and how to load the plate
    // if add page, START with empty table (plate), if existing, pull from formsets
    if (global_plate_check_page_call === 'add') {
        $('.show-when-add').removeClass('hidden');
        // HARDCODED - but just sets a default and do not want to have to put the plate size list into here...
        global_plate_size = 96;
        plateLabels("on_load_add");
    } else {
        $('.show-when-add').addClass('hidden');
        try {
            global_plate_size = $("#id_device").selectize()[0].selectize.items[0];
        } catch(err) {
            global_plate_size = $("#id_device").val();
        }
        plateLabels("on_load_update_or_view");
    }
    // END SECTION FOR LOADING

    // START SECTION THAT SETS TOOLTIPS
    // set lists for the tooltips
    // just add in parallel if need more tooltips - must be para||el!
    let global_plate_tooltip_selector = [
          '#matrix_select_tooltip'
        , '#plate_select_tooltip'
        , '#platemap_select_tooltip'
        , '#sample_time_unit_tooltip'
        , '#collection_volume_unit_tooltip'
        , '#well_use_tooltip'
        , '#plate_cell_count_tooltip'
        , '#sample_time_tooltip'
        , '#sample_default_time_tooltip'
        , '#sample_location_tooltip'
        , '#sample_matrix_item_tooltip'
        , '#standard_tooltip'
        , '#standard_value_tooltip'
        , '#dilution_factor_tooltip'
        , '#file_block_tooltip'
        , '#number_file_block_tooltip'
        , '#map_name_tooltip'
        , '#collection_volume_tooltip'
        , '#collection_time_tooltip'
    ,];
    let global_plate_tooltip_text = [
          "Starting from an existing study matrix is helpful if the experiment was conducted in a plate based model and that same plate was used to perform a plate reader assay."
        , "Build the plate map by selecting study matrix items and placing them in the plate."
        , "If adding a plate map and starting from an existing plate map, if the plate map has been assigned to a file/block, select the File/Block with the desired sample times. Values from uploaded files will not be obtained."
        , "This time unit applies to all sample times and sample collection times for the whole assay plate map."
        , "This unit applies to the sample collection volume. It is required when normalizing."
        , "For blank and empty wells, select the well use and drag on plate. For samples and standards, make requested selections then drag on plate."
        , "Count of cells that are relevant to the assay."
        , "Check box to make change when drag/apply. Currently cannot be edited here. Was obtained during file upload."
        , "Check box to make change when drag/apply. Plate with mixed sample times must be added in the plate map. This sample time will be used if no over-writing sample time is input during file upload."
        , "Check box to make change when drag/apply. Select the location in the model, if applicable, from which the effluent was collected."
        , "Check box to make change when drag/apply. Select the name of the matrix item (chip or well in a plate) associated to the sample. Use the backspace button to clear selection."
        , "Select the target/method/unit associated to this plate map. Required if there is a standard on the plate. Use the backspace button to clear selection. "
        , "The standard value should be in the unit given in the Assay Standard selection. Standard Method/Target/Unit should be added to the study during study set up. "
        , "The dilution factor should be provided for each well in the plate map. "
        , "Changes made to the plate map (including sample location and standard concentration) will apply to all uses of the plate map (all file/blocks). Changes made to the sample time will apply only a specific file/block."
        , "The number of file/blocks this plate map has been assigned to."
        , "Date and time are the default. The map name may be updated by the data provider."
        , "Volume of efflux collected. Required for normalization."
        , "Time over which the efflux was collected. Required for normalization."
    ,];
    // set the tooltips
    $.each(global_plate_tooltip_selector, function (index, show_box) {
        $(show_box).next().html($(show_box).next().html() + make_escaped_tooltip(global_plate_tooltip_text[index]));
    });
    // NOTE: this replaces a bunch of these
    // let global_plate_map_name_tooltip = "Date and time are the default. The map name may be updated by the data provider.";
    // $('#map_name_tooltip').next().html($('#map_name_tooltip').next().html() + make_escaped_tooltip(global_plate_map_name_tooltip));
    // END SECTION THAT SETS TOOLTIPS

    // START - SECTION FOR CHANGES ON PAGE
    // toggle to hide/show the customized show in plate map fancy check boxes (what will and won't show in plate)
    $("#checkboxButton").click(function() {
        $("#platemap_checkbox_section").toggle();
    });
    // class show/hide and also what is checked/unchecked based on radio button of starting option
    $("input[type='radio'][name='start_map']").click(function() {
        global_plate_start_map = $(this).val();
        // console.log(global_plate_start_map)
        $('.pick-a-matrix').addClass('hidden');
        $('.pick-a-platemap').addClass('hidden');
        $('.pick-a-plate').addClass('hidden');
        if (global_plate_start_map === 'a_plate') {
            $('.pick-a-plate').removeClass('hidden');
        } else if (global_plate_start_map === 'a_platemap') {
            $('.pick-a-platemap').removeClass('hidden');
        } else {
            $('.pick-a-matrix').removeClass('hidden');
        }
    });
    $("input[type='radio'][name='change_method']").click(function() {
        global_plate_change_method = $(this).val();
        if (global_plate_change_method === 'increment') {
            $('.increment-section').removeClass('hidden');
        } else {
            $('.increment-section').addClass('hidden');
        }
    });
    $("input[type='radio'][name='increment_direction']").click(function() {
        global_plate_increment_direction = $(this).val();
    });
    // do not try to put these in a list and call a function. It was too much trouble.
    $("#id_se_matrix_item").change(function() {
        global_plate_matrix_item_text = $(this).children("option:selected").text();
        global_plate_matrix_item = $(this).val();
    });
    $("#id_se_location").change(function() {
        global_plate_location_text = $(this).children("option:selected").text();
        global_plate_location = $(this).val();
    });
    // REVIEW ONLY, not change
    // $("#id_form_number_time").mouseout(function() {
    //     global_plate_time_value = $(this).val();
    // });
    $("#id_form_number_default_time").mouseout(function() {
        global_plate_time_value = $(this).val();
    });
    $("#id_form_number_standard_value").mouseout(function() {
        global_plate_standard_value = $(this).val();
    });
    $("#id_form_number_dilution_factor").mouseout(function() {
        global_plate_dilution_factor = $(this).val();
    });
    $("#id_form_number_collection_volume").mouseout(function() {
        global_plate_collection_volume = $(this).val();
    });
    $("#id_form_number_collection_time").mouseout(function() {
        global_plate_collection_time = $(this).val();
    });
    $("#id_form_number_increment_value").mouseout(function() {
        global_plate_increment_value = $(this).val();
    });
    $("#id_se_increment_operation").change(function() {
        global_plate_increment_operation = $(this).val();
    });
    // controlling more of what shows and does not shows on page (options to change) based on selected to apply

    // this option is for when the well use was in a dropdown - not currently using, but keep in case change back
    $("#id_se_well_use").change(function() {
        global_plate_well_use = $(this).val();
        flexibleWellUse()
    });
    // this option is for when the well use is radio buttons
    $("input[type='radio'][name='change_well_use']").click(function() {
        global_plate_well_use = $(this).val();
        flexibleWellUse()
    });

    // set the global or other variables for the selections if file_block change
    // NOTE: this is the file block for THIS plate map (not if selecting from a different plate map)
    // TODO-sck - check this after get file upload working
    $("#id_se_block_select_string").change(function() {
        findValueSet("changed_file_block")
    });

    //change what is shown in the plate map
    $("input[type='checkbox']").change(function() {
        let this_attr_id = $(this).attr('id');
        let this_attr_id_plus = "#" + this_attr_id;
        let my_idx = global_plate_show_hide_fancy_checkbox_selector.indexOf(this_attr_id_plus);
        // another option:  if ($("input[type='checkbox'][name='change_location']").prop('checked') === true) {
        // HANDY to check if something is checked
        if ($(this_attr_id_plus).is(':checked')) {
            // console.log(this_attr_id_plus)
            $(global_plate_show_hide_fancy_checkbox_class[my_idx]).removeClass('hidden');
            // hides what was just checked (turned on) if not applicable to the well based on well use
            changeShowInPlate('changed_check_box');
        } else {
            $(global_plate_show_hide_fancy_checkbox_class[my_idx]).addClass('hidden');
        }
    });
    // NOTE: the above replaces a bunch of these
    //  $('#show_matrix_item').change(function() {
    //      if ($(this).is(':checked')) {
    //          $('.plate-cells-matrix-item').removeClass('hidden');
    //      } else {
    //          $('.plate-cells-matrix-item').addClass('hidden');
    //      }
    //      changeShowInPlate('changed_check_box');
    //  });

    // START CHANGE FROM START TO FINISH SECTION
    // these two changes get a plate_index_list of wells to change and sends to the specificChanges
    // also, for EACH well, sends to welluseChange
    // when one of the "Apply" buttons is clicked in the plate map
    // NOTE - next line did not work as expected so used the document on
    // $(".apply-button").on("click", function(){

    $(document).on('click','.apply-button',function() {
        // this is limited to either one column or one row
        // get the plate_indexes of the selected wells in the plate map table
        let plate_index_list = [];
        // let button_id = e.target.id;
        let my_this = $(this);
        // console.log(my_this)
        let button_column_index = my_this.attr('column-index');
        let button_row_index = my_this.attr('row-index');
        let button_column_or_row = my_this.attr('column-or-row');
        // console.log(button_column_index)
        // console.log(button_row_index)
        // console.log(button_column_or_row)
        console.log(global_plate_size)
        // find the plate map index of matching column or row (which button was click) and send to the function for processing
        for ( var idx = 0, ls = global_plate_size; idx < ls; idx++ ) {
            // console.log($('#well_use-' + idx).attr('column-index'))
            if (button_column_or_row === 'column') {
                if ($('#well_use-' + idx).attr('column-index') == button_column_index) {
                    welluseChange(idx);
                    plate_index_list.push(idx);
                }
            } else {
                if ($('#well_use-' + idx).attr('row-index') == button_row_index) {
                    welluseChange(idx);
                    plate_index_list.push(idx);
                }
            }
        }

        let plate_index_list_ordered = [];
        // standardize the increment by changing order of how selected
        if (global_plate_change_method === 'increment' && (global_plate_increment_direction === 'right-up' || global_plate_increment_direction === 'right-right' || global_plate_increment_direction === 'top-top')) {
            plate_index_list_ordered = plate_index_list.sort(function(a, b){return b-a});
            // console.log("dsc ", plate_index_list_ordered)
        } else {
            // save for reference but should be ordered....plate_index_list_ordered = plate_index_list.map(Number).sort(function(a, b){return a-b});
            plate_index_list_ordered = plate_index_list;
            // console.log("asc ", plate_index_list_ordered)
        }

        specificChanges(plate_index_list_ordered, 'apply_button');
        setFancyCheckBoxes('apply_button');
    });
    // Select wells in platemap to change by drag
    // https:// www.geeksforgeeks.org/how-to-change-selected-value-of-a-drop-down-list-using-jquery/
    // https:// stackoverflow.com/questions/8978328/get-the-value-of-a-dropdown-in-jquery
    // let global_plate_count_this = 0;
    function changeSelected() {
        // global_plate_count_this = global_plate_count_this + 1;
        // console.log("how many times called ", global_plate_count_this)

        // this could include the whole plate
        // IF the incrementer is being used and if one of the - start over at top, left, or right -
        // need to limit to either one column or one row for each call to specificChanges

        // note: not building a Top to bottom then right or Top to bottom then left - will have to build if requested
        let send_me = "one_list";
        if (global_plate_well_use === "blank" || global_plate_well_use === "empty") {
            send_me = "one_list";
            // console.log("b or e ",send_me)
        } else if (global_plate_change_method === "copy") {
            send_me = "one_list";
            // console.log("copy ",send_me)
        } else if (global_plate_increment_direction === 'right-up' || global_plate_increment_direction === 'left-down') {
            // the value does not start over - okay to leave as one list
            send_me = "one_list";
            // console.log("ru ld ",send_me)
        } else {
            // check what is changed and if spans columns or rows
            // if does, need to split to send a list for each column or each row
            send_me = "multi_list";
            // console.log("else ",send_me)
        }

        let plate_index_list = [];
        let plate_indexes_data_index = [];
        let plate_indexes_rows = [];
        let plate_indexes_columns = [];
        // the plate_indexes of the selected cells in the plate map table
        // children of each cell of the plate map table that is selected
        // what cells were selected in the GUI
        plate_index_list = [];
        $('.ui-selected').children().each(function () {
            // send each selected cell of the table to the function for processing
            // console.log("this: ",$(this))
            if ($(this).hasClass("map-well-use")) {
                let idx = $(this).attr('data-index');
                plate_indexes_data_index.push($(this).attr('data-index'));
                plate_indexes_rows.push($(this).attr('row-index'));
                plate_indexes_columns.push($(this).attr('column-index'));
                welluseChange(idx);
                plate_index_list.push(idx);
            }
        });
        let plate_index_list_ordered = [];
        // this was the original functionality, went back and built the multi_list later
        if (send_me === "one_list") {
            specificChanges(plate_index_list, 'drag')
        } else {
            // are we going by column or row
            if (global_plate_increment_direction === 'top-top' || global_plate_increment_direction === 'bottom-bottom') {
                // working with columns with restart
                let column_indexes = [... new Set(plate_indexes_columns)]
                // console.log(column_indexes)
                column_indexes.forEach(function(el) {
                    plate_index_list = [];
                    $('.ui-selected').children().each(function () {
                        // send each selected cell of the table to the function for processing
                        // console.log("this: ",$(this))
                        if ($(this).hasClass("map-well-use") && $(this).attr('column-index') == el) {
                            let idx = $(this).attr('data-index');
                            plate_index_list.push(idx);
                        }
                    });
                    specificChanges(plate_index_list, 'drag')
                });
            } else {
                // working with rows with restart
                let row_indexes = [... new Set(plate_indexes_rows)]
                // console.log(row_indexes)
                row_indexes.forEach(function(el) {
                    // console.log("el ",el)
                    plate_index_list = [];
                    $('.ui-selected').children().each(function () {
                        // send each selected cell of the table to the function for processing
                        // console.log("this: ",$(this))
                        if ($(this).hasClass("map-well-use") && $(this).attr('row-index') == el) {
                            let idx = $(this).attr('data-index');
                            // console.log("idx " , idx)
                            plate_index_list.push(idx);
                        }
                    });
                    specificChanges(plate_index_list, 'drag')
                });
            }
        }

        setFancyCheckBoxes('drag');
    }
    // END CHANGE FROM START TO FINISH SECTION
    // END - SECTION FOR CHANGES ON PAGE

    // START START - SECTION FOR CHANGING PLATEMAP FOR ADD PAGE BASED ON SELECTED "STARTING" PLACE (WITH FUNCTIONS)

    // START - SECTION FOR ADD PAGE - START FROM AN EMPTY PLATE
    $("#id_device").change(function() {
        // console.log("device change fired")
        // update the global plate size based on new selection (add page, user changed directly)
        try {
            global_plate_size = $("#id_device").selectize()[0].selectize.items[0];
        } catch(err) {
            global_plate_size = $("#id_device").val();
        }
        // console.log("changed device what size is plate: ", global_plate_size)
        // only fire on change plate size IF the selection is a_plate, otherwise, the fire will happen twice
        if (global_plate_start_map === 'a_plate') {
            // clear the matrix and exising platemap selections incase go back and repick the same one
            $("#id_se_matrix").selectize()[0].selectize.setValue();
            $("#id_se_platemap").selectize()[0].selectize.setValue();
            //$("#id_device").selectize()[0].selectize.setValue(global_plate_size);
            removeFormsets();
            plateLabels("changed_device");
        }
        // else, just wanted the plate size update for later use, don't fire the rebuild plate!
    });
    // END - SECTION FOR ADD PAGE - START FROM AN EMPTY PLATE

    // START - SECTION FOR ADD PAGE - START FROM AN EXISTING PLATEMAP (CROSSING PLATEMAPS)
    // all 3 call plateLabels();
    $("#id_se_platemap").change(function() {
        // currently, will autopick the lowest file/block pk if one or more file/blocks is assigned
        // maybe let the user pick the file/block at some point, but would need to build that feature
        if (global_plate_start_map === 'a_platemap') {
            let data = {
                    call: 'fetch_assay_study_platemap_for_platemap',
                    study: global_plate_study_id ,
                    platemap: $("#id_se_platemap").selectize()[0].selectize.items[0],
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                }
            window.spinner.spin(document.getElementById("spinner"));
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: data,
                success: function (json) {
                    window.spinner.stop();
                    // $("#test_me1").text("success happened");
                    let exist = true;
                    process_data_platemap(json, exist);
                    // Need to set the form fields too, including size - unlike a plate and a matrix
                    setFormFieldsPlatemap();
                    removeFormsets();
                    plateLabels("changed_platemap");
                },
                // error callback
                error: function (xhr, errmsg, err) {
                    window.spinner.stop();
                    // $("#test_me1").text("error happened");
                    alert('An error has occurred, try closing the file to upload (if it is open) or, try a different matrix, plate map, or start from an empty plate.');
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
    });
    let process_data_platemap = function (json, exist) {
        let platemap_info = json.platemap_info;
        // console.log(platemap_info)
        // these are the same as the ones in the ajax file
        global_plate_iplatemap_dictionary = platemap_info;
        // console.log(global_plate_iplatemap_dictionary[2].name, " ", global_plate_iplatemap_dictionary[2].device)
        // console.log(global_plate_iplatemap_dictionary[0].device)
        // clear the matrix and exising platemap selections incase go back and repick the same one
        $("#id_se_matrix").selectize()[0].selectize.setValue();
        //$("#id_se_platemap").selectize()[0].selectize.setValue();
        let pm_device = global_plate_iplatemap_dictionary[0].device;
        $("#id_device").selectize()[0].selectize.setValue(pm_device);
        global_plate_size = pm_device;
    };
    function setFormFieldsPlatemap() {
        // list_of_map_fields = ['name', 'description', 'device', 'time_unit', 'volume_unit', 'cell_count', 'study_assay_id']
        $('#id_name').val($('#id_name').val() + " - starting from " + global_plate_iplatemap_dictionary[0].name);
        $('#id_description').val(global_plate_iplatemap_dictionary[0].description);
        $('#id_cell_count').val(global_plate_iplatemap_dictionary[0].cell_count);
        // these do not work like fields that are not selectized
        let pm_time_unit = global_plate_iplatemap_dictionary[0].time_unit;
        let pm_volume_unit = global_plate_iplatemap_dictionary[0].volume_unit;
        let pm_study_assay = global_plate_iplatemap_dictionary[0].study_assay_id;
        try {
            $("#id_time_unit").selectize()[0].selectize.setValue(pm_time_unit);
        } catch(err) {
            $("#id_time_unit").removeProp('selected');
        };
        try {
            $("#id_volume_unit").selectize()[0].selectize.setValue(pm_volume_unit);
        } catch(err) {
            $("#id_volume_unit").removeProp('selected');
        }
        try {
            $("#id_study_assay").selectize()[0].selectize.setValue(pm_study_assay);
        } catch(err) {
            $("#id_study_assay").removeProp('selected');
        }
    }
    // END - SECTION FOR ADD PAGE - START FROM AN EXISTING PLATEMAP (CROSSING PLATEMAPS)

    // START - SECTION FOR ADD PAGE - START FROM AN EXISTING MATRIX
    // matrix selector only shows on the ADD page after user radio button to pick from matrix
    // NOTE that, the id_device field was easy to change but the se_matrix was not.
    // one is a query set and one is a list, perhaps therein lies the difference
    $("#id_se_matrix").change(function() {
        if (global_plate_start_map === 'a_matrix') {
            let my_matrix_pk = $(this).val();
            // console.log("mypk: ", my_matrix_pk)
            let matrix_size = 0;
            // these come directly from the views.py for all the matrices...gets size of selected on (not from ajax call)
            let matrix_list_size_split_1 = $("#matrix_list_size").text().trim()
            let matrix_list_size_split = matrix_list_size_split_1.substring(1, matrix_list_size_split_1.length - 1).split(", ");
            let matrix_list_pk_split_1 = $("#matrix_list_pk").text().trim()
            let matrix_list_pk_split = matrix_list_pk_split_1.substring(1, matrix_list_pk_split_1.length - 1).split(", ");
            // console.log("mlss: ", matrix_list_size_split)
            // console.log("mlps: ", matrix_list_pk_split)
            let string_of_matrix_pk = my_matrix_pk.toString();
            // console.log("somp: ", string_of_matrix_pk)
            let matrix_pk_index = matrix_list_pk_split.indexOf(string_of_matrix_pk);
            matrix_size = matrix_list_size_split[matrix_pk_index];
            // console.log("mpi: ", matrix_pk_index)
            // console.log("ms: ", matrix_size)
            global_plate_size = matrix_size;
            getMatrixItemList();
        }
    });
    function getMatrixItemList() {
        // console.log("mypk: ", $("#id_se_matrix").val())
        // get the matrix items (pk, name, row_index, column_index) for the matrix that was selected
        let data = {
                call: 'fetch_assay_study_matrix_for_platemap',
                study: global_plate_study_id ,
                matrix: $("#id_se_matrix").selectize()[0].selectize.items[0],
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            }
        window.spinner.spin(document.getElementById("spinner"));
        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                window.spinner.stop();
                // $("#test_me1").text("success happened");
                let exist = true;
                process_data_matrix(json, exist);
                removeFormsets();
                plateLabels("changed_matrix");
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                // $("#test_me1").text("error happened");
                alert('An error has occurred, please try a different matrix, plate map, or start from an empty plate.');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
    let process_data_matrix = function (json, exist) {
        let mi_list = json.mi_list;
        // make the parallel list for easy search and find
        global_plate_imatrix_item_id = [];
        global_plate_imatrix_item_name = [];
        global_plate_imatrix_item_row_index = [];
        global_plate_imatrix_item_column_index = [];
        global_plate_imatrix_item_row_column_index = [];

        $.each(mi_list, function(index, each) {
            // console.log("each ", each)
            global_plate_imatrix_item_id.push(each.matrix_item_id);
            global_plate_imatrix_item_name.push(each.matrix_item_name);
            global_plate_imatrix_item_row_index.push(each.matrix_item_row_index);
            global_plate_imatrix_item_column_index.push(each.matrix_item_column_index);
            global_plate_imatrix_item_row_column_index.push(each.matrix_item_row_index.toString()+"-"+each.matrix_item_column_index.toString());
        });
        // console.log("matrix items: ", global_plate_imatrix_item_row_column_index)

        // clear the matrix and exising platemap selections incase go back and repick the same one
        //$("#id_se_matrix").selectize()[0].selectize.setValue();
        $("#id_se_platemap").selectize()[0].selectize.setValue();
        $("#id_device").selectize()[0].selectize.setValue(global_plate_size);
    };
    // END - SECTION FOR ADD PAGE - START FROM AN EXISTING MATRIX

    // END END - SECTION FOR CHANGING PLATEMAP FOR ADD PAGE BASED ON SELECTED "STARTING" PLACE

    // START - ADDITIONAL FUNCTION SECTION
    // function to get matrix item setup information instead of passing through the forms
    function populateMatrixItemSetupInfo(){
        // get the matrix item setup info
        let data = {
                call: 'fetch_information_for_plate_map_matrix_item_setup',
                study: global_plate_study_id,
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            }
        window.spinner.spin(document.getElementById("spinner"));
        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                window.spinner.stop();
                let exist = true;
                process_matrix_item_setup(json, exist);
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred.');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
    let process_matrix_item_setup = function (json, exist) {
        let mi_list = json.mi_list;
        // make the parallel list for easy search and find
        global_plate_isetup_matrix_item_id = [];
        global_plate_isetup_compound = [];
        global_plate_isetup_cell = [];
        global_plate_isetup_setting = [];

        $.each(mi_list, function(index, each) {
            // console.log("each ", each)
            global_plate_isetup_matrix_item_id.push(each.matrix_item_id);
            global_plate_isetup_compound.push(each.compound);
            global_plate_isetup_cell.push(each.cell);
            global_plate_isetup_setting.push(each.setting);
        });
        // console.log(global_plate_isetup_matrix_item_id)
        // console.log(global_plate_isetup_compound)
    };

    // make a function to handle changing well use not matte how it is done
    // do this because there has been changing of the mind on dropdown, radio buttons, or ???
    function flexibleWellUse(){
        $("input[name=change_method][value=copy]").prop( "checked", true );
        global_plate_change_method = 'copy';
        if (global_plate_change_method === 'increment') {
            $('.increment-section').removeClass('hidden');
        } else {
            $('.increment-section').addClass('hidden');
        }
        // hide all, then unhide what want to show
        $('.sample-section').addClass('hidden');
        $('.standard-section').addClass('hidden');
        $('.drag-option-section').addClass('hidden');
        if (global_plate_well_use === 'sample') {
            $('.sample-section').removeClass('hidden');
            $('.drag-option-section').removeClass('hidden');
        } else if (global_plate_well_use === 'standard') {
            $('.standard-section').removeClass('hidden');
            $('.drag-option-section').removeClass('hidden');
            $('#show_standard_value').prop('checked', true);
        }
    }

    // this uses the fancy check boxes to set what is visible on the plate map
    // when first draws plate, uses defaults, for subsequent draws, finds what is checked and redisplays them
    function setFancyCheckBoxes(where_called) {
        let x_show_fancy_list = [];
        let x_show_cell_list = [];

        if (global_plate_when_called_checkboxes === "set_to_defaults") {
            if (global_plate_number_file_block_sets < 1) {
                // get the default check boxes to show
                x_show_fancy_list = [
                    '#show_matrix_item',
                    '#show_default_time',
                    '#show_location',
                    '#show_standard_value',
                    '#show_well_use',
                ];
                x_show_cell_list = [
                    '.plate-cells-matrix-item',
                    '.plate-cells-default-time',
                    '.plate-cells-location',
                    '.plate-cells-standard-value',
                    '.plate-cells-well-use',
                ];
            } else {
                // note that this is the value item time, not the default time
                x_show_fancy_list = [
                    '#show_matrix_item',
                    '#show_time',
                    '#show_location',
                    '#show_standard_value',
                    '#show_well_use',
                    '#show_block_raw_value',
                ];
                x_show_cell_list = [
                    '.plate-cells-matrix-item',
                    '.plate-cells-time',
                    '.plate-cells-location',
                    '.plate-cells-standard-value',
                    '.plate-cells-well-use',
                    '.plate-cells-block-raw-value',
                ];
            }
        } else {
            // find what is currently checked and load them into parallel arrays
            let all_idx = 0;
            global_plate_show_hide_fancy_checkbox_selector.forEach(function(show_box) {
                // console.log("show_box2 ", show_box)
                if ($(show_box).is(':checked'))  {
                    x_show_fancy_list.push(global_plate_show_hide_fancy_checkbox_selector[all_idx]);
                    x_show_cell_list.push(global_plate_show_hide_fancy_checkbox_class[all_idx]);
                }
                all_idx = all_idx + 1;
            });
        }
        // use the arrays from above to show/hide and check/uncheck
        let checkidx = 0;
        x_show_fancy_list.forEach(function() {
            $(x_show_fancy_list[checkidx]).prop('checked', true);
            $(x_show_cell_list[checkidx]).removeClass('hidden');
            checkidx = checkidx + 1;
        });
        changeShowInPlate("sfc_"+where_called);
    }
    function findValueSet(called_from) {
        // existing_load or changed_file_block
        // as of 20200111, a set of values with null file should ALWAYS be present
        // this was decided after MUCH self debate and significant restructuring is required to change it
        // there is at least one set that has been assigned to a file/block to get here
        // The indexes of the selection (0 for first block match, 1, for next block match, etc.)
        // what is the index of the current selection
        // remember, no editing of default time, time, or raw value are allowed here.
        // they should make the plate map right before adding data from a file
        // might have to revisit that if users request
        try {
            global_plate_block_index = $("#id_se_block_select_string").selectize()[0].selectize.items[0];
        } catch(err) {
            global_plate_block_index = $("#id_se_block_select_string").val();
        }
        // console.log("global_plate_block_index ", global_plate_block_index)
        // what is the pk of the block
        document.getElementById("id_ns_block_select_pk").selectedIndex = global_plate_block_index;
        global_plate_block_pk = parseInt(document.getElementById('id_ns_block_select_pk').selectedOptions[0].text);
        // console.log("global_plate_block_pk ", global_plate_block_pk)

        // loop through and find the indexes of the value formset that match the selected (by the user) file/block
        // make parallel arrays of the information needed for display in the plate
        let midx = 0;
        global_plate_block_plate_index_list_matches = [];
        global_plate_block_time_matches = [];
        global_plate_block_raw_value_matches = [];
        let my_block_v = "";
        let my_block = 0;
        let my_time_v = "";
        let my_block_raw_value_v = "";
        let my_time = 0;
        let my_block_raw_value = 0;
        // TODO-sck check this
        // if (5==6) {
        //     console.log(global_plate_block_plate_index_list_matches)
        //     console.log("$('#value_formset')")
        //     console.log($('#value_formset'))
        //     console.log("$('#value_formset').find('.inline')")
        //     console.log($('#value_formset').find('.inline'))
        //     console.log("$('#value_formset').find('.inline').first()")
        //     console.log($('#value_formset').find('.inline').first())
        //     console.log("$('#value_formset').find('.inline').first()[0]")
        //     console.log($('#value_formset').find('.inline').first()[0])
        //     console.log("$('#value_formset').find('.inline').first()[0].outerHTML")
        //     console.log($('#value_formset').find('.inline').first()[0].outerHTML)
            $('#value_formset').children().each(function(cfs) {
            // $('#value_formset').find('.inline').forEach(function (cfs) {
                // get values from value item
                my_block_v = "id_assayplatereadermapitemvalue_set-" + cfs + "-assayplatereadermapdatafileblock";
                my_block = $('#' + my_block_v).val();
                my_time_v = "id_assayplatereadermapitemvalue_set-" + cfs + "-time";
                my_block_raw_value_v = "id_assayplatereadermapitemvalue_set-" + cfs + "-raw_value";
                my_time = $('#' + my_time_v).val();
                my_block_raw_value = $('#' + my_block_raw_value_v).val();
                if (global_plate_block_pk == my_block) {
                    global_plate_block_plate_index_list_matches.push(cfs);
                    global_plate_block_time_matches.push(my_time);
                    global_plate_block_raw_value_matches.push(my_block_raw_value);
                }
                midx = midx + 1;
            });
            // console.log(global_plate_block_plate_index_list_matches)
            // console.log(global_plate_block_time_matches)
            // console.log(global_plate_block_raw_value_matches)
        // } else {
        //     alert("Sorry, changing the display of the block does not work yet.")
        // }
        // if the user changed the block, change the displace time and raw value
        if (called_from === "changed_file_block") {
            buildPlate("on_load_update_or_view");
        }
    }
    // called from change checkboxes and from setFancyCheckBoxes 
    // to override check boxes and hide information that is not relevant for well use
    function changeShowInPlate(where_called_from) {
        // changeShowInPlate('changed_check_box') ('sfc_apply_button') ('sfc_build_plate') ('sfc_drag')
        let my_well_use = '';
        // console.log("called well use show in plate")
        // go to each cell in plate map and hide non relevant fields
        for ( var idx = 0, ls = global_plate_size; idx < ls; idx++ ) {
            my_well_use =  document.getElementById ('well_use-' + idx).innerText;
            // console.log("index  ", idx, "  well use inside loop ", my_well_use)
            if (my_well_use === 'blank' || my_well_use === 'empty' || my_well_use === 'standard') {
                $('#matrix_item-' + idx).addClass('hidden');
                $('#location-' + idx).addClass('hidden');
                $('#dilution_factor-' + idx).addClass('hidden');
                $('#compound-' + idx).addClass('hidden');
                $('#cell-' + idx).addClass('hidden');
                $('#setting-' + idx).addClass('hidden');
                $('#collection_volume-' + idx).addClass('hidden');
                $('#collection_time-' + idx).addClass('hidden');
                $('#show_block_raw_value-' + idx).addClass('hidden');
                // TODO-sck CHECK THIS after get data in
                $('#default_time-' + idx).addClass('hidden');
                $('#time-' + idx).addClass('hidden');
            }
            if (my_well_use === 'blank') {
                $('#standard_value-' + idx).addClass('hidden');
            } else if (my_well_use === 'empty') {
                $('#standard_value-' + idx).addClass('hidden');
                $('#well_use-' + idx).addClass('hidden');
            } else if (my_well_use === 'sample') {
                $('#standard_value-' + idx).addClass('hidden');
            } else {
            }
            // trying to remove a class did not work as expected - user will have to turn on-off as needed
            // if (my_well_use === 'blank' || my_well_use === 'empty') {
            //     // regardless of whether well use is CHECKED on or off, it must be on for blank wells
            //     $('#well_use-' + idx).removeClass('hidden');
            // }
        }
    }; 
    // Makes the well labels to use in building the plate map (based on the plate size)
    // this is called when page is loaded and when START is changed (plate size, matrix, platemap)
    function plateLabels(aore) {
        // console.log("plate size before call ajax: ",global_plate_size)
        let data = {
                call: 'fetch_information_for_plate_map_layout',
                plate_size: global_plate_size,
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            }
        window.spinner.spin(document.getElementById("spinner"));
        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                window.spinner.stop();
                let exist = true;
                packPlateLayout(json, exist);
                buildPlate(aore);
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred, please try a different matrix, plate map, or start from an empty plate.');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
    let packPlateLayout = function (json, exist) {
        let packed_lists = json.packed_lists;

        // console.log(packed_lists)

        let row_labels = packed_lists[0].row_labels;
        let col_labels = packed_lists[0].col_labels;
        let row_contents = packed_lists[0].row_contents;

        // console.log(row_labels)
        // console.log(col_labels)
        // console.log(row_contents)

        // NOTE that this arrangement will be first is when 0 for both row and column
        global_plate_data_packed = [col_labels, row_labels, row_contents];
    };

    // This is the guts of the STARTING plate building function
    // It has conditions, based on where the function was called from, which determine the content of the STARTING plate map
    function buildPlate(aore) {
        // console.log("run number build plate: ", global_plate_check_number_run);
        global_plate_check_number_run = global_plate_check_number_run+1;
        // console.log("where called from ", aore)
        // console.log("global_plate_data_packed")
        // console.log(global_plate_data_packed)

        let key_value_plate_index_row_index = {};
        let key_value_plate_index_column_index = {};
        let top_label_button = ' ';
        let side_label_button = ' ';
        // this table's table tag and closing tag are in the html file
        $('#plate_table').empty();
        let thead = document.createElement("thead");
        let headRow = document.createElement("tr");
        // column headers: first, then the rest in loop
        let th=document.createElement("th");
        th.appendChild(document.createTextNode("Label"));
        headRow.appendChild(th);
        let header_col_index = 0;
        //global_plate_data_packed = [col_labels, row_labels, row_contents];
        global_plate_data_packed[0].forEach(function(col) {
            let th=document.createElement("th");
            // th.appendChild(document.createTextNode(col + top_label_button));
            top_label_button = ' <a id="col'+header_col_index+'" column-or-row="column" column-index="'+header_col_index+'" row-index="'+770+'" class="btn btn-sm btn-primary apply-button">Apply to Column</a>'
            $(th).html(col + top_label_button);
            headRow.appendChild(th);
            header_col_index = header_col_index + 1;
        });

        thead.appendChild(headRow);
        plate_table.appendChild(thead);

        // for each row
        let tbody = document.createElement("tbody");
        // let tr = document.createElement("tr");
        // get the first column (A B C D E...)
        let formsetidx = 0;
        let ridx = 0;
        global_plate_data_packed[1].forEach(function(row) {
            let trbodyrow = document.createElement("tr");
            let tdbodyrow = document.createElement("th");

            side_label_button = ' <a id="row'+ridx+'" column-or-row="row" column-index="'+772+'" row-index="'+ridx+'" class="btn btn-sm btn-primary apply-button">Apply to Row</a>'
            // tdbodyrow.appendChild(document.createTextNode(global_plate_data_packed[1][ridx]));
            $(tdbodyrow).html(global_plate_data_packed[1][ridx] + side_label_button);
            trbodyrow.appendChild(tdbodyrow);
            let cidx = 0;
            // build content row (same row as the row_labels (A=A, B=B, etc.)
            // while in a row, go through each column

            global_plate_data_packed[2][ridx].forEach(function(el) {
                // console.log("formsetidx ", formsetidx)
                // make all the parts of the table body (NOTE: 10 possible items for display in plate map)
                let td = document.createElement("td");
                let div_label = document.createElement("div");
                $(div_label).attr('data-index', formsetidx);
                $(div_label).attr('row-index', ridx);
                $(div_label).attr('column-index', cidx);
                $(div_label).attr('id', "label-"+formsetidx);
                $(div_label).addClass('map-label plate-cells-label hidden');
                // for coloring, for hiding, START with hidden

                let div_location = document.createElement("div");
                $(div_location).attr('data-index', formsetidx);
                $(div_location).attr('row-index', ridx);
                $(div_location).attr('column-index', cidx);
                $(div_location).attr('id', "location-"+formsetidx);
                $(div_location).addClass('map-location plate-cells-location hidden');

                let div_matrix_item = document.createElement("div");
                $(div_matrix_item).attr('data-index', formsetidx);
                $(div_matrix_item).attr('row-index', ridx);
                $(div_matrix_item).attr('column-index', cidx);
                $(div_matrix_item).attr('id', "matrix_item-"+formsetidx);
                $(div_matrix_item).addClass('map-matrix-item plate-cells-matrix-item hidden');

                let div_dilution_factor = document.createElement("div");
                $(div_dilution_factor).attr('data-index', formsetidx);
                $(div_dilution_factor).attr('row-index', ridx);
                $(div_dilution_factor).attr('column-index', cidx);
                $(div_dilution_factor).attr('id', "dilution_factor-"+formsetidx);
                $(div_dilution_factor).addClass('map-dilution-factor plate-cells-dilution-factor hidden');

                let div_collection_volume = document.createElement("div");
                $(div_collection_volume).attr('data-index', formsetidx);
                $(div_collection_volume).attr('row-index', ridx);
                $(div_collection_volume).attr('column-index', cidx);
                $(div_collection_volume).attr('id', "collection_volume-"+formsetidx);
                $(div_collection_volume).addClass('map-collection-volume plate-cells-collection-volume hidden');

                let div_collection_time = document.createElement("div");
                $(div_collection_time).attr('data-index', formsetidx);
                $(div_collection_time).attr('row-index', ridx);
                $(div_collection_time).attr('column-index', cidx);
                $(div_collection_time).attr('id', "collection_time-"+formsetidx);
                $(div_collection_time).addClass('map-collection-time plate-cells-collection-time hidden');

                let div_well_use = document.createElement("div");
                $(div_well_use).attr('data-index', formsetidx);
                $(div_well_use).attr('row-index', ridx);
                $(div_well_use).attr('column-index', cidx);
                $(div_well_use).attr('id', "well_use-"+formsetidx);
                $(div_well_use).addClass('map-well-use plate-cells-well-use hidden');

                let div_compound = document.createElement("div");
                $(div_compound).attr('data-index', formsetidx);
                $(div_compound).attr('row-index', ridx);
                $(div_compound).attr('column-index', cidx);
                $(div_compound).attr('id', "compound-"+formsetidx);
                $(div_compound).addClass('map-compound plate-cells-compound hidden');

                let div_cell = document.createElement("div");
                $(div_cell).attr('data-index', formsetidx);
                $(div_cell).attr('row-index', ridx);
                $(div_cell).attr('column-index', cidx);
                $(div_cell).attr('id', "cell-"+formsetidx);
                $(div_cell).addClass('map-cell plate-cells-cell hidden');

                let div_setting = document.createElement("div");
                $(div_setting).attr('data-index', formsetidx);
                $(div_setting).attr('row-index', ridx);
                $(div_setting).attr('column-index', cidx);
                $(div_setting).attr('id', "setting-"+formsetidx);
                $(div_setting).addClass('map-setting plate-cells-setting hidden');

                let div_standard_value = document.createElement("div");
                $(div_standard_value).attr('data-index', formsetidx);
                $(div_standard_value).attr('row-index', ridx);
                $(div_standard_value).attr('column-index', cidx);
                $(div_standard_value).attr('id', "standard_value-"+formsetidx);
                $(div_standard_value).addClass('map-standard-value plate-cells-standard-value hidden');

                let div_default_time = document.createElement("div");
                $(div_default_time).attr('data-index', formsetidx);
                $(div_default_time).attr('row-index', ridx);
                $(div_default_time).attr('column-index', cidx);
                $(div_default_time).attr('id', "default_time-"+formsetidx);
                $(div_default_time).addClass('map-default-time plate-cells-default-time hidden');

                let div_time = document.createElement("div");
                $(div_time).attr('data-index', formsetidx);
                $(div_time).attr('row-index', ridx);
                $(div_time).attr('column-index', cidx);
                $(div_time).attr('id', "time-"+formsetidx);
                $(div_time).addClass('map-time plate-cells-time hidden');

                let div_block_raw_value = document.createElement("div");
                $(div_block_raw_value).attr('data-index', formsetidx);
                $(div_block_raw_value).attr('row-index', ridx);
                $(div_block_raw_value).attr('column-index', cidx);
                $(div_block_raw_value).attr('id', "block_raw_value-"+formsetidx);
                $(div_block_raw_value).addClass('map-block-raw-value plate-cells-block-raw-value hidden');
                // TODO-sck make sure to add/copy over the file related stuff after get the import working
                // HANDY - need the .trim() after the .html() to strip white space
                // console.log('global_plate_check_page_call and aore ',   global_plate_check_page_call, "  ",aore)
                if (global_plate_check_page_call === 'add') {
                    // console.log("in add")
                    // if adding (from any option)
                    // need a formset for EACH well in the plate (for the item and the item value tables)
                    // https:// simpleit.rocks/python/django/dynamic-add-form-with-add-button-in-django-modelformset-template/
                    // console.log("formsetidx ",formsetidx)
                    $('#formset').append(global_plate_first_item_form.replace(/-0-/g, '-' + formsetidx + '-'));
                    $('#id_assayplatereadermapitem_set-TOTAL_FORMS').val(formsetidx + 1);
                    $('#value_formset').append(global_plate_first_value_form.replace(/-0-/g, '-' + formsetidx + '-'));
                    $('#id_assayplatereadermapitemvalue_set-TOTAL_FORMS').val(formsetidx + 1);
                    // this auto fills the fields that are needed to join the items and the items values tables
                    // the platemap id will be the same in both since they are two formsets to the main plate map table
                    // these (item and associated values) MUST stay parallel or problems WILL happen
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-row_index').val(ridx);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-column_index').val(cidx);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-plate_index').val(formsetidx);
                    $('#id_assayplatereadermapitemvalue_set-' + formsetidx + '-plate_index').val(formsetidx);
                }
                // Handle all BUT well use and the matrix item (separate section)
                // this is also called label in the app (well label A1, etc)
                $('#id_assayplatereadermapitem_set-' + formsetidx + '-name').val(el);
                div_label.appendChild(document.createTextNode(el));
                if (aore === "on_load_add" || aore === "changed_device" || aore === "changed_matrix") {
                    // when adding from plate (load or change) or matrix, this content is place holder or autofilled content
                    div_location.appendChild(document.createTextNode("-"));
                    div_dilution_factor.appendChild(document.createTextNode("1"));
                    div_collection_volume.appendChild(document.createTextNode("0"));
                    div_collection_time.appendChild(document.createTextNode("0"));
                    div_standard_value.appendChild(document.createTextNode("0"));
                    div_default_time.appendChild(document.createTextNode("0"));

                    div_time.appendChild(document.createTextNode("0"));
                    div_block_raw_value.appendChild(document.createTextNode("0"));
                } else if (aore === "changed_platemap") {
                    // pull from AN existing plate map, but not THIS one, as a STARTing place (add)
                    // global_plate_iplatemap_dictionary = platemap_info;
                    // console.log(global_plate_iplatemap_dictionary[2].name, " ", global_plate_iplatemap_dictionary[2].plate_index)
                    //list_of_item_fields = ['well_name', 'matrix_item_id', 'well_use', 'location_id', 'standard_value', 'dilution_factor', 'collection_volume', 'collection_time']
                    //list_of_value_fields = ['plate_index', 'time']
                    let platemap_location = 0;
                    try {
                        platemap_location = global_plate_iplatemap_dictionary[formsetidx].location_id;
                    } catch(err) { }
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-location').val(platemap_location);
                    let saved_location = $('#id_assayplatereadermapitem_set-' + formsetidx + '-location').val();
                    $('#id_ns_location').val(saved_location);
                    let saved_text_location = $('#id_ns_location').children("option:selected").text();
                    div_location.appendChild(document.createTextNode(saved_text_location));
                    try {
                        div_dilution_factor.appendChild(document.createTextNode(global_plate_iplatemap_dictionary[formsetidx].dilution_factor));
                    } catch(err) {
                        div_dilution_factor.appendChild(document.createTextNode(1));
                    }
                    try {
                        div_collection_volume.appendChild(document.createTextNode(global_plate_iplatemap_dictionary[formsetidx].collection_volume));
                    } catch(err) {
                        div_collection_volume.appendChild(document.createTextNode(0));
                    }
                    try {
                        div_collection_time.appendChild(document.createTextNode(global_plate_iplatemap_dictionary[formsetidx].collection_time));
                    } catch(err) {
                        div_collection_time.appendChild(document.createTextNode(0));
                    }
                    let this_standard_value = 0;
                    try {
                        this_standard_value = global_plate_iplatemap_dictionary[formsetidx].standard_value;
                    } catch(err) {}

                    div_standard_value.appendChild(document.createTextNode(formatNumber(this_standard_value)));
                    //div_standard_value.appendChild(document.createTextNode(global_plate_iplatemap_dictionary[formsetidx].standard_value));

                    try {
                        div_default_time.appendChild(document.createTextNode(global_plate_iplatemap_dictionary[formsetidx].default_time));;
                    } catch(err) {
                        div_default_time.appendChild(document.createTextNode(0));
                    }
                    // put the default time into the time of the value item set
                    try {
                        div_time.appendChild(document.createTextNode(global_plate_iplatemap_dictionary[formsetidx].default_time));;
                    } catch(err) {
                        div_time.appendChild(document.createTextNode(0));
                    }
                    // raw value to 0, do not get raw value from other platemap
                    div_block_raw_value.appendChild(document.createTextNode("0"));

                } else {
                    // aore = "on_load_update_or_view" or "update_changed_file_block"
                    if (aore === "on_load_update_or_view") {
                        let saved_location = $('#id_assayplatereadermapitem_set-' + formsetidx + '-location').val();
                        $('#id_ns_location').val(saved_location);
                        let saved_text_location = $('#id_ns_location').children("option:selected").text();
                        // console.log("location: ", saved_location)
                        // shouldnot need here....div_label.appendChild(document.createTextNode($('#id_assayplatereadermapitem_set-' + formsetidx + '-name').val()));
                        div_location.appendChild(document.createTextNode(saved_text_location));
                        div_dilution_factor.appendChild(document.createTextNode($('#id_assayplatereadermapitem_set-' + formsetidx + '-dilution_factor').val()));
                        div_collection_volume.appendChild(document.createTextNode($('#id_assayplatereadermapitem_set-' + formsetidx + '-collection_volume').val()));
                        div_collection_time.appendChild(document.createTextNode($('#id_assayplatereadermapitem_set-' + formsetidx + '-collection_time').val()));
                        div_default_time.appendChild(document.createTextNode($('#id_assayplatereadermapitem_set-' + formsetidx + '-default_time').val()));
                        div_standard_value.appendChild(document.createTextNode($('#id_assayplatereadermapitem_set-' + formsetidx + '-standard_value').val()));
                    }
                    // if (aore === "on_load_update_or_view" || global_plate_number_file_block_sets == 0) {
                    if (aore === "on_load_update_or_view" && global_plate_number_file_block_sets == 0) {
                        div_time.appendChild(document.createTextNode($('#id_assayplatereadermapitemvalue_set-' + formsetidx + '-time').val()));
                        div_block_raw_value.appendChild(document.createTextNode($('#id_assayplatereadermapitemvalue_set-' + formsetidx + '-raw_value').val()));
                    } else {
                        div_time.appendChild(document.createTextNode(global_plate_block_time_matches[formsetidx]));
                        div_block_raw_value.appendChild(document.createTextNode(global_plate_block_raw_value_matches[formsetidx]));
                        $(div_time).prop('value-formset-index', global_plate_block_plate_index_list_matches[formsetidx]);
                        $(div_block_raw_value).prop('value-formset-index', global_plate_block_plate_index_list_matches[formsetidx]);
                    }
                }
                // handling the matrix item and well use HERE (well changed if formsets in the welluseChange function
                if (aore === "on_load_add" || aore === "changed_device" || aore === "changed_matrix") {
                    if (aore === "changed_matrix") {
                        //"a_matrix"
                        // console.log("imatrix row col ", global_plate_imatrix_item_row_column_index)
                        let what_row_column = ridx.toString()+"-"+cidx.toString();
                        // console.log("on this one: ", what_row_column)
                        // console.log("formset: ", formsetidx)
                        let index_row_column = global_plate_imatrix_item_row_column_index.indexOf(what_row_column);
                        // console.log("a matrix index row_column ", index_row_column)
                        if (index_row_column < 0) {
                            // if there was not match in the existing matrix for row and column, make it an empty
                            div_well_use.appendChild(document.createTextNode("empty"));
                            div_matrix_item.appendChild(document.createTextNode("-"));
                            div_compound.appendChild(document.createTextNode("-"));
                            div_cell.appendChild(document.createTextNode("-"));
                            div_setting.appendChild(document.createTextNode("-"));
                        } else {
                            // there is a match for the row and column in the selected matrix
                            div_well_use.appendChild(document.createTextNode("sample"));
                            $('#id_assayplatereadermapitem_set-' + formsetidx + '-well_use').val('sample');
                            $('#id_assayplatereadermapitemvalue_set-' + formsetidx + 'well_use').val('sample');
                            let this_matrix_item = global_plate_imatrix_item_id[index_row_column];
                            $('#id_assayplatereadermapitem_set-' + formsetidx + '-matrix_item').val(this_matrix_item);

                            // now same as existing..could streamline code later
                            let saved_matrix_item = $('#id_assayplatereadermapitem_set-' + formsetidx + '-matrix_item').val();
                            $('#id_ns_matrix_item').val(saved_matrix_item);
                            let saved_text_matrix_item = $('#id_ns_matrix_item').children("option:selected").text();
                            div_matrix_item.appendChild(document.createTextNode(saved_text_matrix_item));
                            let my_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(saved_matrix_item));
                            // console.log(my_index)
                            div_compound.appendChild(document.createTextNode(global_plate_isetup_compound[my_index]));
                            div_cell.appendChild(document.createTextNode(global_plate_isetup_cell[my_index]));
                            div_setting.appendChild(document.createTextNode(global_plate_isetup_setting[my_index]));
                            // div_compound.appendChild(document.createTextNode($('#cp' + saved_matrix_item + '-compound-short').text()));
                            // div_cell.appendChild(document.createTextNode($('#cl' + saved_matrix_item + '-cell-short').text()));
                            // div_setting.appendChild(document.createTextNode($('#st' + saved_matrix_item + '-setting-short').text()));
                        }                        
                    } else {
                        div_well_use.appendChild(document.createTextNode("empty"));
                        div_matrix_item.appendChild(document.createTextNode("-"));
                        div_compound.appendChild(document.createTextNode("-"));
                        div_cell.appendChild(document.createTextNode("-"));
                        div_setting.appendChild(document.createTextNode("-"));                        
                    }
                } else if (aore === "changed_platemap") {
                    // console.log(global_plate_iplatemap_dictionary[formsetidx])
                    // pull from AN existing plate map, but not THIS one, as a STARTing place (add)
                    //list_of_item_fields = ['well_name', 'matrix_item_id', 'well_use', 'location_id', 'standard_value', 'dilution_factor', 'collection_volume', 'collection_time']
                    //list_of_value_fields = ['plate_index', 'time']
                    let platemap_well_use = global_plate_iplatemap_dictionary[formsetidx].well_use;
                    div_well_use.appendChild(document.createTextNode(platemap_well_use));
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-well_use').val(platemap_well_use);
                    $('#id_assayplatereadermapitemvalue_set-' + formsetidx + 'well_use').val(platemap_well_use);
                    let saved_matrix_item = global_plate_iplatemap_dictionary[formsetidx].matrix_item_id;
                    $('#id_ns_matrix_item').val(saved_matrix_item);
                    let saved_text_matrix_item = $('#id_ns_matrix_item').children("option:selected").text();
                    div_matrix_item.appendChild(document.createTextNode(saved_text_matrix_item));
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-matrix_item').val(saved_matrix_item);
                    let my_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(saved_matrix_item));
                    // console.log(my_index)
                    div_compound.appendChild(document.createTextNode(global_plate_isetup_compound[my_index]));
                    div_cell.appendChild(document.createTextNode(global_plate_isetup_cell[my_index]));
                    div_setting.appendChild(document.createTextNode(global_plate_isetup_setting[my_index]));
                    // div_compound.appendChild(document.createTextNode($('#cp' + saved_matrix_item + '-compound-short').text()));
                    // div_cell.appendChild(document.createTextNode($('#cl' + saved_matrix_item + '-cell-short').text()));
                    // div_setting.appendChild(document.createTextNode($('#st' + saved_matrix_item + '-setting-short').text()));
                } else {
                    // aore = "on_load_update_or_view" or "update_changed_file_block" 
                    // if changed fileblock, no change or well use or matrix item should be needed
                    if (aore === "on_load_update_or_view") {
                        div_well_use.appendChild(document.createTextNode($('#id_assayplatereadermapitem_set-' + formsetidx + '-well_use').val()));
                        let saved_matrix_item = $('#id_assayplatereadermapitem_set-' + formsetidx + '-matrix_item').val();
                        $('#id_ns_matrix_item').val(saved_matrix_item);
                        let saved_text_matrix_item = $('#id_ns_matrix_item').children("option:selected").text();
                        div_matrix_item.appendChild(document.createTextNode(saved_text_matrix_item));
                        let my_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(saved_matrix_item));
                        // console.log(global_plate_isetup_matrix_item_id)
                        // console.log(saved_matrix_item)
                        // console.log(my_index)
                        div_compound.appendChild(document.createTextNode(global_plate_isetup_compound[my_index]));
                        div_cell.appendChild(document.createTextNode(global_plate_isetup_cell[my_index]));
                        div_setting.appendChild(document.createTextNode(global_plate_isetup_setting[my_index]));
                        // div_compound.appendChild(document.createTextNode($('#cp' + saved_matrix_item + '-compound-short').text()));
                        // div_cell.appendChild(document.createTextNode($('#cl' + saved_matrix_item + '-cell-short').text()));
                        // div_setting.appendChild(document.createTextNode($('#st' + saved_matrix_item + '-setting-short').text()));
                    }
                }                

                key_value_plate_index_row_index[formsetidx] = ridx;
                key_value_plate_index_column_index[formsetidx] = cidx;

                formsetidx = formsetidx + 1;

                // put it all together - here is where the order matters
                let tdbodycell = document.createElement("td");
                // the order here will determine the order in the well plate
                tdbodycell.appendChild(div_label);
                tdbodycell.appendChild(div_well_use);
                tdbodycell.appendChild(div_block_raw_value);
                tdbodycell.appendChild(div_time);
                tdbodycell.appendChild(div_default_time);
                tdbodycell.appendChild(div_dilution_factor);
                tdbodycell.appendChild(div_matrix_item);
                tdbodycell.appendChild(div_location);
                tdbodycell.appendChild(div_compound);
                tdbodycell.appendChild(div_cell);
                tdbodycell.appendChild(div_setting);
                tdbodycell.appendChild(div_collection_volume);
                tdbodycell.appendChild(div_collection_time);
                tdbodycell.appendChild(div_standard_value);
                trbodyrow.appendChild(tdbodycell);
                cidx = cidx + 1;
            });
            tbody.appendChild(trbodyrow);
            ridx = ridx + 1;

        });
        plate_table.appendChild(tbody);
        setFancyCheckBoxes('build_plate');
        global_plate_when_called_checkboxes = "set_as_current_checkboxes";
        return plate_table
    }
    // this is called for each well that is "apply" buttoned or "drag" ed over
    // empties the things that are NOT part of the selected well use for this well in the plate map
    function welluseChange(idx) {
        // if add page or page where no file/block has been assigned, my_value_index = idx,
        // get index of entire value set from the attribute that was found in findValueSet
        // and added when the plate map table was created
        let my_value_formset_index =  idx;
        if (global_plate_number_file_block_sets > 0) {
            my_value_formset_index = $('#time-' + idx).prop('value-formset-index');
            // TODO-sck check times too... formset for raw???
        }
        $('#well_use-' + idx).text(global_plate_well_use);
        $('#id_assayplatereadermapitem_set-' + idx + '-well_use').val(global_plate_well_use);
        $('#id_assayplatereadermapitemvalue_set-' + my_value_formset_index + '-well_use').val(global_plate_well_use);
        //  id_assayplatereadermapitemvalue_set-0-well_use
        // console.log("global_plate_well_use ",global_plate_well_use)
        // console.log("my_value_formset_index ", my_value_formset_index)

        if (global_plate_well_use === 'blank' || global_plate_well_use === 'empty' || global_plate_well_use === 'standard') {
            // reset other fields for user
            $('#matrix_item-' + idx).text("-");
            $('#id_assayplatereadermapitem_set-' + idx + '-matrix_item').val(null);

            // change the compound displayed in the table to nothing
            $('#compound-' + idx).text("-");
            $('#cell-' + idx).text("-");
            $('#setting-' + idx).text("-");

            $('#location-' + idx).text("-");
            $('#id_assayplatereadermapitem_set-' + idx + '-location').val("0");

            $('#dilution_factor-' + idx).text("1");
            $('#id_assayplatereadermapitem_set-' + idx + '-dilution_factor').val("1");
            $('#collection_volume-' + idx).text("0");
            $('#id_assayplatereadermapitem_set-' + idx + '-collection_volume').val("0");
            $('#collection_time-' + idx).text("0");
            $('#id_assayplatereadermapitem_set-' + idx + '-collection_time').val("0");

            // console.log(global_plate_number_file_block_sets)
            // console.log($('#time-' + idx).prop('value-formset-index'))
            // console.log("value formset index: ",my_value_formset_index)

            $('#default_time-' + idx).text("0");
            $('#id_assayplatereadermapitem_set-' + idx + '-default_time').val("0");
            //raw value and time (not default time) should be left alone since any one could have a raw value and time
        }
        if (global_plate_well_use === 'blank' || global_plate_well_use === 'empty' || global_plate_well_use === 'sample') {
            // reset other fields for user
            $('#standard_value-' + idx).text("0");
            $('#id_assayplatereadermapitem_set-' + idx + '-standard-value').val("0");
        }
        // if (global_plate_well_use === 'blank' || global_plate_well_use === 'empty') {
        //     // only ever need to see the well use
        // } else if (global_plate_well_use === 'standard') {
        //     // show the standard value
        // } else {
        //     // show what was showing before
        // }
    }
    //
    // Guts of changing the plate map with drag or apply
    // this executes for a list of wells/cells in the plate map table (selected with drag or Apply button)
    function specificChanges(plate_index_list, apply_or_drag) {
        // may need to add a top and bottom combo if requested
        if (global_plate_change_method === 'increment' && (global_plate_increment_direction === 'right-up' || global_plate_increment_direction === 'right-right' || global_plate_increment_direction === 'bottom-bottom')) {
            plate_index_list_ordered = plate_index_list.sort(function(a, b){return b-a});
            // console.log("dsc ", plate_index_list_ordered)
        } else {
            // save for reference but should be ordered....plate_index_list_ordered = plate_index_list.map(Number).sort(function(a, b){return a-b});
            plate_index_list_ordered = plate_index_list;
            // console.log("asc ", plate_index_list_ordered)
        }

        // console.log(apply_or_drag)
        // console.log(plate_index_list)
        // called from clicking an apply button or dragging over a cells
        // brings a list of plate_indexes to change and changes each well in the list
        // set here to make sure to avoid race errors
        // one way of getting the values
        global_plate_default_time_value = document.getElementById('id_form_number_default_time').value;
        global_plate_dilution_factor = document.getElementById('id_form_number_dilution_factor').value;
        global_plate_collection_volume = document.getElementById('id_form_number_collection_volume').value;
        global_plate_collection_time = document.getElementById('id_form_number_collection_time').value;
        global_plate_increment_value = document.getElementById('id_form_number_increment_value').value;
        global_plate_standard_value = document.getElementById('id_form_number_standard_value').value;
        // another way of getting the values, but this locked the input boxes so could not use.. :O
        // global_plate_time_value = $("#id_se_time").selectize()[0].selectize.items[0];
        // global_plate_dilution_factor = $("#id_form_number_dilution_factor").selectize()[0].selectize.items[0];
        // global_plate_collection_volume = $("#id_form_number_collection_volume").selectize()[0].selectize.items[0];
        // global_plate_collection_time = $("#id_form_number_collection_time").selectize()[0].selectize.items[0];
        // global_plate_increment_value = $("#id_form_number_increment_value").selectize()[0].selectize.items[0];
        // global_plate_standard_value = $("#id_form_number_standard_value").selectize()[0].selectize.items[0];
        let incrementing_default_time_value = parseFloat(global_plate_default_time_value);
        let incrementing_standard_value = parseFloat(global_plate_standard_value);
        // console.log("global_plate_time_value", global_plate_time_value)
        // console.log("global_plate_increment_value", global_plate_increment_value)
        // console.log("global_plate_dilution_factor", global_plate_dilution_factor)
        // console.log("global_plate_collection_volume", global_plate_collection_volume)
        // console.log("global_plate_collection_time", global_plate_collection_time)
        // console.log("global_plate_standard_value", global_plate_standard_value)
        // console.log("incrementing_default_time_value", incrementing_default_time_value)
        // console.log("incrementing_standard_value", incrementing_standard_value)

        let this_operation = global_plate_increment_operation;
        let this_inc_value = global_plate_increment_value;
        let adjusted_inc_value = global_plate_increment_value;

        // reduce to * or +
        if (global_plate_change_method === 'increment') {
            if (this_operation === 'divide') {
                this_operation = '*';
                adjusted_inc_value = 1.0/this_inc_value;
            } else if (this_operation === 'multiply') {
                this_operation = '*';
                adjusted_inc_value = 1.0*this_inc_value;
            } else if (this_operation === 'subtract') {
                this_operation = '+';
                adjusted_inc_value = -1.0*this_inc_value;
            } else if (this_operation === 'add') {
                this_operation = '+';
                adjusted_inc_value = 1.0*this_inc_value;
            } else {
            }
        }

        // keep to identify the first one since it is treated differently
        let which_change_number = 0;
        // console.log("change list: ", plate_index_list_ordered)
        plate_index_list_ordered.forEach(function(idx) {
            // console.log("i: ",idx, " count: ", global_plate_number_file_block_sets)
            // do for things that can ONLY copy (not increment)
            let my_value_formset_index2 = idx;
            if (global_plate_number_file_block_sets > 0) {
                // time and raw value will have a different index since they are in the itemvalue table, not the item table
                my_value_formset_index2 = $('#time-' + idx).prop('value-formset-index');
                // TODO formset for raw??
                // TODO get the right raw value from the right value formset showing in the plate
            }
            // console.log("my_value_formset_index2", my_value_formset_index2)
            if (global_plate_well_use === 'sample') {
                if ($("input[type='checkbox'][name='change_matrix_item']").prop('checked') === true) {
                    $('#matrix_item-' + idx).text(global_plate_matrix_item_text);
                    $('#id_assayplatereadermapitem_set-' + idx + '-matrix_item').val(global_plate_matrix_item);
                    // console.log("matrix item  ",$('#cp' + global_plate_matrix_item + '-compound-short').text())
                    // change the compound displayed in the table
                    let my_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(global_plate_matrix_item));
                    // console.log(my_index)
                    $('#compound-' + idx).text(global_plate_isetup_compound[my_index]);
                    $('#cell-' + idx).text(global_plate_isetup_cell[my_index]);
                    $('#setting-' + idx).text(global_plate_isetup_setting[my_index]);
                    // $('#compound-' + idx).text($('#cp' + global_plate_matrix_item + '-compound-short').text());
                    // $('#cell-' + idx).text($('#cl' + global_plate_matrix_item + '-cell-short').text());
                    // $('#setting-' + idx).text($('#st' + global_plate_matrix_item + '-setting-short').text());
                }
                if ($("input[type='checkbox'][name='change_location']").prop('checked') === true) {
                    $('#location-' + idx).text(global_plate_location_text);
                    $('#id_assayplatereadermapitem_set-' + idx + '-location').val(global_plate_location);
                }
                if ($("input[type='checkbox'][name='change_dilution_factor']").prop('checked') === true) {
                    $('#dilution_factor-' + idx).text(global_plate_dilution_factor);
                    $('#id_assayplatereadermapitem_set-' + idx + '-dilution_factor').val(global_plate_dilution_factor);
                }
                if ($("input[type='checkbox'][name='change_collection_volume']").prop('checked') === true) {
                    $('#collection_volume-' + idx).text(global_plate_collection_volume);
                    $('#id_assayplatereadermapitem_set-' + idx + '-collection_volume').val(global_plate_collection_volume);
                }
                if ($("input[type='checkbox'][name='change_collection_time']").prop('checked') === true) {
                    $('#collection_time-' + idx).text(global_plate_collection_time);
                    $('#id_assayplatereadermapitem_set-' + idx + '-collection_time').val(global_plate_collection_time);
                }
            } else {
                // standard or empty or blank
                // empty and blank changed in well use function, standard value can be incremented..nothing to do here
            }
            // do for things that can copy or increment (Time or Standard Value ONLY)
            // console.log(global_plate_change_method)
            // console.log("change number: ",which_change_number)
            if (global_plate_change_method === 'copy' || (global_plate_change_method === 'increment' && which_change_number == 0 )) {
                // copy selected by user
                // console.log(global_plate_well_use)
                if (global_plate_well_use === 'sample') {
                    // default time is in the item table
                    if ($("input[type='checkbox'][name='change_default_time']").prop('checked') === true) {
                        $('#default_time-' + idx).text(global_plate_default_time_value);
                        $('#id_assayplatereadermapitem_set-' + idx + '-default_time').val(global_plate_default_time_value);

                        if (global_plate_number_file_block_sets == 0) {
                            $('#time-' + idx).text(global_plate_default_time_value);
                            $('#id_assayplatereadermapitemvalue_set-' + idx + '-time').val(global_plate_default_time_value);
                        }
                    }
                } else if (global_plate_well_use === 'standard') {
                        $('#standard_value-' + idx).text(formatNumber(global_plate_standard_value));
                        $('#id_assayplatereadermapitem_set-' + idx + '-standard_value').val(global_plate_standard_value);
                } else {
                    // empty or blank
                }
            } else {
                // increment selected by user
                // let this_operation = * or +
                // let this_inc_value = adjusted to match
                // thought need to do something different with dragging, but this should work like the matrix
                if (this_operation === "*") {
                    incrementing_default_time_value = incrementing_default_time_value * adjusted_inc_value;
                    incrementing_standard_value = incrementing_standard_value * adjusted_inc_value;
                } else {
                    incrementing_default_time_value = incrementing_default_time_value + adjusted_inc_value;
                    incrementing_standard_value = incrementing_standard_value + adjusted_inc_value;
                }
                if (global_plate_well_use === 'sample') {
                    if ($("input[type='checkbox'][name='change_default_time']").prop('checked') === true) {
                        $('#default_time-' + idx).text(incrementing_default_time_value);
                        $('#id_assayplatereadermapitem_set-' + idx + '-default_time').val(incrementing_default_time_value);

                        if (global_plate_number_file_block_sets == 0) {
                            $('#time-' + idx).text(incrementing_default_time_value);
                            $('#id_assayplatereadermapitemvalue_set-' + idx + '-time').val(incrementing_default_time_value);
                        }
                    }
                } else if (global_plate_well_use === 'standard') {
                    // console.log("1445", incrementing_standard_value)
                    $('#standard_value-' + idx).text(formatNumber(incrementing_standard_value));
                    $('#id_assayplatereadermapitem_set-' + idx + '-standard_value').val(incrementing_standard_value);
                } else {
                    // empty or blank
                }
            }
            which_change_number = which_change_number + 1;
        });
    }

    // general function to format numbers
    function formatNumber(this_number_in) {
        // console.log("function format ", this_number_in)
        let this_number = parseFloat(this_number_in);
        if (this_number <= 0.00001) {
            formatted_number = this_number.toExponential(4);
        } else if (this_number <= 0.0001) {
            formatted_number = this_number.toFixed(6);
        } else if (this_number <= 0.001) {
            formatted_number = this_number.toFixed(5);
        } else if (this_number <= 0.01) {
            formatted_number = this_number.toFixed(4);
        } else if (this_number <= 0.1) {
            formatted_number = this_number.toFixed(3);
        } else if (this_number <= 1) {
            formatted_number = this_number.toFixed(2);
        } else if (this_number <= 10) {
            formatted_number = this_number.toFixed(1);
        } else {
            formatted_number = this_number.toFixed(0);
        }
        return formatted_number;
    }
    //
    // function to purge previous formsets before adding new ones when redrawing a plate map - keep
    function removeFormsets() {
        // get rid of previous formsets before try to add more or the indexes get all messed up
        while ($('#formset').find('.inline').length > 0 ) {
            $('#formset').find('.inline').first().remove();
        }
        $('#id_assayplatereadermapitem_set-TOTAL_FORMS').val(0);
        while ($('#value_formset').find('.inline').length > 0 ) {
            $('#value_formset').find('.inline').first().remove();
        }
        $('#id_assayplatereadermapitemvalue_set-TOTAL_FORMS').val(0);
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
    // END - ADDITIONAL FUNCTION SECTION

    // START SECTION OF SPECIALS FOR EXTENDING FEATURES
    // allows table to be selectable, must be AFTER table is created - keep
    $('#plate_table').selectable({
        filter: 'td',
        distance: 25,
        stop: changeSelected
    });
    // activates Bootstrap tooltips, must be AFTER tooltips are created - keep
    $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
    // END SECTION OF SPECIALS FOR EXTENDING FEATURES

    // START - STUFF FOR REFERENCE
    // used to format the reference table - keep if show table, else, do not need this formatting
    // NOTE that the table is needed to pull setup information (using javascript) to show in plate map
    // NOTE: if show table as DataTable, matrix items that are not displayed are not accessible,
    // $('#matrix_items_table').DataTable({
    //  //"iDisplayLength": 25,
    //  "paging": false,
    //  "sDom": '<B<"row">lfrtip>',
    //  fixedHeader: {headerOffset: 50},
    //  responsive: true,
    //  "order": [[2, "asc"]],
    //});

    // keep for reference for now - adding a formset the original way from here:
    // https:// simpleit.rocks/python/django/dynamic-add-form-with-add-button-in-django-modelformset-template/

    // keep this for reference for now - the selected attribute had to be cleared BEFORE another could be assigned!
    // for each option                      clear selected              find one to select                       select it
    // $("#id_ns_method_target_unit option").removeAttr('selected').filter('[value='+global_plate_study_assay+']').attr('selected', true);
    // other suggested methods, might work if deselect first
    // $("#id_ns_method_target_unit").find('option[value=global_plate_study_assay]').attr('selected','selected');
    // $("#id_ns_method_target_unit > [value=global_plate_study_assay]").attr("selected", "true");
    // oR could loop through (this did not work to apply, but could work for remove than apply)
        // for(let i = 0; i < select_study_assay.options.length; i++){
        //  if(select_study_assay.options[i].value == global_plate_study_assay ){
        //      select_study_assay.options[i].selected = true;
        //      document.getElementById().selectedIndex = i;
        //  }
        //}

    // another method to try, do not recall if worked or not, need to retest
    // var $saveme = $('#standard_target_selected').selectize();
    // var myselection = $saveme[0].selectize;;
    // console.log(myselection)
    // example of finding regexp
    //  var needle = ':'
    //  var re = new RegExp(needle,'gi');
    //  var haystack = global_plate_file_block_dict;
    //  var results = new Array();
    //  while (re.exec(haystack)){
    //    results.push(re.lastIndex-1);
    //  }

    // this loop worked as expected at the time time tested
    // $('#formset').children().each(function() {
    //  if ( $(this).hasClass("item") && ( $(this).attr("data-value",'minute') || $(this).attr("data-value",'hour') || $(this).attr("data-value",'day') ) )
    //  {
    //  }
    //});

    // function console_me() {
    //  $( ".apply-button" ).each(function( index ) {
    //    // console.log( index + ": " + $( this ).text() );
    //  });
    //}
    // if can not figure out other ways:
    // let elem_size = document.getElementById ("existing_device_size");
    // global_plate_size = $("#existing_device_size").val(); does not work...
    // global_plate_size = elem_size.innerText;
    // BEST so far
    //     try {
    //         global_plate_size = $("#id_device").selectize()[0].selectize.items[0];
    //     } catch(err) {
    //         global_plate_size = $("#id_device").val();
    //     }
    //
    // WORKS! KEEP, KEEP, KEEP
    // console.log( $("#id_time_unit").selectize()[0].selectize.items[0] )
    // $("#id_time_unit").selectize()[0].selectize.setValue('hour')
});
