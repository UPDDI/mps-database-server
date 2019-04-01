//Get token
// var middleware_token = getCookie('csrftoken');
// DEPRECATED: SLATED FOR DELETION

function whittle(master,master_id,subject,next_model,next_filter) {
    // all_options is actually a deferred promise so that the variable is not assigned before AJAX over
    var all_options = new $.Deferred();

    if (master && master_id && subject) {
        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            dataType: "json",
            data: {
                call: 'fetch_dropdown',

                master: master,
                master_id: master_id,
                subject: subject,
                next_model: next_model,
                next_filter: next_filter,

                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            },
            success: function (json) {
                all_options.resolve(json.dropdown);
            },
            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    // If invalid input, for whatever reason
    else {
        all_options.resolve('<option value="">---------</option>');
    }

    return all_options.promise();
}
