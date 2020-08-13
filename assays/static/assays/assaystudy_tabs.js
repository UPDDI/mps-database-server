// Adds the active class to the current interface
$(document).ready(function() {
    var current_interface = window.location.href.split('/')[6];

    // Get the li in question and make it active
    $('li[data-interface="' + current_interface + '"]')
        .addClass('active')
        // Find the anchor and make it reference the current page
        .find('a').attr('href', '#');

    if (!current_interface || current_interface === '#')
    {
        $('li[data-interface="details"]')
        .addClass('active')
        // Find the anchor and make it reference the current page
        .find('a').attr('href', '#');
    }

    var redirect_confirm = $('#post_submission_override_confirm');
    var redirect_url = $('#id_post_submission_url_override');
    var study_tabs_section = $('#study_tabs_section');
    redirect_confirm.dialog({
        width: 500,
        height:300,
        modal: true,
        buttons: [
        {
            text: 'Save',
            click: function() {
                // Ignore overwrite request
                if (window.OVERWRITE) {
                    window.OVERWRITE.skip_confirmation = true;
                }
                $('#submit').trigger('click');
            }
        },
        {
            text: 'Do Not Save',
            click: function() {
                // Ignore redirect note
                if (window.OVERRIDE) {
                    window.OVERRIDE.skip_confirmation = true;
                }
                $(location).attr('href', redirect_url.val());
            },
            class: 'btn btn-warning'
        },
        {
            text: 'Cancel',
            click: function() {
               $(this).dialog("close");
            },
            class: 'btn btn-danger'
        }],
        close: function() {
            $.ui.dialog.prototype.options.close();

            // Clear redirect url
            redirect_url.val('');
        },
    });
    redirect_confirm.removeProp('hidden');

    // Handle previous button
    $('#submit_previous_button').click(function() {
        // Append next url to post_submission_url_override
        redirect_url.val(
            study_tabs_section.find('li.active').prev('li').find('a').attr('href')
        );

        // Contrived for formless tabs
        // Just redirect if there is no form
        // SUBJECT TO REVISION
        if (!$('form')[0]) {
            $(location).attr('href', redirect_url.val());
            // DO NOT OPEN DIALOG
            return;
        }

        if (redirect_url.val() !== '#') {
            redirect_confirm.dialog('open');
        }
    });

    $('#submit_next_button').click(function() {
        // Append next url to post_submission_url_override
        redirect_url.val(
            study_tabs_section.find('li.active').next('li').find('a').attr('href')
        );

        // Contrived for formless tabs
        // Just redirect if there is no form
        // SUBJECT TO REVISION
        if (!$('form')[0]) {
            $(location).attr('href', redirect_url.val());
            // DO NOT OPEN DIALOG
            return;
        }

        if (redirect_url.val() !== '#') {
            redirect_confirm.dialog('open');
        }
        else {
            // VERY ODD
            let popup_ref = $('div[aria-describedby="post_submission_override_confirm"]');
            popup_ref.find('.btn-warning').remove();
            popup_ref.find('.alert-warning').find('span').eq(2).text('Are you prepared to save this Study and edit its Groups?');
            redirect_confirm.dialog('open');
        }
        // CONTRIVANCE FOR STUDY ADD
        // THIS WOULD JUST SUBMIT, INSTEAD LET US GIVE A REVISED POPUP?
        // else {
        //     $('#submit').trigger('click');
        // }
    });
});
