$(document).ready(function () {
    // Load core chart package
    google.charts.load('current', {'packages':['corechart']});
    // Set the callback
    google.charts.setOnLoadCallback(refresh_pbpk);

    window.GROUPING.refresh_function = refresh_pbpk;
    window.GROUPING.process_get_params();

    // Hide Grouping Criteria Checkboxes
    $('#filtering_tables').find('table tr td:nth-child(2)').hide();
    $('#filtering_tables').find('table tr th:nth-child(2)').hide();
    $('#sidebar').find('h3').html('<u>Filtering</u>');


    var group_table = null;
    var selection_table = null;

    var chart_data = null;
    var header_keys = null;
    var data_groups = null;
    var treatment_groups = null;
    var study_name_to_pk_params = null;

    var checkbox = null;
    var group_number = null;
    var group_num = null;
    var row_info = null;
    var pk_type = null;
    var with_no_cell_data = null;
    var start_time_dropdown = $('#clearance-time-start')[0].selectize;
    var end_time_dropdown = $('#clearance-time-end')[0].selectize;
    var start_time = null;
    var end_time = null;
    var has_no_cells = false;
    var cell_profiles = null;
    var acidic_pka, basic_pka = '';

    var pbpk_intrinsic_clearance = null;
    var prediction_plot_data = null;

    var species_vp_tooltip = "Plasma volume of organism.";
    var species_ve_tooltip = "Extracellular volume of organism.";
    var species_rei_tooltip = "Extravascular/Intravascular ratio for organism.";
    var species_vr_tooltip = "Volume into which drug is distributed minus extracellular space.";
    var species_asr_tooltip = "Intestinal absorptive surface area.";
    var species_ki_tooltip = "Inverse of small intestine transit time.";
    var compound_mw_tooltip = "Molecular weight is a measure of the sum of the atomic weight values of the atoms in a molecule.";
    var compound_logd_tooltip = "Log of octanol/water ratio.";
    var compound_pka_tooltip = "Negative log of the acid dissociation constant or Ka value.";
    // var compound_bioavailability_tooltip = "The proportion of a dose that reaches the systemic circulation.";
    var compound_fu_tooltip = "Fraction of unbound drug in plasma. Value be between 0 and 1.";
    var input_icl_tooltip = "Predicted intrinsic clearance.";
    var input_fa_tooltip = "Fraction absorbed. Default = ka / (ki + ka). Value must be between 0 and 1.";
    var input_ka_tooltip = "Absorption rate constant (range from 0.6 - 4.2).";
    var input_dosing_cp_tooltip = "To predict dose required enter a desired plasma concentration.";
    var input_dosing_interval_tooltip = "Enter a desired dosing interval.";
    var input_plasma_dose_tooltip = "To predict plasma concentration enter a desired dose.";
    var input_plasma_dose_interval_tooltip = "Enter a desired dosing interval.";
    var pk_param_vdss_tooltip = "Volume of distribution at steady state.";
    var pk_param_ke_tooltip = "Elimination rate constant.";
    var pk_param_halflife_tooltip = "The period of time for half of a drug to be eliminated from the plasma.";
    var pk_param_auc_tooltip = "Area under the concentration-vs-time curve.";
    var pk_param_elogd_tooltip = "Oct/water distribution coefficient determined by RP chromatography. ELogD = (0.9638*LogD) + 0.0417";
    var pk_param_vc_tooltip = "Volume of well perfused tissues.";
    var pk_param_logvow_tooltip = "Log of vegetable oil/water ratio.";
    var pk_param_cl_tooltip = "Clearance.";
    var pk_param_fut_tooltip = "Fraction of unbound drug in tissues. Value must be between 0 and 1.";
    var pk_param_fi_tooltip = "Fraction of drug ionized at pH 7.4.";
    var pk_single_mmax_tooltip = "Peak drug amount after single dose.";
    var pk_single_cmax_tooltip = "Peak drug concentration after single dose.";
    var pk_single_tmax_tooltip = "Time to reach peak level.";
    var pk_multi_mss_tooltip = "Average steady state amount of drug after multiple doses.";
    var pk_multi_css_tooltip = "Average steady state concentration of drug after multiple doses.";
    var pk_multi_tmax_tooltip = "Time to reach peak level after a dose for multiple doses.";
    var pk_desired_dose_tooltip = "Calculated required dose to achieve desired level.";
    var pk_desired_50_tooltip = "Number of calculated doses to reach 50% desired level.";
    var pk_desired_90_tooltip = "Number of calculated doses to reach 90% desired level.";

    $("#label-species-vp").html($("#label-species-vp").html() + make_escaped_tooltip(species_vp_tooltip));
    $("#label-species-ve").html($("#label-species-ve").html() + make_escaped_tooltip(species_ve_tooltip));
    $("#label-species-rei").html($("#label-species-rei").html() + make_escaped_tooltip(species_rei_tooltip));
    $("#label-species-vr").html($("#label-species-vr").html() + make_escaped_tooltip(species_vr_tooltip));
    $("#label-species-asr").html($("#label-species-asr").html() + make_escaped_tooltip(species_asr_tooltip));
    $("#label-species-ki").html($("#label-species-ki").html() + make_escaped_tooltip(species_ki_tooltip));
    $("#label-compound-mw").html($("#label-compound-mw").html() + make_escaped_tooltip(compound_mw_tooltip));
    $("#label-compound-logd").html($("#label-compound-logd").html() + make_escaped_tooltip(compound_logd_tooltip));
    $("#label-compound-pka").html($("#label-compound-pka").html() + make_escaped_tooltip(compound_pka_tooltip));
    // $("#label-compound-bioavailability").html($("#label-compound-bioavailability").html() + make_escaped_tooltip(compound_bioavailability_tooltip));
    $("#label-compound-fu").html($("#label-compound-fu").html() + make_escaped_tooltip(compound_fu_tooltip));
    $("#label-input-icl").html($("#label-input-icl").html() + make_escaped_tooltip(input_icl_tooltip));
    $("#label-input-fa").html($("#label-input-fa").html() + make_escaped_tooltip(input_fa_tooltip));
    $("#label-input-ka").html($("#label-input-ka").html() + make_escaped_tooltip(input_ka_tooltip));
    $("#label-input-dosing-cp").html($("#label-input-dosing-cp").html() + make_escaped_tooltip(input_dosing_cp_tooltip));
    $("#label-input-dosing-interval").html($("#label-input-dosing-interval").html() + make_escaped_tooltip(input_dosing_interval_tooltip));
    $("#label-input-plasma-dose").html($("#label-input-plasma-dose").html() + make_escaped_tooltip(input_plasma_dose_tooltip));
    $("#label-input-plasma-dose-interval").html($("#label-input-plasma-dose-interval").html() + make_escaped_tooltip(input_plasma_dose_interval_tooltip));
    $("#label-pk-param-vdss").html($("#label-pk-param-vdss").html() + make_escaped_tooltip(pk_param_vdss_tooltip));
    $("#label-pk-param-ke").html($("#label-pk-param-ke").html() + make_escaped_tooltip(pk_param_ke_tooltip));
    $("#label-pk-param-halflife").html($("#label-pk-param-halflife").html() + make_escaped_tooltip(pk_param_halflife_tooltip));
    $("#label-pk-param-auc").html($("#label-pk-param-auc").html() + make_escaped_tooltip(pk_param_auc_tooltip));
    $("#label-pk-param-elogd").html($("#label-pk-param-elogd").html() + make_escaped_tooltip(pk_param_elogd_tooltip));
    $("#label-pk-param-vc").html($("#label-pk-param-vc").html() + make_escaped_tooltip(pk_param_vc_tooltip));
    $("#label-pk-param-logvow").html($("#label-pk-param-logvow").html() + make_escaped_tooltip(pk_param_logvow_tooltip));
    $("#label-pk-param-cl").html($("#label-pk-param-cl").html() + make_escaped_tooltip(pk_param_cl_tooltip));
    $("#label-pk-param-fut").html($("#label-pk-param-fut").html() + make_escaped_tooltip(pk_param_fut_tooltip));
    $("#label-pk-param-fi").html($("#label-pk-param-fi").html() + make_escaped_tooltip(pk_param_fi_tooltip));
    $("#label-pk-single-mmax").html($("#label-pk-single-mmax").html() + make_escaped_tooltip(pk_single_mmax_tooltip));
    $("#label-pk-single-cmax").html($("#label-pk-single-cmax").html() + make_escaped_tooltip(pk_single_cmax_tooltip));
    $("#label-pk-single-tmax").html($("#label-pk-single-tmax").html() + make_escaped_tooltip(pk_single_tmax_tooltip));
    $("#label-pk-multi-mss").html($("#label-pk-multi-mss").html() + make_escaped_tooltip(pk_multi_mss_tooltip));
    $("#label-pk-multi-css").html($("#label-pk-multi-css").html() + make_escaped_tooltip(pk_multi_css_tooltip));
    $("#label-pk-multi-tmax").html($("#label-pk-multi-tmax").html() + make_escaped_tooltip(pk_multi_tmax_tooltip));
    $("#label-pk-desired-dose").html($("#label-pk-desired-dose").html() + make_escaped_tooltip(pk_desired_dose_tooltip));
    $("#label-pk-desired-50").html($("#label-pk-desired-50").html() + make_escaped_tooltip(pk_desired_50_tooltip));
    $("#label-pk-desired-90").html($("#label-pk-desired-90").html() + make_escaped_tooltip(pk_desired_90_tooltip));

    var group_table_columns = [
        {
            title: "Select",
            "render": function (data, type, row, meta) {
                if (type === 'display') {
                    return '<input type="checkbox" class="big-checkbox pk-set-checkbox" data-row-info="'+ encodeURIComponent(JSON.stringify(["", row.row, study_name_to_pk_params[treatment_groups[data_groups[row.row][4]]["Study"].split("/")[3]]["PK Type"], treatment_groups[data_groups[row.row][4]]["Compounds"], treatment_groups[data_groups[row.row][4]]["Study"].split(">")[1].slice(0,-4), treatment_groups[data_groups[row.row][4]]["MPS Model"].split(">")[1].slice(0,-4), treatment_groups[data_groups[row.row][4]]["Device"], data_groups[row.row][0], data_groups[row.row][2], data_groups[row.row][3], study_name_to_pk_params[treatment_groups[data_groups[row.row][4]]["Study"].split("/")[3]]["Total Device Volume"], study_name_to_pk_params[treatment_groups[data_groups[row.row][4]]["Study"].split("/")[3]]["Flow Rate"], study_name_to_pk_params[treatment_groups[data_groups[row.row][4]]["Study"].split("/")[3]]["Relevant Cells"], treatment_groups[data_groups[row.row][4]]["item_ids"].length, chart_data[row.row].length-1])) +'" data-table-index="' + meta.row + '">';
                }
                return '';
            },
            "className": "dt-center",
            // "createdCell": function (td, cellData, rowData, row, col) {
            //     if (cellData) {
            //         $(td).css('vertical-align', 'middle');
            //     }
            // },
            "sortable": false,
            width: '5%'
        },
        {
            title: "PK Set",
            type: "brute-numeric",
            "render": function (data, type, row) {
                return '<span class="badge badge-primary data-power-analysis-group-info">' + row.row + '</span>';
            },
            width: '5%'
        },
        {
            title: "PK Type",
            "render": function (data, type, row) {
                return study_name_to_pk_params[treatment_groups[data_groups[row.row][4]]["Study"].split("/")[3]]["PK Type"];
            },
            width: '20%'
        },
        {
            title: "Compound",
            "render": function (data, type, row) {
                return treatment_groups[data_groups[row.row][4]]["Compounds"];
            },
            width: '20%'
        },
        {
            title: "Study",
            "render": function (data, type, row) {
                return treatment_groups[data_groups[row.row][4]]["Study"];
            }
        },
        {
            title: "MPS Model",
            "render": function (data, type, row) {
                return treatment_groups[data_groups[row.row][4]]["MPS Model"];
            }
        },
        {
            title: "Device",
            "render": function (data, type, row) {
                return treatment_groups[data_groups[row.row][4]]["Device"];
            }
        },
        {
            title: "Target/Analyte",
            "render": function (data, type, row) {
                return data_groups[row.row][0];
            },
            width: '20%'
        },
        {
            title: "Method/Kit",
            "render": function (data, type, row) {
                return data_groups[row.row][2];
            },
            width: '20%'
        },
        {
            title: "Sample Location",
            "render": function (data, type, row) {
                return data_groups[row.row][3];
            }
        },
        {
            title: "Total Device Volume (&micro;L)",
            "render": function (data, type, row) {
                return study_name_to_pk_params[treatment_groups[data_groups[row.row][4]]["Study"].split("/")[3]]["Total Device Volume"];
            },
            width: '20%'
        },
        {
            title: "Flow Rate (&micro;L/hour)",
            "render": function (data, type, row) {
                return study_name_to_pk_params[treatment_groups[data_groups[row.row][4]]["Study"].split("/")[3]]["Flow Rate"];
            },
            width: '20%'
        },
        {
            title: "No. of Cells in MPS Model",
            "render": function (data, type, row) {
                return study_name_to_pk_params[treatment_groups[data_groups[row.row][4]]["Study"].split("/")[3]]["Relevant Cells"];
            },
            width: '20%'
        },
        {
            title: "No. of Chips",
            "render": function (data, type, row) {
                return treatment_groups[data_groups[row.row][4]]["item_ids"].length;
            },
            width: '20%'
        },
        {
            title: "No. of Time Points",
            "render": function (data, type, row) {
                return chart_data[row.row].length-1;
            },
            width: '20%'
        }
    ];

    // TODO Modify for badges/and selection parameters
    function populate_selection_table(set, current_table) {
        var current_body = current_table.find('tbody');

        var rows = [];

        $.each(header_keys['data'], function(index, key) {
            if (key === 'Target') {
                rows.push(
                    '<th><h4><strong>Target/Analyte</strong></h4></th><td><h4><strong>' + data_groups[set][index] + '</strong></h4></td>'
                );
            } else {
                rows.push(
                    '<th>' + key + '</th><td>' + data_groups[set][index] + '</td>'
                );
            }
        });

        var current_treatment_group = data_groups[set][data_groups[set].length - 1];

        $.each(header_keys['treatment'], function(index, key) {
            rows.push(
                '<th>' + key + '</th><td>' + treatment_groups[current_treatment_group][key] + '</td>'
            );
        });

        rows.push(
            '<th>Studies</th><td>' + data_group_to_studies[set].join('<br>') + '</td>'
        );

        rows = rows.join('');
        current_body.html(rows);
    }

    function refresh_pbpk() {
        window.spinner.spin(
            document.getElementById("spinner")
        );

        // Hide any lingering junk
        $('#pbpk-information').hide();
        // Manually clear clearance among other things (HAR HAR *HAR*)
        clear_pbpk();

        if (group_table) {
            group_table.clear();
            group_table.destroy();

            // KILL ALL LINGERING HEADERS
            $('.fixedHeader-locked').remove();
        }

        group_table = $('#group-table').DataTable({
            ajax: {
                url: '/assays_ajax/',
                data: {
                    call: 'fetch_pbpk_group_table',
                    criteria: JSON.stringify(window.GROUPING.group_criteria),
                    filters: JSON.stringify(window.GROUPING.filters),
                    post_filter: JSON.stringify(window.GROUPING.current_post_filter),
                    full_post_filter: JSON.stringify(window.GROUPING.full_post_filter),
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                type: 'POST',
                dataSrc: function(json) {
                    // console.log(json);
                    header_keys = json.header_keys;
                    chart_data = json.chart_data;
                    data_groups = json.data_groups;
                    treatment_groups = json.treatment_groups;
                    selection_table = json.selection_table;
                    study_name_to_pk_params = json.study_name_to_pk_params;

                    // post_filter setup
                    window.GROUPING.set_grouping_filtering(json.post_filter);

                    // Generate selection TABLES
                    // populate_selection_tables();

                    // Stop spinner
                    window.spinner.stop();

                    var contrived_data = [];

                    $.each(Object.keys(data_groups), function(index, value) {
                        var contrived_vals = {
                            row: value,
                            '0': 0
                        }

                        for (var x = 0; x < 15; x++) {
                            contrived_vals[x] = x;
                        }

                        contrived_data.push(contrived_vals);
                    });

                    // console.log(contrived_data);

                    // return Object.keys(data_groups);
                    return contrived_data;
                },
                // Error callback
                error: function (xhr, errmsg, err) {
                    // Stop spinner
                    window.spinner.stop();

                    alert('An error has occurred, please try different selections.');
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            },
            aoColumns: group_table_columns,
            columnDefs: [
                { "responsivePriority": 1, "targets": [0, 1, 2, 3, 4, 5, 6, 7, 8, 13, 14] },
                { "responsivePriority": 2, "targets": [9, 10, 11, 12] }
            ],
            order: [1, 'asc'],
            responsive: true,
            dom: 'B<"row">lfrtip',
            paging: false,
            fixedHeader: {headerOffset: 50},
            deferRender: true,
        });
    }

    // Group Table Checkbox click event
    $(document).on("click", ".pk-set-checkbox", function() {
        checkbox = $(this);

        // Hide all children rows
        group_table.rows('.parent').nodes().to$().find('td:first-child').trigger('click')

        if (checkbox.is(':checked')) {
            $('.pk-set-checkbox').each(function() {
                if (!this.checked) {
                    $(this).parent().parent().hide();
                }
            });
            group_number = checkbox.attr('data-table-index');
            row_info = JSON.parse(decodeURIComponent(checkbox.attr('data-row-info')));
            pk_type = row_info[2];
            generate_pbpk(pk_type);
        } else {
            $('.pk-set-checkbox').each(function() {
                if (!this.checked) {
                    $(this).parent().parent().show();
                }
            });
            clear_pbpk();
        }

        // Activates Bootstrap tooltips
        $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
        // Recalc Fixed Headers
        $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
    });

    function clear_pbpk() {
        $('#pbpk-information').hide();
        $('#predict-dosing-container').hide();
        $('#calculated-pk-container').hide();
        start_time_dropdown.clear();
        end_time_dropdown.clear();
        start_time_dropdown.clearOptions();
        end_time_dropdown.clearOptions();
        $("#compound-compound").val('');
        $("#compound-mw").val('');
        $("#compound-logd").val('');
        $("#compound-pka").val('');
        // $("#compound-bioavailability").val('');
        $("#compound-fu").val('');
        $('#pbpk-error-container').hide();
        clear_clearance();
    }

    function clear_clearance() {
        $('#pk-summary-graph').empty();
        $('#pk-clearance-graph').empty();
        $('#continuous-infusion-table').empty();
        $("#toggle-continuous-infusion-table").hide();

        // Manually clear clearance (HAR HAR *HAR*)
        $('#input-icl').val('');
    }

    function generate_pbpk(pk_type) {
        $('#pbpk-information').show();
        group_num = parseInt(group_number)+1;

        // Hide appropriate fields depending on PK Type.
        if (pk_type === "Bolus") {
            $("#experiment-total-vol").parent().parent().show();
            $("#experiment-flow-rate").parent().parent().hide();
            $('#continuous-infusion-table').hide();
            $("#toggle-continuous-infusion-table").hide();
            $("#start-time-label").text("Calculation Start Time");
            $("#end-time-label").text("Calculation End Time");
        } else {
            $("#experiment-total-vol").parent().parent().hide();
            $("#experiment-flow-rate").parent().parent().show();
            $('#continuous-infusion-table').hide();
            $("#toggle-continuous-infusion-table").show();
            $("#start-time-label").text("Steady State Start Time");
            $("#end-time-label").text("Steady State End Time");
        }

        // Populate Experiment Parameters Table.
        $("#experiment-pk-type").val(row_info[2]);
        $("#experiment-compound").val(row_info[3]);
        $("#experiment-study").val(row_info[4]);
        $("#experiment-model").val(row_info[5]);
        $("#experiment-device").val(row_info[6]);
        $("#experiment-target").val(row_info[7]);
        $("#experiment-method").val(row_info[8]);
        $("#experiment-location").val(row_info[9]);
        $("#experiment-flow-rate").val(row_info[11]);
        $("#experiment-total-vol").val(row_info[10]);
        $("#experiment-number-cells").val(numberWithCommas(row_info[12]));

        // Populate Experiment Parameters Table.
        $("#experiment-pk-type").attr("title", row_info[2]);
        $("#experiment-compound").attr("title", row_info[3]);
        $("#experiment-study").attr("title", row_info[4]);
        $("#experiment-model").attr("title", row_info[5]);
        $("#experiment-device").attr("title", row_info[6]);
        $("#experiment-target").attr("title", row_info[7]);
        $("#experiment-method").attr("title", row_info[8]);
        $("#experiment-location").attr("title", row_info[9]);
        $("#experiment-flow-rate").attr("title", row_info[11]);
        $("#experiment-total-vol").attr("title", row_info[10]);
        $("#experiment-number-cells").attr("title", numberWithCommas(row_info[12]));

        // PK Type Specific Logic
        $("#number-of-cells-calc").val(numberWithCommas(row_info[12]));
        if (row_info[2] === "Bolus") {
            $("#cell-free").hide();
        } else {
            $("#cell-free").show();
        }

        var pk_compound = row_info[3];

        // Populate Species Parameters Table.
        // TODO Hardcoded for now; to be generalized and allow selection in time.
        $.ajax(
            "/assays_ajax/",
            {
                data: {
                    call: 'fetch_species_parameters',
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
                },
                type: 'POST',
            }
        )
        .done(function(data) {
            // Stop spinner
            window.spinner.stop();

            $("#species-species").val(data.species);
            $("#species-organ").val(data.organ);
            $("#species-body-mass").val(data.body_mass);
            $("#species-total-organ-weight").val(numberWithCommas(data.total_organ_weight));
            $("#species-organ-tissue").val(numberWithCommas(data.organ_tissue));
            $("#species-plasma-vol").val(data.plasma_volume);
            $("#species-vp").val(data.vp);
            $("#species-ve").val(data.ve);
            $("#species-rei").val(data.rei);
            $("#species-vr").val(data.vr);
            $("#species-asr").val(data.asr);
            $("#species-ki").val(data.ki);
            $("#species-reference").html('<a href="'+data.reference_url+'" target="_blank">'+data.reference+'</a><br><br><a href="'+data.additional_reference_url+'" target="_blank">'+data.additional_reference+'</a>');
        })
        .fail(function(xhr, errmsg, err) {
            // Stop spinner
            window.spinner.stop();

            alert('Error retrieving Species Parameters table.');
            console.log(xhr.status + ": " + xhr.responseText);
        });
        // console.log("Done with Species Parameters.")

        // Start/End Time Dropdowns
        $.each(chart_data[group_num].slice(1), function() {
            start_time_dropdown.addOption([{value: this[0], text: this[0]}]);
            end_time_dropdown.addOption([{value: this[0], text: this[0]}]);
        });
        start_time_dropdown.setValue(chart_data[group_num][1][0]);
        end_time_dropdown.setValue(chart_data[group_num][chart_data[group_num].length-1][0]);

        // Cell Parameters Table
        cell_profiles = [];
        has_no_cells = false;

        $.each(chart_data[group_num][0], function() {
            current_cell_profile = this.split('     ')[0].trim();
            if (cell_profiles.indexOf(current_cell_profile) === -1 && current_cell_profile !== '-No Cell Samples-' && current_cell_profile !== 'Time') {
                cell_profiles.push(current_cell_profile);
            }
            if (current_cell_profile === '-No Cell Samples-') {
                has_no_cells = true;
            }
        });

        if (cell_profiles.length === 1) {
            $('#cell-profiles-table').hide();
        } else {
            $('#cell-profiles-table').show();
        }

        if (!has_no_cells) {
            $('#cell-free-checkbox').attr("disabled", true);
            $('#cell-free-checkbox').attr("checked", false);
        } else {
            $('#cell-free-checkbox').attr("disabled", false);
        }

        cell_profiles_table = '<tr><th class="text-center">&nbsp;Select&nbsp;</th><th class="text-center">&nbsp;Cells&nbsp;</th></tr>';
        cell_profile_counter = 1;
        $.each(cell_profiles, function() {
            if (cell_profile_counter === 1) {
                cell_profiles_table += '<tr style="padding: 10px;"><td class="text-center"><input type="radio" class="big-checkbox" name="cell-profile" value="' + cell_profile_counter + '" checked></td><td data-cell-profile="'+cell_profile_counter+'"><br>' + this +'<br>&nbsp;</td></tr>';
            } else {
                cell_profiles_table += '<tr style="padding: 10px;"><td class="text-center"><input type="radio" class="big-checkbox" name="cell-profile" value="' + cell_profile_counter + '"></td><td data-cell-profile="'+cell_profile_counter+'"><br>' + this +'<br>&nbsp;</td></tr>';
            }
            cell_profile_counter += 1;
        })
        $('#cell-profiles-table').html(cell_profiles_table);

        // Create initial chart
        update_chart();

        // Populate Compound Physicochemical Parameters Table.
        $.ajax(
            "/assays_ajax/",
            {
                data: {
                    call: 'fetch_compound_physicochemical_parameters',
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                    pk_compound: pk_compound
                },
                type: 'POST',
            }
        )
        .done(function(data) {
            // Stop spinner
            window.spinner.stop();

            $("#compound-compound").val(data.compound);
            $("#compound-mw").val(data.mw);
            $("#compound-logd").val(data.logd);
            acidic_pka = data.acidic_pka;
            basic_pka = data.basic_pka;
            $("#compound-pka").val(data.basic_pka);
            if ($("#compound-pka").val() == '') {
                $("#compound-pka").val(data.acidic_pka);
            }
            // $("#compound-bioavailability").val(data.bioavailability);
            $("#compound-fu").val(data.fu);
            $("#input-fa").val((parseFloat($("#input-ka").val()) / (parseFloat($("#species-ki").val()) + parseFloat($("#input-ka").val()))).toFixed(3));
            if ($("#input-fa").val() == "NaN") {
                $("#input-fa").val(0.927);
            }
        })
        .fail(function(xhr, errmsg, err) {
            // Stop spinner
            window.spinner.stop();

            alert('Error retrieving Compound Physicochemical Parameters table.');
            console.log(xhr.status + ": " + xhr.responseText);
        });
        // console.log("Done with Compound Parameters.")
    }

    $('#cell-free').change(function() {
        update_chart();
    });

    $(document).on("click", "input[name='cell-profile']", function() {
        update_chart();
    });

    function numberWithCommas(x) {
        return x.toLocaleString('en-US');
    }

    $('#button-dosing').click(function() {
        $('#pbpk-error-container').hide();

        window.spinner.spin(
            document.getElementById("spinner")
        );

        var missing_required_values = false;
        var missing_plasma_values = false;
        var missing_dosing_values = false;
        if ($('#input-icl').val() == '' || isNaN($('#input-icl').val().replace(/\,/g,'')) || $('#input-icl').val()[0] == "-" || !($('#input-icl').val() > 0)) {
            $('#input-icl').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#input-icl').css('background-color', '#fffabb');
        }
        if ($('#species-body-mass').val() == '' || isNaN($('#species-body-mass').val().replace(/\,/g,'')) || $('#species-body-mass').val()[0] == "-" || !($('#species-body-mass').val() > 0)) {
            $('#species-body-mass').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-body-mass').css('background-color', '#fffabb');
        }
        if ($('#compound-mw').val() == '' || isNaN($('#compound-mw').val().replace(/\,/g,'')) || $('#compound-mw').val()[0] == "-") {
            $('#compound-mw').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#compound-mw').css('background-color', '#fffabb');
        }
        if ($('#compound-logd').val() == '' || isNaN($('#compound-logd').val().replace(/\,/g,'')) || $('#compound-logd').val()[0] == "-") {
            $('#compound-logd').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#compound-logd').css('background-color', '#fffabb');
        }
        if ($('#compound-pka').val() == '' || isNaN($('#compound-pka').val().replace(/\,/g,''))) {
            $('#compound-pka').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#compound-pka').css('background-color', '#fffabb');
        }
        if ($('#compound-fu').val() == '' || isNaN($('#compound-fu').val().replace(/\,/g,'')) || $('#compound-fu').val()[0] == "-" || !($('#compound-fu').val() > 0) || $('#compound-fu').val() > 1) {
            $('#compound-fu').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#compound-fu').css('background-color', '#fffabb');
        }
        if ($('#species-vp').val() == '' || isNaN($('#species-vp').val().replace(/\,/g,'')) || $('#species-vp').val()[0] == "-" || !($('#species-vp').val() > 0)) {
            $('#species-vp').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-vp').css('background-color', '#fffabb');
        }
        if ($('#species-ve').val() == '' || isNaN($('#species-ve').val().replace(/\,/g,'')) || $('#species-ve').val()[0] == "-") {
            $('#species-ve').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-ve').css('background-color', '#fffabb');
        }
        if ($('#species-rei').val() == '' || isNaN($('#species-rei').val().replace(/\,/g,'')) || $('#species-rei').val()[0] == "-") {
            $('#species-rei').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-rei').css('background-color', '#fffabb');
        }
        if ($('#species-vr').val() == '' || isNaN($('#species-vr').val().replace(/\,/g,'')) || $('#species-vr').val()[0] == "-") {
            $('#species-vr').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-vr').css('background-color', '#fffabb');
        }
        if ($('#species-asr').val() == '' || isNaN($('#species-asr').val().replace(/\,/g,'')) || $('#species-asr').val()[0] == "-") {
            $('#species-asr').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-asr').css('background-color', '#fffabb');
        }
        if ($('#species-ki').val() == '' || isNaN($('#species-ki').val().replace(/\,/g,'')) || $('#species-ki').val()[0] == "-") {
            $('#species-ki').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-ki').css('background-color', '#fffabb');
        }
        if ($('#input-ka').val() == '' || isNaN($('#input-ka').val().replace(/\,/g,'')) || $('#input-ka').val()[0] == "-" || !($('#input-ka').val() > 0)) {
            $('#input-ka').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#input-ka').css('background-color', '#fffabb');
        }
        if ($('#input-fa').val() == '' || isNaN($('#input-fa').val().replace(/\,/g,'')) || $('#input-fa').val()[0] == "-" || !($('#input-fa').val() > 0) || $('#input-fa').val() > 1) {
            $('#input-fa').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#input-fa').css('background-color', '#fffabb');
        }
        $('#input-dosing-cp').css('background-color', '#fffabb');
        $('#input-dosing-interval').css('background-color', '#fffabb');
        $('#input-plasma-dose').css('background-color', '#fffabb');
        $('#input-plasma-dose-interval').css('background-color', '#fffabb');

        if ($('#input-plasma-dose').val() != '' && !isNaN($('#input-plasma-dose').val().replace(/\,/g,'')) && $('#input-plasma-dose').val()[0] != "-" && $('#input-plasma-dose-interval').val() != '' && !isNaN($('#input-plasma-dose-interval').val().replace(/\,/g,'')) && $('#input-plasma-dose-interval').val()[0] != "-" && $('#input-plasma-dose-interval').val() > 0) {
            if ($('#input-dosing-cp').val() != '' && !isNaN($('#input-dosing-cp').val().replace(/\,/g,'')) && $('#input-dosing-cp').val()[0] != "-" && $('#input-dosing-interval').val() != '' && !isNaN($('#input-dosing-interval').val().replace(/\,/g,'')) && $('#input-dosing-interval').val()[0] != "-" && $('#input-dosing-interval').val() > 0) {
                // BOTH ARE GOOD
            } else {
                // ONLY PLASMA VALUES ARE GOOD
                missing_dosing_values = true;
                if ($('#input-plasma-dose').val() == '' || isNaN($('#input-plasma-dose').val().replace(/\,/g,'')) || $('#input-plasma-dose').val()[0] == "-") {
                    $('#input-plasma-dose').css('background-color', '#f2dede');
                }
                if ($('#input-plasma-dose-interval').val() == '' || isNaN($('#input-plasma-dose-interval').val().replace(/\,/g,'')) || $('#input-plasma-dose-interval').val()[0] == "-" || !($('#input-plasma-dose-interval').val() > 0)) {
                    $('#input-plasma-dose-interval').css('background-color', '#f2dede');
                }
            }
        } else {
            missing_plasma_values = true;
            if ($('#input-dosing-cp').val() != '' && !isNaN($('#input-dosing-cp').val().replace(/\,/g,'')) && $('#input-dosing-cp').val()[0] != "-" && $('#input-dosing-interval').val() != '' && !isNaN($('#input-dosing-interval').val().replace(/\,/g,'')) && $('#input-dosing-interval').val()[0] != "-") {
                // ONLY DOSING VALUES ARE GOOD
                if ($('#input-dosing-cp').val() == '' || isNaN($('#input-dosing-cp').val().replace(/\,/g,'')) || $('#input-dosing-cp').val()[0] == "-") {
                    $('#input-dosing-cp').css('background-color', '#f2dede');
                }
                if ($('#input-dosing-interval').val() == '' || isNaN($('#input-dosing-interval').val().replace(/\,/g,'')) || $('#input-dosing-interval').val()[0] == "-" || !($('#input-dosing-interval').val() > 0)) {
                    $('#input-dosing-interval').css('background-color', '#f2dede');
                }
            } else {
                // NEITHER ARE GOOD
                missing_dosing_values = true;
                if ($('#input-dosing-cp').val() == '' || isNaN($('#input-dosing-cp').val().replace(/\,/g,'')) || $('#input-dosing-cp').val()[0] == "-") {
                    $('#input-dosing-cp').css('background-color', '#f2dede');
                }
                if ($('#input-dosing-interval').val() == '' || isNaN($('#input-dosing-interval').val().replace(/\,/g,'')) || $('#input-dosing-interval').val()[0] == "-" || !($('#input-dosing-interval').val() > 0)) {
                    $('#input-dosing-interval').css('background-color', '#f2dede');
                }
                if ($('#input-plasma-dose').val() == '' || isNaN($('#input-plasma-dose').val().replace(/\,/g,'')) || $('#input-plasma-dose').val()[0] == "-") {
                    $('#input-plasma-dose').css('background-color', '#f2dede');
                }
                if ($('#input-plasma-dose-interval').val() == '' || isNaN($('#input-plasma-dose-interval').val().replace(/\,/g,'')) || $('#input-plasma-dose-interval').val()[0] == "-" || !($('#input-plasma-dose-interval').val() > 0)) {
                    $('#input-plasma-dose-interval').css('background-color', '#f2dede');
                }
            }
        }

        if (missing_required_values || (missing_plasma_values && missing_dosing_values)) {
            window.spinner.stop();
            $('#calculated-pk-container').hide();
            $('#pbpk-error-container').show();
            $('#pbpk-error-text').text('There are missing or invalid values required to perform PBPK analysis. Please fill them out and try again.');
            return;
        }

        $.ajax(
            "/assays_ajax/",
            {
                data: {
                    call: 'fetch_pbpk_dosing_results',
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                    cl_ml_min: $('#input-icl').val().replace(/\,/g,''),
                    body_mass: $('#species-body-mass').val(),
                    MW: $('#compound-mw').val(),
                    logD: $('#compound-logd').val(),
                    pKa: $('#compound-pka').val(),
                    fu: $('#compound-fu').val(),
                    Vp: $('#species-vp').val(),
                    VE: $('#species-ve').val(),
                    REI: $('#species-rei').val(),
                    VR: $('#species-vr').val(),
                    ASR: $('#species-asr').val(),
                    Ki: $('#species-ki').val(),
                    Ka: $('#input-ka').val(),
                    Fa: $('#input-fa').val(),
                    dose_mg: $('#input-plasma-dose').val(),
                    dose_interval: $('#input-plasma-dose-interval').val(),
                    desired_Cp: $('#input-dosing-cp').val(),
                    desired_dose_interval: $('#input-dosing-interval').val(),
                    estimated_fraction_absorbed: $('#input-fa').val(),
                    prediction_time_length: 720,
                    missing_plasma_values: missing_plasma_values,
                    missing_dosing_values: missing_dosing_values,
                    acidic_basic: $("input[name='acid-base']:checked").val()
                },
                type: 'POST',
            }
        )
        .done(function(data) {
            // console.log(data);
            // Stop spinner
            window.spinner.stop();

            if ("error" in data) {
                $('#pbpk-error-text').text(data.error);
                $('#pbpk-error-container').show();
                $('#calculated-pk-container').hide();
            } else {
                $('#calculated-pk-container').show();
                if (missing_plasma_values) {
                    // $('#plasma-container').hide();
                    $('#plasma-dose-container').hide()
                    $('#dosing-chart-container').hide();
                    $('#pk-param-vdss').val(numberWithCommas(data.calculated_pk_parameters['VDss (L)'][0].toFixed(3)));
                    $('#pk-param-ke').val(numberWithCommas(data.calculated_pk_parameters['Ke(1/h)'][0].toFixed(3)));
                    $('#pk-param-half-life-3-confirmed').val(numberWithCommas(data.calculated_pk_parameters['Elimination half-life'][0].toFixed(3)));
                    $('#pk-param-auc').val('');
                } else {
                    $('#plasma-container').show();
                    $('#plasma-dose-container').show()
                    $('#dosing-chart-container').show();
                    $('#pk-param-vdss').val(numberWithCommas(data.calculated_pk_parameters['VDss (L)'][0].toFixed(3)));
                    $('#pk-param-ke').val(numberWithCommas(data.calculated_pk_parameters['Ke(1/h)'][0].toFixed(3)));
                    $('#pk-param-half-life-3-confirmed').val(numberWithCommas(data.calculated_pk_parameters['Elimination half-life'][0].toFixed(3)));
                    $('#pk-param-auc').val(numberWithCommas(data.calculated_pk_parameters['AUC'][0].toFixed(3)));
                    $('#pk-param-elogd').val(numberWithCommas(data.calculated_pk_parameters['ELogD'][0].toFixed(3)));
                    $('#pk-param-vc').val(numberWithCommas(data.calculated_pk_parameters['Vc (L)'][0].toFixed(3)));
                    $('#pk-param-logvow').val(numberWithCommas(data.calculated_pk_parameters['Logvo/w'][0].toFixed(3)));
                    $('#pk-param-cl').val(numberWithCommas(data.calculated_pk_parameters['CL (L/h)'][0].toFixed(3)));
                    $('#pk-param-fut').val(numberWithCommas(data.calculated_pk_parameters['fut'][0].toFixed(3)));
                    $('#pk-param-fi').val(numberWithCommas(data.calculated_pk_parameters['fi(7.4)'][0].toFixed(3)));
                    $('#pk-single-mmax').val(numberWithCommas(data.dosing_data[0].toFixed(3)));
                    $('#pk-single-cmax').val(numberWithCommas(data.dosing_data[1].toFixed(3)));
                    $('#pk-single-tmax').val(numberWithCommas(data.dosing_data[2].toFixed(3)));
                    $('#pk-multi-mss').val(numberWithCommas(data.dosing_data[3].toFixed(3)));
                    $('#pk-multi-css').val(numberWithCommas(data.dosing_data[4].toFixed(3)));
                    $('#pk-multi-tmax').val(numberWithCommas(data.dosing_data[5].toFixed(3)));

                    prediction_plot_data = JSON.parse(JSON.stringify(data.prediction_plot_table));
                    make_dosing_plot(prediction_plot_data, 48)
                    $('#dosing-slider').slider("value", 48);
                    $('#dosing-slider-handle').text("48");
                }
                if (missing_dosing_values) {
                    $('#dosing-container').hide();
                } else {
                    $('#dosing-container').show();
                    $('#pk-desired-dose').val(numberWithCommas(data.dosing_data[6].toFixed(3)));
                    $('#pk-desired-50').val(numberWithCommas(data.dosing_data[7].toFixed(3)));
                    $('#pk-desired-90').val(numberWithCommas(data.dosing_data[8].toFixed(3)));
                }
            }
        })
        .fail(function(xhr, errmsg, err) {
            // Stop spinner
            window.spinner.stop();

            alert('Error retrieving Dosing Prediction.');
            console.log(xhr.status + ": " + xhr.responseText);
        });
        // console.log("Done with Dosing Prediction.")
    })

    $('#button-clearance').click(function() {
        if (start_time_dropdown.getValue() == "") {
            start_time_dropdown.setValue(chart_data[group_num][1][0]);
        }
        if (end_time_dropdown.getValue() == "") {
            end_time_dropdown.setValue(chart_data[group_num][chart_data[group_num].length-1][0]);
        }
        if (pk_type == "Bolus") {
            if (end_time_dropdown.getValue() == start_time_dropdown.getValue()) {
                $('#clearance-error-text').text('"Start Time" and "End Time" must differ for Bolus datasets.');
                $('#clearance-error-container').show();
                clear_clearance();
                return;
            }
            if (end_time_dropdown.getValue() < start_time_dropdown.getValue()) {
                $('#clearance-error-text').text('The Selected "Start Time" comes after the selected "End Time". Please adjust these parameters and run the calculation again.');
                $('#clearance-error-container').show();
                clear_clearance();
                return;
            }
        }

        var missing_required_values = false;
        if ($('#number-of-cells-calc').val() == '' || isNaN($('#number-of-cells-calc').val().replace(/\,/g,'')) || $('#number-of-cells-calc').val()[0] == "-") {
            $('#number-of-cells-calc').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#number-of-cells-calc').css('background-color', '#fffabb');
        }
        if ($('#species-organ-tissue').val() == '' || isNaN($('#species-organ-tissue').val().replace(/\,/g,'')) || $('#species-organ-tissue').val()[0] == "-") {
            $('#species-organ-tissue').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-organ-tissue').css('background-color', '#fffabb');
        }
        if ($('#species-total-organ-weight').val() == '' || isNaN($('#species-total-organ-weight').val().replace(/\,/g,'')) || $('#species-total-organ-weight').val()[0] == "-") {
            $('#species-total-organ-weight').css('background-color', '#f2dede');
            missing_required_values = true;
        } else {
            $('#species-total-organ-weight').css('background-color', '#fffabb');
        }

        if (missing_required_values) {
            window.spinner.stop();
            $('#calculated-pk-container').hide();
            $('#clearance-error-container').show();
            $('#clearance-error-text').text('There are missing or invalid values required to perform PBPK clearance calculations. Please fill them out and try again.');
            clear_clearance();
            return;
        }

        $('#clearance-error-container').hide();

        window.spinner.spin(
            document.getElementById("spinner")
        );

        // An incoherent ternary, but you know, whatever!
        var compound_pk_data = JSON.stringify(chart_data[group_num], function(key, value) {return (value == null) ? null : value});
        for (var x=1; x<compound_pk_data.length; x++) {
            compound_pk_data[x][0] *= 60;
        }
        $.ajax(
            "/assays_ajax/",
            {
                data: {
                    call: 'fetch_pbpk_intrinsic_clearance_results',
                    csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                    pk_type: pk_type,
                    with_no_cell_data: $('#cell-free-checkbox').is(":checked"),
                    cell_name: $("input[name='cell-profile']:checked").parent().next().text(),
                    start_time: start_time_dropdown.getValue(),
                    end_time: end_time_dropdown.getValue(),
                    total_device_vol_ul: $('#experiment-total-vol').val(),
                    total_cells_in_device: $('#number-of-cells-calc').val().replace(/\,/g,''),
                    flow_rate: $('#experiment-flow-rate').val(),
                    cells_per_tissue_g: $('#species-organ-tissue').val().replace(/\,/g,''),
                    total_organ_weight_g: $('#species-total-organ-weight').val().replace(/\,/g,''),
                    compound_conc: $('#experiment-compound').val().split(" ")[$('#experiment-compound').val().split(" ").length - 3],
                    compound_pk_data: compound_pk_data,
                },
                type: 'POST',
            }
        )
        .done(function(data) {
            // Stop spinner
            window.spinner.stop();

            clear_clearance();
            $('#pbpk-error-container').hide();

            if ("error" in data) {
                $('#pbpk-error-text').text(data.error);
                $('#pbpk-error-container').show();
            } else {
                pbpk_intrinsic_clearance = data.clearance;
                $('#input-icl').val(numberWithCommas(pbpk_intrinsic_clearance.toFixed(3)));

                var chart_data_final = JSON.parse(JSON.stringify(chart_data[group_num]));

                var first_row = chart_data_final[0]
                for (var x=0; x<chart_data_final.length; x++) {
                    if (chart_data_final[x][0].toString() === start_time_dropdown.getValue()) {
                        chart_data_final.unshift(first_row);
                        break;
                    } else {
                        chart_data_final.shift();
                        x-=1;
                    }
                }
                for (var x=chart_data_final.length-1; x>0; x--) {
                    if (chart_data_final[x][0].toString() === end_time_dropdown.getValue()) {
                        break;
                    } else {
                        chart_data_final.pop();
                    }
                }

                if (pk_type == 'Bolus') {
                    var bolus_data = JSON.parse(JSON.stringify(chart_data_final));
                    bolus_data[0][0] = "Time (Minutes)";
                    for (var x=1; x<bolus_data.length; x++) {
                        bolus_data[x][0] *= 60;
                    }
                    $("#toggle-continuous-infusion-table").hide();
                    make_chart("", 'Avg Recovered Compound (µM)', $('#pk-summary-graph')[0], JSON.parse(JSON.stringify(bolus_data)), 400);
                } else {
                    var clearance_table_data = data.clearance_data.data;

                    for (var x=0; x<clearance_table_data.length; x++) {
                        // We have to accommodate for diverging times
                        // if (clearance_table_data[x][clearance_table_data[0].length-1].toString() === start_time_dropdown.getValue()) {
                        if (clearance_table_data[x][clearance_table_data[0].length-1] >= parseFloat(start_time_dropdown.getValue())) {
                            break;
                        } else {
                            clearance_table_data.shift();
                            x-=1;
                        }
                    }
                    for (var x=clearance_table_data.length-1; x>0; x--) {
                        // We have to accommodate for diverging times
                        // if (clearance_table_data[x][clearance_table_data[0].length-1].toString() === end_time_dropdown.getValue()) {
                        if (clearance_table_data[x][clearance_table_data[0].length-1] <= parseFloat(end_time_dropdown.getValue())) {
                            break;
                        } else {
                            clearance_table_data.pop();
                        }
                    }

                    clearance_table_data.unshift(data.clearance_data.columns);
                    var clearance_chart_data = JSON.parse(JSON.stringify(clearance_table_data));
                    remove_col(clearance_chart_data, 3);
                    remove_col(clearance_chart_data, 3);
                    remove_col(clearance_chart_data, 0);
                    remove_col(clearance_chart_data, 0);
                    for (var x=0; x<clearance_table_data.length; x++) {
                        clearance_chart_data[x].unshift(clearance_chart_data[x][1])
                    }
                    remove_col(clearance_chart_data, 2);

                    var clearance_table_html = "";
                    if ($('#cell-free-checkbox').is(":checked")) {
                        clearance_table_html = "<tr><th>Compound Recovered From Device Without Cells (&micro;M)</th><th>Compound Recovered From Device With Cells (&micro;M)</th><th>Extraction Ratio</th><th>Clearance from MPS Model (&micro;L/h)</th><th>Predicted Intrinsic Clearance (&micro;L/min)</th><th>Time (Hours)</th></tr>"
                        for (var x=1; x<clearance_table_data.length; x++) {
                            clearance_table_html += "<tr><td>"+clearance_table_data[x][0].toFixed(3)+"</td><td>"+clearance_table_data[x][1].toFixed(3)+"</td><td>"+clearance_table_data[x][2].toFixed(3)+"</td><td>"+clearance_table_data[x][3].toFixed(3)+"</td><td>"+clearance_table_data[x][4].toFixed(3)+"</td><td>"+clearance_table_data[x][5]+"</td></tr>"
                        }
                    } else {
                        clearance_table_html = "<tr><th>Compound Recovered From Device With Cells (&micro;M)</th><th>Extraction Ratio</th><th>Clearance from MPS Model (&micro;L/h)</th><th>Predicted Intrinsic Clearance (&micro;L/min)</th><th>Time (Hours)</th></tr>"
                        for (var x=1; x<clearance_table_data.length; x++) {
                            clearance_table_html += "<tr><td>"+clearance_table_data[x][1].toFixed(3)+"</td><td>"+clearance_table_data[x][2].toFixed(3)+"</td><td>"+clearance_table_data[x][3].toFixed(3)+"</td><td>"+clearance_table_data[x][4].toFixed(3)+"</td><td>"+clearance_table_data[x][5]+"</td></tr>"
                        }
                    }

                    $('#continuous-infusion-table').html(clearance_table_html)
                    $("#toggle-continuous-infusion-table").show();

                    make_chart("", 'Avg Recovered Compound (µM)', $('#pk-summary-graph')[0], JSON.parse(JSON.stringify(chart_data_final)), 250);

                    options = {
                        title: '',
                        interpolateNulls: true,
                        tooltip: {
                            isHtml: true
                        },
                        titleTextStyle: {
                            fontSize: 18,
                            bold: true,
                            underline: true
                        },
                        legend: {
                            position: 'top',
                            maxLines: 5,
                            textStyle: {
                                bold: true
                            }
                        },
                        hAxis: {
                            title: 'Time (Hours)',
                            textStyle: {
                                bold: true
                            },
                            titleTextStyle: {
                                fontSize: 14,
                                bold: true,
                                italic: false
                            }
                        },
                        vAxis: {
                            title: 'Extraction Ratio',
                            format: '',
                            textStyle: {
                                bold: true
                            },
                            titleTextStyle: {
                                fontSize: 14,
                                bold: true,
                                italic: false
                            },
                            minValue: 0,
                            viewWindowMode: 'explicit'
                        },
                        pointSize: 5,
                        'chartArea': {
                            'width': '70%',
                            'height': '70%',
                            left: 100
                        },
                        'height': 250,
                        focusTarget: 'datum',
                        intervals: {
                            'lineWidth': 0.75
                        },
                        tracking: {
                            is_default: true,
                            use_dose_response: false,
                            time_conversion: 1,
                            chart_type: 'scatter',
                            tooltip_type: 'datum',
                            revised_unit: null,
                            use_x_log: false,
                            use_y_log: false
                        },
                        ajax_data: {
                            key: 'device',
                            mean_type: 'arithmetic',
                            interval_type: 'ste',
                            number_for_interval: '1',
                            percent_control: '',
                            truncate_negative: ''
                        }
                    };

                    var data = google.visualization.arrayToDataTable(JSON.parse(JSON.stringify(clearance_chart_data)));
                    chart = new google.visualization.LineChart($('#pk-clearance-graph')[0]);
                    chart.draw(data, options);
                }
            }
        })
        .fail(function(xhr, errmsg, err) {
            // Stop spinner
            window.spinner.stop();

            alert('Error retrieving Intrinsic Clearance.');
            console.log(xhr.status + ": " + xhr.responseText);
        });
        // console.log("Done with Clearance Prediction.")
    });

    function isNumber(obj) {
        return obj !== undefined && typeof(obj) === 'number' && !isNaN(obj);
    }

    function escapeHtml(html) {
        return $('<div>').text(html).html();
    }

    function make_escaped_tooltip(title_text) {
        var new_span = $('<div>').append($('<span>')
            .attr('data-toggle', "tooltip")
            .attr('data-title', escapeHtml(title_text))
            .addClass("glyphicon glyphicon-question-sign")
            .attr('aria-hidden', "true")
            .attr('data-placement', "bottom"));
        return new_span.html();
    }

    $("#toggle-intro-text").click(function() {
        $("#intro-text").toggle();
    });

    $("#toggle-continuous-infusion-table").parent().show();
    $("#toggle-continuous-infusion-table").hide();
    $("#toggle-continuous-infusion-table").click(function() {
        $("#continuous-infusion-table").toggle();
    });

    $('#clearance-time-start-selectized').parent().css("display", "block");
    $('#clearance-time-end-selectized').parent().css("display", "block");

    var remove_col = function(arr, col_index) {
        for (var i = 0; i < arr.length; i++) {
            var row = arr[i];
            row.splice(col_index, 1);
        }
    };

    function update_chart() {
        // Summary Graph
        clear_clearance();
        $('#calculated-pk-container').hide();
        make_chart(row_info[3], 'Avg Recovered Compound (μM)', $('#summary-graph')[0], JSON.parse(JSON.stringify(chart_data[group_num])), 400);
    }

    function make_dosing_plot(data, time) {
        var dosing_data = [["Time (h)", "Multiple Dose (mg/L)", "Single Dose (mg/L)"]];
        for (var x=0; x<=time; x++) {
            dosing_data.push([data["Time (hr)"][x], data["Multiple Dose (mg/L)"][x], data["Single Dose (mg/L)"][x]]);
        }
        options = {
            title: 'Predicted Dosing Plot',
            interpolateNulls: true,
            tooltip: {
                isHtml: true
            },
            titleTextStyle: {
                fontSize: 18,
                bold: true,
                underline: true
            },
            legend: {
                position: 'top',
                maxLines: 5,
                textStyle: {
                    bold: true
                }
            },
            hAxis: {
                title: 'Time (Hours)',
                textStyle: {
                    bold: true
                },
                titleTextStyle: {
                    fontSize: 14,
                    bold: true,
                    italic: false
                }
            },
            vAxis: {
                title: 'Concentration in Plasma (mg/L)',
                format: '',
                textStyle: {
                    bold: true
                },
                titleTextStyle: {
                    fontSize: 14,
                    bold: true,
                    italic: false
                },
                minValue: 0,
                viewWindowMode: 'explicit'
            },
            // pointShape: {visible: false},
            'chartArea': {
                'width': '80%',
                'height': '80%',
            },
            'height': 500,
            focusTarget: 'datum',
            intervals: {
                'lineWidth': 0.75
            },
            tracking: {
                is_default: true,
                use_dose_response: false,
                time_conversion: 1,
                chart_type: 'scatter',
                tooltip_type: 'datum',
                revised_unit: null,
                use_x_log: false,
                use_y_log: false
            },
            ajax_data: {
                key: 'device',
                mean_type: 'arithmetic',
                interval_type: 'ste',
                number_for_interval: '1',
                percent_control: '',
                truncate_negative: ''
            }
        };
        var data = google.visualization.arrayToDataTable(JSON.parse(JSON.stringify(dosing_data)));
        chart = new google.visualization.LineChart($('#dosing-graph')[0]);
        chart.draw(data, options);
    }

    $(function() {
        var handle = $('#dosing-slider-handle');
        $('#dosing-slider').slider({
            range: "min",
            value: 48,
            min: 1,
            max: 720,
            create: function() {
                handle.text($(this).slider("value"));
            },
            slide: function(event, ui) {
                handle.text(ui.value);
                make_dosing_plot(prediction_plot_data, parseInt(ui.value));
            }
        });
    });

    $("input[name='acid-base']").change(function() {
        if (this.value == "acidic") {
            if ($("#compound-pka").val() == basic_pka || $("#compound-pka").val() == '') {
                $("#compound-pka").val(acidic_pka);
            }
        } else {
            if ($("#compound-pka").val() == acidic_pka || $("#compound-pka").val() == '') {
                $("#compound-pka").val(basic_pka);
            }
        }
    });

    function make_chart(assay, unit, selector, data, height) {
        // Clear old chart (when applicable)
        $(selector).empty();

        // Handle No Cell-Free Data
        if (!$('#cell-free-checkbox').is(':checked')) {
            $.each(data[0], function(index) {
                if (this.includes("No Cell Samples")) {
                    remove_col(data, index);
                    remove_col(data, index);
                    remove_col(data, index);
                    return false;
                }
            });
        }

        // Handle Selected Cell Profile
        var cell_text = $("input[name='cell-profile']:checked").parent().next().text().replace(/[\x00-\x1F\x7F-\x9F]/g, "");
        var loop = true;
        while (loop) {
            loop = false;
            $.each(data[0], function(index, current_string) {
                if (current_string.replace(/[\x00-\x1F\x7F-\x9F]/g, "").slice(0, -1) != cell_text.slice(0, -1) && current_string != "Time" && !current_string.includes("No Cell Samples") && current_string != "Time (Minutes)" && current_string.indexOf("~@i")===-1) {
                    remove_col(data, index);
                    remove_col(data, index);
                    remove_col(data, index);
                    loop = true;
                    return false;
                }
            });
        }

        var time_unit = "Hours";
        var trendlines = '';
        var title = assay;
        var yaxis = '';
        if (data[0].indexOf("Time (Minutes)") > -1) {
            yaxis = "log"
            time_unit = "Minutes";
            trendlines = {
                0: {
                    type: 'linear',
                    visibleInLegend: false,
                    pointsVisible: false
                }
            }
            // title = 'Predicted Intrinsic Clearance (μl/min) = ' + pbpk_intrinsic_clearance.toFixed(3);
        }

        // Aliases
        var assay_data = JSON.parse(JSON.stringify(data));

        // Don't bother if empty
        if (assay_data[1] === undefined) {
            selector.innerHTML = '<div class="alert alert-danger" role="alert">' +
                    '<span class="glyphicon glyphicon-warning-sign" aria-hidden="true"></span>' +
                    '<span class="sr-only">Danger:</span>' +
                    ' <strong>' + assay + ' ' + unit + '</strong>' +
                    '<br>This plot doesn\'t have any valid data.' +
                '</div>';
            return;
        }

        options = {
            // TOO SPECIFIC, OBVIOUSLY
            title: title,
            trendlines: trendlines,
            interpolateNulls: true,
            tooltip: {
                isHtml: true
            },
            titleTextStyle: {
                fontSize: 18,
                bold: true,
                underline: true
            },
            // curveType: 'function',
            legend: {
                position: 'top',
                maxLines: 5,
                textStyle: {
                    // fontSize: 8,
                    bold: true
                }
            },
            hAxis: {
                // Begins empty
                title: 'Time ('+time_unit+')',
                textStyle: {
                    bold: true
                },
                titleTextStyle: {
                    fontSize: 14,
                    bold: true,
                    italic: false
                }
            },
            vAxis: {
                title: '',
                // If < 1000 and > 0.001 don't use scientific! (absolute value)
                // y_axis_label_type
                scaleType: yaxis,
                textStyle: {
                    bold: true
                },
                titleTextStyle: {
                    fontSize: 14,
                    bold: true,
                    italic: false
                },
                // This doesn't seem to interfere with displaying negative values
                minValue: 0,
                viewWindowMode: 'explicit',
                format: 'decimal'
                // baselineColor: 'none',
                // ticks: []
            },
            pointSize: 5,
            'chartArea': {
                'width': '70%',
                'height': '70%',
                left: 100
            },
            'height': height,
            // Individual point tooltips, not aggregate
            focusTarget: 'datum',
            intervals: {
                // style: 'bars'
                'lineWidth': 0.75
            },
            tracking: {
                is_default: true,
                use_dose_response: false,
                // A little too odd
                // use_percent_control: false,
                time_conversion: 1,
                chart_type: 'scatter',
                tooltip_type: 'datum',
                revised_unit: null,
                // Log scale
                use_x_log: false,
                use_y_log: false
            },
            ajax_data: {
                key: 'device',
                mean_type: 'arithmetic',
                interval_type: 'ste',
                number_for_interval: '1',
                percent_control: '',
                truncate_negative: ''
            }
        };

        if (options.tracking.revised_unit) {
            unit = options.tracking.revised_unit;
        }

        if (!options) {
            options = $.extend(true, {}, window.CHARTS.global_options);
        }

        // SLOPPY NOT DRY
        // Global max
        var global_max_y = 0;
        var global_min_y = 1e25;

        // Go through y values
        $.each(assay_data.slice(1), function(current_index, current_values) {
            // Idiomatic way to remove NaNs
            var trimmed_values = current_values.slice(1).filter(isNumber);

            var current_max_y = Math.abs(Math.max.apply(null, trimmed_values));
            var current_min_y = Math.abs(Math.min.apply(null, trimmed_values));

            if (global_max_y < current_max_y) {
                global_max_y = current_max_y;
            }
            if (global_min_y > current_min_y) {
                global_min_y = current_min_y;
            }
        });

        // if (global_max_y > 1000 || global_max_y < 0.001 && global_max_y !== 0) {
        //     options.vAxis.format = '0.0E0';
        // }
        // else if (Math.abs(global_max_y - global_min_y) < 10 && Math.abs(global_max_y - global_min_y) > 0.1 && Math.abs(global_max_y - global_min_y) !== 0) {
        //     options.vAxis.format = '0.0';
        // }
        // else if (Math.abs(global_max_y - global_min_y) < 0.1 && Math.abs(global_max_y - global_min_y) !== 0) {
        //     options.vAxis.format = '0.0E0';
        // }
        // else {
        //     options.vAxis.format = '0';
        // }

        var current_min_x = assay_data[1][0];
        var current_max_x = assay_data[assay_data.length - 1][0];
        var current_x_range = current_max_x - current_min_x;

        // Tack on change
        // TODO CHANGE THE TITLE
        options.title = title;
        // TODO GET THE UNIT IN QUESTION
        options.vAxis.title = unit;

        var chart = null;

        var num_colors = 0;
        var truncated_at_index = null;

        $.each(assay_data[0].slice(1), function(index, value) {
            if (value.indexOf('     ~@i') === -1) {
                // NOTE TRUNCATE PAST 40 COLORS
                if (num_colors >= 40) {
                    truncated_at_index = index;

                    if (assay_data[0][index + 1].indexOf('     ~@i') !== -1) {
                        truncated_at_index += 2;
                    }

                    $.each(assay_data, function(row_index, current_row) {
                        assay_data[row_index] = current_row.slice(0, truncated_at_index + 1);
                    });

                    // Indicate truncated in title?
                    options.title = options.title + ' {TRUNCATED}';

                    return false;
                }

                num_colors++;
            }
        });

        var data = google.visualization.arrayToDataTable(assay_data);

        chart = new google.visualization.LineChart(selector);

        // Change the options
        if (options.hAxis.scaleType !== 'mirrorLog') {
            options.hAxis.viewWindowMode = 'explicit';
            options.hAxis.viewWindow = {
                max: current_max_x + 0.1 * current_x_range,
                min: current_min_x - 0.1 * current_x_range
            };
        }

        if (chart) {
            var dataView = new google.visualization.DataView(data);

            // Change interval columns to intervals
            var interval_setter = [0];

            i = 1;
            while (i < data.getNumberOfColumns()) {
                interval_setter.push(i);
                if (i + 2 < data.getNumberOfColumns() && assay_data[0][i+1].indexOf('     ~@i1') > -1) {
                    interval_setter.push({sourceColumn: i + 1, role: 'interval'});
                    interval_setter.push({sourceColumn: i + 2, role: 'interval'});
                    i += 2;
                }
                i += 1;
            }
            dataView.setColumns(interval_setter);

            chart.draw(dataView, options);
        }
    }
});
