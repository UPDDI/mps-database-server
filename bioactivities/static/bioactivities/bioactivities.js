// Ancient Cruft
$(document).ready(function () {

    /*
    $("th").each(function () {
        $(this).append('<input type="number" placeholder="priority">');
    });
    */

    $('#regenerate-data-cache-button').click(function() {
        $.ajax({
            type: 'GET',
            url: '/bioactivities/initialize_data/',
            dataType: 'json',
            success: function (data) {
                $("#the-table").pivotUI(data);
                alert('k');
            }
        });
    });

});
