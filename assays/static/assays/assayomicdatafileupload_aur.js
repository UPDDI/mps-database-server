$(document).ready(function () {

    // $('.has-popover').popover({'trigger':'hover'});

    let global_omic_upload_group_id_working = 0
    let global_omic_upload_group_pk_working = 0
    let global_omic_upload_group_id_working2 = 0
    let global_omic_upload_group_pk_working2 = 0
    let global_omic_upload_called_from = 'add'

    let global_omic_current_group1 = $('#id_group_1')[0].selectize.items[0]
    let global_omic_current_group2 = $('#id_group_2')[0].selectize.items[0]

    //start this hidden
    $('#omic_file_format_details_section').hide();

    //set the required ness of the groups on load based on data type on load
    changed_data_type();

    let global_omic_upload_check_load = $('#check_load').html().trim();
    if (global_omic_upload_check_load === 'review') {
        // HANDY - to make everything on a page read only (for review page)
        $('.selectized').each(function() { this.selectize.disable() });
        $(':input').attr('disabled', 'disabled');
    } else if (global_omic_upload_check_load === 'add') {
        global_omic_upload_called_from = 'add'
        global_omic_upload_group_id_working = 1
        global_omic_upload_group_pk_working = $('#id_group_1')[0].selectize.items[0]
        global_omic_upload_group_id_working2 = 2
        global_omic_upload_group_pk_working2 = $('#id_group_2')[0].selectize.items[0]
        get_group_sample_info()
    }

    // tool tip requirements
    // here here update the tool tips for the different file formats
    let global_omic_upload_omic_file_format_deseq2_log2fc_tooltip = 'For DESeq2 Log2Fold change data, the following headers are required to be located in the first row of the file or worksheet: baseMean, log2FoldChange, lfcSE, stat, pvalue, padj, and gene or name.';
    $('#omic_file_format_deseq2_log2fc_tooltip').next().html($('#omic_file_format_deseq2_log2fc_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_deseq2_log2fc_tooltip));
    let global_omic_upload_omic_file_format_normcounts_tooltip = 'Under Development - Normalized counts data files must have one header row. the first column must be named "name" and contain a reference to the gene. The remaining columns must be named with the chip or well name as assigned in the MPS Database. ';
    $('#omic_file_format_normcounts_tooltip').next().html($('#omic_file_format_normcounts_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_normcounts_tooltip));
    let global_omic_upload_omic_file_format_rawcounts_tooltip = 'Under Development - Raw counts data files must have one header row. The first column must be named "name" and contain a reference to the gene. The remaining columns must be named with the chip or well name as assigned in the MPS Database. ';
    $('#omic_file_format_rawcounts_tooltip').next().html($('#omic_file_format_rawcounts_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_rawcounts_tooltip));
let global_omic_method_tooltip = 'Assay Method';
    $('#omic_method_tooltip').next().html($('#omic_method_tooltip').next().html() + make_escaped_tooltip(global_omic_method_tooltip));


    // activates Bootstrap tooltips, must be AFTER tooltips are created - keep
    $('[data-toggle="tooltip"]').tooltip({container:'body', html: true});

    // tool tip functions
    function escapeHtml(html) {
        return $('<div>').text(html).html();
    }

    function make_escaped_tooltip(title_text) {
        let new_span = $('<div>').append($('<span>')
            .attr('data-toggle', 'tooltip')
            .attr('data-title', escapeHtml(title_text))
            .addClass('glyphicon glyphicon-question-sign')
            .attr('aria-hidden', 'true')
            .attr('data-placement', 'bottom'));
        return new_span.html();
    }

    $('#fileFormatDetailsButton').click(function () {
        $('#omic_file_format_details_section').toggle();
    });


    /**
     * On change data type, change what is required
    */
    $('#id_data_type').change(function () {
        changed_data_type();
    });
    function changed_data_type() {
        if ($('#id_data_type')[0].selectize.items[0] == 'log2fc') {
            $('#id_group_1').next().addClass('required');
            $('.one-group').show();
            $('#id_group_2').next().addClass('required');
            $('.two-groups').show();
        } else {
            //here here to update when ready
            alert('Uploading of Normalized and Raw Count Data is Currently in Development.');
            $('#id_group_1').next().removeClass('required');
            $('.one-group').hide();
            $('#id_group_1')[0].selectize.setValue('not-full');
            $('#id_time_1_day').val(0);
            $('#id_time_1_hour').val(0);
            $('#id_time_1_minute').val(0);
            global_omic_current_group1 = $('#id_group_1')[0].selectize.items[0];

            $('#id_group_2').next().removeClass('required');
            $('.two-groups').hide();
            $('#id_group_2')[0].selectize.setValue('not-full');
            $('#id_time_2_day').val(0);
            $('#id_time_2_hour').val(0);
            $('#id_time_2_minute').val(0);
            global_omic_current_group2 = $('#id_group_2')[0].selectize.items[0];
        }
    }
    /**
     * On change method
    */
    $('#id_method').change(function () {
        method_value = $('#id_method')[0].selectize.items[0];
        try {
            method_text = $('#id_method')[0].selectize.options[method_value]['text'];
            if (method_text.toLowerCase() == 'tempo-seq') {
                new_value = 'temposeq_probe';
            } else {
                new_value = 'entrez_gene';
            }
            $('#id_name_reference')[0].selectize.setValue(new_value);
        } catch {
            $('#id_name_reference')[0].selectize.setValue('entrez_gene');
        }
    });

    /**
     * On change a group, call a function that gets sample info
    */
    $('#id_group_1').change(function () {
        //console.log('change 1')
        if ($('#id_group_1')[0].selectize.items[0] == $('#id_group_2')[0].selectize.items[0]) {
            $('#id_group_1')[0].selectize.setValue(global_omic_current_group1);
            send_user_different_message();
        } else {
            global_omic_upload_called_from = 'change';
            global_omic_upload_group_id_working = 1;
            global_omic_upload_group_pk_working = $('#id_group_1')[0].selectize.items[0];
            get_group_sample_info('change');
        }
        global_omic_current_group1 = $('#id_group_1')[0].selectize.items[0];
    });
    $('#id_group_2').change(function () {
        if ($('#id_group_1')[0].selectize.items[0] == $('#id_group_2')[0].selectize.items[0]) {
            $('#id_group_2')[0].selectize.setValue(global_omic_current_group2);
            send_user_different_message();
        } else {
            global_omic_upload_called_from = 'change';
            //console.log('change 2')
            global_omic_upload_group_id_working = 2;
            global_omic_upload_group_pk_working = $('#id_group_2')[0].selectize.items[0];
            get_group_sample_info('change');
        }
        global_omic_current_group2 = $('#id_group_2')[0].selectize.items[0];
    });

    function send_user_different_message() {
        if (typeof $('#id_group_1')[0].selectize.items[0] !== 'undefined') {
            alert('Group 1 and Group 2 must be different or both must be empty.');
        }
    }

     /**
      * When a group is changed, if that group has already been added to the data upload file
      * get the first occurrence that has sample information.
    */
    function get_group_sample_info() {
        // console.log(global_omic_upload_group_id_working)

        // HANDY if using js split time
        // time_in_minutes = 121
        // var split_time = window.SPLIT_TIME.get_split_time(time_in_minutes);
        // $.each(split_time, function(time_name, time_value) {
        //     console.log(time_name)
        //     console.log(time_value)
        // });

        let data = {
            call: 'fetch_omic_sample_info_from_upload_data_table',
            called_from: global_omic_upload_called_from,
            groupId: global_omic_upload_group_id_working,
            groupPk: global_omic_upload_group_pk_working,
            groupId2: global_omic_upload_group_id_working2,
            groupPk2: global_omic_upload_group_pk_working2,
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };
        window.spinner.spin(document.getElementById('spinner'));
        $.ajax({
            url: '/assays_ajax/',
            type: 'POST',
            dataType: 'json',
            data: data,
            success: function (json) {
                window.spinner.stop();
                if (json.errors) {
                    // Display errors
                    alert(json.errors);
                }
                else {
                    let exist = true;
                    get_group_sample_info_ajax(json, exist);
                }
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred (finding group sample information). Enter the information manually.');
                console.log(xhr.status + ': ' + xhr.responseText);
            }
        });
    }
    // post processing from ajax call
    /**
     * Put the sample data where it needs to go
    */
    let get_group_sample_info_ajax = function (json, exist) {
        // bringing back the D, H, M, and sample location (if found)

        // console.log('--- '+global_omic_upload_group_id_working)
        // console.log(json.timemess)
        // console.log(json.day)
        // console.log(json.hour)
        // console.log(json.minute)
        // console.log(json.locmess)
        // console.log(json.sample_location_pk)
        // console.log(json.timemess2)
        // console.log(json.day2)
        // console.log(json.hour2)
        // console.log(json.minute2)
        // console.log(json.locmess2)
        // console.log(json.sample_location_pk2)

        if (global_omic_upload_called_from == 'add') {
            $('#id_time_1_day').val(json.day);
            $('#id_time_1_hour').val(json.hour);
            $('#id_time_1_minute').val(json.minute);
            $('#id_location_1')[0].selectize.setValue(json.sample_location_pk);
            $('#id_time_2_day').val(json.day2);
            $('#id_time_2_hour').val(json.hour2);
            $('#id_time_2_minute').val(json.minute2);
            $('#id_location_2')[0].selectize.setValue(json.sample_location_pk2);
        } else {
            $('#id_time_'+global_omic_upload_group_id_working+'_day').val(json.day);
            $('#id_time_'+global_omic_upload_group_id_working+'_hour').val(json.hour);
            $('#id_time_'+global_omic_upload_group_id_working+'_minute').val(json.minute);
            $('#id_location_'+global_omic_upload_group_id_working)[0].selectize.setValue(json.sample_location_pk);
        }

        //HANDY get the value from selectized
        // $('#id_se_block_standard_borrow_string')[0].selectize.items[0];
        //HANDY set value of selectized
        //$('#id_ns_blah')[0].selectize.setValue(global_omic_upload_blah);
        //HANDY get the text from selectized
        //global_omic_upload_aa = $('#id_aa')[0].selectize.options[global_omic_upload_aa]['text'];

    };

});

