//GLOBAL-SCOPE
window.OMICS = {
    draw_plots: null,
    omics_data: null
};

$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages': ['corechart']});
    google.charts.load('visualization', '1', {'packages': ['imagechart']});

    // $('.has-popover').popover({'trigger':'hover'});

    let global_omic_upload_group_id_working = 0;
    let global_omic_upload_group_pk_working = 0;
    let global_omic_upload_group_id_working2 = 0;
    let global_omic_upload_group_pk_working2 = 0;
    let global_omic_upload_called_from = 'add';

    let global_omic_current_group1 = $('#id_group_1')[0].selectize.items[0];
    let global_omic_current_group2 = $('#id_group_2')[0].selectize.items[0];

    let global_make_the_group_change = true;

    //set the required-ness of the groups on load based on data type on load
    changed_something_important("load");

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
    // todo here here update the tool tips for the different file formats
    let global_omic_upload_omic_file_format_deseq2_log2fc_headers = '"name", "baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"';
    let global_omic_upload_omic_file_format_deseq2_log2fc_tooltip = 'For DESeq2 Log2Fold change data, the header "log2FoldChange" must be in the first row. Other optional columns headers are: "baseMean", "lfcSE", "stat", "pvalue", "padj", and "gene reference" (or "name" or "gene").';
    $('#omic_file_format_deseq2_log2fc_tooltip').next().html($('#omic_file_format_deseq2_log2fc_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_deseq2_log2fc_tooltip));
    let global_omic_upload_omic_file_format_normcounts_tooltip = 'Under Development - ?????? Normalized counts data files must have one header row. the first column must be named "name" and contain a reference to the gene. The remaining columns must be named with the chip or well name as assigned in the MPS Database. ';
    $('#omic_file_format_normcounts_tooltip').next().html($('#omic_file_format_normcounts_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_normcounts_tooltip));
    let global_omic_upload_omic_file_format_rawcounts_tooltip = 'Under Development - ???????? Raw counts data files must have one header row. The first column must be named "name" and contain a reference to the gene. The remaining columns must be named with the chip or well name as assigned in the MPS Database. ';
    $('#omic_file_format_rawcounts_tooltip').next().html($('#omic_file_format_rawcounts_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_rawcounts_tooltip));
    let global_omic_anaylsis_method_tooltip = 'The method (i.e. data processing tool, pipeline, etc.) used to process data.';
    $('#omic_anaylsis_method_tooltip').next().html($('#omic_anaylsis_method_tooltip').next().html() + make_escaped_tooltip(global_omic_anaylsis_method_tooltip));

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

    /**
     * On click to toggle
    */
    $('#fileFormatDetailsButton').click(function () {
        $('#omic_file_format_details_section').toggle();
    });

    // hide/show the graph sections
    $('#omicPreviewTheGraphsButton').click(function () {
        $('#omic_preview_the_graphs_section').toggle();
        $('#omic_preview_the_graphs_section2').toggle();
    });
    /**
     * On change data file
    */
    $('#id_omic_data_file').on('change', function (e) {
        //when first change the file, make the preview button available
        $('#omic_preview_button_section').show();
        $('#omic_preview_the_graphs_section').show();
        $('#omic_preview_the_graphs_section2').show();
        changed_something_important("data_file");
    });
    /**
     * On change data type, change what is required page logic
    */
    $('#id_data_type').change(function () {
        changed_something_important("data_type");
    });
    /**
     * On changes that affect the graphs/plots on the preview page
    */
    $('#id_anaylsis_method').on('change', function (e) {
        changed_something_important("analysis_method");
    });

    function changed_something_important(called_from) {
        if ($('#id_data_type')[0].selectize.items[0] == 'log2fc') {
            $('#id_group_1').next().addClass('required');
            $('.one-group').show();
            $('#id_group_2').next().addClass('required');
            $('.two-groups').show();
            if (called_from != 'load') {
                get_data_for_this_file_ready_for_preview()
            }
        } else {
            //here here to update when ready
            alert('Uploading of Normalized and Raw Count Data is Currently in Development.');

            global_make_the_group_change = false;
            $('#id_group_1')[0].selectize.setValue('not-full');
            $('#id_group_2')[0].selectize.setValue('not-full');
            global_make_the_group_change = true;

            $('#id_location_1')[0].selectize.setValue('not-full');
            $('#id_time_1_day').val(0);
            $('#id_time_1_hour').val(0);
            $('#id_time_1_minute').val(0);
            global_omic_current_group1 = $('#id_group_1')[0].selectize.items[0];
            $('.one-group').hide();

            $('#id_location_2')[0].selectize.setValue('not-full');
            $('#id_time_2_day').val(0);
            $('#id_time_2_hour').val(0);
            $('#id_time_2_minute').val(0);
            global_omic_current_group2 = $('#id_group_2')[0].selectize.items[0];
            $('.two-groups').hide();
        }
    }

    // START section for preview page
    // To make the preview in the upload page
    // NOTE: the upload page has the following elements
    // that are used in getting the data needed
    // form name="omic_file"
    // id="id_data_type"
    // id="id_anaylsis_method"
    // id="id_omic_data_file"
    // And, these elements were added to the upload page
    // id="plots"
    // id="volcano-plots"
    // id="ma-plots"
    function get_data_for_this_file_ready_for_preview() {
        let data = {
            call: 'fetch_omics_data_for_upload_preview_prep',
            csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
        };
        let form = document.omic_file;
        let serializedData = $('form').serializeArray();
        let formData = new FormData(form);
        $.each(serializedData, function(index, field) {
            formData.append(field.name, field.value);
        });
        let study_id = 1;
        formData.append('study_id', study_id);
        let file_id = 1;
        formData.append('file_id', file_id);

        $.each(data, function(index, contents) {
            formData.append(index, contents);
        });

        window.spinner.spin(document.getElementById('spinner'));
        $.ajax({
            url: '/assays_ajax/',
            type: 'POST',
            dataType: 'json',
            cache: false,
            contentType: false,
            processData: false,
            data: formData,
            success: function (json) {
                window.spinner.stop();
                if (json.errors) {
                    alert(json.errors);
                }
                else {
                    let exist = true;
                    // console.log("a DATA", json)
                    // omics_data = json['data'];
                    // omics_target_name_to_id = json['target_name_to_id'];
                    // omics_file_id_to_name = json['file_id_to_name'];
                    // omics_table = json['table'];
                    // console.log("b data ", omics_data)
                    // console.log("c target_name_to_id ", omics_target_name_to_id)
                    // console.log("d file_id_to_name ", omics_file_id_to_name)
                    // console.log("e table ", omics_table)
                    window.OMICS.omics_data = JSON.parse(JSON.stringify(json));
                    omics_file_id_to_name_all = window.OMICS.omics_data['file_id_to_name'];
                    omics_file_id_to_name = omics_file_id_to_name_all[1];
                    // maxL2FC_a = window.OMICS.omics_data['max_fold_change'];
                    // maxPval_a = window.OMICS.omics_data['max_pvalue'];
                    // minL2FC_a = window.OMICS.omics_data['min_fold_change'];
                    // minPval_a = window.OMICS.omics_data['min_pvalue'];
                    // console.log("a")
                    // console.log(maxL2FC_a)
                    // console.log(maxPval_a)
                    // console.log(minL2FC_a)
                    // console.log(minPval_a)
                    // maxL2FC = -Math.log10(maxL2FC_a);
                    // maxPval = -Math.log10(maxPval_a);
                    // minL2FC = -Math.log10(minL2FC_a);
                    // minPval = -Math.log10(minPval_a);
                    // console.log("no a")
                    // console.log(maxL2FC)
                    // console.log(maxPval)
                    // console.log(minL2FC)
                    // console.log(minPval)
                    // console.log("window.OMICS.omics_data ")
                    // console.log(window.OMICS.omics_data)
                    window.OMICS.draw_plots(window.OMICS.omics_data, true, 0, 0, 0, 0, 0, 0, 0, 'upload');
                    // function(omics_data, firstTime, minPval, maxPval, minL2FC, maxL2FC, minPval_neg, maxPval_neg, L2FC_abs)
                }
            },
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('an error in processing data');
                console.log(xhr.status + ': ' + xhr.responseText);
            }
        });
    };
    // END section for preview page

    /**
     * On change method
    */
    $('#id_study_assay').change(function () {
        study_assay_value = $('#id_study_assay')[0].selectize.items[0];
        try {
            study_assay_text = $('#id_study_assay')[0].selectize.options[study_assay_value]['text'];
            if (study_assay_text.toLowerCase().includes('tempo-seq')) {
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
        if (global_make_the_group_change) {
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
        }
    });
    $('#id_group_2').change(function () {
        if (global_make_the_group_change) {
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
        }
    });

    // https://www.bitdegree.org/learn/best-code-editor/javascript-download-example-1
    function download(filename, text) {
      var element = document.createElement('a');
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
      element.setAttribute('download', filename);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
    /**
     * On click to download
    */
    // Start file download.
    document.getElementById("fileFileFormatTwoGroup").addEventListener("click", function(){
    // Start the download of yournewfile.txt file with the content from the text area
        // could tie this to selections in the GUI later, if requested.
        // change with tool tip
        var text = global_omic_upload_omic_file_format_deseq2_log2fc_headers;
        var filename = "TwoGroupDESeq2Omic.txt";

        download(filename, text);
    }, false);

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

