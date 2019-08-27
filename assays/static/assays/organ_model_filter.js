window.device = null;
window.organ_model = null;
window.organ_model_protocol = null;

$(document).ready(function() {
    var protocol_display = $('#protocol_display');

    var organ_model_div = $('#organ_model_div');
    var protocol_div = $('#protocol_div');
    var variance_div = $('#variance_div');

    window.get_organ_models = function(device) {
        if (device) {
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_organ_models',
                    device: device,
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                success: function (json) {
                    var options = json.dropdown;
                    var current_value = window.organ_model.val();
                    window.organ_model[0].selectize.clear();
                    window.organ_model[0].selectize.clearOptions();
                    window.organ_model[0].selectize.addOption(options);
                    if (current_value) {
                        window.organ_model[0].selectize.setValue(current_value);
                    }
                    // else {
                    //     window.organ_model.val('');
                    // }

                    organ_model_div.show('fast');
                    window.get_protocols(window.organ_model.val());
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
        else {
            // Clear selections
            window.organ_model[0].selectize.clear();
            window.organ_model[0].selectize.clearOptions();
            window.organ_model_protocol[0].selectize.clear();
            window.organ_model_protocol[0].selectize.clearOptions();

            // Hide
            organ_model_div.hide('fast');
            protocol_div.hide('fast');
            variance_div.hide('fast');
        }
    };

    window.get_protocols = function(organ_model) {
        if (organ_model) {
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_protocols',
                    organ_model: organ_model,
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                success: function (json) {
                    var options = json.dropdown;
                    var current_value = window.organ_model_protocol.val();
                    window.organ_model_protocol[0].selectize.clear();
                    window.organ_model_protocol[0].selectize.clearOptions();
                    window.organ_model_protocol[0].selectize.addOption(options);
                    if (current_value) {
                        window.organ_model_protocol[0].selectize.setValue(current_value);
                    }

                    if (window.organ_model_protocol.val()) {
                        variance_div.show('fast');
                    }
                    else {
                        variance_div.hide('fast');
                    }

                    // Don't show an empty protocol div
                    if (options.length <= 1) {
                        protocol_div.hide('fast');
                    }
                    else {
                        protocol_div.show('fast');
                    }

                    window.display_protocol(window.organ_model_protocol.val());
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
        else {
            window.organ_model_protocol[0].selectize.clear();
            window.organ_model_protocol[0].selectize.clearOptions();

            // Hide
            protocol_div.hide('fast');
            variance_div.hide('fast');
        }
    };

    window.display_protocol = function(protocol) {
        if (protocol) {
            $.ajax({
                url: "/assays_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_protocol',
                    protocol: protocol,
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                success: function (json) {
                    if (json) {
                        protocol_display.attr('href', json.href);
                        protocol_display.text(json.file_name);
                        variance_div.show('fast');
                    }
                    else {
                        protocol_display.text();
                    }
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        }
        else {
            // Clear protocol display
            protocol_display.text('');
            protocol_display.attr('href', '');

            // Hide
            variance_div.hide('fast');
        }
    };
});
