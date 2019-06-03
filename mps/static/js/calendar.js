// WHY IS THERE THIS FILE *AND* datepicker.js?
$(document).ready(function () {
    // OLD METHOD
    $.each($('.calendar-container'), function() {
        // Setup date picker
        var date = $(this).find('input');
        var curr_date = date.val();
        date.datepicker();
        date.datepicker("option", "dateFormat", "yy-mm-dd");
        date.datepicker("setDate", curr_date);
    });
    // SUPERIOR METHOD
    $.each($('.datepicker-input'), function() {
        // Setup date picker
        var date = $(this);
        var curr_date = date.val();
        date.datepicker();
        date.datepicker("option", "dateFormat", "yy-mm-dd");
        date.datepicker("setDate", curr_date);
    });
});
