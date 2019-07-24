$(document).ready(function () {
    // Resolve anchors going to the incorrect location
    var offset = 60;

    $(".collapsible1, .collapsible2, .collapsible3").click(function() {
        var content = this.nextElementSibling;
        if ($(content).css("display") != "none") {
            $(content).css("display", "none");
        } else {
            $(content).css("display", "block");
        }
    });

    $('a').not("[href*='/']").click(function(event) {
        event.preventDefault();
        if ($($(this).attr('href'))[0]) {
            $('html, body').animate({
                scrollTop: $($(this).attr('href')).offset().top -offset
            }, 500);
            $($(this).attr('href')).find('button').next().first().css("display", "block");
        }
    });

    var initial_hash = window.location.hash;
    if (initial_hash) {
        $('html, body').animate({
            scrollTop: $(initial_hash).offset().top - offset
        }, 500);
        $(initial_hash).find('button').next().first().css("display", "block");
    }

    // Call datatables for glossary
    var about_studies_for_release_table = $('#about_studies_for_release_table').DataTable({
        dom: 'B<"row">lfrtip',
        "iDisplayLength": 10,
        responsive: true
    });
});
