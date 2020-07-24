$(document).ready(function () {
    let global_check_load = $("#check_load").html().trim();
    if (global_check_load === 'review') {
        // HANDY - to make everything on a page read only
        $('.selectized').each(function() { this.selectize.disable() });
        $(':input').attr('disabled', 'disabled');
    }
});

