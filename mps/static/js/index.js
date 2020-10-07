$(function() {
    var initial = $('#id_app').val();

    if (initial == 'Bioactivities') {
        $("#bioactivities_search").show();
        $("#search_bar").hide();
    }

    $('#search_options li').click(function(e) {
        $("#bioactivities_search").show("slow");
        $("#search_bar").hide("slow");
        $("#id_app").val("Bioactivities");
    });

    $('#back').click(function() {
        $("#bioactivities_search").hide("slow");
        $("#search_bar").show("slow");
        $("#id_app").val("Global");
    });

    $("#id_search_term").autocomplete({
        source: function (request, response) {
            $.ajax({
                url: "/search_ajax/",
                type: "POST",
                dataType: "json",
                data: {
                    call: 'fetch_global_search_suggestions',
                    text: request.term,
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                success: function (json) {
                    response(json);
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        },
        minLength: 2
    });

    // Hard coded at the moment
    // if (!localStorage.getItem('hide_banner')) {
    //     $('#webinar_banner').show('slow');
    // }

    // $('#close_webinar_banner').click(function() {
    //     $('#webinar_banner').hide('slow');
    //     localStorage.setItem('hide_banner', 'TRUE');
    // });
});
