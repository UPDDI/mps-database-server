$(document).ready(function() {
    // Prevent CSS conflict with Bootstrap
    // $.fn.button.noConflict();

    // Prevent accidental form submission
    $(document).on("keypress", ":input:not(textarea)", function(event) {
        return event.keyCode != 13;
    });

    var ids = [
        '#matrices',
        '#matrix_items'
    ];

    // var middleware_token = getCookie('csrftoken');
    var study_id = Math.floor(window.location.href.split('/')[5]);

    $.each(ids, function(index, table_id) {
        if ($(table_id)[0]) {
            $(table_id).DataTable({
                "iDisplayLength": 10,
                dom: 'B<"row">lfrtip',
                fixedHeader: {headerOffset: 50},
                responsive: false,
                // Initially sort on start date (descending), not ID
                "order": [[1, "asc"], [2, "desc"]],
                "aoColumnDefs": [
                    {
                        "bSortable": false,
                        "aTargets": [0]
                    },
                    {
                        "width": "10%",
                        "targets": [0]
                    }
                ]
            });
        }
    });

    // TODO CHANGE POPUP BEHAVIOR
    var ready_for_sign_off_section = $('#ready_for_sign_off_section');
    ready_for_sign_off_section.dialog({
       height:500,
       width:900,
       modal: true,
       buttons: {
            Send: function() {
                process_email_request();
                // $(this).dialog("close");
                $('.ui-dialog-buttonset').empty();
                $(this).dialog('option', 'buttons', {
                    Close: function() { $(this).dialog("close"); }
                });
            },
            Cancel: function() {
               $(this).dialog("close");
            }
       }
    });
    ready_for_sign_off_section.removeProp('hidden');

    $('#indicate_study_is_ready_for_sign_off').click(function() {
        ready_for_sign_off_section.dialog('open');
    });

    function process_email_request() {
        var data = {
            call: 'send_ready_for_sign_off_email',
            study: study_id,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };

        var serializedData = $('form').serializeArray();
        var formData = new FormData();
        $.each(serializedData, function (index, field) {
            formData.append(field.name, field.value);
        });

        $.each(data, function (index, contents) {
            formData.append(index, contents);
        });

        $.ajax({
            url: "/assays_ajax/",
            type: "POST",
            data: formData,
            dataType: 'json',
            cache: false,
            contentType: false,
            processData: false,
            success: function (json) {
                $('#ready_for_sign_off_form').remove();

                if (json.errors) {
                    $('#email_failure').show();
                    $('#email_failure_message').text('"' + json.errors + '"');
                }
                else {
                    $('#email_message').text('"' + json.message + '"');
                    $('#email_success').show();
                }
            },
            error: function (xhr, errmsg, err) {
                alert('An unknown error has occurred.');
            }
        });
    }
});
