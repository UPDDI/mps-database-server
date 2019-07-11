$(document).ready(function () {
    var group_selector = $('#id_group');
    var center_name_selector = $('#center_name');
    var image_selector = $('#id_image');
    var image_display_selector = $('#image_display');
    var current_image_display_selector = $('#current_display');

    // MOVED TO consolidated js
    // var organ_model = $('#id_organ_model');
    // var protocol = $('#id_organ_model_protocol');
    //
    // window.organ_model = organ_model;
    // window.organ_model_protocol = protocol;

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

    // Handling Device flow
    // Make sure global var exists before continuing
    // if (window.get_organ_models) {
    //     organ_model.change(function() {
    //         // Get and display correct protocol options
    //         window.get_protocols(organ_model.val());
    //     });
    //
    //     window.get_protocols(organ_model.val());
    //
    //     // NOTE THAT THIS IS TRIGGERED ON LOAD
    //     protocol.change(function() {
    //         window.MASS_EDIT.set_new_protocol();
    //     }).trigger('change');
    // }
});
