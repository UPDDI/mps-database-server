$(document).ready(function () {
    // Resolve anchors going to the incorrect location
    var offset = 60;

    $(".collapsible1, .collapsible2, .collapsible3, .collapsible4").click(function() {
        var content = this.nextElementSibling;
        if ($(content).css("display") != "none") {
            $(content).css("display", "none");
        } else {
            $(content).css("display", "block");
        }
    });

    //https://api.jquery.com/click/
    $("#expand_all").click(function(){
        //alert( "Handler for .click() called." );
        //console.log("clicked the button")
        //https://stackoverflow.com/questions/24844566/click-all-buttons-on-page
        // Get all buttons with the name 'all' and store in a NodeList called 'buttons'
        var buttons = document.getElementsByName('my_buttons');
        // Loop through and call the click() function on each button
        for(var i = 0; i <= buttons.length; i++)
           //console.log(i)
           buttons[i].click();
           var content = this.nextElementSibling;
           $(content).css("display", "block");
    })

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

    var _alphabetSearch = '';

    $.fn.dataTable.ext.search.push(function(settings, searchData ) {
        if (!_alphabetSearch) {
            return true;
        }

        else if (searchData[0].charAt(0) === _alphabetSearch) {
            return true;
        }

        return false;
    });

    // Call datatables for glossary
    var glossary_table = $('#glossary_table').DataTable({
        dom: 'B<"row">lfrtip',
        "iDisplayLength": 10,
        responsive: true
    });

    var alphabet = $('<div class="alphabet"/>').append('Search: ');

    // Add none
    $('<a/>')
        .attr('data-letter', '')
        .attr('role', 'button')
        .html('None')
        .addClass('btn btn-sm')
        .appendTo(alphabet);

    for(var i=0 ; i<26 ; i++) {
        var letter = String.fromCharCode(65 + i);

        $('<a/>')
            .attr('data-letter', letter)
            .attr('role', 'button')
            .html(letter)
            .addClass('btn btn-sm')
            .appendTo(alphabet);
    }

    alphabet.insertBefore(glossary_table.table().container());

    alphabet.on('click', 'a', function() {
        alphabet.find('.active').removeClass('active');
        $(this).addClass('active');

        _alphabetSearch = $(this).attr('data-letter');
        glossary_table.draw();
    });
});
