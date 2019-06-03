$(document).ready(function () {
    function cluster(cluster_data_json, bioactivities, compounds) {
        // Show graphic
        $('#graphic').prop('hidden',false);
        // Hide error
        $('#error_message').prop('hidden',true);

        // Clear old (if present)
        $('#cluster').html('');
        $('#query').html('');
        $('#compound').html('');


        var height = null;
        var find = Object.keys(compounds).length;

        if (find < 11) {
            height = 600;
        }
        else if (find < 20) {
            height = 800;
        }
        else if (find < 50) {
            height = 1000;
        }
        else if (find < 80) {
            height = 1600;
        }
        else if(find < 100) {
            height = 2000;
        }
        else if(find < 150) {
            height = 2800;
        }
        else {
            height = 3600;
        }

        var width = $("#cluster").width();

        var cluster = d3.layout.cluster()
            .size([height, width - 160]);

        var diagonal = d3.svg.diagonal()
            .projection(function (d) {
                return [d.y, d.x];
            });

        var svg = d3.select("#cluster").append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(40,0)");

        var root = cluster_data_json;

        var nodes = cluster.nodes(root),
            links = cluster.links(nodes);

        var link = svg.selectAll(".link")
            .data(links)
            .enter().append("path")
            .attr("class", "link")
            .attr("d", diagonal);

        var node = svg.selectAll(".node")
            .data(nodes)
            .enter().append("g")
            .attr("class", "node")
            .attr("id", function (d) {
                // Note removed characters
                return d.name.replace(/\s/g, "").replace(/[',()\[\]]/g,'');
            })
            .attr("transform", function (d) {
                return "translate(" + d.y + "," + d.x + ")";
            });

        node.append("circle")
            .attr("r", 4.5);

        node.on("mouseover", function (d) {
            var recurse = function(node) {
                // Change the class to selected node
                $('#'+node.name.replace(/\s/g, "").replace(/[',()\[\]]/g,'')).attr('class', 'node-s');

                // Stop at leaves
                if (!node.children) {
                    return;
                }
                // For nodes with children
                else {
                    for (var child in node.children) {
                        recurse(node.children[child]);
                    }
                }
            };
            recurse(d);
        });

        node.on("mouseout", function (d) {
            node.attr("class", "node");
        });

        node.on("click", function (d) {
            $('#compound').html("");
            var names = d.name.split('\n');
            for (var i  in names) {
                if (compounds[names[i]]) {
                    var com = compounds[names[i]];
                    var box = "<div id='com" + i + "' class='thumbnail text-center'>";
                    box += '<button id="X' + i + '" type="button" class="btn-xs btn-danger">X</button>';
                    // box += "<img src='https://www.ebi.ac.uk/chembldb/compound/displayimage/"+ com.CHEMBL + "' class='img-polaroid'>";
                    box += "<img src='https://www.ebi.ac.uk/chembl/api/data/image/"+ com.CHEMBL + ".svg?engine=indigo' style='width: 200px; height: 200px;' class='img-polaroid'>";
                    box += "<strong>" + com.name + "</strong><br>";
                    box += "Known Drug: ";
                    box += com.knownDrug ? "<span class='glyphicon glyphicon-ok text-success'></span><br>" : "<span class='glyphicon glyphicon-remove text-danger'></span><br>";
                    box += "Passes Rule of 3: ";
                    box += com.ro3 ? "<span class='glyphicon glyphicon-ok text-success'></span><br>" : "<span class='glyphicon glyphicon-remove text-danger'></span><br>";
                    box += "Rule of 5 Violations: " + com.ro5 + "<br>";
                    box += "Species: " + com.species;
                    box += "</div>";
                    $('#compound').prepend(box);
                }
                // Break at 10
//                if (i >= 9){
//                    break;
//                }
            }
            // Add some padding to the bottom
            $('#compound').append('<div style="height: 300px;vertical-align: top;">');
        });

        //Titles for hovering
        node.append("title")
            .text(function (d) {
                return d.name.indexOf("\n") > -1 ? "" : d.name;
        });

        node.append("text")
            .attr("dx", function (d) {
                return d.children ? -8 : 8;
            })
            .attr("dy", 3)
            .style("text-anchor", function (d) {
                return d.children ? "end" : "start";
            })
            .text(function (d) {
                return d.name.indexOf("\n") > -1 ? "" : d.name;
            });

        d3.select(self.frameElement).style("height", height + "px");

        // Display the original query in terms of what bioactivity-target pairs were used
        var queryHeight = $(window).height()/2;
        var queryWidth = $('#query_box').width();
        var query = "<div style='width:" + queryWidth + "px; height: "+ queryHeight + "px;!important;overflow: scroll;'><table class='table table-striped table-hover'><thead><tr><td><b>Target</b></td><td><b>Bioactivity</b></td></tr></thead>";

        for (var i in bioactivities){
            var bioactivity = bioactivities[i].split('_');
            if (bioactivity.length > 2) {
                query += "<tr><td>" + bioactivity[0] + '_' + bioactivity[1] + "</td><td>" + bioactivity[2] + "</td></tr>";
            }
            else {
                query += "<tr><td>Drug Trial</td><td>" + bioactivity[0] + "</td></tr>";
            }
        }

        // Add some blank rows for padding the bottom
        for (i=0; i<4; i++) {
            query += "<tr><td> </td><td> </td></tr>";
        }

        query += "</table></div>";

        $('#query').html(query);

        $('#compound').html('<div id="com" class="thumbnail text-center">Click a node or compound name to view additional information</div>');

        $(function () {
            $(document).on("click", function (e) {
                if (e.target.id.indexOf("X") > -1) {
                    var num = e.target.id.replace( /^\D+/g, '');
                    $("#com" + num).remove();
                    e.stopPropagation();
                    return false;
                }
            });
        });
    }

    function submit() {
        // Clear all filters
        // bioactivities_filter = [];
        // targets_filter = [];
        // compounds_filter = [];
        // drugtrials_filter = [];
        //
        // // Get bioactivities
        // $("#bioactivities input[type='checkbox']:checked").each( function() {
        //     bioactivities_filter.push({"name":this.value, "is_selected":this.checked});
        // });
        //
        // // Get targets
        // $("#targets input[type='checkbox']:checked").each( function() {
        //     targets_filter.push({"name":this.value, "is_selected":this.checked});
        // });
        //
        // // Get compounds
        // $("#compounds input[type='checkbox']:checked").each( function() {
        //     compounds_filter.push({"name":this.value, "is_selected":this.checked});
        // });
        //
        // // Get drugtrials
        // $("#drugtrials input[type='checkbox']:checked").each( function() {
        //     drugtrials_filter.push({"name":this.value, "is_selected":this.checked});
        // });

        // Hide Selection html
        $('#selection').prop('hidden',true);
        // Hide error
        $('#error_message').prop('hidden',true);

        // Show spinner
        window.spinner.spin(
            document.getElementById("spinner")
        );

        $.ajax({
            url:  '/bioactivities/gen_cluster/',
            type: 'POST',
            dataType: 'json',
            data: {
                form: JSON.stringify({
                    'exclude_questionable': FILTER.exclude_questionable,
                    'pubchem': FILTER.pubchem,
                    'bioactivities_filter': FILTER.bioactivities_filter,
                    'targets_filter': FILTER.targets_filter,
                    'compounds_filter': FILTER.compounds_filter,
                    'drugtrials_filter': FILTER.drugtrials_filter,
                    'target_types_filter': FILTER.target_types,
                    'organisms_filter': FILTER.organisms,
                    'log_scale': FILTER.log_scale,
                    'normalize_bioactivities': FILTER.normalize_bioactivities,
                    'metric': FILTER.metric,
                    'method': FILTER.method,
                    'chemical_properties': FILTER.chemical_properties
                }),
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            },
            success: function (json) {
                // Stop spinner
                window.spinner.stop();
                //console.log(json);

                if (json.data_json) {
                    //console.log(json);
                    cluster(json.data_json, json.bioactivities, json.compounds);
//                    document.location.hash = "display";
                }
                else {
                    if (json.error) {
                        $('#error').html(json.error);
                    }
                    // Show error
                    $('#error_message').prop('hidden',false);
                    // Show Selection
                    $('#selection').prop('hidden',false);
                }

            },
            error: function (xhr, errmsg, err) {
                // Stop spinner
                window.spinner.stop();

                console.log(xhr.status + ": " + xhr.responseText);

                // Show error
                $('#error_message').prop('hidden',false);
                // Show Selection
                $('#selection').prop('hidden',false);
            }
        });
    }

    var targets_filter = [];
    var compounds_filter = [];
    var bioactivities_filter = [];
    var drugtrials_filter = [];

    $('#submit').click(function(evt) {
        submit();
    });
});
