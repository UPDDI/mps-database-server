$(document).ready(function () {
    const group_selector = $('#id_group');
    const center_name_selector = $('#center_name');
    const image_selector = $('#id_image');
    const image_display_selector = $('#image_display');
    const current_image_display_selector = $('#current_display');

    const disease_model_selector = $('#id_disease');
    const diseases_section_selector = $('#diseases_section');

    function get_center_id() {
        if (group_selector.val()) {
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_center_id',
                    id: group_selector.val(),
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                success: function (json) {
                    center_name_selector.html(json.name + ' (' + json.center_id + ')');
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
        else {
            center_name_selector.html('');
        }
    }

    // Need to have condition for adding vs. changing data
    get_center_id();

    // Needs an AJAX call to get centerID
    group_selector.change(function (evt) {
        get_center_id();
    });

    // Change image preview as necessary
    image_selector.change(function() {
        IMAGES.display_image(image_selector, image_display_selector, current_image_display_selector);
    });

    // PBPK
    // var is more or less deprecated
    var pbpk_trigger = $('#id_pbpk');
    var pbpk_section = $('#pbpk_section');

    var pbpk_steady_state_radio = $('#id_pbpk_steady_state_radio');
    var pbpk_bolus_radio = $('#id_pbpk_bolus_radio');

    var pbpk_steady_state = $('#id_pbpk_steady_state');
    var pbpk_bolus = $('#id_pbpk_bolus');

    var total_device_volume = $('#total_device_volume_container');
    var flow_rate = $('#flow_rate_container');

    if (pbpk_steady_state.prop('checked')) {
        pbpk_trigger.prop('checked', true);
        pbpk_bolus.prop('checked', false);
        pbpk_steady_state_radio.prop('checked', true);
    }
    else if (pbpk_bolus.prop('checked')) {
        pbpk_trigger.prop('checked', true);
        pbpk_steady_state.prop('checked', false);
        pbpk_bolus_radio.prop('checked', true);
    }

    pbpk_trigger.change(function() {
        // Toggle radio buttons
        if ($(this).prop('checked')) {
            pbpk_section.show('slow');
            pbpk_steady_state_radio.trigger('change');
            pbpk_bolus_radio.trigger('change');

            // TERRIBLE: UNCCHECK AND DISABLE ALL OTHER STUDY TYPES
            $('#id_toxicity').prop('checked', false);
            $('#id_efficacy').prop('checked', false);
            $('#id_disease').prop('checked', false);
            $('#id_cell_characterization').prop('checked', false);
            $('#id_omics').prop('checked', false);

            $('#id_toxicity').prop('disabled', true);
            $('#id_efficacy').prop('disabled', true);
            $('#id_disease').prop('disabled', true);
            $('#id_cell_characterization').prop('disabled', true);
            $('#id_omics').prop('disabled', true);
        }
        else {
            pbpk_section.hide('slow');
            pbpk_steady_state.prop('checked', false);
            pbpk_bolus.prop('checked', false);

            // ENABLE ALL OTHER STUDY TYPES
            $('#id_toxicity').prop('disabled', false);
            $('#id_efficacy').prop('disabled', false);
            $('#id_disease').prop('disabled', false);
            $('#id_cell_characterization').prop('disabled', false);
            $('#id_omics').prop('disabled', false);
        }
    }).trigger('change');

    pbpk_steady_state_radio.change(function() {
        if (pbpk_trigger.prop('checked') && $(this).prop('checked')) {
            pbpk_steady_state.prop('checked', true);
            pbpk_bolus.prop('checked', false);
            flow_rate.show('slow');
            total_device_volume.hide('slow');
        }
    }).trigger('change');

    pbpk_bolus_radio.change(function() {
        if (pbpk_trigger.prop('checked') && $(this).prop('checked')) {
            pbpk_steady_state.prop('checked', false);
            pbpk_bolus.prop('checked', true);
            flow_rate.hide('slow');
            total_device_volume.show('slow');
        }
    }).trigger('change');

    // Handling for diseases
    disease_model_selector.change(function() {
        if ($(this).prop('checked')) {
            diseases_section_selector.show('slow');
        }
        else {
            diseases_section_selector.hide('slow');
        }
    }).trigger('change');
});
