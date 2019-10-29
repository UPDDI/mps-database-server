// SLOPPY: PREVENT DOUBLE SUBMISSION
$(document).ready(function () {
    var form_selector = $('form');

    if (form_selector[0]) {
        // On submit, disable all submit buttons
        form_selector.submit(function () {
            $(':submit').attr('disabled', 'disabled');
            return true;
        });
    }
});
