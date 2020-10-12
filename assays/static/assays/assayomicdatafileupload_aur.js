//GLOBAL-SCOPE
window.OMICS = {
    draw_plots: null,
    omics_data: null
};

$(document).ready(function () {
    //show the validation stuff
    $('#form_errors').show()
    // Load core chart package
    google.charts.load('current', {'packages': ['corechart']});
    google.charts.load('visualization', '1', {'packages': ['imagechart']});

    // $('.has-popover').popover({'trigger':'hover'});
    
    let global_omic_upload_group_id_change = 0;
    let global_omic_upload_group_pk_change = 0;
    
    let global_omic_upload_group_id_load_1 = 0;
    let global_omic_upload_group_pk_load_1 = 0;
    let global_omic_upload_group_id_load_2 = 0;
    let global_omic_upload_group_pk_load_2 = 0;
    let global_omic_upload_called_from = 'add';

    let global_omic_current_group1 = $('#id_group_1')[0].selectize.items[0];
    let global_omic_current_group2 = $('#id_group_2')[0].selectize.items[0];

    let global_make_the_group_change = true;

    //set the required-ness of the groups on load based on data type on load
    changed_something_important("load");

    let global_omic_upload_check_load = $('#check_load').html().trim();

    if (global_omic_upload_check_load === 'review') {
        global_omic_upload_called_from = 'load-review' 
        // HANDY - to make everything on a page read only (for review page)
        $('.selectized').each(function() { this.selectize.disable() });
        $(':input').attr('disabled', 'disabled');
    } else {
        global_omic_upload_group_id_load_1 = 1
        global_omic_upload_group_pk_load_1 = $('#id_group_1')[0].selectize.items[0]
        global_omic_upload_group_id_load_2 = 2
        global_omic_upload_group_pk_load_2 = $('#id_group_2')[0].selectize.items[0]      
        
        if (global_omic_upload_check_load === 'add') {
            global_omic_upload_called_from = 'load-add'
            get_group_sample_info('load-add')
        } else {
            global_omic_upload_called_from = 'load-update'
            get_group_sample_info('load-update')
        }
    }

    // tool tip requirements
    // todo here here update the tool tips for the different file formats
    let global_omic_upload_omic_file_format_deseq2_log2fc_headers = '"name", "baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"';
    let global_omic_upload_omic_file_format_deseq2_log2fc_tooltip = 'For DESeq2 Log2Fold change data, the header "log2FoldChange" must be in the first row. Other optional columns headers are: "baseMean", "lfcSE", "stat", "pvalue", "padj", and "gene reference" (or "name" or "gene").';
    $('#omic_file_format_deseq2_log2fc_tooltip').next().html($('#omic_file_format_deseq2_log2fc_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_deseq2_log2fc_tooltip));

    // let global_count_files = 'Counts data files must have one header row labeled "Sample ID" with each column labeled with a sample ID. The metadata file must have headers: Sample ID, Chip ID, Sample Location, Day, Hour, Minute, and Assay Well ID. Headers are required but only the Sample ID and Chip ID are required to be filled in. The Sample ID must match the Sample ID provided in the count data file. ';
    // let global_omic_upload_omic_file_format_normcounts_tooltip = 'Under Development - Two files required: 1) normalized counts and 2) sample metadata. ' + global_count_files;
    // $('#omic_file_format_normcounts_tooltip').next().html($('#omic_file_format_normcounts_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_normcounts_tooltip));
    // let global_omic_upload_omic_file_format_rawcounts_tooltip = 'Under Development - Two files required: 1) raw counts and 2) sample metadata. ' + global_count_files;
    // $('#omic_file_format_rawcounts_tooltip').next().html($('#omic_file_format_rawcounts_tooltip').next().html() + make_escaped_tooltip(global_omic_upload_omic_file_format_rawcounts_tooltip));
    //

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
     * A function to clear the validation errors on change of any field
     */
    function clear_validation_errors() {
        $('#form_errors').hide();
    }

    /**
     * On click to toggle
    */
    // the file format details
    $('#fileFormatDetailsButton').click(function () {
        $('#omic_file_format_details_section').toggle();
    });
    // the graph sections
    $('#omicPreviewTheGraphsButton').click(function () {
        $('#omic_preview_the_graphs_section').toggle();
        $('#omic_preview_the_graphs_section2').toggle();
    });
    /**
     * On change data file
    */
    $('#id_omic_data_file').on('change', function (e) {
        clear_validation_errors();
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
        clear_validation_errors();
        changed_something_important("data_type");
    });
    /**
     * On changes that affect the graphs/plots on the preview page
    */
    $('#id_anaylsis_method').on('change', function (e) {
        clear_validation_errors();
        changed_something_important("analysis_method");
    });

    function changed_something_important(called_from) {

        if ($('#id_data_type')[0].selectize.items[0] == 'log2fc') {
            $('#id_group_1').next().addClass('required');
            $('.one-group').show();
            $('#id_group_2').next().addClass('required');
            $('.two-groups').show();
            if (called_from != 'load') {
                get_data_for_this_file_ready_for_preview(called_from)
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
    function get_data_for_this_file_ready_for_preview(called_from) {
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

        let is_data = true;
        if (document.getElementById("id_omic_data_file").files.length > 0) {
            is_data = true;
        } else {
            is_data = false;
        }

        if (is_data) {
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
                    } else {
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

                        // put here to avoid race errors
                        if (called_from == 'data_file') {
                            try {
                                id_omic_data_file = $('#id_omic_data_file').val();
                                check_file_add_update(id_omic_data_file);
                            } catch {
                            }
                        }
                    }
                },
                error: function (xhr, errmsg, err) {
                    window.spinner.stop();
                    alert('Encountered an error when trying to make a preview plot. Check to make sure the Data Type selected matches the file selected.');
                    console.log(xhr.status + ': ' + xhr.responseText);
                }
            });
        }
    };
    // END section for preview page

    /**
     * On change method
    */
    $('#id_study_assay').change(function () {
        clear_validation_errors();
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
        clear_validation_errors();
        //console.log('change 1')
        if (global_make_the_group_change) {
            if ($('#id_group_1')[0].selectize.items[0] == $('#id_group_2')[0].selectize.items[0]) {
                $('#id_group_1')[0].selectize.setValue(global_omic_current_group1);
                send_user_groups_are_different_message();
            } else {
                global_omic_upload_called_from = 'change';
                global_omic_upload_group_id_change = 1;
                global_omic_upload_group_pk_change = $('#id_group_1')[0].selectize.items[0];

                if ($('#id_group_'+global_omic_upload_group_id_change)[0].selectize.items[0] != null) {
                    get_group_sample_info('change');
                } else {
                    $('#id_group_'+global_omic_upload_group_id_change)[0].selectize.items[0];
                    $('#id_time_'+global_omic_upload_group_id_change+'_day').val(null);
                    $('#id_time_'+global_omic_upload_group_id_change+'_hour').val(null);
                    $('#id_time_'+global_omic_upload_group_id_change+'_minute').val(null);

                    let $this_dropdown = $(document.getElementById('id_location_'+global_omic_upload_group_id_change));
                    $this_dropdown.selectize()[0].selectize.clearOptions();
                    $('#id_location_'+global_omic_upload_group_id_change)[0].selectize.setValue();
                }
            }
            global_omic_current_group1 = $('#id_group_1')[0].selectize.items[0];
        }
    });
    $('#id_group_2').change(function () {
        clear_validation_errors();
        if (global_make_the_group_change) {
            if ($('#id_group_1')[0].selectize.items[0] == $('#id_group_2')[0].selectize.items[0]) {
                $('#id_group_2')[0].selectize.setValue(global_omic_current_group2);
                send_user_groups_are_different_message();
            } else {
                global_omic_upload_called_from = 'change';
                //console.log('change 2')
                global_omic_upload_group_id_change = 2;
                global_omic_upload_group_pk_change = $('#id_group_2')[0].selectize.items[0];

                if ($('#id_group_'+global_omic_upload_group_id_change)[0].selectize.items[0] != null) {
                    get_group_sample_info('change');
                } else {
                    $('#id_group_'+global_omic_upload_group_id_change)[0].selectize.items[0];
                    $('#id_time_'+global_omic_upload_group_id_change+'_day').val(null);
                    $('#id_time_'+global_omic_upload_group_id_change+'_hour').val(null);
                    $('#id_time_'+global_omic_upload_group_id_change+'_minute').val(null);

                    let $this_dropdown = $(document.getElementById('id_location_'+global_omic_upload_group_id_change));
                    $this_dropdown.selectize()[0].selectize.clearOptions();
                    $('#id_location_'+global_omic_upload_group_id_change)[0].selectize.setValue();
                }
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
    // Start the download of yournewfile.csv file with the content from the text area
        // could tie this to selections in the GUI later, if requested.
        // change with tool tip
        var text = global_omic_upload_omic_file_format_deseq2_log2fc_headers;
        var filename = "TwoGroupDESeq2Omic.csv";

        download(filename, text);
    }, false);

    function send_user_groups_are_different_message() {
        if (typeof $('#id_group_1')[0].selectize.items[0] !== 'undefined') {
            alert('Group 1 and Group 2 must be different or both must be empty.');
        }
    }

     /**
      * When a group is changed, if that group has already been added to the data upload file
      * get the first occurrence that has sample information.
    */
    function get_group_sample_info(called_from) {
        // console.log('1: '+global_omic_upload_group_pk_change)
        // console.log('2: '+global_omic_upload_group_pk_load_1)
        // console.log('3: '+global_omic_upload_group_pk_load_2)
        // console.log('4: '+global_omic_upload_called_from)

        // HANDY if using js split time
        // time_in_minutes = 121
        // var split_time = window.SPLIT_TIME.get_split_time(time_in_minutes);
        // $.each(split_time, function(time_name, time_value) {
        //     console.log(time_name)
        //     console.log(time_value)
        // });

        // if changing a group, need to get all the updated info
        // if an add page, need to call to clear out the location list
        // if update page, need to get the model location list

        let data = {
            call: 'fetch_omic_sample_info_from_upload_data_table',
            called_from: global_omic_upload_called_from,
            groupIdc: global_omic_upload_group_id_change,
            groupPkc: global_omic_upload_group_pk_change,
            groupId1: global_omic_upload_group_id_load_1,
            groupPk1: global_omic_upload_group_pk_load_1,
            groupId2: global_omic_upload_group_id_load_2,
            groupPk2: global_omic_upload_group_pk_load_2,
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
                alert('An error has occurred (finding group sample information). ');
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

        // console.log('--- '+global_omic_upload_group_id_load_1)
        // console.log(json.timemess1)
        // console.log(json.day1)
        // console.log(json.hour1)
        // console.log(json.minute1)
        // console.log(json.locmess1)
        // console.log(json.sample_location_pk1)
        // console.log(json.location_dict1)
        // console.log(json.timemess2)
        // console.log(json.day2)
        // console.log(json.hour2)
        // console.log(json.minute2)
        // console.log(json.locmess2)
        // console.log(json.sample_location_pk2)
        // console.log(json.location_dict2)

        if (global_omic_upload_called_from == 'load-add') {
            // just do the location lists
        } else if (global_omic_upload_called_from == 'load-update') {
            // just do the location lists to restrict to the model
            let pk_loc_1 = $('#id_location_1')[0].selectize.items[0];
            let pk_loc_2 = $('#id_location_2')[0].selectize.items[0];

            let $this_dropdown1 = $(document.getElementById('id_location_1'));
            $this_dropdown1.selectize()[0].selectize.clearOptions();
            let this_dict1 = $this_dropdown1[0].selectize;
            // fill the dropdown with what brought back from ajax call
            $.each(json.location_dict1[0], function( pk, text ) {
                // console.log("1 "+pk+ "  "+text)
                this_dict1.addOption({value: pk, text: text});
            });

            let $this_dropdown2 = $(document.getElementById('id_location_2'));
            $this_dropdown2.selectize()[0].selectize.clearOptions();
            let this_dict2 = $this_dropdown2[0].selectize;
            // fill the dropdown with what brought back from ajax call
            $.each(json.location_dict2[0], function( pk, text ) {
                // console.log("2 "+pk+ "  "+text)
                this_dict2.addOption({value: pk, text: text});
            });

            $('#id_location_1')[0].selectize.setValue(pk_loc_1);
            $('#id_location_2')[0].selectize.setValue(pk_loc_2);
        } else {
            // called from a change of one of the groups
            $('#id_time_'+global_omic_upload_group_id_change+'_day').val(json.day1);
            $('#id_time_'+global_omic_upload_group_id_change+'_hour').val(json.hour1);
            $('#id_time_'+global_omic_upload_group_id_change+'_minute').val(json.minute1);

            // https://github.com/selectize/selectize.js/blob/master/docs/api.md
            // HANDY to set the options of selectized dropdown
            let $this_dropdown = $(document.getElementById('id_location_'+global_omic_upload_group_id_change));
            $this_dropdown.selectize()[0].selectize.clearOptions();
            let this_dict = $this_dropdown[0].selectize;
            // fill the dropdown with what brought back from ajax call
            //the changed one is always returned as the first
            $.each(json.location_dict1[0], function( pk, text ) {
                // console.log("c "+pk+ "  "+text)
                this_dict.addOption({value: pk, text: text});
            });
            $('#id_location_'+global_omic_upload_group_id_change)[0].selectize.setValue(json.sample_location_pk1);
        }

        //HANDY get the value from selectized
        // $('#id_se_block_standard_borrow_string')[0].selectize.items[0];
        //HANDY set value of selectized
        //$('#id_ns_blah')[0].selectize.setValue(global_omic_upload_blah);
        //HANDY get the text from selectized
        //global_omic_upload_aa = $('#id_aa')[0].selectize.options[global_omic_upload_aa]['text'];

    };

     /**
      * When the file is changed and is not null, check to see if the file
      * is already in this study
    */
    function check_file_add_update(id_omic_data_file) {
        if ($("#check_load").html().trim() === 'add') {
            data_file_pk = 0;
        } else {
            parseInt(document.getElementById("this_file_id").innerText.trim())
        }
        let data = {
            call: 'fetch_this_file_is_this_study',
            omic_data_file: id_omic_data_file,
            study_id: parseInt(document.getElementById("this_study_id").innerText.trim()),
            data_file_pk: data_file_pk,
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
                    if (json.true_to_continue.toString().toLowerCase() === 'false') {
                       alert(json.message);
                    }
                }
            },
            // error callback
            error: function (xhr, errmsg, err) {
                window.spinner.stop();
                alert('An error has occurred checking the file name. ');
                console.log(xhr.status + ': ' + xhr.responseText);
            }
        });
    }

});

