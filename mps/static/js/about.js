$(document).ready(function () {
    // Resolve anchors going to the incorrect location
    var offset = 60;

    //For Frequently Asked Questions
    $(".collapsible1").click(function() {
        var content = this.nextElementSibling;
        if ($(content).css("display") != "none") {
            $(content).css("display", "none");
        } else {
            $(content).css("display", "block");
        }
    });

    //For Key Features
    // $(".collapsible2").click(function() {
    // console.log(this);
    //     var content = $(this).find('.content2');
    //     $('.content2').css("display", "none");
    //     content.css("display", "block");
    // });
    //
    // // Initially show the first
    // console.log($('.collapsible2').first());
    // $('.collapsible2').first().trigger('click');

    $('.blues1').click(function() {
        $('.content2').css('display', 'none');
        var current_index = $('.blues1').index($(this));
        $('.blues1').css('font-weight', 'normal');
        $('#feature_list').find('.blues1:eq("' + current_index + '")').css('font-weight', 'bold');
        //console.log(current_index);
        //console.log($('#feature_section').find('.content2:eq("' + current_index + '")'));
        $('#feature_section').find('.content2:eq("' + current_index + '")').css('display', 'block');
        if (current_index==3){
            //console.log(current_index, "I am here in 9");
            $('.study-releases').css('display', 'block');
        } else {
            $('.study-releases').css('display', 'none');
        }
        if (current_index==1){
            //console.log(current_index, "I am here in 2");
            $('.organs-and-models').css('display', 'block');
        } else {
            $('.organs-and-models').css('display', 'none');
        }
    });

    $('.blues1').first().trigger('click');

    $('a').not("[href*='/']").click(function(event) {
        event.preventDefault();
        if ($($(this).attr('href'))[0]) {
            $('html, body').animate({
                scrollTop: $($(this).attr('href')).offset().top - offset
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

    // Call datatables
    var about_studies_for_release_table = $('#about_studies_for_release_table').DataTable({
        dom: 'B<"row">lfrtip',
        "iDisplayLength": 10,
        responsive: true
    });

/*    var about_models_and_centers_table = $('#about_models_and_centers_table').DataTable({
        dom: 'B<"row">lfrtip',
        "iDisplayLength": 10,
        responsive: true
    });*/

    var about_models_and_centers_distinct_table = $('#about_models_and_centers_distinct_table').DataTable({
        dom: 'B<"row">lfrtip',
        "iDisplayLength": 10,
        responsive: true
    });
});
