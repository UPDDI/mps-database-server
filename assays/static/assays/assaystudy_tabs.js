// Adds the active class to the current interface
$(document).ready(function() {
    var current_interface = window.location.href.split('/')[6];

    // Get the li in question and make it active
    $('li[data-interface="' + current_interface + '"]')
        .addClass('active')
        // Find the anchor and make it reference the current page
        .find('a').attr('href', '#');

    console.log(current_interface);

    if (!current_interface || current_interface === '#')
    {
        $('li[data-interface="details"]')
        .addClass('active')
        // Find the anchor and make it reference the current page
        .find('a').attr('href', '#');
    }
});
