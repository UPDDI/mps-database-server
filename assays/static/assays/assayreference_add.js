$(document).ready(function() {
    $("#fetch_reference_info").click(function(e) {
        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );
        e.preventDefault();
        $.ajax({
            type: "POST",
            url: "/assays_ajax/",
            data: {
                call: 'get_pubmed_reference_data',
                pubmedid: $('#id_pubmed_id').val(),
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
            },
            success: function(result) {
                // Stop spinner
                window.spinner.stop();
                $("#ref_title").html('<div class="col-sm-2"><label class="pull-right">Title</label></div><div class="col-sm-10">'+result['title'])+'<div class="col-sm-10">';
                $("#id_title").val(result['title']);
                $("#ref_authors").html('<div class="col-sm-2"><label class="pull-right">Authors</label></div><div class="col-sm-10">'+result['authors'])+'</div>';
                $("#id_authors").val(result['authors']);
                if (result['abstract'].length > 4000){
                    $("#ref_abstract").html('<div class="col-sm-2"><label class="pull-right">Abstract</label></div><div class="col-sm-10"><em>(Note: Exceeds 4000 characters. Result will be trimmed.)</em><br><br>'+(result['abstract'].substring(0,3997))+'...')+'</div>';
                    $("#id_abstract").val((result['abstract'].substring(0,3997)+'...'));
                } else {
                    $("#ref_abstract").html('<div class="col-sm-2"><label class="pull-right">Abstract</label></div><div class="col-sm-10">'+result['abstract'])+'</div>';
                    $("#id_abstract").val(result['abstract']);
                }
                $("#ref_publication").html('<div class="col-sm-2"><label class="pull-right">Publication</label></div><div class="col-sm-10">'+result['publication'])+'</div>';
                $("#id_publication").val(result['publication']);
                $("#ref_doi").html('<div class="col-sm-2"><label class="pull-right">DOI</label></div><div class="col-sm-10"><a href="https://doi.org/'+result['doi']+'" target="_blank">'+result['doi']+'</a></div>');
                $("#id_doi").val(result['doi']);
            },
            error: function(result) {
                // Stop spinner
                window.spinner.stop();
                console.log(xhr.status + ": " + xhr.responseText);
                alert('Error');
            }
        });
    });
});
