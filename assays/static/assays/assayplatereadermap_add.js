$(document).ready(function () {

    // Load core chart package
    google.charts.load('current', {'packages': ['corechart']});

    // These must be parallel! The second set is the column headers for the table (MIF-C file)
    // the first set is the order returning from the ajax call
    // look in the utils.py for the list that must match this in order! WATCH CAREFUL!
    let column_table_headers = [
        'Plate_Index',
        'Chip ID',
        'Matrix Item ID',
        'Cross Reference',

        'Assay Plate ID',
        'Assay Well ID',
        'Well Use',

        'Day',
        'Hour',
        'Minute',

        'Target/Analyte',
        'Subtarget',
        'Method/Kit',
        'Sample Location',
        'Sample Location ID',

        'Raw Value',
        'Measurement Unit',
        'Average Sample Blanks',
        'Adjusted Raw',
        'Fitted Value',

        'Dilution Factor',
        'Sample Volume',
        'Sample Volume Unit',
        'Duration Sample Collection (days)',

        'Multiplier',
        'Value',
        'Value Unit',

        'Replicate',
        'Caution Flag',
        'Exclude',
        'Notes',
        'Processing Details',
    ];

     //color ramp options for heatmap of raw data
    global_color_ramp_light_to_medium_purple = [
        '#F9F6FB',
        '#f2e6ff',
        '#e6ccff',
        '#d9b3ff',
        '#cc99ff',
        '#bf80ff',
        '#b366ff',
        // '#a64dff',
        // '#9933ff',
        // '#8c1aff',
        // '#8000ff',
    ];

    global_color_ramp_light_to_dark_red = [
        '#F8F8F8',
        '#FFEBEE',
        '#FFCDD2',
        '#EF9A9A',
        '#E57373',
        '#EF5350',
        '#F44336',
        '#E53935',
        '#D32F2F',
        '#C62828',
        '#B71C1C',
    ];

    global_color_ramp_light_to_dark_indigo = [
        '#F8F8F8',
        '#E8EAF6',
        '#C5CAE9',
        '#9FA8DA',
        '#7986CB',
        '#5C6BC0',
        '#3F51B5',
        '#3949AB',
        '#303F9F',
        '#283593',
        '#1A237E',
    ];

    global_color_ramp_light_to_dark_dark_orange = [
        '#F8F8F8',
        '#FBE9E7',
        '#FFCCBC',
        '#FFAB91',
        '#FF8A65',
        '#FF7043',
        '#FF5722',
        '#F4511E',
        '#E64A19',
        '#D84315',
        '#BF360C',
    ];

    global_color_ramp_light_to_dark_orange = [
        '#F8F8F8',
        '#FFF3E0',
        '#FFE0B2',
        '#FFCC80',
        '#FFB74D',
        '#FFA726',
        '#FF9800',
        '#FB8C00',
        '#F57C00',
        '#EF6C00',
        '#E65100',
    ];

    // pick the color ramp to use for the raw data values in the plate map
    global_color_ramp_use_this_ramp = global_color_ramp_light_to_medium_purple;

    // START SECTION THAT SETS TOOLTIPS - and some variables
    // make lists for the tooltips
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
        , '#standard_unit_tooltip'
        , '#standard_value_tooltip'
        , '#dilution_factor_tooltip'

        , '#file_block_tooltip'
        , '#number_file_block_tooltip'
        , '#map_name_tooltip'
        , '#collection_volume_tooltip'
        , '#collection_time_tooltip'

        , '#platemap_locked_tooltip'
        , '#plate_blank_handling_tooltip'
        , '#plate_calibration_curve_method_tooltip'
        , '#plate_replicate_handling_tooltip'
        , '#plate_standard_bounds_tooltip'

        , '#plate_molecular_weight_tooltip'
        , '#plate_volume_assay_plate_well_tooltip'
        , '#plate_file_block_with_standards_to_borrow_tooltip'
        , '#plate_mark_for_exclusion_tooltip'
        , '#plate_map_has_no_standards_tooltip'

        , '#plate_map_multiplier_for_processing'
        ,];
    let global_plate_tooltip_text = [
        "Starting from an existing study matrix is helpful if the experiment was conducted in a plate based model and that same plate was used to perform a plate reader assay."
        , "Build the assay plate map by selecting study matrix items and placing them in the plate."
        , "When starting from an existing assay plate map, if the assay plate map selected has been assigned to a file/block, values from uploaded files will not be obtained."
        , "This time unit applies to all sample times and sample collection times (efflux collection duration times) for the whole assay plate map."
        , "This unit applies to the sample collection volume. It is required when normalizing. It is also required if the measurement unit is /well. Note that, this unit will apply to both data types."

        , "For blank and empty wells, select the well use and drag on plate. For samples and standards, make requested selections then drag on plate. Use Copy to copy sections of the assay plate map to other wells in the plate."
        , "Count of cells that are relevant to the assay."
        , "Currently cannot be edited here. Was obtained during file upload."
        , "Check box to make change when drag/apply. Plate with mixed sample times must be added in the assay plate map. This sample time will be used if no over-writing sample time is provided during file upload."
        , "Check box to make change when drag/apply. Select the sample location in the model, if applicable, from which the effluent was collected. Use the backspace button to clear selection."

        , "Check box to make change when drag/apply. Select the name of the matrix item (chip or well in a plate) associated to the sample. Use the backspace button to clear selection."
        , "Select the unit, target, and method associated to this assay plate map. Use the backspace button to clear selection. If the option needed is not here, it has likely not be added to the study during study set up. Note that, units that include time should be in 'day', 'minute', or 'hour' to convert properly (i.e. 'days', 'hr', 'min' may not work correctly when calculating a multiplier)."
        , "If a standard is used in the assay plate map, enter the unit of the standard, else, enter the measurement unit of the raw value. If this unit is different than the Reporting Unit, unit conversion will be performed if possible. There are limits to this conversion tool. "
        , "The standard value should be in the unit given in the Standard Unit. The standard blank should be assigned a well use of 'standard' and a concentration of 0 (exactly, not 0.00001). "
        , "The dilution factor should be provided for each well in the assay plate map. "

        , "Changes made to the assay plate map (including sample location and standard concentration) will apply to all uses of the assay plate map."
        , "The number of data blocks this assay plate map has been assigned to."
        , "Date and time are the default. The map name may be updated by the data provider."
        , "Volume of sample efflux collected. Required for normalization."
        , "Time over which the sample efflux was collected. Required for normalization."

        , "The assay plate map information above can be edited, but not the well information. If there is an error in the well information, make a new assay plate map. Start with this assay plate map and make the correction. Then, go to the file and replace the assay plate map with the new one and submit. Then, delete this assay plate map."
        , "Select how the blanks should be handled. Note that, to be considered a Standard Blank, the concentration of the standard in the plate map must be set to 0 (exactly). When fitting a standard curve, points at the same concentration are averaged prior to fitting."
        , "Select the calibration method to use."
        , "When the same sample is added to multiple wells in an assay plate, each value can be added to the main database, or an average can be added. Select the option that is appropriate for this assay."
        , "Change these bounds to limit the range of the standard concentrations used to generate the calibration curve. These should be in the Measurement Unit. There must be points at a minimum of four concentrations to work correctly. Samples with fitted results above or below the calibration curve at these bounds will receive a Caution Flag of E. If null, all standards will be used in fitting. All points will be shown on the graph."

        , "The molecular weight of the standard is needed in cases were the standard unit is in moles and the unit in the target, method, unit is a mass unit."
        , "If the standard concentration a unit of moles per well, this value will be used to convert to a molar unit."
        , "In cases where no calibration is being performed or when standards to be used for calibration are in a different block of data, the appropriate selection should be made here. When standards are taken from another data block, the raw values are taken from selected data block. The units and other associated values must be specified in THIS plate map (at the top of the page). "
        , "Points that are marked for exclusion are available for use in the study summary if the appropriate selections are made by the user, but they are hidden by default."
        , "This plate map has no standards. To calibrate, a block of data with the standards must be selected."

        , "If calibrating, this is the multiplier that will be applied to the calibrated values. If not calibrating, this is the multiplier that will be applied to the raw values. Click to show the details for more information. Not all conversions are possible with this tool. Some tips: Reporting units that include per cell should include 10^, measurement units that include /well must be molar not mass, and reporting units with /time/10^# cells should have the time in 'day', 'hour', or 'minute', NOT other representations of time (i.e. 'days'). If necessary, the multiplier can be editted manually, but do so with care."
        ,];
    // load-function
    // set the tooltips
    $.each(global_plate_tooltip_selector, function (index, show_box) {
        $(show_box).next().html($(show_box).next().html() + make_escaped_tooltip(global_plate_tooltip_text[index]));
    });
    // NOTE: this replaces a bunch of these
    // let global_plate_map_name_tooltip = "Date and time are the default. The map name may be updated by the data provider.";
    // $('#map_name_tooltip').next().html($('#map_name_tooltip').next().html() + make_escaped_tooltip(global_plate_map_name_tooltip));
    // END SECTION THAT SETS TOOLTIPS


    // START SECTION TO SET GLOBAL VARIABLES plus some logic when needed

    let global_plate_check_page_call = $("#check_load").html().trim();

    // must have this variable for other load page element logic
    let global_plate_number_file_block_sets = 0;
    try {
        global_plate_number_file_block_sets = document.getElementById("id_form_number_file_block_combos").value;
    } catch (err) {
    }

    let global_calibration_multiplier = null;
    let global_calibration_multiplier_string = "Not computed yet.";
    let global_calibration_multiplier_string_display = "";

    let global_plate_this_platemap_id = parseInt(document.getElementById('this_platemap_id').innerText.trim());
    let global_plate_study_id = parseInt(document.getElementById("this_study_id").innerText.trim());

    // HARDCODED - but just sets a default and do not want to have to put the plate size list into here...
    let global_plate_size = 96;
    try {
        global_plate_size = $("#id_device").selectize()[0].selectize.items[0];
    } catch (err) {
        global_plate_size = $("#id_device").val();
    }

    let global_plate_whole_plate_index_list = [];
    for (var idx = 0, ls = global_plate_size; idx < ls; idx++) {
        global_plate_whole_plate_index_list.push(idx);
    }

    // these control what shows on page and/or are used across functions
    // so keep global, but some could change since some could be pulled directly from doms
    // be careful if change the content keep it in valid value list for doms
    let global_plate_well_use = "sample";
    try {
        global_plate_well_use = displayRadioButtonSelectedValue('change_well_use');
    } catch (err) {
    }

    let global_plate_change_method = 'copy';
    try {
        global_plate_change_method = displayRadioButtonSelectedValue('change_method');
    } catch (err) {
    }

    let global_plate_increment_direction = 'left-left';
    try {
        global_plate_increment_direction = displayRadioButtonSelectedValue('increment_direction');
    } catch (err) {
    }

    let global_plate_increment_operation = 'divide';
    try {
        global_plate_increment_operation = $("#id_se_increment_operation").selectize()[0].selectize.items[0];
    } catch (err) {
        global_plate_increment_operation = $("#id_se_increment_operation").val();
    }
    // console.log(global_plate_increment_operation)

    let global_plate_start_map = 'a_plate';
    try {
        global_plate_start_map = displayRadioButtonSelectedValue('start_map');
    } catch (err) {
    }

    // if review or update, need the correct defaults of fancy check box adjustments
    if (global_plate_check_page_call !== 'add') {
        global_plate_start_map = 'a_platemap';
    }
    // not a dom, hence the etc
    let global_plate_add_or_edit_etc = "add";

    // only want to populate the matrix item setup once
    // will do it in the same ajax call when the plate labels are determined, but not if the plate size is changed
    let yes_if_matrix_item_setup_already_run = 'no';

    // these hold the lists of well setup information when the copys/paste feature is used
    let global_plate_copys_plate_index = [];
    let global_plate_copys_well_use = [];
    let global_plate_copys_matrix_item = [];
    let global_plate_copys_matrix_item_text = [];
    let global_plate_copys_location = [];
    let global_plate_copys_location_text = [];
    let global_plate_copys_dilution_factor = [];
    let global_plate_copys_collection_volume = [];
    let global_plate_copys_collection_time = [];
    let global_plate_copys_standard_value = [];
    let global_plate_copys_default_time = [];
    let global_plate_copys_compound = [];
    let global_plate_copys_cell = [];
    let global_plate_copys_setting = [];
    let global_plate_copys_time = [];
    let global_plate_copys_block_raw_value = [];

    // these hold the lists of well content for add and change
    // when adding or loading existing - called from build plate (all plate indexs_
    // when changing - called from change plate (subset of plate indexes)
    let global_plate_mems_plate_index = [];
    let global_plate_mems_well_use = [];
    let global_plate_mems_matrix_item = [];
    let global_plate_mems_matrix_item_text = [];
    let global_plate_mems_location = [];
    let global_plate_mems_location_text = [];
    let global_plate_mems_dilution_factor = [];
    let global_plate_mems_collection_volume = [];
    let global_plate_mems_collection_time = [];
    let global_plate_mems_standard_value = [];
    let global_plate_mems_default_time = [];
    let global_plate_mems_compound = [];
    let global_plate_mems_cell = [];
    let global_plate_mems_setting = [];
    let global_plate_mems_time = [];
    let global_plate_mems_block_raw_value = [];

    // these are for holding what returned from an ajax call to get the info that matches the selected
    // data block when one or more data blocks have been assigned to the assay assay plate map
    let global_plate_block_plate_index_list_imatches = [];
    let global_plate_block_time_imatches = [];
    let global_plate_block_raw_value_imatches = [];
    let global_plate_block_raw_value_imatches_bin_index = [];

    // make the para||el lists of the matrix id, compound, cell, setting setup info
    // instead of sending from back end and needing a doc id for each
    // these are needed in several functions so keep as global variables
    let global_plate_isetup_matrix_item_id = [];
    let global_plate_isetup_compound = [];
    let global_plate_isetup_cell = [];
    let global_plate_isetup_setting = [];
    let global_plate_isetup_long_compound = [];
    let global_plate_isetup_long_cell = [];
    let global_plate_isetup_long_setting = [];

    // lists to use to show/hide content in assay plate map based on the fancy check boxes
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

    // On 20200114, changed the approach. If one or more file blocks is attached to the map,
    // the value set is None. This will improve load time and save time.
    // when the page is loaded get the copy of an empty item formset and an empty value formset (the "extra" in the forms.py)
    // in this feature, I am working with inlines - to see another option, see the assay plate file update feature
    let global_plate_first_item_form = $('#formset').find('.inline').first()[0].outerHTML;

    let global_plate_first_value_form = null;
    if (global_plate_number_file_block_sets == 0) {
        global_plate_first_value_form = $('#value_formset').find('.inline').first()[0].outerHTML;
    }

    // load-function
    // don't worry about the extra formset in the update or view page since it won't be populated or saved
    // but, when on add page, after copied to global variable, delete the extra formset so it is not saved during submit
    if ($('#formset').find('.inline').length === 1 && global_plate_check_page_call === 'add') {
        $('#formset').find('.inline').first().remove();
    }

    if (global_plate_number_file_block_sets == 0) {
        if ($('#value_formset').find('.inline').length === 1 && global_plate_check_page_call === 'add') {
            $('#value_formset').find('.inline').first().remove();
        }
    }
    // NOTE: when added the following code here (after the above), made 2x forms, so moved it back to the loop
    // $('#id_assayplatereadermapitem_set-TOTAL_FORMS').val(global_plate_size);
    //}).trigger('change');


    // this will get populated when the plate gets loaded (ajax call)
    let global_plate_well_use_count_of_standards_this_platemap = 0;

    let global_floater_study_assay = "";
    let global_floater_target = "";
    let global_floater_method = "";
    let global_floater_unit = "";
    let global_floater_standard_unit = "";
    let global_floater_volume_unit = "";
    let global_floater_well_volume = "";
    let global_floater_cell_count = "";
    let global_floater_molecular_weight = "";
    let global_floater_time_unit = "";
    let global_showhide_samples = "hide_samples";

    // END SECTION TO SET GLOBAL VARIABLES plus some


    // START - the CALIBRATION SECTION

    // global variables for the calibration
    let global_calibrate_true_if_blocks_in_study_with_standards_are_loaded_to_memory = false;

    let global_calibrate_block_borrowing_standard_from_string  = "0";
    let global_calibrate_block_borrowing_standard_from_pk = -1;
    let global_calibrate_block_borrowing_standard_from_pk_platemap = -1;


    let global_calibrate_borrowed_index_block = [];
    let global_calibrate_borrowed_pk_block = [];
    let global_calibrate_borrowed_pk_platemap = [];
    let global_calibrate_borrowed_metadata_block = [];

    let global_counter_to_check_calibration_runs = 1;
    let global_lol_samples = [];
    let global_lol_standards_points = [];
    let global_lol_standards_ave_points = [];
    let global_lol_standards_curve = [];

    $('input[name=radio_replicate_handling_average_or_not][value=average]').prop('checked',true);
    $('input[name=radio_standard_option_use_or_not][value=no_calibration]').prop('checked',true);
    let global_calibrate_radio_replicate_handling_average_or_not_0 = 'average';
    let global_calibrate_radio_standard_option_use_or_not = 'no_calibration';

    let global_calibrate_calibration_curve_method = 'select_one';
    if (global_plate_number_file_block_sets > 0) {
        try {
            global_calibrate_calibration_curve_method = $("#id_se_form_calibration_curve").selectize()[0].selectize.items[0];
        } catch (err) {
            global_calibrate_calibration_curve_method = $("#id_se_form_calibration_curve").val();
        }
        // set the default to wait
        $('#refresh_needed_indicator').text('wait');
    }
    let global_calibrate_calibration_curve_method_prev = global_calibrate_calibration_curve_method;

    let global_calibrate_block_select_string_is_block_working_with_string  = "0";
    let global_calibrate_block_select_string_is_block_working_with_pk = 0;

    // load-function
    if (global_plate_number_file_block_sets > 0) {
        findThePkForTheSelectedString("#id_se_block_select_string", "id_ns_block_select_pk");
    }

    function findThePkForTheSelectedString(thisStringElement, thisPkElement) {
        // get the selected index of the pk of the selected data block (0 to # file/blocks-1) and get index of the selection box = 0, 1, 2, 3...
        if (global_calibrate_block_select_string_is_block_working_with_string) {
            try {
                global_calibrate_block_select_string_is_block_working_with_string = $(thisStringElement).selectize()[0].selectize.items[0];
            } catch (err) {
                global_calibrate_block_select_string_is_block_working_with_string = $(thisStringElement).val();
            }
        }
        // console.log("global_calibrate_block_select_string_is_block_working_with_string ",global_calibrate_block_select_string_is_block_working_with_string)
        // using the local block index, find the actual pk of the file/block selected
        document.getElementById(thisPkElement).selectedIndex = global_calibrate_block_select_string_is_block_working_with_string;
        // using the index (a number from [0, 1, 2]), get the pk of the data block block from the list [22, 234, 255]
        global_calibrate_block_select_string_is_block_working_with_pk = parseInt(document.getElementById(thisPkElement).selectedOptions[0].text);
    }

    // load-function
    // when the page is loaded, get the what and how to load/build the plate
    // if add page:
    // start with and empty plate, and pull from formset and value formset
    // if existing:
    // if file/block is attached, pull from formset and data pass in
    // if file/block is not attached, pull from formset and value formset
    if (global_plate_check_page_call === 'add') {
        $('.show-when-add').removeClass('hidden');
        global_plate_add_or_edit_etc = "add_first_load_starting_from_empty_plate";
        packPlateLabelsAndBuildOrChangePlate_ajax();
    } else {
        $('.show-when-add').addClass('hidden');
        if (global_plate_number_file_block_sets < 1) {
            // no data blocks are attached, the value formset should be passed in and work as on the add page
            global_plate_add_or_edit_etc = "update_or_view_first_load";
            packPlateLabelsAndBuildOrChangePlate_ajax();
        } else {
            // one or more data blocks are attached, so
            // the findValueSet populates the "matches" based on the first (top) file data block passed into the page
            findValueSetInsteadOfValueFormsetPackPlateLabelsBuildPlate_ajax("update_or_view_first_load");
        }
    }


    // on CHANGE calibration on change events
    $("input[type='radio'][name='radio_replicate_handling_average_or_not']").click(function () {
        global_calibrate_radio_replicate_handling_average_or_not_0 = $(this).val();
    });

    $("#id_form_min_standard").change(function () {
        changedTheCalibrationCurveAndOtherChangesThatMightCauseRunCalibrate('change_min');
    });
    $("#id_form_max_standard").change(function () {
        changedTheCalibrationCurveAndOtherChangesThatMightCauseRunCalibrate('change_max');
    });
    $("#id_se_form_blank_handling").change(function () {
        changedTheCalibrationCurveAndOtherChangesThatMightCauseRunCalibrate('change_blank_handling');
    });

    // changed the borrowed standard file block selection option - this is only possible if calibration HAS been selected
    $("input[type='radio'][name='radio_standard_option_use_or_not']").click(function () {
        global_calibrate_radio_standard_option_use_or_not = $(this).val();

        // if there are not standards on this plate - this button should not show in this case, but check anyway
        if (global_plate_well_use_count_of_standards_this_platemap == 0) {

            if ($('input[name=radio_standard_option_use_or_not]:checked').val() === 'pick_block') {

                // this is a tangent - on first time using this is picked, have to load the drop down
                // did not want to do on page load because it took too long
                if (!global_calibrate_true_if_blocks_in_study_with_standards_are_loaded_to_memory) {
                    loadTheFileBlocksWithStandardsDropdown();
                    global_calibrate_true_if_blocks_in_study_with_standards_are_loaded_to_memory = true;
                }
                $('.pick-standard-file-block').removeClass('hidden');
            } else {
                $('.pick-standard-file-block').addClass('hidden');
            }
        } else {
            // if no calibration in this radio button is selected, do not show the box to pick a file block
            $('.pick-standard-file-block').addClass('hidden');
        }
        changedTheCalibrationCurveAndOtherChangesThatMightCauseRunCalibrate('change_standard_option_button');
    });

    // change the file block for the standards
    $("#id_se_block_standard_borrow_string").change(function () {

        try {
            global_calibrate_block_borrowing_standard_from_string = $("#id_se_block_standard_borrow_string").selectize()[0].selectize.items[0];
        } catch (err) {
            global_calibrate_block_borrowing_standard_from_string = $("#id_se_block_standard_borrow_string").val();
        }
        let the_index_of_the_element = global_calibrate_borrowed_metadata_block.indexOf(global_calibrate_block_borrowing_standard_from_string);
        global_calibrate_block_borrowing_standard_from_pk = global_calibrate_borrowed_pk_block[the_index_of_the_element];
        global_calibrate_block_borrowing_standard_from_pk_platemap = global_calibrate_borrowed_pk_platemap[the_index_of_the_element];

        $("#id_form_block_standard_borrow_pk_single_for_storage").val(global_calibrate_block_borrowing_standard_from_pk);
        $("#id_form_block_standard_borrow_pk_platemap_single_for_storage").val(global_calibrate_block_borrowing_standard_from_pk_platemap);

        // console.log("global_calibrate_block_borrowing_standard_from_string ", global_calibrate_block_borrowing_standard_from_string)
        // console.log("the_index_of_the_element ", the_index_of_the_element)

        changedTheCalibrationCurveAndOtherChangesThatMightCauseRunCalibrate('change_standard_pk_and_string');
    });


    // change the calibration method
    // every change above this on the page that will affect this turns it back to Select One so the user HAS to select
    $("#id_se_form_calibration_curve").change(function () {
        global_calibrate_calibration_curve_method_prev = global_calibrate_calibration_curve_method;
        global_calibrate_calibration_curve_method = $("#id_se_form_calibration_curve").selectize()[0].selectize.items[0];
        changedTheCalibrationCurveAndOtherChangesThatMightCauseRunCalibrate('change_curve');
    });

    function changedTheCalibrationCurveAndOtherChangesThatMightCauseRunCalibrate(called_from) {

        if (global_calibrate_calibration_curve_method == 'select_one') {
            $('.plate-calibration-or-processing-yes').addClass('hidden');
            $('.plate-calibration-yes').addClass('hidden');
            $('.plate-calibration-guts-yes').addClass('hidden');

            // do not call calibration script - nothing to do - user needs to make a move
            $('#refresh_needed_indicator').text('wait');
            $('.plate-calibration-curve-yes').addClass('hidden');
            $('.plate-calibration-curve-guts-yes').addClass('hidden');

        } else if ($('#id_form_data_processing_multiplier').val() == 0) {
            alert("Something is wrong with the multiplier. Check to make sure all the information that is needed for unit conversion has been provided.\n");
            $('.plate-calibration-or-processing-yes').addClass('hidden');
            $('.plate-calibration-yes').addClass('hidden');
            $('.plate-calibration-guts-yes').addClass('hidden');
            // do not call calibration script - nothing to do - user needs to make a move
            $('#refresh_needed_indicator').text('wait');
            $('.plate-calibration-curve-yes').addClass('hidden');
            $('.plate-calibration-curve-guts-yes').addClass('hidden');

        } else {

            if (global_calibrate_calibration_curve_method == 'no_calibration') {
                $('.plate-calibration-or-processing-yes').removeClass('hidden');
                $('.plate-calibration-yes').addClass('hidden');
                $('.plate-calibration-guts-yes').addClass('hidden');

                // run with no calibration - should have what need
                $('#refresh_needed_indicator').text('need');
                changesThatAffectCalibrationPlusCallCalibrate(called_from, 'no_calibration');
                $('.plate-calibration-curve-yes').addClass('hidden');
                $('.plate-calibration-curve-guts-yes').addClass('hidden');

            } else {

                // run a calibration
                $('.plate-calibration-or-processing-yes').removeClass('hidden');
                $('.plate-calibration-yes').removeClass('hidden');
                $('.plate-calibration-guts-yes').removeClass('hidden');

                if (global_plate_well_use_count_of_standards_this_platemap == 0) {
                    // calibration method was selected but there are not standards on the plate
                    $('.plate-map-options-standards-blocks').removeClass('hidden');
                    // no standards on this plate
                    if(global_calibrate_radio_standard_option_use_or_not == 'no_calibration') {
                        // but not calibrating, so do not need standards
                        $('.pick-standard-file-block').addClass('hidden');
                        $('#refresh_needed_indicator').text('need');
                        changesThatAffectCalibrationPlusCallCalibrate(called_from, 'no standards but also no calibration');
                        $('.plate-calibration-curve-yes').addClass('hidden');
                        $('.plate-calibration-curve-guts-yes').addClass('hidden');
                    } else {
                        $('.pick-standard-file-block').removeClass('hidden');
                        if (global_calibrate_block_borrowing_standard_from_pk > 0) {
                            // the borrow pk is been populated, okay to go
                            $('#refresh_needed_indicator').text('need');
                            changesThatAffectCalibrationPlusCallCalibrate(called_from, 'borrow pk is selected');
                            $('.plate-calibration-curve-yes').removeClass('hidden');
                            $('.plate-calibration-curve-guts-yes').removeClass('hidden');

                        } else {
                            // user needs to pick a borrow pk
                            $('#refresh_needed_indicator').text('wait');
                            $('.plate-calibration-curve-yes').addClass('hidden');
                            $('.plate-calibration-curve-guts-yes').addClass('hidden');
                        }
                    }
                } else {
                    $('.plate-map-options-standards-blocks').addClass('hidden');
                    // this will run with the blank handling and min and max bound defaults
                    $('#refresh_needed_indicator').text('need');
                    changesThatAffectCalibrationPlusCallCalibrate(called_from, 'standards are on this plate');
                    $('.plate-calibration-curve-yes').removeClass('hidden');
                    $('.plate-calibration-curve-guts-yes').removeClass('hidden');
                }
            }
        }
    };


    function changesThatAffectCalibrationPlusCallCalibrate(called_from, other_info) {
        // changesThatAffectCalibrationPlusCallCalibrate('change_curve', 'standards are on this plate');
        // if get here, should have everything needed and the $('#refresh_needed_indicator').text('need');
        goAheadWithCalibrationAndOrProcessing(called_from);
    }

    // calibration FUNCTIONS
    function goAheadWithCalibrationAndOrProcessing(called_from) {
        // console.log("goAheadWithCalibrationAndOrProcessing called_from: ", called_from)
        //console.log("counter ", global_counter_to_check_calibration_runs)

        global_counter_to_check_calibration_runs=global_counter_to_check_calibration_runs + 1;
        packProcessedData();
    }

    // Get what is needed for the calibration/processing
    function packProcessedData() {
        // console.log("packProcessedData")

        let form_blank_handling = "";
        try {
            form_blank_handling = $("#id_se_form_blank_handling").selectize()[0].selectize.items[0];
        } catch (err) {
            form_blank_handling = $("#id_se_form_blank_handling").val();
        }

        // console.log('global_floater_target  ',    global_floater_target)
        // console.log('global_floater_method  ',    global_floater_method)
        // console.log('global_floater_unit  ',      global_floater_unit )

        let data = {
            call: 'fetch_data_processing_for_plate_map_integration',
            called_from: 'javascript',
            study: global_plate_study_id,
            pk_platemap: global_plate_this_platemap_id,
            pk_data_block: global_calibrate_block_select_string_is_block_working_with_pk,
            plate_name: $("#id_name").val(),
            form_calibration_curve: global_calibrate_calibration_curve_method,
            multiplier: global_calibration_multiplier,
            unit: global_floater_unit,
            standard_unit: global_floater_standard_unit,
            form_min_standard: $("#id_form_min_standard").val(),
            form_max_standard: $("#id_form_max_standard").val(),
            form_blank_handling: form_blank_handling,
            radio_standard_option_use_or_not: global_calibrate_radio_standard_option_use_or_not,
            radio_replicate_handling_average_or_not_0: global_calibrate_radio_replicate_handling_average_or_not_0,
            borrowed_block_pk: global_calibrate_block_borrowing_standard_from_pk,
            borrowed_platemap_pk: global_calibrate_block_borrowing_standard_from_pk_platemap,
            count_standards_current_plate: global_plate_well_use_count_of_standards_this_platemap,
            target: global_floater_target,
            method: global_floater_method,
            time_unit: global_floater_time_unit,
            volume_unit: global_floater_volume_unit,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };
        window.spinner.spin(document.getElementById("spinner"));
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
                    packProcessedDataSection(json, exist);
                }
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred (finding processed data). Could be caused by many errors or by injection of invalid values.');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
    // post processing from ajax call
    let packProcessedDataSection = function (json, exist) {
        let sendmessage = json.sendmessage;
        // console.log(sendmessage)
        $("#id_form_data_parsable_message").val(sendmessage);

        let list_of_dicts_of_each_sample_row = json.list_of_dicts_of_each_sample_row;
        let list_of_dicts_of_each_standard_row_points = json.list_of_dicts_of_each_standard_row_points;
        let list_of_dicts_of_each_standard_row_ave_points = json.list_of_dicts_of_each_standard_row_ave_points;
        let list_of_dicts_of_each_standard_row_curve = json.list_of_dicts_of_each_standard_row_curve;

        let dict_of_curve_info = json.dict_of_curve_info;
        // console.log('dict_of_curve_info ', dict_of_curve_info)
        // console.log('dict_of_curve_info.method ', dict_of_curve_info.method)
        $("#id_form_calibration_curve_method_used").val(dict_of_curve_info.method);
        $("#id_form_calibration_equation").val(dict_of_curve_info.equation);
        $("#id_form_calibration_rsquared").val(dict_of_curve_info.rsquared);
        $("#id_used_curve").val(dict_of_curve_info.used_curve);

        let dict_of_standard_info = json.dict_of_standard_info;
        $("#id_form_calibration_standard_fitted_min_for_e").val(dict_of_standard_info.min);
        $("#id_form_calibration_standard_fitted_max_for_e").val(dict_of_standard_info.max);
        $("#id_form_calibration_standard_standard0_average").val(dict_of_standard_info.standard0average);
        $("#id_form_calibration_sample_blank_average").val(dict_of_standard_info.blankaverage);

        let dict_of_parameter_labels = json.dict_of_parameter_labels;
        let dict_of_parameter_values = json.dict_of_parameter_values;
        $("#id_form_calibration_parameter_1_string").val(dict_of_parameter_labels.p1);
        $("#id_form_calibration_parameter_2_string").val(dict_of_parameter_labels.p2);
        $("#id_form_calibration_parameter_3_string").val(dict_of_parameter_labels.p3);
        $("#id_form_calibration_parameter_4_string").val(dict_of_parameter_labels.p4);
        $("#id_form_calibration_parameter_5_string").val(dict_of_parameter_labels.p5);
        $("#id_form_calibration_parameter_1_value").val(dict_of_parameter_values.p1);
        $("#id_form_calibration_parameter_2_value").val(dict_of_parameter_values.p2);
        $("#id_form_calibration_parameter_3_value").val(dict_of_parameter_values.p3);
        $("#id_form_calibration_parameter_4_value").val(dict_of_parameter_values.p4);
        $("#id_form_calibration_parameter_5_value").val(dict_of_parameter_values.p5);

        buildTableOfProcessedData_ajax(list_of_dicts_of_each_sample_row);
        buildTableOfStandardsDataPoints_ajax(list_of_dicts_of_each_standard_row_points);
        buildTableOfStandardsDataAvePoints_ajax(list_of_dicts_of_each_standard_row_ave_points);
        buildTableOfStandardsDataCurve_ajax(list_of_dicts_of_each_standard_row_curve);

        // console.log("##in js back from ajax");
        // console.log("##list_of_dicts_of_each_sample_row");
        // console.log(list_of_dicts_of_each_sample_row);
        // console.log("##list_of_dicts_of_each_standard_row_ave_points");
        // console.log(list_of_dicts_of_each_standard_row_ave_points);
        // console.log("##list_of_dicts_of_each_standard_row_points");
        // console.log(list_of_dicts_of_each_standard_row_points);
        // console.log("##list_of_dicts_of_each_standard_row_curve");
        // console.log(list_of_dicts_of_each_standard_row_curve);

        drawCalibrationCurve();
        $('#refresh_needed_indicator').text('done');
    };

    function buildTableOfProcessedData_ajax(list_of_dicts_of_each_sample_row) {
        //also storing what needed for calibration curve in memory
        global_lol_samples = [];

        //['Standard Concentration', 'Fitted Curve', 'Standard Response', 'Sample Response'],
        // for samples, need fitted value (19) as the X and the adjusted raw (15) as the Y
        //[0.0, null, null, .05]
        // 19                15

        // column_table_headers
        let lol_processed = [];
        // TRICKY - keep these all parallel with each other and with the utils.py call or problems will result!

        let showthisalert = false;

        //console.log('list_of_dicts_of_each_sample_row ', list_of_dicts_of_each_sample_row)
        $.each(list_of_dicts_of_each_sample_row, function (index, each) {
            let thisline = [];
            let myconcentration = 0;
            let myresponse = 0;
            let counterEachItemInThisRow = 0;
            //console.log("each ", each)
            $.each(each, function (indexi, eachi) {
                thisline.push(eachi);

                // console.log("counterEachItemInThisRow ", counterEachItemInThisRow)

                // CAREFUL WATCH if change order, these will be wrong...
                if (counterEachItemInThisRow == 19) {
                    myconcentration = eachi;
                    if (myconcentration == null){
                        if (showthisalert == false) {
                            alert('One or more of your raw values was null. This will cause errors and/or odd behavior on this page.');
                            showthisalert = true;
                        }
                    }
                    // console.log(myconcentration)
                };
                if (counterEachItemInThisRow == 15) {
                    myresponse = eachi;
                    // console.log(myresponse)
                };
                
                //console.log("eachi: ", eachi)

                //console.log("each.plate_index ", each.plate_index)
                //console.log("each[eachi] ", each[eachi])
                // HANDY get each. variable name use each[variable name]
                counterEachItemInThisRow = counterEachItemInThisRow + 1;
            });
            lol_processed.push(thisline);
            //console.log("thisline ", thisline)
            global_lol_samples.push([parseFloat(myconcentration), null, null, null, parseFloat(myresponse)]);
        });
        
        //todo get a different list to pack the graph...later

        buildTheProcessedDataTable_ajax(lol_processed);
    }

    function buildTheProcessedDataTable_ajax(lol_processed) {
        // so that the DataTable will work, make the whole table each time so can destroy it and bring it back

        // HANDY delete child node
        var elem = document.getElementById('div_for_processed_samples_table');
        elem.removeChild(elem.childNodes[0]);

        var myTableDiv = document.getElementById("div_for_processed_samples_table");
        var myTable = document.createElement('TABLE');
        $(myTable).attr('id', 'processed_samples_table');
        $(myTable).attr('cellspacing', '0');
        $(myTable).attr('width', '100%');
        $(myTable).addClass('display table table-striped table-hover');

        var tableHead = document.createElement("THEAD");
        var tr = document.createElement('TR');
        $(tr).attr('hrow-index', 0);

        tableHead.appendChild(tr);
        var hcolcounter = 0;
        $.each(column_table_headers, function (index, header) {
            //console.log("header ", header)
            var th = document.createElement('TH');
            $(th).attr('hcol-index', hcolcounter);
            th.appendChild(document.createTextNode(header));
            tr.appendChild(th);
            hcolcounter = hcolcounter+1;
        });
        myTable.appendChild(tableHead);

        var tableBody = document.createElement('TBODY');
        var rowcounter = 0;
        $.each(lol_processed, function (ir, row) {
            // console.log("rowcounter ", rowcounter)
            // console.log("--row ", row)
            var tr = document.createElement('TR');
            $(tr).attr('row-index', rowcounter);
            tableBody.appendChild(tr);


            var colcounter = 0;
            let myCellContentWithCommas = "";
            $.each(row, function (ii, col) {
                // console.log("colcounter ", colcounter)
                // console.log("--col ", col)
                var td = document.createElement('TD');
                $(td).attr('col-index', colcounter);
                let myCellContent = col;
                if (ii == 7  || ii == 8  || ii == 9  ||
                    ii == 15 || ii == 17 || ii == 18 || ii == 19 ||
                    ii == 24 || ii == 25){
                    myCellContent = generalFormatNumber(parseFloat(col));
                    myCellContent = thousands_separators(myCellContent);
                }

                td.appendChild(document.createTextNode(myCellContent));
                tr.appendChild(td);
                colcounter = colcounter+1;
            });

            rowcounter = rowcounter+1
        });
        myTable.appendChild(tableBody);
        myTableDiv.appendChild(myTable);

        // to format the table - after creating it
        // these column number are in the table cell tags - use them to keep everything straight
        $('#processed_samples_table').DataTable({
            //     $(myTable).DataTable({
            "iDisplayLength": 25,
            "sDom": '<B<"row">lfrtip>',
            fixedHeader: {headerOffset: 50},
            responsive: true,
            "order": [[2, "asc"]],

            "columnDefs": [
                // target is the column number starting from 0
                // NOTE: these numbers rely on the order of the arrays
                {"targets": [   0], "visible": false, },
                //{"targets": [   1], "visible": false, },
                {"targets": [   2], "visible": false, },
                {"targets": [   3], "visible": false, },

                {"targets": [   4], "visible": false, },
                //{"targets": [   5], "visible": false, },
                {"targets": [   6], "visible": false, },

                //{"targets": [   7], "visible": false, },
                //{"targets": [   8], "visible": false, },
                //{"targets": [   9], "visible": false, },

                {"targets": [  10], "visible": false, },
                {"targets": [  11], "visible": false, },
                {"targets": [  12], "visible": false, },
                {"targets": [  13], "visible": false, },
                {"targets": [  14], "visible": false, },

                //{"targets": [  15], "visible": false, },
                {"targets": [  16], "visible": false, },
                {"targets": [  17], "visible": false, },
                //{"targets": [  18], "visible": false, },
                //{"targets": [  19], "visible": false, },

                {"targets": [  20], "visible": false, },
                {"targets": [  21], "visible": false, },
                {"targets": [  22], "visible": false, },
                {"targets": [  23], "visible": false, },

                //{"targets": [  24], "visible": false, },
                //{"targets": [  25], "visible": false, },
                //{"targets": [  26], "visible": false, },

                {"targets": [  27], "visible": false, },
                //{"targets": [  28], "visible": false, },
                {"targets": [  29], "visible": false, },
                {"targets": [  30], "visible": false, },
                {"targets": [  31], "visible": false, }
            ]

        });

        return myTable;
    }

    function buildTableOfStandardsDataCurve_ajax(list_of_dicts_of_each_standard_row_curve) {
        global_lol_standards_curve = [];

        $.each(list_of_dicts_of_each_standard_row_curve, function (index, each) {
            let myconcentration = 0;
            let myobservedresponse = 0;
            let mypredictedresponse = 0;
            let counterEachItemInThisRow = 0;
            $.each(each, function (indexi, eachi) {
                if (counterEachItemInThisRow == 0) {
                    myconcentration = eachi;
                };
                if (counterEachItemInThisRow == 2) {
                    mypredictedresponse = eachi;
                };
                counterEachItemInThisRow = counterEachItemInThisRow + 1;
            });
            global_lol_standards_curve.push([parseFloat(myconcentration), parseFloat(mypredictedresponse), null, null, null]);
        });
    }

    function buildTableOfStandardsDataAvePoints_ajax(list_of_dicts_of_each_standard_row_ave_points) {
        global_lol_standards_ave_points = [];

        $.each(list_of_dicts_of_each_standard_row_ave_points, function (index, each) {
            let myconcentration = 0;
            let myadjustedresponse = 0;
            let myobservedresponse = 0;
            let counterEachItemInThisRow = 0;
            $.each(each, function (indexi, eachi) {
                if (counterEachItemInThisRow == 0) {
                    myconcentration = eachi;
                };
                if (counterEachItemInThisRow == 1) {
                    myadjustedresponse = eachi;
                };
                counterEachItemInThisRow = counterEachItemInThisRow + 1;
            });
            global_lol_standards_ave_points.push([parseFloat(myconcentration), null, parseFloat(myadjustedresponse), null, null]);
        });
    }

    function buildTableOfStandardsDataPoints_ajax(list_of_dicts_of_each_standard_row_points) {
        global_lol_standards_points = [];

        $.each(list_of_dicts_of_each_standard_row_points, function (index, each) {
            let myconcentration = 0;
            let myadjustedresponse = 0;
            let myobservedresponse = 0;
            let counterEachItemInThisRow = 0;
            $.each(each, function (indexi, eachi) {
                if (counterEachItemInThisRow == 0) {
                    myconcentration = eachi;
                };
                if (counterEachItemInThisRow == 1) {
                    myadjustedresponse = eachi;
                };
                counterEachItemInThisRow = counterEachItemInThisRow + 1;
            });
            global_lol_standards_points.push([parseFloat(myconcentration), null, null, parseFloat(myadjustedresponse), null]);
        });
    }

    $("#showHideSamplesOnGraphButton").click(function () {
        // console.log("sh ", global_showhide_samples)
        if (global_showhide_samples == "hide_samples") {
            global_showhide_samples = "show_samples";
            drawCalibrationCurve();
        } else {
            global_showhide_samples = "hide_samples";
            drawCalibrationCurve();
        }
    });

    function drawCalibrationCurve(){

        let testForError = $('#id_form_data_parsable_message').val();

        if (testForError.search('ERROR') >= 0) {
            $('.plate-calibration-curve').addClass('hidden');
            $('.plate-calibration-curve-yes').addClass('hidden');
            $('.plate-calibration-curve-guts-yes').addClass('hidden');
            $('.data-processing-errors').removeClass('hidden');
        } else {
            $('.data-processing-errors').addClass('hidden');

            google.charts.setOnLoadCallback(drawStandardCurve01);

            function drawStandardCurve01() {

                // global_fitted
                var fitted = global_lol_standards_curve;
                // console.log('fitted ', fitted)

                // NOTE: ADDED a fifth column to all to accomodate this
                var ave_standards = global_lol_standards_ave_points;
                // console.log('ave_standards ', ave_standards)

                // global_lol_standards_points
                var standards = global_lol_standards_points;
                // console.log('standards ', standards)

                // global_lol_samples
                var samples = global_lol_samples;

                // var preData = [
                //     ['Standard Concentration', 'Fitted Curve', 'Standard Response', 'Sample Response'  added a fifth],
                //     [0.0, 0.0, null, null],
                //     [0.1, 0.2, null, null],
                //     [0.2, 0.4, null, null],
                //     [0.3, 0.6, null, null],
                //     [0.4, 0.8, null, null],
                //     [0.5, 1.0, null, null],
                //     [0.6, 1.2, null, null],
                //     [0.7, 1.4, null, null],
                //     [0.8, 1.6, null, null],
                //     [0.9, 1.8, null, null],
                //
                //     [0.0, null, null, .05],
                //
                //     [0.0, null, 0.01, null],
                //     [0.1, null, 0.192, null],
                //     [0.2, null, 0.394, null],
                //     [0.3, null, 0.61, null],
                //     [0.4, null, 0.83, null]
                // ];

                // 5th spot place holder
                var placeHolder =
                    [
                        [0, null, null, null, 0],
                    ];

                var preData = {};
                var colHeaders = {};
                var options = {};

                if (global_showhide_samples == "hide_samples") {
                    colHeaders =
                        [
                            ['Standard Concentration', 'Fitted Standard Curve', 'Standard (Average)', 'Standard (All Points)', '']
                        ];

                    preData = $.merge($.merge($.merge($.merge($.merge([],
                        colHeaders),
                        placeHolder),
                        standards),
                        fitted),
                        ave_standards);

                    options = {
                        title: global_floater_method,
                        seriesType: 'scatter',
                        series: {
                            // 0: {pointShape: 'square'}, pointSize: 1,
                            0: {type: 'line'},
                            1: {
                                pointShape: 'diamond', pointSize: 10,
                            },
                            2: { pointShape: 'circle', pointSize: 3,
                                 // pointShape: {type: 'star', sides: 8, dent: 0.05}, pointSize: 8,
                            },
                            3: {
                                pointShape: {type: 'star', sides: 4, dent: 0.1}, pointSize: 1,
                            },
                        },
                        legend: {position: 'bottom'},
                        vAxis: {title: 'Signal'},
                        hAxis: {title: global_floater_standard_unit},
                        colors: ['MidnightBlue', 'MediumBlue', 'SteelBlue', 'White'],
                    };
                } else {
                    colHeaders =
                        [
                            ['Standard Concentration', 'Fitted Standard Curve', 'Standard (Average)', 'Standard (All Points)', 'Samples']
                        ];

                    preData = $.merge($.merge($.merge($.merge($.merge([],
                        colHeaders),
                        samples),
                        standards),
                        fitted),
                        ave_standards);

                    // https://developers.google.com/chart/interactive/docs/points

                    options = {
                        title: global_floater_method,
                        seriesType: 'scatter',
                        series: {
                            // 0: {pointShape: 'square'}, pointSize: 0.3,
                            0: {type: 'line'},
                            1: {
                                pointShape: 'diamond', pointSize: 10,
                            },
                            2: { pointShape: 'circle', pointSize: 3,
                                // pointShape: {type: 'star', sides: 8, dent: 0.05}, pointSize: 8,
                            },
                            3: {
                                pointShape: {type: 'star', sides: 5, dent: 0.5}, pointSize: 13,
                            },
                        },
                        legend: {position: 'bottom'},
                        //vAxis: {title: global_floater_target},
                        vAxis: {title: 'Signal'},
                        hAxis: {title: global_floater_standard_unit},
                        colors: ['MidnightBlue', 'MediumBlue', 'SteelBlue', 'FireBrick'],
                    };

                }

                var data = google.visualization.arrayToDataTable(preData);
                var dataView = new google.visualization.DataView(data);

                // console.log(global_calibrate_calibration_curve_method)
                let thisCurveMethod = $("#id_used_curve").val();

                // have to use the curve method brought back due to best fit
                if (thisCurveMethod == 'logistic4') {
                    options.hAxis.scaleType = 'mirrorLog';
                    //options.hAxis.scaleType = 'log';
                } else {
                    options.hAxis.scaleType = 'linear';
                }

                // if want to compute the line, but I think I am going to send it over
                // var yCol1 = {
                //   calc: function (data, row) {
                //     return (1.1 * data.getValue(row, 1));
                //   },
                //   type: 'number',
                //   label: 'Y1'
                // };

                // use above object as Y1
                //dataView.setColumns([0, yCol1]);
                // dataView.setColumns([0, 1, 2, 3, yCol1]);

                // view.setColumns([0, 1, 2, 3 {
                //   label: 'y = 2x + 0',
                //   type: 'number',
                //   calc: function (dt, row) {
                //     return dt.getValue(row, 0)
                //   }
                // }]);

                var chart = new google.visualization.ComboChart(document.getElementById('chart_div'));
                chart.draw(dataView, options);
            }
        }
    }

    function loadTheFileBlocksWithStandardsDropdown(){
        //populate the dropdown with the file block options with file blocks in this study that have standards
        let data = {
            call: 'fetch_information_for_study_platemap_standard_file_blocks',
            study: global_plate_study_id,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };
        window.spinner.spin(document.getElementById("spinner"));
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
                    processFindBlocksWithStandards(json, exist);
                }
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred (finding data blocks with standards), please try a different matrix, assay plate map, or start from an empty plate.');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
    // post processing from ajax call
    let processFindBlocksWithStandards = function (json, exist) {
        let block_data_pk = json.block_data_fileblock_database_pk;
        let block_data_string = json.block_data_string;
        let block_data_pk_platemap = json.block_data_platemap_pk;

        global_calibrate_borrowed_index_block = [];
        global_calibrate_borrowed_pk_block = [];
        global_calibrate_borrowed_pk_platemap = [];
        global_calibrate_borrowed_metadata_block = [];

        $.each(block_data_pk, function (index, each) {
            global_calibrate_borrowed_index_block.push(index);
            global_calibrate_borrowed_pk_block.push(Object.values(each)[0]);
        });
        $.each(block_data_string, function (index, each) {
            global_calibrate_borrowed_metadata_block.push(Object.values(each)[0]);
        });
        $.each(block_data_pk_platemap, function (index, each) {
            global_calibrate_borrowed_pk_platemap.push(Object.values(each)[0]);
        });

        // console.log(global_calibrate_borrowed_index_block)
        // console.log(global_calibrate_borrowed_pk_block)
        // console.log(global_calibrate_borrowed_metadata_block)

        // index = 0;
        // for (var key in block_data) {
        //     console.log("key " + key + " has value " + block_data[key]);
        //     index = index + 1;
        // }

        // $.each(block_data, function (index, each) {
        //     // console.log("key ",Object.keys(each)[0]);
        //     // console.log("value ",Object.values(each)[0]);
        //     global_calibrate_borrowed_index_block.push(index);
        //     global_calibrate_borrowed_pk_block.push(Object.keys(each)[0]);
        //     global_calibrate_borrowed_metadata_block.push(Object.values(each)[0]);
        // });

        // https://github.com/selectize/selectize.js/blob/master/docs/api.md HANDY
        var $this_block_standard_borrow_string = $(document.getElementById('id_se_block_standard_borrow_string'));
        var this_block = $this_block_standard_borrow_string[0].selectize;
        // fill the dropdown with what brought back from ajax call
        for(i=0; i < global_calibrate_borrowed_metadata_block.length; i++){
            this_block.addOption({value: global_calibrate_borrowed_metadata_block[i], text: global_calibrate_borrowed_metadata_block[i]});
        }
        //user will need to select on to make the borrow standards pull
    };

    // END - the calibrate google charts section

    // these need to exist on the page before changing them, some moved them down
    try {
        let element_id5 = 'id_form_data_processing_multiplier';
        document.getElementById(element_id5).style.backgroundColor = 'Gainsboro';
    } catch (err) { // this is not on the page, skip it
    }

    if (global_plate_number_file_block_sets > 0) {
        try {
            // set a default
            document.getElementById("id_radio_replicate_handling_average_or_not_0").checked = true;
        } catch (err) { // this is not on the page, skip it
        }
    }

    // CALIBRATE SECTION IS ABOVE (EXCEPT SOME FUNCTIONS ARE BELOW)

    // START - SECTION FOR CHANGES ON PAGE that have to keep track of to change on page display
    // set the global or other variables for the selections if file_block change
    // NOTE: this is the file block for THIS assay plate map
    // (NOT NOT NOT if on add page and selecting to start from a different assay plate map)
    // this box only shows if there is/are file/block associated

    $("#id_se_block_select_string").change(function () {
        findThePkForTheSelectedString("#id_se_block_select_string", "id_ns_block_select_pk");
        findValueSetInsteadOfValueFormsetPackPlateLabelsBuildPlate_ajax("update_or_view_change_block");
        theSuiteOfPreCalibrationChecks();
    });
    $("#id_cell_count").change(function () {
        theSuiteOfPreCalibrationChecks();
    });
    $("#id_study_assay").change(function () {
        theSuiteOfPreCalibrationChecks();
    });
    $("#id_volume_unit").change(function () {
       theSuiteOfPreCalibrationChecks();
    });
    $("#id_standard_unit").change(function () {
        theSuiteOfPreCalibrationChecks();
    });
    $("#id_well_volume").change(function () {
       theSuiteOfPreCalibrationChecks();
    });
    $("#id_standard_molecular_weight").change(function () {
       theSuiteOfPreCalibrationChecks();
    });
    $("#id_time_unit").change(function () {
        global_floater_time_unit = $('#id_time_unit').children("option:selected").text().trim();
        theSuiteOfPreCalibrationChecks();
    });
    // load-function
    // do this on the load of the page
    theSuiteOfPreCalibrationChecks();

    //end section of change functions to warn the user about order of processing data

    // change to show by default by forcing the click button on load for add page, but not calibrate page
    if (global_plate_number_file_block_sets == 0) {
        setTimeout(function () {
            $("#checkboxButton").trigger('click');
        }, 10);
    }
    //start with it off
    $(".plate-map-page-show-multiplier-details").toggle();
    $(".plate-map-page-show-parameter-details").toggle();

    // toggle to hide/show the customized show in assay plate map fancy check boxes (what will and won't show in plate)
    $("#checkboxButton").click(function () {
        $("#platemap_checkbox_section").toggle();
    });
    $("#multiplierDetailsButton").click(function () {
        $(".plate-map-page-show-multiplier-details").toggle();
    });
    $("#parameterDetailsButton").click(function () {
        $(".plate-map-page-show-parameter-details").toggle();
    });

    $("#uncheckAllFancyChecksButton").click(function () {
        // run through and uncheck all fancy checkboxes
        setFancyCheckBoxesLoopOverFancyCheckboxClass(global_plate_whole_plate_index_list, 'clear');
    });
    $("#checkAllFancyChecksButton").click(function () {
        // run through and uncheck all fancy checkboxes
        setFancyCheckBoxesLoopOverFancyCheckboxClass(global_plate_whole_plate_index_list, 'show');
    });

    // class show/hide and also what is checked/unchecked based on radio button of starting option
    $("input[type='radio'][name='start_map']").click(function () {
        global_plate_start_map = $(this).val();
        // console.log("where starting from when making assay plate map: ", global_plate_start_map)
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

    // if copy or increment (show different options and behave differently)
    $("input[type='radio'][name='change_method']").click(function () {
        global_plate_change_method = $(this).val();
        if (global_plate_change_method === 'increment') {
            $('.increment-section').removeClass('hidden');
        } else {
            $('.increment-section').addClass('hidden');
        }
    });

    $("input[type='radio'][name='increment_direction']").click(function () {
        global_plate_increment_direction = $(this).val();
    });

    $("#id_se_increment_operation").change(function () {
        global_plate_increment_operation = $(this).val();
    });

    // if the user checked to change a sample box that was currently hidden, show it
    $("#checkbox_matrix_item").change(function () {
        if($(this).prop("checked") == true) {
            x_show_fancy_list = ['#show_matrix_item', ];
            x_show_cell_list = ['.plate-cells-matrix-item', ];
            setFancyCheckBoxesCheckedUncheckedUsingArrays('change', x_show_fancy_list, x_show_cell_list);
            setWhatHiddenInEachWellOfPlateLoopsOverPlate(global_plate_whole_plate_index_list, 'change');
        }
    });
    $("#checkbox_location").change(function () {
        if($(this).prop("checked") == true) {
            x_show_fancy_list = ['#show_location', ];
            x_show_cell_list = ['.plate-cells-location', ];
            setFancyCheckBoxesCheckedUncheckedUsingArrays('change', x_show_fancy_list, x_show_cell_list);
            setWhatHiddenInEachWellOfPlateLoopsOverPlate(global_plate_whole_plate_index_list, 'change');
        }
    });
    $("#checkbox_default_time").change(function () {
        if($(this).prop("checked") == true) {
            x_show_fancy_list = ['#show_default_time', ];
            x_show_cell_list = ['.plate-cells-default-time', ];
            setFancyCheckBoxesCheckedUncheckedUsingArrays('change', x_show_fancy_list, x_show_cell_list);
            setWhatHiddenInEachWellOfPlateLoopsOverPlate(global_plate_whole_plate_index_list, 'change');
        }
    });
    $("#checkbox_dilution_factor").change(function () {
        if($(this).prop("checked") == true) {
            x_show_fancy_list = ['#show_dilution_factor', ];
            x_show_cell_list = ['.plate-cells-dilution-factor', ];
            setFancyCheckBoxesCheckedUncheckedUsingArrays('change', x_show_fancy_list, x_show_cell_list);
            setWhatHiddenInEachWellOfPlateLoopsOverPlate(global_plate_whole_plate_index_list, 'change');
        }
    });
    $("#checkbox_collection_volume").change(function () {
        if($(this).prop("checked") == true) {
            x_show_fancy_list = ['#show_collection_volume', ];
            x_show_cell_list = ['.plate-cells-collection-volume', ];
            setFancyCheckBoxesCheckedUncheckedUsingArrays('change', x_show_fancy_list, x_show_cell_list);
            setWhatHiddenInEachWellOfPlateLoopsOverPlate(global_plate_whole_plate_index_list, 'change');
        }
    });
    $("#checkbox_collection_time").change(function () {
        if($(this).prop("checked") == true) {
            x_show_fancy_list = ['#show_collection_time', ];
            x_show_cell_list = ['.plate-cells-collection-time', ];
            setFancyCheckBoxesCheckedUncheckedUsingArrays('change', x_show_fancy_list, x_show_cell_list);
            setWhatHiddenInEachWellOfPlateLoopsOverPlate(global_plate_whole_plate_index_list, 'change');
        }
    });

    // controlling more of what shows and does not show on page (options to change) based on selected to apply
    // this option is for when the well use was in a dropdown - not currently using, but keep in case change back
    // $("#id_se_well_use").change(function () {
    //     global_plate_well_use = $(this).val();
    //     changePageSectionShownWhenChangeRadioWellUse()
    // });
    // this option is for when the well use is radio buttons - currently using
    // Well use: sample, standard, blank, empty, copy, and paste (extended the function to copy and paste)
    $("input[type='radio'][name='change_well_use']").click(function () {
        global_plate_well_use = $(this).val();
        changePageSectionShownWhenChangeRadioWellUse()
    });

    //change what is shown in the assay plate map if changed a fancy check box selection
    $("input[type='checkbox']").change(function () {
        // limit to checkboxes that are part of the fancy check box selections
        // (not the check boxes that get check for what gets changed when click apply or drag)
        let data_group = $(this).attr('data-group')
        if (data_group === "fancy-checkbox") {
            let this_attr_id = $(this).attr('id');
            let this_attr_id_plus = "#" + this_attr_id;
            let my_idx = global_plate_show_hide_fancy_checkbox_selector.indexOf(this_attr_id_plus);
            // another option:  if ($("input[type='checkbox'][name='change_location']").prop('checked') === true) {
            // HANDY to check if something is checked
            if ($(this_attr_id_plus).is(':checked')) {
                // console.log(this_attr_id_plus)
                $(global_plate_show_hide_fancy_checkbox_class[my_idx]).removeClass('hidden');
                // hides what was just checked (turned on) if not applicable to the well based on well use
                setWhatHiddenInEachWellOfPlateLoopsOverPlate(global_plate_whole_plate_index_list, 'change_fancy_checkbox:'+this_attr_id);
            } else {
                $(global_plate_show_hide_fancy_checkbox_class[my_idx]).addClass('hidden');
            }
        }
    });
    // NOTE: the above replaces a bunch of these
    //  $('#show_matrix_item').change(function() {
    //      if ($(this).is(':checked')) {
    //          $('.plate-cells-matrix-item').removeClass('hidden');
    //      } else {
    //          $('.plate-cells-matrix-item').addClass('hidden');
    //      }
    //      setWhatHiddenInEachWellOfPlateLoopsOverPlate(plate_index_list, 'change_check_box');
    //  });

    // START SECTION FOR CHANGING PLATEMAP FOR ADD PAGE BASED ON SELECTED "STARTING" PLACE (WITH FUNCTIONS)
    // --START FROM AN EMPTY PLATE
    $("#id_device").change(function () {
        // console.log("device change fired")
        // this fires when the user changes AND/OR when one of the other start methods is selected
        // update the global plate size based on new selection (add page, user changed directly)
        try {
            global_plate_size = $("#id_device").selectize()[0].selectize.items[0];
        } catch (err) {
            global_plate_size = $("#id_device").val();
        }
        for (var idx = 0, ls = global_plate_size; idx < ls; idx++) {
            global_plate_whole_plate_index_list.push(idx);
        }
        // console.log("changed device what size is plate: ", global_plate_size)
        // set to only fire on change plate size IF the selection is a_plate (an empty plate)
        if (global_plate_start_map === 'a_plate') {
            startFromAnEmptyPlate();
        }
        // else, just wanted the plate size update for later use, don't fire the rebuild plate!
        // fired in secondary selection (when the matrix or platemap is selected)
    });

    // --START FROM AN EXISTING PLATEMAP (CROSSING PLATEMAPS)
    $("#id_se_platemap").change(function () {
        startFromAnOtherPlatemap_ajax();
    });

    // --START FROM AN EXISTING MATRIX
    // matrix selector only shows on the ADD page after user radio button to pick from matrix
    // NOTE that, the id_device field was easy to change but the se_matrix was not.
    // one is a query set and one is a list, perhaps therein lies the difference
    $("#id_se_matrix").change(function () {
        let my_matrix_pk = $(this).val();
        startFromAnExistingMatrix_ajax(my_matrix_pk);
    });

    // END - SECTION FOR CHANGING PLATEMAP FOR ADD PAGE BASED ON SELECTED "STARTING" PLACE

    // START - secondary changes to assay plate map (Apply and Drag)
    // these get a plate_index_list of wells to change and sends to do the changes
    // NOTE - next line did not work as expected so used the document on HANDY
    // $(".apply-button").on("click", function(){
    $(document).on('click', '.apply-button', function () {
        let apply_button_that_was_clicked = $(this);
        callChangeSelectedByClickApply(apply_button_that_was_clicked);
    });
    // Select wells in platemap to change by drag - selected cells in table
    // https:// www.geeksforgeeks.org/how-to-change-selected-value-of-a-drop-down-list-using-jquery/
    // https:// stackoverflow.com/questions/8978328/get-the-value-of-a-dropdown-in-jquery
    function selectableDragOnPlateMaster() {
        callChangeSelectedByDragOnPlate()
    }  
    // END - secondary changes to assay plate map (Apply and Drag)

    // START - ADDITIONAL FUNCTION SECTION
    function startFromAnEmptyPlate(){
        // only here if a_plate - no ajax call needed since all defaults
        // clear the matrix and exising platemap selections incase go back and repick the same one
        $("#id_se_matrix").selectize()[0].selectize.setValue();
        $("#id_se_platemap").selectize()[0].selectize.setValue();
        //$("#id_device").selectize()[0].selectize.setValue(global_plate_size);
        addPageRemoveFormsetsBeforeBuildPlate();
        global_plate_add_or_edit_etc = 'add_change_device_size_starting_from_empty_plate';
        packPlateLabelsAndBuildOrChangePlate_ajax();
    }

    function startFromAnOtherPlatemap_ajax() {
        // load data from file/block pk if one or more file/blocks is assigned
        if (global_plate_start_map === 'a_platemap') {
            let data = {
                call: 'fetch_assay_study_platemap_for_platemap',
                study: global_plate_study_id,
                platemap: $("#id_se_platemap").selectize()[0].selectize.items[0],
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            };
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
                    addPageRemoveFormsetsBeforeBuildPlate();
                    global_plate_add_or_edit_etc = "add_change_starting_from_other_platemap";
                    packPlateLabelsAndBuildOrChangePlate_ajax();
                },
                // error callback
                error: function (xhr, errmsg, err) {
                    window.spinner.stop();
                    // $("#test_me1").text("error happened");
                    alert('An error has occurred (starting from another plate map), try a different matrix, assay plate map, or start from an empty plate.');
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
    };
    // post processing from ajax call
    let process_data_platemap = function (json, exist) {
        let platemap_info = json.platemap_info;
        let item_info = json.item_info;
        // console.log(platemap_info)
        // console.log(item_info)

        let platemap_info_0 = platemap_info[0];

        // reset the device form field and the other selection options
        $("#id_se_matrix").selectize()[0].selectize.setValue();
        //$("#id_se_platemap").selectize()[0].selectize.setValue();
        let pm_device = platemap_info_0.device;
        $("#id_device").selectize()[0].selectize.setValue(pm_device);
        global_plate_size = pm_device;

        // Need to set the other form fields
        $('#id_name').val($('#id_name').val() + " - starting from " + platemap_info_0.name);
        $('#id_description').val(platemap_info_0.description);
        $('#id_cell_count').val(platemap_info_0.cell_count);
        $('#id_well_volume').val(platemap_info_0.well_volume);
        // these do not work like fields that are not selectized
        let pm_time_unit = platemap_info_0.time_unit;
        let pm_volume_unit = platemap_info_0.volume_unit;
        let pm_well_volume = platemap_info_0.well_volume;
        let pm_study_assay = platemap_info_0.study_assay_id;
        let pm_standard_unit = platemap_info_0.standard_unit;
        global_floater_time_unit = pm_time_unit;
        try {$("#id_time_unit").selectize()[0].selectize.setValue(pm_time_unit);
        } catch (err) {$("#id_time_unit").removeProp('selected');
        }
        try {$("#id_volume_unit").selectize()[0].selectize.setValue(pm_volume_unit);
        } catch (err) {$("#id_volume_unit").removeProp('selected');
        }
        try {$("#id_well_volume").selectize()[0].selectize.setValue(pm_well_volume);
        } catch (err) {$("#id_well_volume").removeProp('selected');
        }
        try {$("#id_study_assay").selectize()[0].selectize.setValue(pm_study_assay);
        } catch (err) {$("#id_study_assay").removeProp('selected');
        }
        try {$("#id_standard_unit").selectize()[0].selectize.setValue(pm_standard_unit);
        } catch (err) {$("#id_standard_unit").removeProp('selected');
        }

        global_plate_mems_well_use = [];
        global_plate_mems_standard_value = [];
        global_plate_mems_matrix_item = [];
        global_plate_mems_matrix_item_text = [];
        global_plate_mems_location = [];
        global_plate_mems_location_text = [];
        global_plate_mems_dilution_factor = [];
        global_plate_mems_collection_volume = [];
        global_plate_mems_collection_time = [];
        global_plate_mems_default_time = [];
        // the time will be gotten from default time in the build plate function

        // make the changes to the well content memory variables
        for (var idx = 0, ls = global_plate_size; idx < ls; idx++) {
            global_plate_mems_well_use.push(item_info[idx].well_use);
            global_plate_mems_standard_value.push(item_info[idx].standard_value);
            global_plate_mems_matrix_item.push(item_info[idx].matrix_item);
            global_plate_mems_matrix_item_text.push(item_info[idx].matrix_item_text);
            global_plate_mems_location.push(item_info[idx].location);
            global_plate_mems_location_text.push(item_info[idx].location_text);
            global_plate_mems_dilution_factor.push(item_info[idx].dilution_factor);
            global_plate_mems_collection_volume.push(item_info[idx].collection_volume);
            global_plate_mems_collection_time.push(item_info[idx].collection_time);
            global_plate_mems_default_time.push(item_info[idx].default_time);
        }
    };

    function startFromAnExistingMatrix_ajax(my_matrix_pk) {
        if (global_plate_start_map === 'a_matrix') {
            let data = {
                call: 'fetch_assay_study_matrix_for_platemap',
                study: global_plate_study_id,
                matrix: $("#id_se_matrix").selectize()[0].selectize.items[0],
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            };
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
                    addPageRemoveFormsetsBeforeBuildPlate();
                    global_plate_add_or_edit_etc = 'add_change_starting_from_study_matrix';
                    packPlateLabelsAndBuildOrChangePlate_ajax();
                },
                // error callback
                error: function (xhr, errmsg, err) {
                    window.spinner.stop();
                    // $("#test_me1").text("error happened");
                    alert('An error has occurred (starting from an existing matrix), please try a different matrix, assay plate map, or start from an empty plate.');
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
    }
    // post processing from ajax call
    let process_data_matrix = function (json, exist) {
        let mi_list = json.mi_list;
        let device_size = parseInt(json.device_size);
        let number_columns = parseInt(json.number_columns);
        let row_index = 0;
        let column_index = 0;
        let plate_index = 0;
        global_plate_mems_plate_index = [];
        global_plate_mems_matrix_item = [];
        global_plate_mems_matrix_item_text = [];
        global_plate_mems_well_use = [];

        // console.log("device size: ",device_size)
        // clear the matrix and exising platemap selections incase go back and repick the same one
        //$("#id_se_matrix").selectize()[0].selectize.setValue();
        $("#id_se_platemap").selectize()[0].selectize.setValue();
        global_plate_size = device_size;
        $("#id_device").selectize()[0].selectize.setValue(global_plate_size);

        // since this is going to be a BUILD plate, not a CHANGE plate
        // it make life easier to have a complete plate

        // this set of mems will be a partial list, not a complete plate set (unless the matrix was completely filled
        $.each(mi_list, function(index, each) {
            // console.log("each ", each)
            row_index = parseInt(each.matrix_item_row_index);
            column_index = parseInt(each.matrix_item_column_index);
            plate_index = (row_index*number_columns)+column_index;
            global_plate_mems_plate_index.push(plate_index);
            global_plate_mems_matrix_item.push(each.matrix_item_id);
            global_plate_mems_matrix_item_text.push(each.matrix_item_text);
            global_plate_mems_well_use.push('sample');
        });

        // console.log(global_plate_mems_plate_index)
        // console.log(global_plate_mems_matrix_item_text)
    };

    function callChangeSelectedByClickApply(apply_button_that_was_clicked) {
        global_plate_add_or_edit_etc = "apply";

        if (global_plate_well_use == 'pastes' || global_plate_well_use == 'copys') {
            alert('Copy/Paste does not work with Apply buttons. Use Copy and drag.');
        } else {
            // this is limited to either one column or one row 
            // if make an Apply to All, don't send 
            // get the plate_indexes of the selected wells in the assay plate map table
            let plate_index_list = [];
            // what button was pushed (what column, what row, a column or row header)
            // find the assay plate map index of matching column or row (which button was click)
            let button_column_index = apply_button_that_was_clicked.attr('column-index');
            let button_row_index = apply_button_that_was_clicked.attr('row-index');
            let button_column_or_row = apply_button_that_was_clicked.attr('column-or-row');
            // console.log(button_column_index)
            // console.log(button_row_index)
            // console.log(button_column_or_row)
            // console.log("plate size: ", global_plate_size)
            // and send the assay plate map indexes to the function for processing
            for (var idx = 0, ls = global_plate_size; idx < ls; idx++) {
                // console.log($('#well_use-' + idx).attr('column-index'))
                if (button_column_or_row === 'column') {
                    if ($('#well_use-' + idx).attr('column-index') == button_column_index) {
                        plate_index_list.push(idx);
                    }
                } else {
                    // should match a row
                    if ($('#well_use-' + idx).attr('row-index') == button_row_index) {
                        plate_index_list.push(idx);
                    }
                }
            }
            // console.log(plate_index_list)

            // remember, on one row or one column is selected with the apply, so only need one list
            loadPlatemapIndexAndOtherReplacementInfo(plate_index_list);
            makeSpecificChangesToPlateUsingPlatemapIndexList(plate_index_list);

            // if make any changes that split the list, call these after all lists are processed so only file once
            setFancyCheckBoxesLoopOverFancyCheckboxClass(plate_index_list, "change");
            // setWhatHiddenInEachWellOfPlateLoopsOverPlate(plate_index_list, "sfc_" + "apply");
        }
    }

    function callChangeSelectedByDragOnPlate() {
        if (global_plate_well_use == 'pastes' && global_plate_copys_plate_index.length == 0) {
            alert('Copy/Paste will not work without a selected section to copy. Use Copy and drag.');
        } else {
            // load the lists based on what is dragged over
            // the plate_indexes of the selected cells in the assay plate map table
            // children of each cell of the assay plate map table that is selected
            // what cells were selected in the GUI
            let plate_index_list = [];
            let plate_indexes_rows = [];
            let plate_indexes_columns = [];
            $('.ui-selected').children().each(function () {
                if ($(this).hasClass("map-well-use")) {
                    let idx = $(this).attr('data-index');
                    plate_index_list.push(idx);
                    plate_indexes_rows.push($(this).attr('row-index'));
                    plate_indexes_columns.push($(this).attr('column-index'));
                }
            });
            // call for pastes or sample, empty, blank, standard
            callChangeSelectedByDragOnPlate2(plate_index_list, plate_indexes_rows, plate_indexes_columns);
        }
    }

    function callChangeSelectedByDragOnPlate2(plate_index_list, plate_indexes_rows, plate_indexes_columns) {
        // this could include the whole plate - so,
        // IF the incrementer is being used and if one of the - start over at top, left, or right 
        // then, need to limit to either one column or one row for EACH call to makeSpecificChangesToPlateUsingPlatemapIndexList

        // this is called when drag and any well use option (including copys and pastes), so, have to handle all logic
        global_plate_add_or_edit_etc = 'drag';

        // note: not building an option for Top to Bottom then Right or Top to Bottom then Left - will have to build if requested
        let true_if_changes_made_and_ready_to_recolor_plate = true;
        if (global_plate_well_use === "copys") {
            // change happens for the paste, not the copy, set to false
            true_if_changes_made_and_ready_to_recolor_plate = false;

            // need to load the setup for the selected wells into memory for pasting, but not pasting/changing yet
            storeCurrentWellInfoForCopysFeature(plate_index_list);
            // memory is loaded as long as user does not change the radio button selection
            // auto change the radio but selection pastes
            $("#radio_pastes").prop("checked", true).trigger("click");
            global_plate_well_use = 'pastes';
        } else if (global_plate_well_use === "pastes") {
            // may need to build some logic to look columns (hang over)
            // right now, if the user places the paste and it wraps past the column, it will just wrap
            // may want to make it crop instead

            // some special changes for pastes to control change behavior
            // set all the check boxes to make changes to true so that all will change
            $("#checkbox_matrix_item").prop("checked", true);
            $("#checkbox_location").prop("checked", true);
            $("#checkbox_default_time").prop("checked", true);
            $("#checkbox_dilution_factor").prop("checked", true);
            $("#checkbox_collection_volume").prop("checked", true);
            $("#checkbox_collection_time").prop("checked", true);

            // the assay plate map index list is the pastes drag index
            // console.log("plate index list before load: ", plate_index_list)
            loadPlatemapIndexAndOtherReplacementInfo(plate_index_list);
            // console.log("plate index list after load: ", plate_index_list)
            makeSpecificChangesToPlateUsingPlatemapIndexList(plate_index_list);

            // assume users are doing this so they can change the default time, and turn off all the rest
            $("#checkbox_matrix_item").prop("checked", false);
            $("#checkbox_location").prop("checked", false);
            $("#checkbox_dilution_factor").prop("checked", false);
            $("#checkbox_collection_volume").prop("checked", false);
            $("#checkbox_collection_time").prop("checked", false);
        } else {
            // this is when well use is blank, empty, standard, or sample
            if (
                global_plate_well_use === "blank" ||
                global_plate_well_use === "empty" ||
                global_plate_change_method === "copy") {
                loadPlatemapIndexAndOtherReplacementInfo(plate_index_list);
                makeSpecificChangesToPlateUsingPlatemapIndexList(plate_index_list);
            } else if (
                global_plate_increment_direction === "right-up" ||
                global_plate_increment_direction === "left-down") {
                // the value does not start over - okay to leave as one list
                loadPlatemapIndexAndOtherReplacementInfo(plate_index_list);
                makeSpecificChangesToPlateUsingPlatemapIndexList(plate_index_list);
            } else {
                // check what is changed and see if spans columns or rows
                // if does, need to split a loop of list for each of the columns or each of the rows
                // make a copy of a subset of the plate_index_list and call for each subset
                if (global_plate_increment_direction === 'top-top' ||
                    global_plate_increment_direction === 'bottom-bottom') {
                    // we are working with columns with restart
                    let column_indexes = [...new Set(plate_indexes_columns)];
                    column_indexes.forEach(function (el) {
                        let plate_index_list_sub = [];
                        $('.ui-selected').children().each(function () {
                            // send each selected cell of the table to the function for processing
                            // console.log("this: ",$(this))
                            if ($(this).hasClass("map-well-use") && $(this).attr('column-index') == el) {
                                let idx = $(this).attr('data-index');
                                plate_index_list_sub.push(idx);
                            }
                        });
                        plate_index_list_sub_ordered = loadPlatemapIndexAndOtherReplacementInfo(plate_index_list_sub);
                        // console.log("LIST: ", plate_index_list_sub)
                        makeSpecificChangesToPlateUsingPlatemapIndexList(plate_index_list_sub_ordered);
                    });
                } else {
                    // we are working with rows with restart
                    let row_indexes = [...new Set(plate_indexes_rows)]
                    row_indexes.forEach(function (el) {
                        // console.log("ggggt row indexex ", el)
                        let plate_index_list_sub = [];
                        $('.ui-selected').children().each(function () {
                            // send each selected cell of the table to the function for processing
                            // console.log("this: ",$(this))
                            if ($(this).hasClass("map-well-use") && $(this).attr('row-index') == el) {
                                let idx = $(this).attr('data-index');
                                plate_index_list_sub.push(idx);
                            }
                        });
                        plate_index_list_sub_ordered = loadPlatemapIndexAndOtherReplacementInfo(plate_index_list_sub);
                        // console.log("LIST: ", plate_index_list_sub)
                        makeSpecificChangesToPlateUsingPlatemapIndexList(plate_index_list_sub_ordered);
                    });
                }
            }
        }

        if (true_if_changes_made_and_ready_to_recolor_plate === true) {
            // now, all changes made and ready to what shows in plate based on well use
            setFancyCheckBoxesLoopOverFancyCheckboxClass(plate_index_list, "change");
            // setWhatHiddenInEachWellOfPlateLoopsOverPlate(plate_index_list, "sfc_" + "drag");
        }
    }

    function loadPlatemapIndexAndOtherReplacementInfo(plate_index_list) {
        // console.log("plate_index_list ", plate_index_list)
        // the plate index list will hold the index of the plate that is going to be replaced
        // and all the replacement content for those indexes

        let d_well_use = 'empty';
        let d_standard_value = "0";
        let d_matrix_item = null;
        let d_matrix_item_text = "";
        let d_location = null;
        let d_location_text = "";
        let d_dilution_factor = "1";
        let d_collection_volume = "0";
        let d_collection_time = "0";
        let d_compound = "";
        let d_cell = "";
        let d_setting = "";
        let d_default_time = "0";
        let d_time = "0";
        let d_block_raw_value = "0";

        // here we do want to reset all so we can push our subset
        global_plate_mems_plate_index = [];
        global_plate_mems_well_use = [];
        global_plate_mems_matrix_item = [];
        global_plate_mems_matrix_item_text = [];
        global_plate_mems_location = [];
        global_plate_mems_location_text = [];
        global_plate_mems_dilution_factor = [];
        global_plate_mems_collection_volume = [];
        global_plate_mems_collection_time = [];
        global_plate_mems_standard_value = [];
        global_plate_mems_default_time = [];
        global_plate_mems_time = [];
        global_plate_mems_block_raw_value = [];

        global_plate_mems_compound = [];
        global_plate_mems_cell = [];
        global_plate_mems_setting = [];


        // after the initial load of an existing platemap that has file blocks attached
        // when the user selects a different file block, only two fields in the platemap need changed
        // to save time, build a special case here that only loads the time and raw value

        if (global_plate_number_file_block_sets > 0) {
            // this is the case where it is an edit or view page
            // not the first time it is build
            // but after the default data block is changed to something else
            // should be whole plate, but treat as subset - should be the same
            let block_list_index = 0;
            global_plate_block_plate_index_list_imatches.forEach(function () {
                // first is just a copy, could just copy the whole thing, but this keeps everything lined up
                global_plate_mems_plate_index.push(global_plate_block_plate_index_list_imatches[block_list_index]);
                global_plate_mems_time.push(global_plate_block_time_imatches[block_list_index]);

                if (global_plate_block_raw_value_imatches[block_list_index] !== null) {
                    global_plate_mems_block_raw_value.push(global_plate_block_raw_value_imatches[block_list_index]);
                } else {
                    global_plate_mems_block_raw_value.push("-");
                }

                block_list_index = block_list_index + 1;
            });

        } else if (global_plate_well_use === "pastes") {
            // planning to copys/pastes everything on the plate
            // find the plate index offset from the copys section to the pastes section
            // what we want to be pasted is in already in the copys, so check copy over for all but index
            // the plate_index_list could be longer than one if the user dragged over more,
            // but we only care about the first one (top left of paste)
            // let delta_index = plate_index_list[0] - global_plate_copys_plate_index[0];
            // console.log('delta_index ', delta_index)

            let copys_list_index = 0;
            global_plate_copys_plate_index.forEach(function () {
                // this will be the copys formset number
                global_plate_mems_plate_index.push(global_plate_copys_plate_index[copys_list_index]);
                global_plate_mems_well_use.push(global_plate_copys_well_use[copys_list_index]);
                global_plate_mems_matrix_item.push(global_plate_copys_matrix_item[copys_list_index]);
                global_plate_mems_matrix_item_text.push(global_plate_copys_matrix_item_text[copys_list_index]);
                global_plate_mems_location.push(global_plate_copys_location[copys_list_index]);
                global_plate_mems_location_text.push(global_plate_copys_location_text[copys_list_index]);
                global_plate_mems_dilution_factor.push(global_plate_copys_dilution_factor[copys_list_index]);
                global_plate_mems_collection_volume.push(global_plate_copys_collection_volume[copys_list_index]);
                global_plate_mems_collection_time.push(global_plate_copys_collection_time[copys_list_index]);
                global_plate_mems_standard_value.push(global_plate_copys_standard_value[copys_list_index]);
                global_plate_mems_default_time.push(global_plate_copys_default_time[copys_list_index]);

                // whats this matrix item
                let c_matrix_item = global_plate_copys_matrix_item[copys_list_index];
                if (c_matrix_item != "undefined") {
                    let my_matrix_item_setup_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(c_matrix_item));
                    let c_compound = global_plate_isetup_compound[my_matrix_item_setup_index];
                    let c_cell = global_plate_isetup_cell[my_matrix_item_setup_index];
                    let c_setting = global_plate_isetup_setting[my_matrix_item_setup_index];
                    global_plate_mems_compound.push(c_compound);
                    global_plate_mems_cell.push(c_cell);
                    global_plate_mems_setting.push(c_setting);
                } else {
                    global_plate_mems_compound.push(global_plate_copys_compound[copys_list_index]);
                    global_plate_mems_cell.push(global_plate_copys_cell[copys_list_index]);
                    global_plate_mems_setting.push(global_plate_copys_setting[copys_list_index]);
                }

                global_plate_mems_time.push(global_plate_copys_default_time[copys_list_index]);
                // pastes is not allowed after file block is added so this can stay null
                global_plate_mems_block_raw_value.push(null);
                copys_list_index = copys_list_index + 1;
            });

        } else {

            // this should be for sample, standard, blank, or empty

            // (copys should not come here and pastes is above)
            // Guts of loading for changing the assay plate map with drag or apply for sample, standard, blank, empty
            // this executes for a list of wells/cells in the assay plate map table (selected with drag or Apply button)
            // in these cases, all should be replaced with the selected thing
            // EXCEPT when INCREMENT is used

            // these are the ones the user selects when CHANGING on plate
            let this_matrix_item_text = $('#id_se_matrix_item').children("option:selected").text();
            let this_matrix_item = $('#id_se_matrix_item').children("option:selected").val();
            let this_location_text = $('#id_se_location').children("option:selected").text();
            let this_location = $('#id_se_location').children("option:selected").val();

            // console.log("this_location ", this_location)
            // console.log("this_location_text ",  this_location_text)
            // console.log("this_matrix_item ", this_matrix_item)
            // console.log("this_matrix_item_text ",  this_matrix_item_text)
            let this_increment_value = 1.0;
            try {this_increment_value = parseFloat(document.getElementById('id_form_number_increment_value').value);
            } catch (err) {}
            let this_dilution_factor = 1.0;
            try {this_dilution_factor = parseFloat(document.getElementById('id_form_number_dilution_factor').value);
            } catch (err) {}
            let this_collection_volume = 0.0;
            try {this_collection_volume = (document.getElementById('id_form_number_collection_volume').value);
            } catch (err) {}
            let this_collection_time = 0.0;
            try {this_collection_time = parseFloat(document.getElementById('id_form_number_collection_time').value);
            } catch (err) {}
            let this_standard_value = 0.0;
            try {this_standard_value = parseFloat(document.getElementById('id_form_number_standard_value').value);
            } catch (err) {}
            let this_default_time_value = 0.0;
            try {this_default_time_value = parseFloat(document.getElementById('id_form_number_default_time').value);
            } catch (err) {}

            let plate_index_list_ordered = [];

            // changing order of how selected to apply the change so that, if incrementing, will go the right way
            // in the following cases, reverse the order of the selected plate indexes
            if (global_plate_change_method === 'increment' && (global_plate_increment_direction === 'right-up' || global_plate_increment_direction === 'right-right' || global_plate_increment_direction === 'bottom-bottom')) {
                plate_index_list_ordered = plate_index_list.sort(function (a, b) {
                    return b - a
                });
                // console.log("dsc ", plate_index_list_ordered)
            } else {
                // save for reference but should be ordered....plate_index_list_ordered = plate_index_list.map(Number).sort(function(a, b){return a-b});
                plate_index_list_ordered = plate_index_list;
                // console.log("asc ", plate_index_list_ordered)
            }
            global_plate_mems_plate_index = plate_index_list_ordered;

            // just declare them
            let incremented_default_time_value = 1.0;
            let incremented_standard_value = 1.0;

            // NOTE: all mems variables should be in ordered index order

            // when increment, the first will be treated as a copy
            let increment_number = 0;
            let formset_number = 0;
            let my_delta  = 0;

            let idx = 0;
            global_plate_mems_plate_index.forEach(function () {

                formset_number = global_plate_mems_plate_index[idx];

                // for each in the stored plate index
                // note that, mems plate index is a working subset in this case
                // the main plate index (that stores all the indices for the drag, is in the calling function

                // need one for EACH of the wells in the index list
                global_plate_mems_well_use.push(global_plate_well_use);

                // current residing in the formsets (text from the assay plate map)
                let c_standard_value =         $('#id_assayplatereadermapitem_set-' + formset_number + '-standard_value').val();
                let c_matrix_item =            $('#id_assayplatereadermapitem_set-' + formset_number + '-matrix_item').val();
                let c_matrix_item_text =       $('#matrix_item-' + formset_number).text();
                let c_location =               $('#id_assayplatereadermapitem_set-' + formset_number + '-location').val();
                let c_location_text =          $('#location-' + formset_number).text();
                let c_dilution_factor =        $('#id_assayplatereadermapitem_set-' + formset_number + '-dilution_factor').val();
                let c_collection_volume =      $('#id_assayplatereadermapitem_set-' + formset_number + '-collection_volume').val();
                let c_collection_time =        $('#id_assayplatereadermapitem_set-' + formset_number + '-collection_time').val();
                let c_compound =               $('#id_assayplatereadermapitem_set-' + formset_number + '-compound').val();
                let c_cell =                   $('#id_assayplatereadermapitem_set-' + formset_number + '-cell').val();
                let c_setting =                $('#id_assayplatereadermapitem_set-' + formset_number + '-setting').val();
                let c_default_time =           $('#id_assayplatereadermapitem_set-' + formset_number + '-default_time').val();
                let c_time =                   $('#id_assayplatereadermapitemvalue_set-' + formset_number + '-time').val();
                let c_block_raw_value =        d_block_raw_value;

                // overwrite the current with conditional changes, when needed
                // do for the direct copy if the box was checked to change (for samples)

                // this is for the fields that can NOT be incremented
                if (global_plate_well_use === 'sample') {
                    if ($("input[type='checkbox'][name='change_matrix_item']").prop('checked') === true) {
                        c_matrix_item = this_matrix_item;
                        c_matrix_item_text = this_matrix_item_text;
                        let my_matrix_item_setup_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(this_matrix_item));
                        c_compound = global_plate_isetup_compound[my_matrix_item_setup_index];
                        c_cell = global_plate_isetup_cell[my_matrix_item_setup_index];
                        c_setting = global_plate_isetup_setting[my_matrix_item_setup_index];
                    }
                    if ($("input[type='checkbox'][name='change_location']").prop('checked') === true) {
                        c_location = this_location;
                        c_location_text = this_location_text;
                    }
                    if ($("input[type='checkbox'][name='change_dilution_factor']").prop('checked') === true) {
                        c_dilution_factor =  this_dilution_factor;
                    }
                    if ($("input[type='checkbox'][name='change_collection_volume']").prop('checked') === true) {
                        c_collection_volume = this_collection_volume;
                    }
                    if ($("input[type='checkbox'][name='change_collection_time']").prop('checked') === true) {
                        c_collection_time = this_collection_time;
                    }
                } else {
                    c_matrix_item = d_matrix_item;
                    c_matrix_item_text = d_matrix_item_text;
                    c_compound = d_compound;
                    c_cell = d_cell;
                    c_setting = d_setting;
                    c_location = d_location;
                    c_location_text = d_location_text;
                    c_dilution_factor =  d_dilution_factor;
                    c_collection_volume = d_collection_volume;
                    c_collection_time = d_collection_time;
                }

                // do for things that can copy or increment (Time and Default time or Standard Value ONLY)
                if (global_plate_change_method === 'copy' || (global_plate_change_method === 'increment' && increment_number === 0)) {
                    if (global_plate_well_use === 'sample') {
                        if ($("input[type='checkbox'][name='change_default_time']").prop('checked') === true) {
                            c_default_time = generalFormatNumber(parseFloat(this_default_time_value));
                            c_time = c_default_time;
                        }
                    } else {
                        c_default_time = d_default_time;
                        c_time = c_default_time;
                    }

                    if (global_plate_well_use === 'standard') {
                        c_standard_value = this_standard_value;
                    }  else {
                        c_standard_value = d_standard_value;
                    }
                } else {
                    // should be increment only and not the first one in the series

                    if (global_plate_increment_operation === 'divide' || global_plate_increment_operation === 'multiply') {
                        my_delta = Math.pow(parseFloat(this_increment_value), parseFloat(increment_number));
                    } else if (global_plate_increment_operation === 'subtract' || global_plate_increment_operation === 'add') {
                        my_delta = parseFloat(this_increment_value) * parseFloat(increment_number);
                    } else {
                        my_delta = 1;
                    }

                    if (global_plate_well_use === 'sample') {

                        if (global_plate_increment_operation === 'divide') {
                            incremented_default_time_value = this_default_time_value / my_delta;
                        } else if (global_plate_increment_operation === 'multiply') {
                            incremented_default_time_value = this_default_time_value * my_delta;
                        } else if (global_plate_increment_operation === 'subtract') {
                            incremented_default_time_value = this_default_time_value - my_delta;
                        } else if (global_plate_increment_operation === 'add') {
                            incremented_default_time_value = this_default_time_value + my_delta;
                        } else {
                            incremented_default_time_value = 999;
                        }

                        if ($("input[type='checkbox'][name='change_default_time']").prop('checked') === true) {
                            c_default_time = generalFormatNumber(incremented_default_time_value);
                            c_time = c_default_time;
                        } else {
                            c_default_time = d_time;
                            c_time = c_default_time;
                        }
                        c_standard_value = d_standard_value;

                    } else if (global_plate_well_use === 'standard') {
                        if (global_plate_increment_operation === 'divide') {
                            incremented_standard_value = this_standard_value / my_delta;
                        } else if (global_plate_increment_operation === 'multiply') {
                            incremented_standard_value = this_standard_value * my_delta;
                        } else if (global_plate_increment_operation === 'subtract') {
                            incremented_standard_value = this_standard_value - my_delta;
                        } else if (global_plate_increment_operation === 'add') {
                            incremented_standard_value = this_standard_value + my_delta;
                        } else {
                            incremented_standard_value = 999;
                        }
                        c_standard_value = generalFormatNumber(incremented_standard_value);
                        c_default_time = d_time;
                        c_time = d_time;
                    } else {
                        c_standard_value = d_standard_value;
                        c_default_time = d_time;
                        c_time = d_time;
                    }
                }

                // now push them to the memory variables
                global_plate_mems_matrix_item.push(c_matrix_item);
                global_plate_mems_matrix_item_text.push(c_matrix_item_text);
                global_plate_mems_location.push(c_location);
                global_plate_mems_location_text.push(c_location_text);
                global_plate_mems_dilution_factor.push(c_dilution_factor);
                global_plate_mems_collection_volume.push(c_collection_volume);
                global_plate_mems_collection_time.push(c_collection_time);
                global_plate_mems_block_raw_value.push(c_block_raw_value);

                global_plate_mems_compound.push(c_compound);
                global_plate_mems_cell.push(c_cell);
                global_plate_mems_setting.push(c_setting);

                global_plate_mems_standard_value.push(c_standard_value);
                global_plate_mems_default_time.push(c_default_time);
                global_plate_mems_time.push(c_time);

                increment_number = increment_number + 1;
                idx = idx + 1;
            });
            // console.log("plate_index_list: ", plate_index_list)
            // console.log("matrix_item: ", global_plate_mems_matrix_item);
            // console.log("matrix_item_text: ", global_plate_mems_matrix_item_text);
            // console.log("location: ", global_plate_mems_location);
            // console.log("location_text: ", global_plate_mems_location_text);
            // console.log("dilution_factor: ", global_plate_mems_dilution_factor);
            // console.log("collection_volume: ", global_plate_mems_collection_volume);
            // console.log("collection_time: ", global_plate_mems_collection_time);
            // console.log("block_raw_value: ", global_plate_mems_block_raw_value);
            // console.log("compound: ", global_plate_mems_compound);
            // console.log("cell: ", global_plate_mems_cell);
            // console.log("setting: ", global_plate_mems_setting);
            // console.log("well_use: ", global_plate_mems_well_use);
            // console.log("standard_value: ", global_plate_mems_standard_value);
            // console.log("default_time: ", global_plate_mems_default_time);
            // console.log("time: ", global_plate_mems_time);

        }
        return global_plate_mems_plate_index;
    }

    function loadPlatemapIndexAndOtherInfoForPlateBuild() {
        // the plate index list will hold the index of the plate that is going to be replaced

        let d_well_use = 'empty';
        let d_standard_value = "0";
        let d_matrix_item = null;
        let d_matrix_item_text = "";
        let d_location = null;
        let d_location_text = "";
        let d_dilution_factor = "1";
        let d_collection_volume = "0";
        let d_collection_time = "0";
        let d_compound = "";
        let d_cell = "";
        let d_setting = "";
        let d_default_time = "0";
        let d_time = "0";
        let d_block_raw_value = "0";
        let my_matrix_item_setup_index = 0;

        if (global_plate_add_or_edit_etc === "add_change_starting_from_other_platemap") {
            global_plate_mems_compound = [];
            global_plate_mems_cell = [];
            global_plate_mems_setting = [];

            for (var formsetidx = 0, ls = global_plate_size; formsetidx < ls; formsetidx++) {
                d_matrix_item = global_plate_mems_matrix_item[formsetidx];
                my_matrix_item_setup_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(d_matrix_item));
                d_compound = global_plate_isetup_compound[my_matrix_item_setup_index];
                d_cell = global_plate_isetup_cell[my_matrix_item_setup_index];
                d_setting = global_plate_isetup_setting[my_matrix_item_setup_index];

                global_plate_mems_compound.push(d_compound);
                global_plate_mems_cell.push(d_cell);
                global_plate_mems_setting.push(d_setting);
            }
        } else if (global_plate_add_or_edit_etc === "add_change_starting_from_study_matrix") {
            // when starting from a matrix, there is NOT a compute plate in the mems, only if there was a matrix item
            global_plate_mems_compound = [];
            global_plate_mems_cell = [];
            global_plate_mems_setting = [];

            global_plate_mems_plate_index.forEach(function (row) {
                d_matrix_item = global_plate_mems_matrix_item[formsetidx];
                my_matrix_item_setup_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(d_matrix_item));
                d_compound = global_plate_isetup_compound[my_matrix_item_setup_index];
                d_cell = global_plate_isetup_cell[my_matrix_item_setup_index];
                d_setting = global_plate_isetup_setting[my_matrix_item_setup_index];

                global_plate_mems_compound.push(d_compound);
                global_plate_mems_cell.push(d_cell);
                global_plate_mems_setting.push(d_setting);
            });
        // } else if (global_plate_add_or_edit_etc === "update_or_view_first_load" || global_plate_add_or_edit_etc === "update_or_view_change_block") {
        } else if (global_plate_add_or_edit_etc === "update_or_view_first_load") {
            // the change block is handled as a change, not a build plate (to save time)
            // clear them all out and get them from the formset
            global_plate_mems_well_use = [];
            global_plate_mems_matrix_item = [];
            global_plate_mems_matrix_item_text = [];
            global_plate_mems_location = [];
            global_plate_mems_location_text = [];
            global_plate_mems_dilution_factor = [];
            global_plate_mems_collection_volume = [];
            global_plate_mems_collection_time = [];
            global_plate_mems_standard_value = [];
            global_plate_mems_default_time = [];
            global_plate_mems_time = [];
            global_plate_mems_block_raw_value = [];

            global_plate_mems_compound = [];
            global_plate_mems_cell = [];
            global_plate_mems_setting = [];

            for (var formsetidx = 0, ls = global_plate_size; formsetidx < ls; formsetidx++) {
                global_plate_mems_well_use.push($('#id_assayplatereadermapitem_set-' + formsetidx + '-well_use').val());
                global_plate_mems_standard_value.push($('#id_assayplatereadermapitem_set-' + formsetidx + '-standard_value').val());
                d_matrix_item = $('#id_assayplatereadermapitem_set-' + formsetidx + '-matrix_item').val();
                $('#id_ns_matrix_item').val(parseInt(d_matrix_item));
                d_matrix_item_text = $('#id_ns_matrix_item').children("option:selected").text();
                global_plate_mems_matrix_item.push(d_matrix_item);
                global_plate_mems_matrix_item_text.push(d_matrix_item_text);
                d_location = $('#id_assayplatereadermapitem_set-' + formsetidx + '-location').val();
                $('#id_ns_location').val(parseInt(d_location));
                d_location_text = $('#id_ns_location').children("option:selected").text();
                global_plate_mems_location.push(d_location);
                global_plate_mems_location_text.push(d_location_text);
                global_plate_mems_dilution_factor.push($('#id_assayplatereadermapitem_set-' + formsetidx + '-dilution_factor').val());
                global_plate_mems_collection_volume.push($('#id_assayplatereadermapitem_set-' + formsetidx + '-collection_volume').val());
                global_plate_mems_collection_time.push($('#id_assayplatereadermapitem_set-' + formsetidx + '-collection_time').val());
                global_plate_mems_default_time.push($('#id_assayplatereadermapitem_set-' + formsetidx + '-default_time').val());

                if (global_plate_number_file_block_sets == 0) {
                    d_time = $('#id_assayplatereadermapitemvalue_set-' + formsetidx + '-time').val();
                    d_block_raw_value = $('#id_assayplatereadermapitemvalue_set-' + formsetidx + '-raw_value').val();
                } else {
                    d_time = global_plate_block_time_imatches[formsetidx];

                    if (global_plate_block_raw_value_imatches[formsetidx] !== null) {
                        d_block_raw_value = global_plate_block_raw_value_imatches[formsetidx];
                    } else {
                        d_block_raw_value = "-";
                    }
                }

                global_plate_mems_time.push(d_time);
                global_plate_mems_block_raw_value.push(d_block_raw_value);

                my_matrix_item_setup_index = global_plate_isetup_matrix_item_id.indexOf(parseInt(d_matrix_item));
                d_compound = global_plate_isetup_compound[my_matrix_item_setup_index];
                d_cell = global_plate_isetup_cell[my_matrix_item_setup_index];
                d_setting = global_plate_isetup_setting[my_matrix_item_setup_index];
                // console.log(global_plate_isetup_matrix_item_id)
                // console.log("mi ", d_matrix_item)
                // console.log("ind ",my_matrix_item_setup_index)
                global_plate_mems_compound.push(d_compound);
                global_plate_mems_cell.push(d_cell);
                global_plate_mems_setting.push(d_setting);

            }
        }

        // console.log("matrix_item: ", global_plate_mems_matrix_item);
        // console.log("matrix_item_text: ", global_plate_mems_matrix_item_text);
        // console.log("location: ", global_plate_mems_location);
        // console.log("location_text: ", global_plate_mems_location_text);
        // console.log("dilution_factor: ", global_plate_mems_dilution_factor);
        // console.log("collection_volume: ", global_plate_mems_collection_volume);
        // console.log("collection_time: ", global_plate_mems_collection_time);
        // console.log("block_raw_value: ", global_plate_mems_block_raw_value);
        // console.log("compound: ", global_plate_mems_compound);
        // console.log("cell: ", global_plate_mems_cell);
        // console.log("setting: ", global_plate_mems_setting);
        // console.log("well_use: ", global_plate_mems_well_use);
        // console.log("standard_value: ", global_plate_mems_standard_value);
        // console.log("default_time: ", global_plate_mems_default_time);
        // console.log("time: ", global_plate_mems_time);
        // console.log("block_raw_value ", global_plate_mems_block_raw_value);

            // full list
            // global_plate_mems_well_use = [];
            // global_plate_mems_matrix_item = [];
            // global_plate_mems_matrix_item_text = [];
            // global_plate_mems_location = [];
            // global_plate_mems_location_text = [];
            // global_plate_mems_dilution_factor = [];
            // global_plate_mems_collection_volume = [];
            // global_plate_mems_collection_time = [];
            // global_plate_mems_standard_value = [];
            // global_plate_mems_default_time = [];
            // global_plate_mems_compound = [];
            // global_plate_mems_cell = [];
            // global_plate_mems_setting = [];
            // global_plate_mems_time = [];
            // global_plate_mems_block_raw_value = [];

            // for (var formsetidx = 0, ls = global_plate_size; formsetidx < ls; formsetidx++) {
            //     global_plate_mems_well_use.push(d_well_use);
            //     global_plate_mems_standard_value.push(d_standard_value);
            //     global_plate_mems_matrix_item.push(d_matrix_item);
            //     global_plate_mems_matrix_item_text.push(d_matrix_item_text);
            //     global_plate_mems_location.push(d_location);
            //     global_plate_mems_location_text.push(d_location_text);
            //     global_plate_mems_dilution_factor.push(d_dilution_factor);
            //     global_plate_mems_collection_volume.push(d_collection_volume);
            //     global_plate_mems_collection_time.push(d_collection_time);
            //     global_plate_mems_compound.push(d_compound);
            //     global_plate_mems_cell.push(d_cell);
            //     global_plate_mems_setting.push(d_setting);
            //     global_plate_mems_default_time.push(d_default_time);
            //     global_plate_mems_time.push(d_time);
            //     global_plate_mems_block_raw_value.push(d_block_raw_value);
            // }
    }

    // make a function to handle changing well use not matte how it is done
    // do this because there has been changing of the mind on dropdown, radio buttons, or ???
    // remember - copy is the copy vrs increment and copys is the copy section of assay plate map
    function changePageSectionShownWhenChangeRadioWellUse() {
        // called when the well use is changed
        // $("input[name=change_method][value=copy]").prop("checked", true);
        // global_plate_change_method = 'copy';
        // if (global_plate_change_method === 'increment') {
        //     $('.increment-section').removeClass('hidden');
        // } else {
        //     $('.increment-section').addClass('hidden');
        // }
        // hide all, then unhide what want to show
        $('.sample-section').addClass('hidden');
        $('.standard-section').addClass('hidden');
        $('.empty-section').addClass('hidden');
        $('.blank-section').addClass('hidden');
        $('.drag-option-section').addClass('hidden');
        $('.copys-section').addClass('hidden');
        $('.pastes-section').addClass('hidden');
        if (global_plate_well_use === 'sample') {
            $('.sample-section').removeClass('hidden');
            $('.drag-option-section').removeClass('hidden');
            $("input[name=change_method][value=copy]").prop("checked", true);
            global_plate_change_method = 'copy';
        } else if (global_plate_well_use === 'standard') {
            $('.standard-section').removeClass('hidden');
            $('.drag-option-section').removeClass('hidden');
            $('#show_standard_value').prop('checked', true);
            $("input[name=change_method][value=increment]").prop("checked", true);
            global_plate_change_method = 'increment';
        } else if (global_plate_well_use === 'copys') {
            $('.copys-section').removeClass('hidden');
            // open for loading plate well setup into memory
        } else if (global_plate_well_use === 'pastes') {
            $('.pastes-section').removeClass('hidden');
        } else if (global_plate_well_use === 'blank') {
            $('.blank-section').removeClass('hidden');
            // open for loading plate well setup into memory
        } else if (global_plate_well_use === 'empty') {
            $('.empty-section').removeClass('hidden');
        }
        if (global_plate_change_method === 'increment') {
            $('.increment-section').removeClass('hidden');
        } else {
            $('.increment-section').addClass('hidden');
        }
    }

    // this uses the fancy check boxes to set what fields of the formset are visible on the assay plate map
    // when first draws plate, uses defaults,
    // for subsequent draws, finds what is checked and redisplays them
    function setFancyCheckBoxesLoopOverFancyCheckboxClass(plate_index_list, build_or_change_or_clear_or_show) {
        //console.log("in setFancyCheckBoxes ", build_or_change_or_clear_or_show)
        //console.log("global_plate_start_map ", global_plate_start_map);

        let x_show_fancy_list = [];
        let x_show_cell_list = [];

        let call_hide_by_welluse = true;

        // on page load, set to defaults to show in the plate based  on well use selected
        if (build_or_change_or_clear_or_show === "build" && global_plate_start_map === "a_plate") {
            call_hide_by_welluse = false;
            x_show_fancy_list = [
                '#show_well_use',
            ];
            x_show_cell_list = [
                '.plate-cells-well-use',
            ];
        } else if (build_or_change_or_clear_or_show === "build") {
            // Build was from assay plate map or study matrix and they could have changed well use, get the defaults
            // leave it as true - call_hide_by_welluse = true;
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
                    // '#show_matrix_item',
                    // '#show_time',
                    // '#show_location',
                    // '#show_standard_value',
                    '#show_well_use',
                    '#show_block_raw_value',
                ];
                x_show_cell_list = [
                    // '.plate-cells-matrix-item',
                    // '.plate-cells-time',
                    // '.plate-cells-location',
                    // '.plate-cells-standard-value',
                    '.plate-cells-well-use',
                    '.plate-cells-block-raw-value',
                ];
            }
        } else if (build_or_change_or_clear_or_show === "show" || build_or_change_or_clear_or_show === "clear") {
            // clicked the button to clear all out of the plate
                x_show_fancy_list = global_plate_show_hide_fancy_checkbox_selector;
                x_show_cell_list = global_plate_show_hide_fancy_checkbox_class;
        } else {
            // this is a change plate call
            // leave it as true - call_hide_by_welluse = true;
            // find what is currently checked and load them into parallel arrays
            let all_idx = 0;
            global_plate_show_hide_fancy_checkbox_selector.forEach(function (show_box) {
                if ($(show_box).is(':checked')) {
                    x_show_fancy_list.push(global_plate_show_hide_fancy_checkbox_selector[all_idx]);
                    x_show_cell_list.push(global_plate_show_hide_fancy_checkbox_class[all_idx]);
                }
                all_idx = all_idx + 1;
                //console.log(x_show_fancy_list)
            });

            // use the arrays from above to show/hide and check/uncheck
            let checkidx = 0;
            x_show_fancy_list.forEach(function () {
                //console.log($(x_show_fancy_list[checkidx]))
                $(x_show_fancy_list[checkidx]).prop('checked', true);
                $(x_show_cell_list[checkidx]).removeClass('hidden');
                checkidx = checkidx + 1;
            });

            // just in case the main ones were not on, add them on to
            // yes, some of these may have already been checked and this is duplication the above
            // 20200226 Richard did not like these being turned back on, so leave them off
            // x_show_fancy_list = [
            //     '#show_matrix_item',
            //     '#show_default_time',
            //     '#show_location',
            //     '#show_standard_value',
            //     '#show_well_use',
            // ];
            // x_show_cell_list = [
            //     '.plate-cells-matrix-item',
            //     '.plate-cells-default-time',
            //     '.plate-cells-location',
            //     '.plate-cells-standard-value',
            //     '.plate-cells-well-use',
            // ];

        }

        setFancyCheckBoxesCheckedUncheckedUsingArrays(build_or_change_or_clear_or_show, x_show_fancy_list, x_show_cell_list);

        // call the secondary show/hide based on well use, if needed
        if (call_hide_by_welluse === true) {
            setWhatHiddenInEachWellOfPlateLoopsOverPlate(plate_index_list, build_or_change_or_clear_or_show);
        }
    }

    function setFancyCheckBoxesCheckedUncheckedUsingArrays(build_or_change_or_clear_or_show, x_show_fancy_list, x_show_cell_list) {
        // use the arrays from above to show/hide and check/uncheck
        let checkidx = 0;
        x_show_fancy_list.forEach(function () {
            if (build_or_change_or_clear_or_show != 'clear') {
                $(x_show_fancy_list[checkidx]).prop('checked', true);
                $(x_show_cell_list[checkidx]).removeClass('hidden');
            } else {
                $(x_show_fancy_list[checkidx]).prop('checked', false);
                $(x_show_cell_list[checkidx]).addClass('hidden');
            }
            checkidx = checkidx + 1;
        });
    }

    function findValueSetInsteadOfValueFormsetPackPlateLabelsBuildPlate_ajax(called_from) {
        let data = {
            call: 'fetch_information_for_value_set_of_plate_map_for_data_block',
            pk_data_block: global_calibrate_block_select_string_is_block_working_with_pk,
            pk_platemap: global_plate_this_platemap_id,
            num_colors: global_color_ramp_use_this_ramp.length,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };
        window.spinner.spin(document.getElementById("spinner"));
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
                    processFindValueSet(json, exist);
                    if (called_from === 'update_or_view_first_load') {
                        global_plate_add_or_edit_etc = 'update_or_view_first_load';
                        packPlateLabelsAndBuildOrChangePlate_ajax()
                    } else {
                        global_plate_add_or_edit_etc = 'update_or_view_change_block';
                        packPlateLabelsAndBuildOrChangePlate_ajax()
                    }
                }
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred (finding value set), please try a different matrix, assay plate map, or start from an empty plate.');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
    // post processing from ajax call
    let processFindValueSet = function (json, exist) {
        let block_data = json.block_data;
        // make parallel arrays of the information needed for display in the plate
        global_plate_block_plate_index_list_imatches = [];
        global_plate_block_time_imatches = [];
        global_plate_block_raw_value_imatches = [];
        global_plate_block_raw_value_imatches_bin_index = [];

        $.each(block_data, function (index, each) {
            // console.log("each ", each)
            global_plate_block_plate_index_list_imatches.push(index);
            global_plate_block_time_imatches.push(each.time);
            global_plate_block_raw_value_imatches.push(each.raw_value);
            global_plate_block_raw_value_imatches_bin_index.push(each.bin_index);
        });


        // console.log(global_plate_block_plate_index_list_imatches)
        // console.log(global_plate_block_time_imatches)
        // console.log(global_plate_block_raw_value_imatches)
    };

    // called from change checkboxes and from setFancyCheckBoxesLoopOverFancyCheckboxClass
    // to override check boxes and hide information that is not relevant for well use
    function setWhatHiddenInEachWellOfPlateLoopsOverPlate(plate_index_list, build_or_change_or_clear_or_show) {
        // setWhatHiddenInEachWellOfPlateLoopsOverPlate(plate_index_list, 'change_check_box') ('sfc_apply') ('sfc_build_plate') ('sfc_drag')
        // console.log("in setWhatHidden ", build_or_change)
        // console.log(plate_index_list)

        // I have not thought of a way around going through every well (that is any less complicated)

        let my_well_use = "";
        // console.log("called well use show in plate from ", where_called_from)
        // go to each cell in assay plate map and hide non relevant fields

        for (var idx = 0, ls = global_plate_size; idx < ls; idx++) {
            setHeatMapColorOfRawValue(idx);
            // plate_index_list.forEach(function (idx) {
            // note, cannot use the mems well use because it is not a complete list for the study matrix start
            // my_well_use =  $('#id_assayplatereadermapitem_set-' + idx + '-well_use').val();
            my_well_use = document.getElementById('well_use-' + idx).innerText;
            // console.log("index  ", idx, "  well use inside loop -", my_well_use, "-")
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
            }
            if (my_well_use === 'blank') {
                $('#standard_value-' + idx).addClass('hidden');
                $('#default_time-' + idx).addClass('hidden');
            } else if (my_well_use === 'empty') {
                $('#standard_value-' + idx).addClass('hidden');
                $('#default_time-' + idx).addClass('hidden');
                $('#time-' + idx).addClass('hidden');
                // $('#well_use-' + idx).addClass('hidden');
            } else if (my_well_use === 'standard') {
                $('#default_time-' + idx).addClass('hidden');
            } else if (my_well_use === 'sample') {
                $('#standard_value-' + idx).addClass('hidden');
            } else {
            }
        }
        // });
        // console.log("leaving setWhatHidden")
    }

    // Makes the well labels to use in building the assay plate map (based on the plate size)
    // this is called when page is loaded and when START is changed (plate size, matrix, platemap)
    function packPlateLabelsAndBuildOrChangePlate_ajax() {
        // console.log("plate size before call ajax: ",global_plate_size)
        // console.log("yes_if_matrix_item_setup_already_run: ",yes_if_matrix_item_setup_already_run)
        //
        let data = {
            call: 'fetch_information_for_plate_map_layout',
            study: global_plate_study_id,
            plate_size: global_plate_size,
            yes_if_matrix_item_setup_already_run: yes_if_matrix_item_setup_already_run,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };
        window.spinner.spin(document.getElementById("spinner"));
        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: data,
            success: function (json) {
                window.spinner.stop();
                let exist = true;
                local_plate_data_packed = packPlateLayout(json, exist);
                if (global_plate_add_or_edit_etc == 'update_or_view_change_block') {
                    // in this case, only the time and raw_value are changing, plate was already built
                    loadPlatemapIndexAndOtherReplacementInfo(global_plate_whole_plate_index_list);
                    makeSpecificChangesToPlateUsingPlatemapIndexList(global_plate_whole_plate_index_list);
                    // do not need to reset the fancy check boxes since only changed time and value
                } else {
                    // need to build the plate
                    loadPlatemapIndexAndOtherInfoForPlateBuild();
                    buildPlate(local_plate_data_packed);
                    // when doing the calibration, need to know if any wells are standards
                    countWellsThatAreStandards();
                }
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred, please try a different matrix, assay plate map, or start from an empty plate.');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
    // post processing from ajax call
    let packPlateLayout = function (json, exist) {
        let packed_lists = json.packed_lists;
        let mi_list = json.mi_list;

        // console.log(packed_lists)
        // Part 1 packed labels
        let row_labels = packed_lists[0].row_labels;
        let col_labels = packed_lists[0].col_labels;
        let row_contents = packed_lists[0].row_contents;

        // console.log(row_labels)
        // console.log(col_labels)
        // console.log(row_contents)

        // get matrix item setup information instead
        // of passing through the views and needing to load them as dom elements
        // happens when rebuild plate layout
        // really only needed it to happen ONCE, but, encountered race errors
        // calling two ajaxs subs on load
        // store in memory for access whenever a matrix item is added/changed in the platemap

        if (yes_if_matrix_item_setup_already_run == 'no') {
            // Part 2 matrix item setup
            // make the parallel list for easy search and find
            global_plate_isetup_matrix_item_id = [];
            global_plate_isetup_compound = [];
            global_plate_isetup_cell = [];
            global_plate_isetup_setting = [];
            // in the matrix in the other part of the database, there is an option to do long
            // they are here IF need them later
            global_plate_isetup_long_compound = [];
            global_plate_isetup_long_cell = [];
            global_plate_isetup_long_setting = [];

            $.each(mi_list, function (index, each) {
                // console.log("each ", each)
                global_plate_isetup_matrix_item_id.push(each.matrix_item_id);
                global_plate_isetup_compound.push(each.compound);
                global_plate_isetup_cell.push(each.cell);
                global_plate_isetup_setting.push(each.setting);
            });

            yes_if_matrix_item_setup_already_run = 'yes';

            //console.log("matrix_item_id returned: ", global_plate_isetup_matrix_item_id)
            //console.log("compound returned: ", global_plate_isetup_compound)
        }

        // NOTE that this arrangement will be first is when 0 for both row and column
        // global_plate_data_packed = [col_labels, row_labels, row_contents];
        return [col_labels, row_labels, row_contents]
    };
    // post processing from ajax call
    // This is the guts of the STARTING plate building function
    // It has conditions, based on where the function was called from, which determine the content of the STARTING assay plate map
    function buildPlate(local_plate_data_packed) {
        // console.log("global_plate_isetup_matrix_item_id
        // console.log(global_plate_isetup_matrix_item_id
        // console.log("local_plate_data_packed")
        // console.log(local_plate_data_packed)
        let key_value_plate_index_row_index = {};
        let key_value_plate_index_column_index = {};
        let top_label_button = ' ';
        let side_label_button = ' ';
        // this table's table tag and closing tag are in the html file
        $('#plate_table').empty();
        let thead = document.createElement("thead");
        let headRow = document.createElement("tr");
        // column headers: first, then the rest in loop
        let th = document.createElement("th");
        th.appendChild(document.createTextNode("Label"));
        headRow.appendChild(th);
        let header_col_index = 0;
        //local_plate_data_packed = [col_labels, row_labels, row_contents];
        local_plate_data_packed[0].forEach(function (colnumber) {

            let th = document.createElement("th");
            // th.appendChild(document.createTextNode(colnumber + top_label_button));
            if (global_plate_number_file_block_sets > 0) {
                //top_label_button = colnumber;
                top_label_button = '';
            } else {
                top_label_button = ' <a id="col' + header_col_index + '" column-or-row="column" column-index="'
                    + header_col_index + '" row-index="' + 770
                    //+ '" class="btn btn-sm btn-primary apply-button">Apply to Column</a>'
                    + '" class="btn btn-sm btn-primary apply-button">'
                    // + 'Apply '
                    // + colnumber
                    + '<span class="glyphicon glyphicon-arrow-down" aria-hidden="true"></span>'

                    // trying to add a tooltip....
                    // + ' &nbsp;'
                    // + '<span data-toggle="tooltip" data-title="Apply to Column" class="glyphicon glyphicon-arrow-down" aria-hidden="true" data-placement="bottom" data-original-title="" title=""></span>'

                    + ' </a>'
            }
            $(th).html(colnumber + top_label_button);
            headRow.appendChild(th);
            header_col_index = header_col_index + 1;
        });

        thead.appendChild(headRow);
        plate_table.appendChild(thead);

        // for each row
        let tbody = document.createElement("tbody");
        // let tr = document.createElement("tr");
        // get the first column (A B C D E...)
        // construct variables and set the default for add_first_load_starting_from_empty_plate
        let ret_well_use = 'empty';
        let ret_standard_value = "0";
        let ret_matrix_item = null;
        let ret_matrix_item_text = "";
        let ret_location = null;
        let ret_location_text = "";
        let ret_dilution_factor = "1";
        let ret_collection_volume = "0";
        let ret_collection_time = "0";
        let ret_compound = "";
        let ret_cell = "";
        let ret_setting = "";
        let ret_default_time = "0";
        let ret_time = "0";
        let ret_block_raw_value = "0";

        let formsetidx = 0;
        let ridx = 0;
        // console.log("start build plate")
        local_plate_data_packed[1].forEach(function (row) {
            let trbodyrow = document.createElement("tr");
            let tdbodyrow = document.createElement("th");
            let rowletter = local_plate_data_packed[1][ridx];
            if (global_plate_number_file_block_sets > 0) {
                //side_label_button = rowletter;
                side_label_button = '';
            } else {
                side_label_button = ' <a id="row' + ridx + '" column-or-row="row" column-index="' + 772
                    + '" row-index="' + ridx
                    //+ '" class="btn btn-sm btn-primary apply-button">Apply to Row</a>'
                    + '" class="btn btn-sm btn-primary apply-button">'
                    // + 'Apply '
                    // + rowletter
                    + '<span class="glyphicon glyphicon-arrow-right" aria-hidden="true"></span>'
                    + ' </a>'
            }
            // this is older -> tdbodyrow.appendChild(document.createTextNode(local_plate_data_packed[1][ridx]));
            $(tdbodyrow).html(rowletter + side_label_button);
            trbodyrow.appendChild(tdbodyrow);


            let cidx = 0;
            // build content row (same row as the row_labels (A=A, B=B, etc.)
            // while in a row, go through each column

            local_plate_data_packed[2][ridx].forEach(function (el) {
                // What is loaded may be all the plate or part of the plate
                // just do the part that is to be changed
                // console.log("formsetidx ", formsetidx)
                // make all the parts of the table body
                let td = document.createElement("td");
                let div_label = document.createElement("div");
                $(div_label).attr('data-index', formsetidx);
                $(div_label).attr('row-index', ridx);
                $(div_label).attr('column-index', cidx);
                $(div_label).attr('id', "label-" + formsetidx);
                $(div_label).addClass('map-label plate-cells-label hidden');
                // for coloring, for hiding, START with hidden

                let div_location = document.createElement("div");
                $(div_location).attr('data-index', formsetidx);
                $(div_location).attr('row-index', ridx);
                $(div_location).attr('column-index', cidx);
                $(div_location).attr('id', "location-" + formsetidx);
                $(div_location).attr('title', "Sample Location");
                $(div_location).addClass('map-location plate-cells-location hidden');

                let div_matrix_item = document.createElement("div");
                $(div_matrix_item).attr('data-index', formsetidx);
                $(div_matrix_item).attr('row-index', ridx);
                $(div_matrix_item).attr('column-index', cidx);
                $(div_matrix_item).attr('id', "matrix_item-" + formsetidx);
                $(div_matrix_item).attr('title', "Matrix Item");
                $(div_matrix_item).addClass('map-matrix-item plate-cells-matrix-item hidden');

                let div_dilution_factor = document.createElement("div");
                $(div_dilution_factor).attr('data-index', formsetidx);
                $(div_dilution_factor).attr('row-index', ridx);
                $(div_dilution_factor).attr('column-index', cidx);
                $(div_dilution_factor).attr('id', "dilution_factor-" + formsetidx);
                $(div_dilution_factor).attr('title', "Dilution Factor");
                $(div_dilution_factor).addClass('map-dilution-factor plate-cells-dilution-factor hidden');

                let div_collection_volume = document.createElement("div");
                $(div_collection_volume).attr('data-index', formsetidx);
                $(div_collection_volume).attr('row-index', ridx);
                $(div_collection_volume).attr('column-index', cidx);
                $(div_collection_volume).attr('id', "collection_volume-" + formsetidx);
                $(div_collection_volume).attr('title', "Sample Efflux Volume");
                $(div_collection_volume).addClass('map-collection-volume plate-cells-collection-volume hidden');

                let div_collection_time = document.createElement("div");
                $(div_collection_time).attr('data-index', formsetidx);
                $(div_collection_time).attr('row-index', ridx);
                $(div_collection_time).attr('column-index', cidx);
                $(div_collection_time).attr('id', "collection_time-" + formsetidx);
                $(div_collection_time).attr('title', "Sample Efflux Time");
                $(div_collection_time).addClass('map-collection-time plate-cells-collection-time hidden');

                let div_well_use = document.createElement("div");
                $(div_well_use).attr('data-index', formsetidx);
                $(div_well_use).attr('row-index', ridx);
                $(div_well_use).attr('column-index', cidx);
                $(div_well_use).attr('id', "well_use-" + formsetidx);
                $(div_well_use).attr('title', "Well Content");
                $(div_well_use).addClass('map-well-use plate-cells-well-use hidden');

                let div_compound = document.createElement("div");
                $(div_compound).attr('data-index', formsetidx);
                $(div_compound).attr('row-index', ridx);
                $(div_compound).attr('column-index', cidx);
                $(div_compound).attr('id', "compound-" + formsetidx);
                $(div_compound).addClass('map-compound plate-cells-compound hidden');

                let div_cell = document.createElement("div");
                $(div_cell).attr('data-index', formsetidx);
                $(div_cell).attr('row-index', ridx);
                $(div_cell).attr('column-index', cidx);
                $(div_cell).attr('id', "cell-" + formsetidx);
                $(div_cell).addClass('map-cell plate-cells-cell hidden');

                let div_setting = document.createElement("div");
                $(div_setting).attr('data-index', formsetidx);
                $(div_setting).attr('row-index', ridx);
                $(div_setting).attr('column-index', cidx);
                $(div_setting).attr('id', "setting-" + formsetidx);
                $(div_setting).addClass('map-setting plate-cells-setting hidden');

                let div_standard_value = document.createElement("div");
                $(div_standard_value).attr('data-index', formsetidx);
                $(div_standard_value).attr('row-index', ridx);
                $(div_standard_value).attr('column-index', cidx);
                $(div_standard_value).attr('id', "standard_value-" + formsetidx);
                $(div_standard_value).attr('title', "Standard Value");
                $(div_standard_value).addClass('map-standard-value plate-cells-standard-value hidden');

                let div_default_time = document.createElement("div");
                $(div_default_time).attr('data-index', formsetidx);
                $(div_default_time).attr('row-index', ridx);
                $(div_default_time).attr('column-index', cidx);
                $(div_default_time).attr('id', "default_time-" + formsetidx);
                $(div_default_time).attr('title', "Default Sample Time");
                $(div_default_time).addClass('map-default-time plate-cells-default-time hidden');

                let div_time = document.createElement("div");
                $(div_time).attr('data-index', formsetidx);
                $(div_time).attr('row-index', ridx);
                $(div_time).attr('column-index', cidx);
                $(div_time).attr('id', "time-" + formsetidx);
                $(div_time).attr('title', "Sample Time");
                $(div_time).addClass('map-time plate-cells-time hidden');

                let div_block_raw_value = document.createElement("div");
                $(div_block_raw_value).attr('data-index', formsetidx);
                $(div_block_raw_value).attr('row-index', ridx);
                $(div_block_raw_value).attr('column-index', cidx);
                $(div_block_raw_value).attr('id', "block_raw_value-" + formsetidx);
                $(div_block_raw_value).attr('title', "Block Raw Value");
                $(div_block_raw_value).addClass('map-block-raw-value plate-cells-block-raw-value hidden');

                // Get the formsets working correctly for the add page - do NOT need to change for view or update page
                // HANDY - need the .trim() after the .html() to strip white space
                // will call for any add option each time
                if (global_plate_check_page_call === 'add') {
                    // console.log("in add")
                    // if adding (from any add option)
                    // need a formset for EACH well in the plate (for the item and the item value tables)
                    // https:// simpleit.rocks/python/django/dynamic-add-form-with-add-button-in-django-modelformset-template/
                    // console.log("formsetidx ",formsetidx)
                    $('#formset').append(global_plate_first_item_form.replace(/-0-/g, '-' + formsetidx + '-'));
                    $('#id_assayplatereadermapitem_set-TOTAL_FORMS').val(formsetidx + 1);

                    if (global_plate_number_file_block_sets == 0) {
                        $('#value_formset').append(global_plate_first_value_form.replace(/-0-/g, '-' + formsetidx + '-'));
                        $('#id_assayplatereadermapitemvalue_set-TOTAL_FORMS').val(formsetidx + 1);
                    }
                    // this auto fills the fields that are needed to join the items and the items values tables
                    // the platemap id will be the same in both since they are two formsets to the main assay plate map table
                    // these (item and associated values) MUST stay parallel or problems WILL happen
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-row_index').val(ridx);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-column_index').val(cidx);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-plate_index').val(formsetidx);
                    $('#id_assayplatereadermapitemvalue_set-' + formsetidx + '-plate_index').val(formsetidx);
                }
                $('#id_assayplatereadermapitem_set-' + formsetidx + '-name').val(el);
                div_label.appendChild(document.createTextNode(el));

                // ignore if these since they will use all the defaults
                // if (global_plate_add_or_edit_etc === "add_first_load_starting_from_empty_plate" )
                // if (global_plate_add_or_edit_etc === "add_change_device_size_starting_from_empty_plate")

                if (global_plate_add_or_edit_etc === "add_change_starting_from_study_matrix") {
                    // call the stored memory variables as needed
                    // mems only holds those with samples
                    // this is different than the other, so, must set defaults when not sample in matrix
                    // if there is sample, get info, else use defaults
                    // find the index in the mems arrays of the this formset, if it is there
                    let sample_index = global_plate_mems_plate_index.indexOf(formsetidx);
                    // if found in the mems plate index, get the associated info
                    // console.log("**formset: ", formsetidx)
                    // console.log('**sample_index ',sample_index)
                    if (sample_index > -1) {
                        ret_well_use = global_plate_mems_well_use[sample_index];
                        ret_matrix_item = global_plate_mems_matrix_item[sample_index];
                        ret_matrix_item_text = global_plate_mems_matrix_item_text[sample_index];
                        ret_compound = global_plate_mems_compound[sample_index];
                        ret_cell = global_plate_mems_cell[sample_index];
                        ret_setting = global_plate_mems_setting[sample_index];
                        // times are all defaults
                    } else {
                        ret_well_use = 'empty';
                        ret_matrix_item = null;
                        ret_matrix_item_text = "";
                        ret_compound = "";
                        ret_cell = "";
                        ret_setting = "";
                    }
                    // console.log('--mi text ', ret_matrix_item_text)
                    // console.log('--well use ',ret_well_use)
                } else if (global_plate_add_or_edit_etc === "add_change_starting_from_other_platemap") {
                    ret_well_use = global_plate_mems_well_use[formsetidx];
                    ret_standard_value = global_plate_mems_standard_value[formsetidx];
                    ret_matrix_item = global_plate_mems_matrix_item[formsetidx];
                    ret_matrix_item_text = global_plate_mems_matrix_item_text[formsetidx];
                    ret_location = global_plate_mems_location[formsetidx];
                    ret_location_text = global_plate_mems_location_text[formsetidx];
                    ret_dilution_factor = global_plate_mems_dilution_factor[formsetidx];
                    ret_collection_volume = global_plate_mems_collection_volume[formsetidx];
                    ret_collection_time = global_plate_mems_collection_time[formsetidx];
                    ret_compound = global_plate_mems_compound[formsetidx];
                    ret_cell = global_plate_mems_cell[formsetidx];
                    ret_setting = global_plate_mems_setting[formsetidx];
                    ret_default_time = global_plate_mems_default_time[formsetidx];
                    ret_time = ret_default_time;
                // } else if (global_plate_add_or_edit_etc === "update_or_view_first_load" || global_plate_add_or_edit_etc === "update_or_view_change_block") {
                } else if (global_plate_add_or_edit_etc === "update_or_view_first_load") {
                    // the change block is handled as a change, not a build plate (to save time)
                    ret_well_use = global_plate_mems_well_use[formsetidx];
                    ret_standard_value = global_plate_mems_standard_value[formsetidx];
                    ret_matrix_item = global_plate_mems_matrix_item[formsetidx];
                    ret_matrix_item_text = global_plate_mems_matrix_item_text[formsetidx];
                    ret_location = global_plate_mems_location[formsetidx];
                    ret_location_text = global_plate_mems_location_text[formsetidx];
                    ret_dilution_factor = global_plate_mems_dilution_factor[formsetidx];
                    ret_collection_volume = global_plate_mems_collection_volume[formsetidx];
                    ret_collection_time = global_plate_mems_collection_time[formsetidx];
                    ret_compound = global_plate_mems_compound[formsetidx];
                    ret_cell = global_plate_mems_cell[formsetidx];
                    ret_setting = global_plate_mems_setting[formsetidx];
                    ret_default_time = global_plate_mems_default_time[formsetidx];
                    ret_time = global_plate_mems_time[formsetidx];
                    ret_block_raw_value = global_plate_mems_block_raw_value[formsetidx];
                }

                if ((global_plate_check_page_call === 'add')) {
                    // set the values in the formset and value formset that just got added above for the add page
                    // the raw value formset is NEVER changed in this GUI
                    // Make the changes to the formset (s)
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-well_use').val(ret_well_use);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-standard_value').val(ret_standard_value);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-matrix_item').val(ret_matrix_item);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-location').val(ret_location);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-dilution_factor').val(ret_dilution_factor);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-collection_volume').val(ret_collection_volume);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-collection_time').val(ret_collection_time);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-compound').val(ret_compound);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-cell').val(ret_cell);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-setting').val(ret_setting);
                    $('#id_assayplatereadermapitem_set-' + formsetidx + '-default_time').val(ret_default_time);

                    if (global_plate_number_file_block_sets > 0) {
                        // do not need to change the value formset because it is not pulled in,
                        // only the data are pulled in for display
                    } else {
                        $('#id_assayplatereadermapitemvalue_set-' + formsetidx + 'well_use').val(ret_well_use);
                        $('#id_assayplatereadermapitemvalue_set-' + formsetidx + '-time').val(ret_time);
                    }
                }
                // else, the map was previously saved and we are not changing the formsets

                // fill content in assay plate map during the build
                // which happens on load (add, view, update) and when starting point changed
                div_well_use.appendChild(document.createTextNode(ret_well_use));
                div_standard_value.appendChild(document.createTextNode(ret_standard_value));
                div_dilution_factor.appendChild(document.createTextNode(ret_dilution_factor));
                div_matrix_item.appendChild(document.createTextNode(ret_matrix_item_text));
                div_location.appendChild(document.createTextNode(ret_location_text));
                div_compound.appendChild(document.createTextNode(ret_compound));
                div_cell.appendChild(document.createTextNode(ret_cell));
                div_setting.appendChild(document.createTextNode(ret_setting));
                div_collection_volume.appendChild(document.createTextNode(ret_collection_volume));
                div_collection_time.appendChild(document.createTextNode(ret_collection_time));
                div_default_time.appendChild(document.createTextNode(ret_default_time));
                div_time.appendChild(document.createTextNode(ret_time));
                div_block_raw_value.appendChild(document.createTextNode(ret_block_raw_value));

                key_value_plate_index_row_index[formsetidx] = ridx;
                key_value_plate_index_column_index[formsetidx] = cidx;

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

                formsetidx = formsetidx + 1;
                cidx = cidx + 1;
            });
            tbody.appendChild(trbodyrow);
            ridx = ridx + 1;

        });
        // console.log("done build plate: ", plate_index_list)

        plate_table.appendChild(tbody);

        setFancyCheckBoxesLoopOverFancyCheckboxClass(global_plate_whole_plate_index_list, "build");
        // setWhatHiddenInEachWellOfPlateLoopsOverPlate(plate_index_list, "sfc_" + "build_plate");
        return plate_table
    }

    function storeCurrentWellInfoForCopysFeature(plate_index_list) {
        global_plate_copys_plate_index = [];
        global_plate_copys_well_use = [];
        global_plate_copys_matrix_item = [];
        global_plate_copys_matrix_item_text = [];
        global_plate_copys_default_time = [];
        global_plate_copys_location = [];
        global_plate_copys_location_text = [];
        global_plate_copys_standard_value = [];
        global_plate_copys_dilution_factor = [];
        global_plate_copys_collection_volume = [];
        global_plate_copys_collection_time = [];
        global_plate_copys_compound = [];
        global_plate_copys_cell = [];
        global_plate_copys_setting = [];

        // load the assay plate map values/text for the setup info into variables
        plate_index_list.forEach(function (idx) {
            global_plate_copys_plate_index.push(idx);
            global_plate_copys_well_use.push($('#well_use-' + idx).text());
            global_plate_copys_matrix_item.push($('#id_assayplatereadermapitem_set-' + idx + '-matrix_item').val());
            global_plate_copys_matrix_item_text.push($('#matrix_item-' + idx).text());
            global_plate_copys_default_time.push($('#default_time-' + idx).text());
            global_plate_copys_location.push($('#id_assayplatereadermapitem_set-' + idx + '-location').val());
            global_plate_copys_location_text.push($('#location-' + idx).text());
            global_plate_copys_standard_value.push($('#standard_value-' + idx).text());
            global_plate_copys_dilution_factor.push($('#dilution_factor-' + idx).text());
            global_plate_copys_collection_volume.push($('#collection_volume-' + idx).text());
            global_plate_copys_collection_time.push($('#collection_time-' + idx).text());
            global_plate_copys_compound.push($('#compound-' + idx).text());
            global_plate_copys_cell.push($('#cell-' + idx).text());
            global_plate_copys_setting.push($('#setting-' + idx).text());
        });

        // console.log("storeCurrentWellInfoForCopysFeature")
        // console.log(global_plate_copys_matrix_item)
        // console.log(global_plate_copys_matrix_item_text)
        // console.log(global_plate_copys_location)
        // console.log(global_plate_copys_location_text)
    }

    function makeSpecificChangesToPlateUsingPlatemapIndexList(plate_index_list) {
        // console.log("make specific plate_index_list ", plate_index_list)
        // set the defaults - only need this to keep from getting the implicit declaration warning
        let ret_well_use = 'empty';
        let ret_standard_value = "0";
        let ret_matrix_item = null;
        let ret_matrix_item_text = "";
        let ret_location = null;
        let ret_location_text = "";
        let ret_dilution_factor = "1";
        let ret_collection_volume = "0";
        let ret_collection_time = "0";
        let ret_compound = "";
        let ret_cell = "";
        let ret_setting = "";
        let ret_default_time = "0";
        let ret_time = "0";
        let ret_block_raw_value = "0";
        let formset_number = 0;

        let idx = 0;

        // remember, this is the change, not the build plate

        // after the initial load of an existing platemap that has file blocks attached
        // when the user selects a different file block, only two fields in the platemap need changed
        // to save time, build a special case here that only changes the time and raw value in the plate

        if (global_plate_number_file_block_sets > 0) {
            // plate was already build, just changing what is display for time and raw value
            // remember, as of 20200113, no value formset is present after file data has been attached to the platemap
            plate_index_list.forEach(function () {
                formset_number = plate_index_list[idx];
                ret_time = global_plate_mems_time[idx];
                ret_block_raw_value = global_plate_mems_block_raw_value[idx];
                $('#time-' + formset_number).text(ret_time);
                $('#block_raw_value-' + formset_number).text(ret_block_raw_value);
                idx = idx + 1;
                // console.log(formset_number)
                // console.log(ret_time)
                // console.log(ret_block_raw_value)
            });

        } else {

            plate_index_list.forEach(function () {
                // this is the pastes formset list, so, if dragged on one well, will be one well
                // if dragged over two, will be two
                // with fill from left to right and top to bottom of selected area
                formset_number = plate_index_list[idx];
                // console.log("this formset number: ", formset_number)
                ret_well_use = global_plate_mems_well_use[idx];
                ret_standard_value = global_plate_mems_standard_value[idx];
                ret_matrix_item = global_plate_mems_matrix_item[idx];
                ret_matrix_item_text = global_plate_mems_matrix_item_text[idx];
                ret_location = global_plate_mems_location[idx];
                ret_location_text = global_plate_mems_location_text[idx];
                ret_dilution_factor = global_plate_mems_dilution_factor[idx];
                ret_collection_volume = global_plate_mems_collection_volume[idx];
                ret_collection_time = global_plate_mems_collection_time[idx];
                ret_compound = global_plate_mems_compound[idx];
                ret_cell = global_plate_mems_cell[idx];
                ret_setting = global_plate_mems_setting[idx];
                ret_default_time = global_plate_mems_default_time[idx];
                ret_time = global_plate_mems_time[idx];
                ret_block_raw_value = global_plate_mems_block_raw_value[idx];

                // Make the changes to the formset (s)
                $('#id_assayplatereadermapitem_set-' + formset_number + '-well_use').val(ret_well_use);
                $('#id_assayplatereadermapitem_set-' + formset_number + '-standard_value').val(ret_standard_value);
                $('#id_assayplatereadermapitem_set-' + formset_number + '-matrix_item').val(ret_matrix_item);

                $('#id_assayplatereadermapitem_set-' + formset_number + '-location').val(ret_location);

                $('#id_assayplatereadermapitem_set-' + formset_number + '-dilution_factor').val(ret_dilution_factor);
                $('#id_assayplatereadermapitem_set-' + formset_number + '-collection_volume').val(ret_collection_volume);
                $('#id_assayplatereadermapitem_set-' + formset_number + '-collection_time').val(ret_collection_time);
                $('#id_assayplatereadermapitem_set-' + formset_number + '-compound').val(ret_compound);
                $('#id_assayplatereadermapitem_set-' + formset_number + '-cell').val(ret_cell);
                $('#id_assayplatereadermapitem_set-' + formset_number + '-setting').val(ret_setting);
                $('#id_assayplatereadermapitem_set-' + formset_number + '-default_time').val(ret_default_time);

                if (global_plate_number_file_block_sets > 0) {
                    // do not need to change the value formset because it is not pulled in,
                    // only the data are pulled in for display
                } else {
                    $('#id_assayplatereadermapitemvalue_set-' + formset_number + '-well_use').val(ret_well_use);
                    $('#id_assayplatereadermapitemvalue_set-' + formset_number + '-time').val(ret_time);
                }

                // Make the changes to the plate
                $('#well_use-' + formset_number).text(ret_well_use);

                $('#matrix_item-' + formset_number).text(ret_matrix_item_text);

                $('#location-' + formset_number).text(ret_location_text);
                $('#dilution_factor-' + formset_number).text(ret_dilution_factor);
                $('#collection_volume-' + formset_number).text(ret_collection_volume);
                $('#collection_time-' + formset_number).text(ret_collection_time);
                $('#standard_value-' + formset_number).text(ret_standard_value);
                $('#compound-' + formset_number).text(ret_compound);
                $('#cell-' + formset_number).text(ret_cell);
                $('#setting-' + formset_number).text(ret_setting);
                $('#default_time-' + formset_number).text(ret_default_time);
                $('#time-' + formset_number).text(ret_time);
                $('#block_raw_value-' + formset_number).text(ret_block_raw_value);

                idx = idx + 1;
            });
        }
    }

    // the suite of pre calibration checks
    function theSuiteOfPreCalibrationChecks() {
        loadAndReloadTheAssayInfoPlus();
        let yesToContinue = changingOptionalToRequiredCalling();
        if (yesToContinue == 'yes'){
            reviewInformationNeededForUnitConversionAndWarningIfMissingAndFindMultiplier();
        }
        if (global_plate_number_file_block_sets > 0) {
            global_calibrate_calibration_curve_method = 'select_one';
            //this will trigger the change event for recalibrating
            $("#id_se_form_calibration_curve").selectize()[0].selectize.setValue(global_calibrate_calibration_curve_method);
        }

        $('#refresh_needed_indicator').text('wait');
    }

    function loadAndReloadTheAssayInfoPlus() {
        global_floater_study_assay = $('#id_study_assay').children("option:selected").text().trim();
        global_floater_standard_unit = $('#id_standard_unit').children("option:selected").text().trim();
        global_floater_volume_unit = $('#id_volume_unit').children("option:selected").text().trim();
        global_floater_well_volume = $('#id_well_volume').val();
        global_floater_cell_count = $('#id_cell_count').val();
        // watch these! be if change how Unit, Target, Method are, will need to UPDATE these WATCH CAREFUL!
        // global_floater_target = global_floater_study_assay.substring(global_floater_study_assay.indexOf("TARGET") + 8, global_floater_study_assay.indexOf("METHOD")).trim();
        // global_floater_method = global_floater_study_assay.substring(global_floater_study_assay.indexOf("METHOD") + 8, global_floater_study_assay.indexOf("UNIT")).trim();
        // global_floater_unit   = global_floater_study_assay.substring(global_floater_study_assay.indexOf("UNIT") + 6, global_floater_study_assay.length).trim();
        global_floater_target = global_floater_study_assay.substring(global_floater_study_assay.indexOf("TARGET") + 8, global_floater_study_assay.indexOf("METHOD")-3).trim() + ' (Detected)';
        global_floater_method = global_floater_study_assay.substring(global_floater_study_assay.indexOf("METHOD") + 8, global_floater_study_assay.length).trim();
        global_floater_unit   = global_floater_study_assay.substring(0, global_floater_study_assay.indexOf("TARGET")-5).trim();
        // console.log('global_floater_target  ',    global_floater_target)
        // console.log('global_floater_method  ',    global_floater_method)
        // console.log('global_floater_unit  ',      global_floater_unit )
        global_floater_molecular_weight = $('#id_standard_molecular_weight').val();
        global_floater_time_unit = $('#id_time_unit').children("option:selected").text().trim();
    }

    function changingOptionalToRequiredCalling() {

        let result = 'yes';
        if (global_floater_standard_unit.search('well') >= 0) {
            $('#id_well_volume').addClass('required');
        } else {
            $('#id_well_volume').removeClass('required');
        }

        // if have mL (no mass or mole) and going to mass in reporting unit, don't have...
        if (
            ( 2 + parseInt(global_floater_standard_unit.search('g'))
                + parseInt(global_floater_standard_unit.search('mol'))
                + parseInt(global_floater_standard_unit.search('M'))
            ) < 0
            && global_floater_unit.search('g') >= 0 ) {

            global_calibration_multiplier = 0.0;
            global_calibration_multiplier_string = "This unit conversion is beyond my capability.";
            global_calibration_multiplier_string_display = global_calibration_multiplier_string;
            $('#id_form_data_processing_multiplier').val(generalFormatNumber(global_calibration_multiplier));
            $('#id_form_data_processing_multiplier_string').val(global_calibration_multiplier_string);
            $('#id_display_multiplier_message').text(global_calibration_multiplier_string_display);
            result = 'no'
        } else {
            if (
                ((global_floater_standard_unit.search('mol') >= 0
                    || global_floater_standard_unit.search('M') >= 0
                    || global_floater_standard_unit.search('N') >= 0)
                    && global_floater_unit.search('g') >= 0)
                ||
                ((global_floater_unit.search('mol') >= 0
                    || global_floater_unit.search('M') >= 0
                    || global_floater_unit.search('N') >= 0)
                    && global_floater_standard_unit.search('g') >= 0)
            ) {
                $('#id_standard_molecular_weight').addClass('required');
            } else {
                $('#id_standard_molecular_weight').removeClass('required');
            }

            if (global_floater_standard_unit.search('day') < 0
                && global_floater_unit.search('day') >= 0) {
                $('#id_cell_count').addClass('required');
            } else {
                $('#id_cell_count').removeClass('required');
            }

            if ((global_floater_standard_unit.search('day') < 0
                && global_floater_unit.search('day') >= 0)
                || global_floater_standard_unit.search('well') >= 0) {
                $('#id_volume_unit').next().addClass('required');
            } else {
                $('#id_volume_unit').next().removeClass('required');
            }
        }
        return result;
    }

    function reviewInformationNeededForUnitConversionAndWarningIfMissingAndFindMultiplier() {
        let listOfIds = ['#id_study_assay', '#id_standard_unit', '#id_volume_unit', '#id_time_unit'
                        , '#id_cell_count', '#id_well_volume', '#id_standard_molecular_weight'];

        let mycounter = 0;
        listOfIds.forEach(function(item) {
            let isRequired = $(item).hasClass('required');
            let myValueLength = "";
            if (isRequired) {
                myValueLength = $(item).val().length;
                if (myValueLength < 1) {
                    mycounter = mycounter + 1;
                }
            }
        });

        //console.log("counter ", mycounter)
        // if there is info missing, give a message but do not call the find multiplier
        if (mycounter > 0) {

            global_calibration_multiplier = 0.0;
            global_calibration_multiplier_string = "The sample time unit and/or information that is required for unit conversion is missing.";
            global_calibration_multiplier_string_display = global_calibration_multiplier_string;
            $('#id_form_data_processing_multiplier').val(generalFormatNumber(global_calibration_multiplier));
            $('#id_form_data_processing_multiplier_string').val(global_calibration_multiplier_string);
            $('#id_display_multiplier_message').text(global_calibration_multiplier_string_display);

            $('#refresh_needed_indicator').text('missed');
        } else {
            dataProcessingFindTheMultiplier(mycounter);
        }
    }

    // somewhat general function for unit conversion
    function dataProcessingFindTheMultiplier(mycounter){
        let incomingMultiplier = $("#id_form_data_processing_multiplier").val();

        // should have info to be able to calculate the multiplier or should not be here
        //easy cases
        if (global_floater_standard_unit == global_floater_unit) {

            global_calibration_multiplier = 1.0;
            global_calibration_multiplier_string = "No unit conversion is required.";
            global_calibration_multiplier_string_display = global_calibration_multiplier_string;
            $('#id_form_data_processing_multiplier').val(generalFormatNumber(global_calibration_multiplier));
            $('#id_form_data_processing_multiplier_string').val(global_calibration_multiplier_string);
            $('#id_display_multiplier_message').text(global_calibration_multiplier_string_display);

        } else {
            // do after functions in call since ajax race issues
            gutsFindTheMultiplier();
        }
        if (incomingMultiplier == global_calibration_multiplier) {
            $('#refresh_needed_indicator').text('updated');
        } else {
            $('#refresh_needed_indicator').text('needed');
        }
    }

    function gutsFindTheMultiplier(){
        // remember - this is really separate from calibration
        let data = {
            call: 'fetch_multiplier_for_data_processing_plate_map_integration',
            target: global_floater_target,
            method: global_floater_method,
            unit: global_floater_unit,
            standard_unit: global_floater_standard_unit,
            volume_unit: global_floater_volume_unit,
            well_volume: global_floater_well_volume,
            cell_count: global_floater_cell_count,
            molecular_weight: global_floater_molecular_weight,
            time_unit: global_floater_time_unit,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };
        window.spinner.spin(document.getElementById("spinner"));
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
                    processGutsFindTheMultiplier(json, exist);
                }
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred (finding the unit conversion multiplier). If no other option, enter the multiplier manually.');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
    // post processing from ajax call
    let processGutsFindTheMultiplier = function (json, exist) {
        let multiplier_data = json.multiplier_data;
        let returnedMultiplier = multiplier_data[0].multiplier;
        let returnedMultiplierString = multiplier_data[0].multiplier_string;
        let returnedMultiplierStringDisplay = multiplier_data[0].multiplier_string_display;
        //console.log("returnedMultiplierString ",returnedMultiplierString)

        global_calibration_multiplier = returnedMultiplier;
        // console.log("returnedMultiplier ",returnedMultiplier)
        global_calibration_multiplier_string = returnedMultiplierString;
        global_calibration_multiplier_string_display = returnedMultiplierStringDisplay;
        $('#id_form_data_processing_multiplier').val(generalFormatNumber(parseFloat(global_calibration_multiplier)));
        $('#id_form_data_processing_multiplier_string').val(global_calibration_multiplier_string);
        $('#id_display_multiplier_message').text(global_calibration_multiplier_string_display);

    };

    function countWellsThatAreStandards(){
        let mycount = 0;
        global_plate_mems_well_use.forEach(function(item, index) {
            if (item == 'standard') {
                mycount = mycount + 1;
            }
        });
        global_plate_well_use_count_of_standards_this_platemap = mycount;
    }

    function setHeatMapColorOfRawValue(formsetidx) {
        let this_color = global_color_ramp_use_this_ramp[global_plate_block_raw_value_imatches_bin_index[formsetidx]];
        // console.log(formsetidx)
        // console.log(this_color)
        let this_element = 'block_raw_value-' + formsetidx;
        document.getElementById(this_element).style.backgroundColor = this_color;
    }

    // general function to find selected radio button
    function displayRadioButtonSelectedValue(elementName) {
        var ele = document.getElementsByName(elementName);

        for(i = 0; i < ele.length; i++) {
            if (ele[i].checked) {
                selected_value = ele[i].value;
                break
            }
        }
        return selected_value
    }

    // general function to format numbers
    function generalFormatNumber(this_number_in) {
        let formatted_number = 0;
        // console.log("function format ", this_number_in)
        let this_number = parseFloat(this_number_in);
        if (this_number == 0) {
            formatted_number = this_number.toFixed(0);
        } else if (this_number < 0.00001) {
            formatted_number = this_number.toExponential(2);
        } else if (this_number < 0.0001) {
            formatted_number = this_number.toExponential(2);
        } else if (this_number < 0.001) {
            formatted_number = this_number.toFixed(4);
        } else if (this_number < 0.01) {
            formatted_number = this_number.toFixed(3);
        } else if (this_number < 0.1) {
            formatted_number = this_number.toFixed(3);
        } else if (this_number < 1.0) {
            formatted_number = this_number.toFixed(3);
        } else if (this_number < 10) {
            formatted_number = this_number.toFixed(2);
        } else if (this_number < 30) {
            formatted_number = this_number.toFixed(2);
        } else if (this_number < 100) {
            formatted_number = this_number.toFixed(1);
        } else if (this_number < 1000) {
            formatted_number = this_number.toFixed(0);
        } else if (this_number < 10000) {
            formatted_number = this_number.toFixed(0);
        } else if (this_number < 100000) {
            formatted_number = this_number.toFixed(0);
        } else if (this_number < 1000000) {
            formatted_number = this_number.toFixed(0);
        } else if (this_number < 10000000) {
            formatted_number = this_number.toFixed(0);
        } else {
            formatted_number = this_number.toExponential(2);
        }

        return formatted_number;
    }

  //    https://www.wikitechy.com/tutorials/javascript/print-a-number-with-commas-as-thousands-separators-in-javascript
    function thousands_separators(num)
        {
            var num_parts = num.toString().split(".");
            num_parts[0] = num_parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            return num_parts.join(".");
        }



    // function to purge previous formsets before adding new ones when redrawing a assay plate map - keep
    function addPageRemoveFormsetsBeforeBuildPlate() {
        // get rid of previous formsets before try to add more or the indexes get all messed up
        while ($('#formset').find('.inline').length > 0) {
            $('#formset').find('.inline').first().remove();
        }
        $('#id_assayplatereadermapitem_set-TOTAL_FORMS').val(0);
        while ($('#value_formset').find('.inline').length > 0) {
            $('#value_formset').find('.inline').first().remove();
        }
        $('#id_assayplatereadermapitemvalue_set-TOTAL_FORMS').val(0);
    }

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
        distance: 15,
        stop: selectableDragOnPlateMaster
    });
    // activates Bootstrap tooltips, must be AFTER tooltips are created - keep
    $('[data-toggle="tooltip"]').tooltip({container: "body", html: true});
    // END SECTION OF SPECIALS FOR EXTENDING FEATURES

});



// START - STUFF FOR REFERENCE
// used to format the reference table - keep if show table, else, do not need this formatting
// NOTE that the table is needed to pull setup information (using javascript) to show in assay plate map
// NOTE: if show table as DataTable, matrix items that are not display are not accessible,
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

// HANDY to know for going through a formset
// console.log("$('#value_formset')")
// console.log($('#value_formset'))
// console.log("$('#value_formset').find('.inline')")
// console.log($('#value_formset').find('.inline'))
// console.log("$('#value_formset').find('.inline').first()")
// console.log($('#value_formset').find('.inline').first())
// console.log("$('#value_formset').find('.inline').first()[0]")
// console.log($('#value_formset').find('.inline').first()[0])
// console.log("$('#value_formset').find('.inline').first()[0].outerHTML")
// console.log($('#value_formset').find('.inline').first()[0].outerHTML)
// $('#value_formset').children().each(function(cfs) {
//  my_block_raw_value_v = "id_assayplatereadermapitemvalue_set-" + cfs + "-raw_value";
//  }

// keep for reference
// let standardblock = $('input[name=standard_pick]:checked').val();

// https://stackoverflow.com/questions/195951/how-can-i-change-an-elements-class-with-javascript
// document.getElementById("MyElement").className =
// document.getElementById("MyElement").className.replace
// ( /(?:^|\s)MyClass(?!\S)/g , '' )
// /* Code wrapped for readability - above is all one statement */
// //    https://stackoverflow.com/questions/39139490/how-do-i-add-a-class-to-a-selectize-option-dynamically


// $("#id_ns_block_standard_borrow_string").find('option').remove();
// for(i=0; i < global_calibrate_borrowed_metadata_block.length; i++){
//     $("#id_ns_block_standard_borrow_string").append('<option value="'
//         +global_calibrate_borrowed_metadata_block[i]+'">'
//         +global_calibrate_borrowed_metadata_block[i]+'</option>');
// }
//
// let block_pk = global_calibrate_borrowed_metadata_block.indexOf($("#id_ns_block_standard_borrow_string").val());
// getTheStandardsFromThisFileBlock(block_pk);

// https://www.caveofprogramming.com/guest-posts/introduction-to-jquery-populating-creating-dynamic-dropdowns.html
// var CARS = new Array("Ford","Honda","Toyota","Suzuki");
//     $("#dropdown").find('option').remove();
//     for(i=0; i < CARS .length; i++){
//         $("#dropdown").append('<option value="'+CARS [i]+'">'+CARS [i]+'</option>');
//      }