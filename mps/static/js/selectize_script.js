// CRUDE GLOBAL
window.SELECTIZE = {
    refresh_dropdown: null
};

// Experiment with dropdown searching using selectize.js
$(document).ready(function () {
    $('select').each(function(i, obj){
        var current_select = $(obj);
        if (!current_select.parent().hasClass('no-selectize') && !current_select.hasClass('no-selectize')) {
            current_select.selectize({
                diacritics: true
            });
        }
    });

    window.SELECTIZE.refresh_dropdown = function(
            current_app,
            current_model,
            new_pk,
            new_name
    ) {
        // Descendent selectors are bad
        // var current_selectize_input = dropdown.find('input');
        // var current_id = current_selectize_input.attr('id').replace('-selectized', '');
        // var current_input = $('#' + current_id);
        var current_inputs = $('select[data_app="' + current_app + '"][data_model="' + current_model + '"]');

        // Get the new dropdown
        // Start spinner
        var options = [
            {
                value: new_pk,
                text: new_name,
            }
        ];

        current_inputs.each(function() {
            var current_value = $(this).val();

            var current_selectize = this.selectize;

            current_selectize.blur();

            current_selectize.addOption(options);

            // SLOPPY! NEED TO PREVENT INLINES FROM EXPLODING
            if (new_pk && !current_value && !$(this).parent().parent().hasClass('inline')) {
                current_selectize.setValue(new_pk);
            }
            else if (current_value) {
                current_selectize.setValue(current_value);
            }
        });
    }

    // SLOPPY TRIGGERS FOR REFRESHING DROPDOWNS
    // DUMB, BAD
    // Excessive if there is only going to be the one new one?
    // window.SELECTIZE.refresh_dropdown = function(
    //         current_app,
    //         current_model,
    //         new_pk,
    //         new_value
    // ) {
    //     // Descendent selectors are bad
    //     // var current_selectize_input = dropdown.find('input');
    //     // var current_id = current_selectize_input.attr('id').replace('-selectized', '');
    //     // var current_input = $('#' + current_id);
    //     var current_inputs = $('select[data_app="' + current_app + '"][data_model="' + current_model + '"]');
    //
    //     // Get the new dropdown
    //     // Start spinner
    //     window.spinner.spin(
    //         document.getElementById("spinner")
    //     );
    //     $.ajax({
    //         url: "/assays_ajax/",
    //         type: "POST",
    //         dataType: "json",
    //         data: {
    //             call: 'fetch_dropdown',
    //             csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
    //             app: current_app,
    //             model: current_model,
    //         },
    //     })
    //     .done(function (json) {
    //         // Stop spinner
    //         window.spinner.stop();
    //
    //         var options = json.dropdown;
    //
    //         current_inputs.each(function() {
    //             var current_value = $(this).val();
    //
    //             var current_selectize = this.selectize;
    //
    //             current_selectize.blur();
    //
    //             current_selectize.clear();
    //             current_selectize.clearOptions();
    //
    //             current_selectize.addOption(options);
    //
    //             // SLOPPY! NEED TO PREVENT INLINES FROM EXPLODING
    //             if (new_pk && !current_value && !$(this).parent().parent().hasClass('inline')) {
    //                 current_selectize.setValue(new_value);
    //             }
    //             else if (current_value) {
    //                 current_selectize.setValue(current_value);
    //             }
    //         });
    //     })
    //     .fail(function (xhr, errmsg, err) {
    //         // Stop spinner
    //         window.spinner.stop();
    //
    //         console.log(xhr.status + ": " + xhr.responseText);
    //     });
    // }


    // TESTING: Comment out for the moment
    // $('.selectize-input').click(function() {
    //     // Descendent selectors are bad
    //     var current_selectize_input = $(this).find('input');
    //     var current_id = current_selectize_input.attr('id').replace('-selectized', '');
    //     var current_input = $('#' + current_id);
    //     var current_selectize = current_input[0].selectize;
    //
    //     // Get the new dropdown
    //     // Start spinner
    //     window.spinner.spin(
    //         document.getElementById("spinner")
    //     );
    //     $.ajax({
    //         url: "/assays_ajax/",
    //         type: "POST",
    //         dataType: "json",
    //         data: {
    //             call: 'fetch_dropdown',
    //             csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
    //             app: current_input.attr('data_app'),
    //             model: current_input.attr('data-model'),
    //         },
    //     })
    //     .done(function (json) {
    //         // Stop spinner
    //         window.spinner.stop();
    //
    //         var options = json.dropdown;
    //         var current_value = current_input.val();
    //         current_selectize.clear();
    //         current_selectize.clearOptions();
    //
    //         current_selectize.addOption(options);
    //
    //         if (current_value) {
    //             current_selectize.setValue(current_value);
    //         }
    //
    //         current_selectize.blur();
    //         current_selectize.focus();
    //     })
    //     .fail(function (xhr, errmsg, err) {
    //         // Stop spinner
    //         window.spinner.stop();
    //
    //         console.log(xhr.status + ": " + xhr.responseText);
    //     });
    // });
});
