$(document).ready(function () {

    // a cross reference between hashes (anchors)
    // make Lukes hashes the key then pull the value (Help page links)
    var anchor_xref = {
        // {# overview #}
        "": "#overview_section",
        // "": "#help_overview_background",
        "": "#help_overview_components",
        "": "#help_overview_organization",
        "": "#help_overview_sources",
        "": "#help_overview_features",
        "": "#help_overview_permission",

        "": "#global_database_tools_section",
        "": "#help_global_search",
        "": "#help_table_search",
        "": "#help_download_button",

        "": "#video_webinar_section",
        "": "#video_presentation_section",

        // {# features using study data #}
        "": "#study_data_feature_section",
        "": "#help_study_component",
        "": "#help_assay_data_viz",
        "": "#help_omic_data_viz",
        "": "#help_image_and_video",
        "": "#help_power_analysis",
        "": "#help_reproducibility_analysis",
        "": "#help_study_set",
        "": "#help_collaborator_group",
        "": "#help_access_group",
        "": "#help_pbpk_analysis",
        "": "#help_disease_portal",
        "": "#help_compound_report",
        "": "#help_reference",

        "": "#study_data_customization_section",
        "": "#help_custom_filtering_sidebar",
        "": "#help_custom_graphing_sidebar",
        "": "#help_custom_graphing_individual",

        // {# reference data #}
        "": "#non_study_data_feature_section",
        "": "#help_chemical_data",
        "": "#help_bioactivities",
        "": "#help_drug_trials",
        "": "#help_adverse_events",
        "": "#help_compare_adverse_events",
        "": "#help_heatmap_bioactivities",
        "": "#help_cluster_chemicals",

        // {# providing data #}
        "": "#study_editor_section",
        "": "#help_join_group",
        "": "#help_study_component_pointer",
        "": "#help_add_study",
        "": "#help_study_detail",
        "": "#help_study_treatment_group",
        "": "#help_chip_and_plate",
        "": "#help_target_and_method",
        "": "#help_data_upload",
        "": "#help_image_video",
        "": "#help_flags_and_notes",
        "": "#help_study_signoff",

        "": "#component_admin_section",
        "": "#glossary",

        // {# if all null, grabs last one #}
        "": "#help_overview_background",

    };

    var initial_hash = window.location.hash;
    var initial_hash_help = anchor_xref[initial_hash];
    if (!initial_hash_help) {
        initial_hash_help = '#help_overview_background';
    }

    var if_all_are_open_true = false;
    // need a listener click for after the search....
    //https://api.jquery.com/click/
    $(document).on('click', '#expand_all', function() {
    // $("#expand_all").click(function(){
        expand_or_close_all(selector, 'e');
        if_all_are_open_true = true;
    })
    $(document).on('click', '#close_all', function() {
    // $("#close_all").click(function(){
        expand_or_close_all(selector, 'c');
    })

    function expand_or_close_all(selector, what_doing) {
        //https://stackoverflow.com/questions/24844566/click-all-buttons-on-page
        // Get all buttons with the name and store in a NodeList called 'buttons'
        // console.log("selector "+selector)
        // console.log("what_doing "+what_doing)
        var buttons = document.getElementsByName('help_button');
        // Loop through and change display of the content
        for (var i = 0; i <= buttons.length; i++) {
            try {
                var content = buttons[i].nextElementSibling;
                change_display(content, what_doing);
            } catch {
            }
        }
    }

    $(document).on('click', '.help-collapsible', function() {
    // $(".help-collapsible").click(function() {
        change_display(this.nextElementSibling, 't');
    });

    $(document).on('click', '.video-collapsible', function() {
    // $(".help-collapsible").click(function() {
        change_display(this.nextElementSibling, 't');
    });

    function change_display(content, what_doing) {
        // console.log("content "+content)
        // console.log("what_doing "+what_doing)
        if (what_doing === 't') {
            if ($(content).css("display") != "none") {
                $(content).css("display", "none");
                if_all_are_open_true = false;
            } else {
                $(content).css("display", "block");
            }
        } else if (what_doing === 'e') {
            $(content).css("display", "block");
        } else {
            $(content).css("display", "none");
            if_all_are_open_true = false;
        }
    }

    // START SEARCH SECTION

    var selector = "#realTimeContents";
    var searchTerm = null;

    // mark.js and https://jsfiddle.net/julmot/973gdh8g/
    //make them disabled on load
    $('#search_next').attr('disabled', 'disabled');
    $('#search_prev').attr('disabled', 'disabled');

    function change_search_ables_to_search(which) {
        if (which) {
            $('#search_next').attr('disabled', 'disabled');
            $('#search_prev').attr('disabled', 'disabled');
            $('#search_gooo').removeAttr('disabled');
        } else {
            $('#search_next').removeAttr('disabled');
            $('#search_prev').removeAttr('disabled');
            $('#search_gooo').attr('disabled', 'disabled');
        }
    }

    $(document).on('click', '#caseSensitive', function() {
    // $("#caseSensitive").click(function() {
        if (searchTerm) {
            // not null
            gooo();
        }
        change_search_ables_to_search(true);
    });

    // consider on input
    document.getElementById("search_term").onfocus = function() {
        myFunction()
    };

    function myFunction() {
        change_search_ables_to_search(true);
    }

    // mark.js and https://www.jquery-az.com/jquery/demo.php?ex=153.0_3
    // the input field
    var $input = $("input[type='search']");
    // clear button
    var $clearBtn = $("button[data-search='clear']");
    // prev button
    var $prevBtn = $("button[data-search='prev']");
    // next button
    var $nextBtn = $("button[data-search='next']");
    // the context where to search
    var $content = $(".content");
    // jQuery object to save <mark> elements
    var $results;
    // the class that will be appended to the current
    // focused element
    var currentClass = "current";
    // top offset for the jump (the search bar)
    var offsetTop = 200;
    // the current index of the focused element
    var currentIndex = 0;

    /**
    * Jumps to the element matching the currentIndex
    */
    function jumpTo() {
        if ($results.length) {
            var position;
            var $current = $results.eq(currentIndex);
            $results.removeClass(currentClass);
            if ($current.length) {
                $current.addClass(currentClass);
                position = $current.offset().top - offsetTop;
                window.scrollTo(0, position);
            }
        }
    }

    /**
    * Searches for the entered keyword in the
    * specified context on input
    */
    // $input.on("input", function() {
    $(document).on('click', '#search_gooo', function() {
        gooo();
    });

    function gooo() {
        change_search_ables_to_search(false);

        var caseSensitive = false;
        if ($('#caseSensitive').prop('checked')){
            caseSensitive = true;
        }

        searchTerm = $("input[name='keyword']").val();

        // console.log("searchTerm ", searchTerm)

        if (searchTerm.length === 0) {
            change_search_ables_to_search(true);
            removeOldHighlights();
            alert("Search box is empty");
        }
        else {
            // open all the collapsibles if they are not already open
            // console.log("if_all_are_open_true ", if_all_are_open_true)
            if (!if_all_are_open_true) {
                expand_or_close_all(selector, 'e');
            }

            // when acrossElements = true, the count of mark tags might be greater than actual # matches
            // because multiple <mark> tags are created to keep tags opening and closing correctly
            // var searchVal = this.value;
            var searchVal = searchTerm
            $content.unmark({
                done: function () {
                    $content.mark(searchVal, {
                        separateWordSearch: false,
                        caseSensitive: caseSensitive,
                        acrossElements: true,
                        done: function () {
                            $results = $content.find("mark");
                            currentIndex = 0;
                            jumpTo();
                        }
                    });
                }
            });
            if ($results.length == 0) {
                alert("Could not find a match");
                change_search_ables_to_search(true);
            }
        }
    }

    function removeOldHighlights() {
        change_search_ables_to_search(true);
        $content.unmark();
        $input.val("").focus();
    }

    /**
    * Clears the search
    */
    $clearBtn.on("click", function() {
        change_search_ables_to_search(true);
        $content.unmark();
        $input.val("").focus();
    });

    /**
    * Next and previous search jump to
    */
    $nextBtn.add($prevBtn).on("click", function() {
        change_search_ables_to_search(false);
        if ($results.length) {
            currentIndex += $(this).is($prevBtn) ? -1 : 1;
            if (currentIndex < 0) {
                currentIndex = $results.length - 1;
            }
            if (currentIndex > $results.length - 1) {
                currentIndex = 0;
            }
            jumpTo();
        }
    });

    // END SEARCH SECTION

    // START GLOSSARY SECTION
    var offset = 110;

    $('a').not("[href*='/']").click(function(event) {
        event.preventDefault();
        if ($($(this).attr('href'))[0]) {
            $('html, body').animate({
                scrollTop: $($(this).attr('href')).offset().top - offset
            }, 500);
            $($(this).attr('href')).find('button').next().first().css("display", "block");
        }
    });

    var _alphabetSearch = '';

    $.fn.dataTable.ext.search.push(function(settings, searchData ) {
        // fires when click a letter
        if (!_alphabetSearch) {
            return true;
        }

        else if (searchData[0].charAt(0) === _alphabetSearch) {
            return true;
        }

        else if (searchData[0].charAt(0).toUpperCase() === _alphabetSearch) {
            return true;
        }

        return false;
    });

    // Call datatables for glossary
    var glossary_table = $('#glossary_table').DataTable({
        dom: '<Bl<"row">frptip>',
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

    for(var i=0; i<26; i++) {
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
        // fires when click a letter (for each glossary term)
        alphabet.find('.active').removeClass('active');
        $(this).addClass('active');
        _alphabetSearch = $(this).attr('data-letter');
        glossary_table.draw();
    });
    // END GLOSSARY SECTION

    // after the page is loaded, change location on page

    console.log("ih ", initial_hash)
    console.log("ihh ", initial_hash_help)
    animate_scroll_hash(initial_hash_help);
    function animate_scroll_hash(anchor) {
        // if the anchor is NOT on the page, do not cause and error in the console
        // this error causes the glossary NOT to display!!!
        console.log("h ",anchor)
        if ($(anchor).length)
        {
            $('html, body').animate({
                scrollTop: $(anchor).offset().top - offset
            }, 500);
            $(anchor).find('button').next().first().css("display", "block");
        }
    }
});


//HANDY - iterate vrs first - keep for reference
    // //Remove the spans and old matches
    // $span = $('#realTimeContents .match');
    // // NO NO NO - this does not iterate as expected, it just pulls one - $span.replaceWith($span.html());
    // // the following makes sure to iterate through
    // $span.each(function() {
    //     $(this).replaceWith($(this).html());
    // });

    //var help_offset = 200;
    // var buttons = null;
    // var searchTermRegEx = null;
    // var caseSensitive_flag = "ig";
    // var help_buttons = null;
    // var matches = null;
    // var match_index = 0;
    // var matches_length = 0;

// HANDY - Some references that ended up not using, but keep in case need again
// https://www.aspforums.net/Threads/211834/How-to-search-text-on-web-page-similar-to-CTRL-F-using-jQuery/
// http://jsfiddle.net/wjLmx/23/

// HANDY - References for making a callback
// https://www.aspforums.net/Threads/211834/How-to-search-text-on-web-page-similar-to-CTRL-F-using-jQuery/
// http://jsfiddle.net/wjLmx/23/
// https://codeburst.io/javascript-what-the-heck-is-a-callback-aba4da2deced

    // function findMatches_search0(callback1) {
    //     // console.log("searchTermRegEx "+searchTermRegEx)
    //
    //     // matches = $(selector).text().match(searchTermRegEx);
    //     $('.mark-content').mark(searchTerm, options);
    //     matches = $(".mark").map(function() {
    //         return this.innerHTML;
    //     }).get();
    //
    //     callback1();
    // }
    //
    // function afterFindMatches_search1() {
    //     if (!matches) {
    //         matches = [];
    //     }
    //     matches_length = matches.length;
    //     // console.log("step 1 matches "+matches)
    //     // console.log("step 1 number matches = "+matches_length)
    //
    //     if (matches != null && matches_length > 0) {
    //         // unique_matches = matches.filter(function(itm, i, a) {
    //         //     return i == matches.indexOf(itm);
    //         // });
    //         // if (searchTerm === "&") {
    //         //     searchTerm = "&amp;";
    //         //     searchTermRegEx = new RegExp(searchTerm, caseSensitive_flag);
    //         // }
    //         // console.log("searchTerm ",searchTerm)
    //         labelMatchSpan_search2(continueFunction_search3);
    //     }
    // }

    //
    // function continueFunction_search3() {
    //     // the previous function replaced with the search term, fix to match the original case
    //     // if ($('.match').length != matches_length) {
    //     //     alert("there is a mismatch in the counting....")
    //     // }
    //     if ($('.mark').length != matches_length) {
    //         alert("there is a mismatch in the counting....")
    //     }
    //     $('.match').each(function (index, currentElement) {
    //         currentElement.innerHTML = matches[index];
    //         $(this).html(matches[index]);
    //     });
    //     // $('.match:first').addClass('highlighted');
    //     $('.match:first').addClass('mark');
    //     match_index = 0;
    //     // console.log("in search 3 - getting ready to highlight")
    //     // when the search is clicked - finds the first occurrence
    //     // if ($('.highlighted:first').length) {
    //     if ($('.mark:first').length) {
    //         //if match found, scroll to where the first one appears
    //         // this did not work for study summary....do not know why
    //         // $(window).scrollTop($('.highlighted:first').position().top - help_offset);
    //         $('html, body').animate({
    //             // scrollTop: $('.highlighted:visible:first').offset().top - help_offset
    //             // scrollTop: $('.mark:visible:first').offset().top - help_offset
    //             $current = $('.match').eq(match_index);
    //             position = $current.offset().top - offsetTop;
    //             window.scrollTo(0, position);
    //         }, 400);
    //     }
    // }
    //
    // $(document).on('click', '#search_next', function () {
    // // $("#search_next").click(function() {
    //     // $('.next_h').off('click').on('click', function () {
    //     match_index =  match_index + 1;
    //     if (match_index >= $('.match').length) {
    //         match_index = 0;
    //     }
    //     $('.match').removeClass('highlighted');
    //     $('.match').eq(match_index).addClass('highlighted');
    //     $('html, body').animate({
    //         // scrollTop: $('.highlighted:visible:first').offset().top - help_offset
    //         scrollTop: $('.mark:visible:first').offset().top - help_offset
    //     }, 400);
    // });
    //
    // $(document).on('click', '#search_prev', function () {
    // // $("#search_prev").click(function() {
    //     // $('.previous_h').off('click').on('click', function () {
    //     match_index = match_index - 1;
    //     if (match_index < 0) {
    //         match_index = $('.match').length - 1;
    //     }
    //     $('.match').removeClass('highlighted');
    //     $('.match').eq(match_index).addClass('highlighted');
    //     $('html, body').animate({
    //         scrollTop: $('.highlighted:visible:first').offset().top - help_offset
    //     }, 400);
    // });