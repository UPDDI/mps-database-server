$(document).ready(function () {
    $('#sidebar')
        .find('input, select')
        .change(function() {
            // Odd, perhaps innapropriate!
            window.GROUPING.refresh_wrapper();
        });
});
