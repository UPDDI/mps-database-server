$(document).ready(function () {
    // Check for existence of sidebar_wrapper on 100ms interval, moving it when found.
    var existCondition = setInterval(function() {
        console.log("Checking...");
        if ($('.sidebar_wrapper').length) {
            console.log("Exists!");
            clearInterval(existCondition);
            // $('#clustergrammer-sidebar-container').append($('.sidebar_wrapper').clone());
            // $('#container-id-1 .sidebar_wrapper').hide();
            $('.icons_section').remove();
            // $('.sidebar_wrapper').css('height', '725px');
        }
    })

    $(window).on('resize', function(){
        $('#container-id-1').css("width","90%");
    });
});
