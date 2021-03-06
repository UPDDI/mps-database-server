$(document).ready(function () {

    var glossary_spans_on = true;
    //after done editing, do this **change-star (uncomment the next line to make the text black instead of glossary red
    strip_the_glossary_spans();

    var set_hash_default = '#search_help_page_section';
    var incoming_hash = window.location.hash;
    var help_hash = set_hash_default;
    //navigate_to_anchor function is called at the bottom so all loading happens first

    var if_all_are_open_true = false;
    // need a listener click for after the search....
    //https://api.jquery.com/click/
    $(document).on('click', '#expand_all', function() {
    // $('#expand_all').click(function(){
        expand_or_close_all(selector, 'e');
        if_all_are_open_true = true;
    })
    $(document).on('click', '#close_all', function() {
    // $('#close_all').click(function(){
        expand_or_close_all(selector, 'c');
    })

    function expand_or_close_all(selector, what_doing) {
        //https://stackoverflow.com/questions/24844566/click-all-buttons-on-page
        // Get all buttons with the name and store in a NodeList called 'buttons'
        // console.log('selector '+selector)
        // console.log('what_doing '+what_doing)
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
    // $('.help-collapsible').click(function() {
        change_display(this.nextElementSibling, 't');
    });

    $(document).on('click', '.video-collapsible', function() {
    // $('.help-collapsible').click(function() {
        change_display(this.nextElementSibling, 't');
    });

    function change_display(content, what_doing) {
        // console.log('content '+content)
        // console.log('what_doing '+what_doing)
        if (what_doing === 't') {
            if ($(content).css('display') != 'none') {
                $(content).css('display', 'none');
                if_all_are_open_true = false;
            } else {
                $(content).css('display', 'block');
            }
        } else if (what_doing === 'e') {
            $(content).css('display', 'block');
        } else {
            $(content).css('display', 'none');
            if_all_are_open_true = false;
        }
    }

    // START SEARCH SECTION
    var selector = '#realTimeContents';
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
    // $('#caseSensitive').click(function() {
        if (searchTerm) {
            // not null
            gooo();
        }
        change_search_ables_to_search(true);
    });

    // consider on input
    document.getElementById('search_term').onfocus = function() {
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
    var $content = $('.content');
    // jQuery object to save <mark> elements
    var $results;
    // the class that will be appended to the current
    // focused element
    var currentClass = 'current';
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
    // $input.on('input", function() {
    $(document).on('click', '#search_gooo', function() {
        gooo();
    });

    function gooo() {
        if (glossary_spans_on) {
            strip_the_glossary_spans();
        }

        change_search_ables_to_search(false);

        var caseSensitive = false;
        if ($('#caseSensitive').prop('checked')){
            caseSensitive = true;
        }

        searchTerm = $("input[name='keyword']").val();

        // console.log('searchTerm ', searchTerm)

        if (searchTerm.length === 0) {
            change_search_ables_to_search(true);
            removeOldHighlights();
            alert('Search box is empty');
        }
        else {
            // open all the collapsibles if they are not already open
            // console.log('if_all_are_open_true ', if_all_are_open_true)
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
                            $results = $content.find('mark');
                            currentIndex = 0;
                            jumpTo();
                        }
                    });
                }
            });

            // $('#glossary_table_filter')[0].childNodes[0].childNodes[1];
            //same as $('#glossary_table_filter').children().children()[0];
            //same as $('#glossary_table_filter :input');

            $('#glossary_table_filter :input').val(searchTerm).trigger('input');

            // another option, but have to to through all the inputs and is much longer....
            // var glossary_search_box = null;
            // $('input:input').each(function() {
            //     if ($(this)[0].getAttribute('type') === 'search' && $(this).attr("id") != 'search_term') {
            //         glossary_search_box = $(this);
            //         glossary_search_box.val(searchTerm);
            //         glossary_search_box.trigger('input');
            //     }
            // });

            if ($results.length == 0) {
                // alert('Could not find a match in the main body of the help. Try searching the Glossary.');
                animate_scroll_hash('#glossary');
                change_search_ables_to_search(true);
            }
        }
    }

    function removeOldHighlights() {
        change_search_ables_to_search(true);
        $content.unmark();
        $input.val('').focus();
    }

    /**
    * Clears the search
    */
    $clearBtn.on('click', function() {
        change_search_ables_to_search(true);
        $content.unmark();
        $input.val('').focus();

        $('#glossary_table_filter :input').val(null).trigger('input');

    });

    /**
    * Next and previous search jump to
    */
    $nextBtn.add($prevBtn).on('click', function() {
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

    // this is in the glossary section but is general
    $('a').not("[href*='/']").click(function(event) {
        event.preventDefault();
        // console.log("$(this).hasClass('help-anchor') ",$(this).hasClass('help-anchor'))
        if ($(this).hasClass('help-anchor')) {
            //this will happen if the user clicks on link to Help from Help
            // previously did this, but do not need since put in the a's $('.help-anchor').click(function (event) {
            help_hash = $(this).attr('href');
            if (help_hash.indexOf('help2') >= 0) {
                change_display($('#help2_study_component_feature')[0].nextElementSibling, 'e');
            }
            navigate_to_anchor('in');
        } else {
            if ($($(this).attr('href'))[0]) {
                $('html, body').animate({
                    scrollTop: $($(this).attr('href')).offset().top - offset
                }, 500);
                $($(this).attr('href')).find('button').next().first().css('display', 'block');
            }
        }
    });

    var _alphabetSearch = '';

    $.fn.dataTable.ext.search.push(function(settings, searchData ) {
        // fires when click a letter
        // somehow, searchData[0] has a space in the first spot.
        // strip it out if this happens
        var searchString = searchData[0].trim();
        if (!_alphabetSearch) {
            return true;
        }
        else if (searchString.charAt(0) === _alphabetSearch) {
            return true;
        }
        else if (searchString.charAt(0).toUpperCase() === _alphabetSearch) {
            return true;
        }
        return false;
    });

    // Call datatables for glossary
    var glossary_table = $('#glossary_table').DataTable({
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

    // START section to find anchor location
    navigate_to_anchor('out');
    function navigate_to_anchor(in_or_out) {
        if (in_or_out === 'out') {
            //if there is a specific anchor when coming to the page from outside the page
            // pull the anchor it matches on the page (may not be one to one)
            var anchor_xref = {
                // '': '#global_database_tools_section',

                '#assays-studycomponents': '#help_overview_components',
                '#assays-assaystudy-summary': '#help_assay_data_viz',
                '#assays-assaystudyset-data-plots': '#help_assay_data_viz',

                // '': '#help_omic_data_viz',

                '#assays-assaystudy-images': '#help_image_and_video',
                '#assays-power-analysis-study': '#help_power_analysis',
                '#assays-interstudy-reproducibility': '#help_reproducibility_analysis',
                '#assays-assaystudy-reproducibility': '#help_reproducibility_analysis',
                '#assays-assaystudyset-reproducibility': '#help_reproducibility_analysis',
                '#assays-graphing-reproducibility': '#help_reproducibility_analysis',
                '#assays-assaystudyset-add': '#help_study_set',
                '#assays-assaystudyset-list': '#help_study_set',

                // '': '#help_collaborator_group',
                // '': '#help_access_group',

                '#assays-pbpk-filter': '#help_pbpk_analysis',

                // '': '#help_disease_portal',

                '#compounds-compound-report': '#help_compound_report',
                '#assays-assayreference-list': '#help_reference',

                '#compounds-compound-list': '#help_chemical_data',
                'bioactivities/table/#filter': '#help_bioactivities',
                '#bioactivities-table': '#help_bioactivities',
                '#drugtrial_list': '#help_drug_trials',
                '#adverse_events_list': '#help_adverse_events',
                '#compare_adverse_events': '#help_compare_adverse_events',

                // '': '#help_heatmap_bioactivities',
                // '': '#help_cluster_chemicals',

                '#assays-assaystudy-add': '#help_study_detail',
                '#assays-assaystudy-update-details': '#help_study_detail',
                '#assays-assaystudy-update-groups': '#help_study_treatment_group',
                '#assays-assaystudy-update-chips': '#help_chip_and_plate',
                '#assays-assaystudy-update-plates': '#help_chip_and_plate',
                '#assays-assaystudy-update-assays': '#help_target_and_method',
                '#assays-assaystudy-data-index': '#help_data_upload',
                '#assays-assaystudy-sign-off': '#help_study_signoff',
                '#assays-editable-study-list': '#help_overview_organization',
                '#assays-assaystudy-list': '#help_overview_organization',
                '#assays-assaystudy-index': '#help_overview_organization',
            };

            if (!incoming_hash || incoming_hash == '#None' || incoming_hash == '#') {
                help_hash = set_hash_default;
            } else {
                help_hash = anchor_xref[incoming_hash];
                // there was not an anchor match, try some other possibilities
                var expand_study_component = false;
                if (!help_hash) {
                    //is it a study component, and if so, is it one that requires multiple sections be opened
                    if (incoming_hash.indexOf('assays-assaytarget') >= 0) {
                        expand_study_component = true;
                        help_hash = '#help2_target'
                    } else if (incoming_hash.indexOf('assays-assaymethod') >= 0) {
                        expand_study_component = true;
                        help_hash = '#help2_method'
                    } else if (incoming_hash.indexOf('microdevices-organmodelprotocol') >= 0) {
                        expand_study_component = true;
                        help_hash = '#help2_modelversion'
                    } else if (incoming_hash.indexOf('microdevices-organmodel') >= 0) {
                        expand_study_component = true;
                        help_hash = '#help2_model'
                    } else if (incoming_hash.indexOf('compounds-compound') >= 0) {
                        expand_study_component = true;
                        help_hash = '#help2_compound'
                    } else if (incoming_hash.indexOf('cellsamples-') >= 0) {
                        expand_study_component = true;
                        help_hash = '#help2_cell'
                    } else if (
                        incoming_hash.indexOf('assays-assaymeasurementtype') >= 0
                        || incoming_hash.indexOf('assays-physicalunits') >= 0
                        || incoming_hash.indexOf('assays-assaysamplelocation') >= 0
                        || incoming_hash.indexOf('assays-assaysetting') >= 0
                        || incoming_hash.indexOf('assays-assaysupplier') >= 0
                        || incoming_hash.indexOf('assays-assayreference') >= 0
                        || incoming_hash.indexOf('microdevices-microdevice') >= 0
                        || incoming_hash.indexOf('microdevices-manufacturer') >= 0
                    ) {
                        help_hash = '#help_study_component';
                    } else {
                        help_hash = set_hash_default;
                    }
                    // this is a special pre-open that allows for opening of specific study components
                    if (expand_study_component) {
                        //help2_study_component_feature is the id of the button
                        change_display($('#help2_study_component_feature')[0].nextElementSibling, 'e');
                    }
                }
            }
            //if still null
            if (!help_hash) {
                help_hash = set_hash_default;
            }
            animate_scroll_hash(help_hash);
        } else {
            animate_scroll_hash(help_hash);
        }
    }

    // after the page is loaded or the hash is changed or user clicks on has link, change location on page
    function animate_scroll_hash(anchor) {
        //opens and scrolls (leave open here for glossary and help hash changes.

        // if the anchor is NOT on the page, does not cause and error in the console
        // this error causes the glossary NOT to display!!!

        var offset_anchor = 110;

        if (anchor === '#search_help_page_section') {
            $('#search_help_page_section').removeClass('hidden');
        } else {
            $('#search_help_page_section').addClass('hidden');
        }

        if ($(anchor).length)
        {
            $('html, body').animate({
                scrollTop: $(anchor).offset().top - offset_anchor
            }, 500);
            $(anchor).find('button').next().first().css('display', 'block');
        }
    }

    //this will happen if the user clicks on Help from the main database and the Help is already open
    $(window).on('hashchange', function(e) {
        incoming_hash = window.location.hash;
        help_hash = set_hash_default;
        navigate_to_anchor('out');
    })
    // END section to find anchor location

    function strip_the_glossary_spans() {
        //remove the class on the glossary extracts so the search will work better
        // when use $('#realTimeContents .gse0') you do not get the glossary :o
        $span = $('#realTimeContents .gse0');
        $span.each(function() {
            $(this).replaceWith($(this).html());
        });
        $span = $('#realTimeContents .gse1');
        $span.each(function() {
            $(this).replaceWith($(this).html());
        });
        $span = $('#glossaryContents .gse0');
        $span.each(function() {
            $(this).replaceWith($(this).html());
        });
        $span = $('#glossaryContents .gse1');
        $span.each(function() {
            $(this).replaceWith($(this).html());
        });
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
    // var caseSensitive_flag = 'ig';
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
    //     // console.log('searchTermRegEx '+searchTermRegEx)
    //
    //     // matches = $(selector).text().match(searchTermRegEx);
    //     $('.mark-content').mark(searchTerm, options);
    //     matches = $('.mark').map(function() {
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
    //     // console.log('step 1 matches '+matches)
    //     // console.log('step 1 number matches = '+matches_length)
    //
    //     if (matches != null && matches_length > 0) {
    //         // unique_matches = matches.filter(function(itm, i, a) {
    //         //     return i == matches.indexOf(itm);
    //         // });
    //         // if (searchTerm === '&') {
    //         //     searchTerm = '&amp;';
    //         //     searchTermRegEx = new RegExp(searchTerm, caseSensitive_flag);
    //         // }
    //         // console.log('searchTerm ',searchTerm)
    //         labelMatchSpan_search2(continueFunction_search3);
    //     }
    // }

    //
    // function continueFunction_search3() {
    //     // the previous function replaced with the search term, fix to match the original case
    //     // if ($('.match').length != matches_length) {
    //     //     alert('there is a mismatch in the counting....')
    //     // }
    //     if ($('.mark').length != matches_length) {
    //         alert('there is a mismatch in the counting....')
    //     }
    //     $('.match').each(function (index, currentElement) {
    //         currentElement.innerHTML = matches[index];
    //         $(this).html(matches[index]);
    //     });
    //     // $('.match:first').addClass('highlighted');
    //     $('.match:first').addClass('mark');
    //     match_index = 0;
    //     // console.log('in search 3 - getting ready to highlight')
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
    // // $('#search_next').click(function() {
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
    // // $('#search_prev').click(function() {
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