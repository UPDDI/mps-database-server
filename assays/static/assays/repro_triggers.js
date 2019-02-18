$(document).ready(function () {
    $('#repro_options_tables')
        .find('input, select')
        .change(function() {
            // Odd, perhaps innapropriate!
            window.GROUPING.refresh_wrapper();
        });
});
