$(document).ready(function () {
    // Check for existence of sidebar_wrapper on 100ms interval, moving it when found.
    var existCondition = setInterval(function() {
        console.log("Checking...");
        if ($('.sidebar_wrapper').length) {
            console.log("Exists!");
            clearInterval(existCondition);
            $('#clustergrammer-sidebar-container').append($('.sidebar_wrapper'));
            $('.icons_section').remove();
            $('.sidebar_wrapper').css('height', '725px');
        }
    })
});
