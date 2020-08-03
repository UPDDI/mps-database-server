$(document).ready(function () {
    //
    // $('.has-popover').popover({'trigger':'hover'});

    let global_check_load = $("#check_load").html().trim();
    if (global_check_load === 'review') {
        // HANDY - to make everything on a page read only (for review page)
        $('.selectized').each(function() { this.selectize.disable() });
        $(':input').attr('disabled', 'disabled');
    }

    $("#id_omic_data_file").change(function () {
        document.getElementById("id_file_was_added_or_changed").checked = true;
    });
});

