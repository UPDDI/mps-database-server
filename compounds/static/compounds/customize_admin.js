$(document).ready(function () {
    var middleware_token = $('[name=csrfmiddlewaretoken]').attr('value');
    var chemblid = null;

    var chembl_search_results = $('#chembl_search_results');
    var chembl_search_submit = $('#chembl_search_submit');
    var chembl_search = $('#chembl_search');

    var chembl_id_selector = $('#id_chemblid');

    // Add the retrieve button
    // TODO REVISE
    $('<input type="button" value="Retrieve" id="retrieve" name="_fetch">')
            .insertAfter(chembl_id_selector);
    var retrieve_selector = $('#retrieve');

    // Set override exception to include chembl_search (so it doesn't trigger the submission)
    window.OVERRIDE.exceptions.push(chembl_search);
    window.OVERRIDE.exceptions.push(chembl_id_selector);

    // Open and then close dialog so it doesn't get placed in window itself
    var dialog = $('#dialog');
    dialog.dialog({
        width: 825,
        height: 500,
    });
    dialog.removeProp('hidden');

//    function compound_finalizer(data) {
//        $('#id_name').val(data.compound.preferredCompoundName);
//        $('#id_inchikey').val(data.compound.stdInChiKey);
//        $('#id_smiles').val(data.compound.smiles);
//        // Note that the synonyms are modified so that there is a space after
//        // Each comma. Replace can not be performed on undefined variables.
//        if (data.compound.synonyms) {
//            $('#id_synonyms').val(data.compound.synonyms.replace(/,/g, ', '));
//        }
//        $('#id_molecular_formula').val(data.compound.molecularFormula);
//        $('#id_molecular_weight').val(data.compound.molecularWeight);
//        $('#id_rotatable_bonds').val(data.compound.rotatableBonds);
//        $('#id_acidic_pka').val(data.compound.acdAcidicPka);
//        $('#id_basic_pka').val(data.compound.acdBasicPka);
//        $('#id_logp').val(data.compound.acdLogp);
//        $('#id_logd').val(data.compound.acdLogd);
//        $('#id_alogp').val(data.compound.alogp);
//        $('#id_ro5_violations').val(data.compound.numRo5Violations);
//        $('#id_species').val(data.compound.species);
//
//        if ("Yes" === data.compound.knownDrug) {
//            $('#id_known_drug').prop('checked', true);
//        } else {
//            $('#id_known_drug').prop('checked', false);
//        }
//
//        // Deprecated
////        if ("Yes" === data.compound.medChemFriendly) {
////            $('#id_medchem_friendly').prop('checked', true);
////        } else {
////            $('#id_medchem_friendly').prop('checked', false);
////        }
//
//        if ("Yes" === data.compound.passesRuleOfThree) {
//            $('#id_ro3_passes').prop('checked', true);
//        } else {
//            $('#id_ro3_passes').prop('checked', false);
//        }
//
//        // Call drugbank
//        get_drugbank_data();
//    }

    function compound_finalizer(data) {
        $('#id_name').val(data.name);
        $('#id_inchikey').val(data.inchikey);
        $('#id_smiles').val(data.smiles);
        $('#id_synonyms').val(data.synonyms);
        $('#id_molecular_formula').val(data.molecular_formula);
        $('#id_molecular_weight').val(data.molecular_weight);
        $('#id_rotatable_bonds').val(data.rotatable_bonds);
        $('#id_acidic_pka').val(data.acidic_pka);
        $('#id_basic_pka').val(data.basic_pka);
        $('#id_logp').val(data.logp);
        $('#id_logd').val(data.logd);
        $('#id_alogp').val(data.alogp);
        $('#id_ro5_violations').val(data.ro5_violations);
        $('#id_species').val(data.species);

        if (data.known_drug) {
            $('#id_known_drug').prop('checked', true);
        } else {
            $('#id_known_drug').prop('checked', false);
        }

        if (data.ro3_passes) {
            $('#id_ro3_passes').prop('checked', true);
        } else {
            $('#id_ro3_passes').prop('checked', false);
        }


        if (data.medchem_alerts) {
            $('#id_medchem_alerts').prop('checked', true);
        } else {
            $('#id_medchem_alerts').prop('checked', false);
        }
        // Call drugbank
        get_drugbank_data();
    }

    function caller(selection, chemblid, middleware_token) {
        return $.ajax({
            url: "/compounds_ajax/",
            type: "POST",
            dataType: "json",
            data: {
                // Function to call within the view is defined by `call:`
                //call: 'fetch_chemblid_data',
                call: 'fetch_chembl_compound_data',

                // First token is the var name within views.py
                // Second token is the var name in this JS file
                chemblid: chemblid,

                // Select assay data return
                //selector: selection,

                // Always pass the CSRF middleware token with every AJAX call
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            },
            success: function (json) {

                if (json.error) {
                    alert(json.error);
                    retrieve_selector.removeAttr('disabled').val('Retrieve');
                } else {
                    if ('compound' === selection) {
                        compound_finalizer(json);
                    }
                }

            },
            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }

    function apply_drugbank_data(data) {
        $('#id_drugbank_id').val(data.drugbank_id);
        $('#id_drug_class').val(data.drug_class);
        $('#id_protein_binding').val(data.protein_binding);
        $('#id_half_life').val(data.half_life);
        $('#id_bioavailability').val(data.bioavailability);
        $('#id_clearance').val(data.clearance);
        $('#id_absorption').val(data.absorption);

        $('#id_pubchemid').val(data.pubchemid);

        // TODO WORK OUT HOW TO CREATE TARGET ENTRIES HERE
        for (var x in data.targets) {
            var target = data.targets[x];
            var add_to = '#id_compoundtarget_set-' + x + '-';

            for (var field in target) {
                var id_field = add_to + field;
                $(id_field).val(target[field]);
            }
        }

        retrieve_selector.removeAttr('disabled').val('Retrieve');
    }

    function get_drugbank_data() {
        $.ajax({
            url: "/compounds_ajax/",
            type: "POST",
            dataType: "json",
            data: {
                call: 'fetch_drugbank_data',
                chembl_id: chemblid,
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            },
            success: function (json) {
                if (json.error) {
                    alert(json.error);
                }
                else {
                    // TODO Think of a better way to generate the rows
                    var add_button = $('#add_button-compoundtarget_set');
                    if (add_button[0]) {
                        for (var x in json.targets) {
                            add_button.trigger('click');
                        }
                    }
                    // TODO Alternative for admin SHOULD PROBABLY BE MADE
                    else {
                        // WHY DOES IT SAY django.jQuery?
                        // It is because Django admin has a namespace for its jQuery copy!
                        add_button = django.jQuery(django.jQuery('table')[0]).find('a');
                        for (var x in json.targets) {
                           add_button.trigger('click');
                        }
                    }
                    // Apply the data
                    apply_drugbank_data(json);
                }
            },
            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
                retrieve_selector.removeAttr('disabled').val('Retrieve');
            }
        });
    }

    function get_search_results() {
        chembl_search_submit.prop('disabled', true)
            .removeClass('btn-primary')
            .addClass('btn-warning')
            .text('Loading...');

        $.ajax({
            url: "/compounds_ajax/",
            type: "POST",
            dataType: "json",
            data: {
                call: 'fetch_chembl_search_results',
                query: chembl_search.val(),
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            },
            success: function (json) {
                if (json) {
                    display_search_results(json);
                }
                else {
                    alert('No results found.')
                }
                chembl_search_submit.prop('disabled', false)
                    .addClass('btn-primary')
                    .removeClass('btn-warning')
                    .text('Search');
            },
            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
                alert('An error occurred!');
                chembl_search_submit.prop('disabled', false)
                    .addClass('btn-primary')
                    .removeClass('btn-warning')
                    .text('Search');
            }
        });
    }

    function display_search_results(results) {
        // Clear old results
        chembl_search_results.html('');

        for (var index in results) {
            var result = results[index];

            var current_id = result.chembl_id;

            var row = $('<tr>').append(
                $('<td>').append($('<a>')
                    .attr('href', 'https://www.ebi.ac.uk/chembl/compound/inspect/' + result.chembl_id)
                    .attr('target', '_blank')
                    .text(result.chembl_id)))
                .append($('<td>')
                     .text(result.name))
                .append($('<td>')
                     .text(result.synonyms))
                .append($('<td>').append($('<img>')
                     .attr('src', 'https://www.ebi.ac.uk/chembldb/compound/displayimage/' + result.chembl_id)))
                .append($('<td>').append($('<button>')
                    .addClass('btn btn-primary')
                    .text('Select')
                    .attr('data-chemblid', current_id)
                    .click(function(){apply_selection(this)})));

            chembl_search_results.append(row);
        }
    }

    function apply_selection(selection) {
        var chembl_id = selection.getAttribute('data-chemblid');
        chembl_id_selector.val(chembl_id);
        dialog.dialog('close');
    }

    // FOR ADMIN ONLY
    if ($('.object-tools > li > .addlink').length) {
        $(".object-tools").append(
            '<li><a href="add_multi/" class="addlink">Add multiple</a></li>'
        );
    }

    // FOR ADMIN ONLY
    if (!$('#id_locked').prop('checked')) {
        retrieve_selector.click(function () {
            chemblid = chembl_id_selector.val();

            if (chemblid.match("^CHEMBL")) {
                /* If we match CHEMBL, display the fact that we are in the
                 * process of retrieving data */
                retrieve_selector.val('Retrieving').attr('disabled', 'disabled');

                // Not sure why this was originally written like this
                // Should perform refactor soon
                var selection = 'compound';

                caller(selection, chemblid, middleware_token);
            }
            else {
                alert("Please enter a ChEMBL id.");
            }
        });
    }

    $('#search_chembl').click(function() {
        dialog.dialog('open');
    });

    chembl_search_submit.click(function() {
        get_search_results();
    });

    // Override the enter key (again) to search when entering on chembl_search
    $(window).keydown(function(event) {
        if(event.keyCode == 13) {
            // If SPECIFICALLY chembl search is focused
            if(chembl_search.is(":focus")) {
                chembl_search_submit.trigger('click');
                return false;
            }
            // If SPECIFICALLY chemblid selector is focused
            else if(chembl_id_selector.is(":focus")) {
                retrieve_selector.trigger('click');
                return false;
            }
        }
    });
});
