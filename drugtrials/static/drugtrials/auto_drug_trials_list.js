$(document).ready(function() {
    window.TABLE = $('#auto_drug_trial_data').DataTable({
        dom: 'B<"row">lfrtip',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        iDisplayLength: 50,
        deferRender: true,
        ajax: {
            url: '/drugtrials_ajax/',
            data: {
                call: 'fetch_auto_drug_trial_data',
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken,
                disease: $.urlParam('disease')
            },
            type: 'POST',
            dataSrc: function(json) {
                console.log(json);
                return json.data;
            },
            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        },
        columns: [
            {
                data: 'nct_id',
                render:function (data, type, row, meta) {
                    var methods = [];
                    methods.push("<a href=https://clinicaltrials.gov/ct2/show/"+data+" target=\"_blank\">"+data+"</a>");
                    return methods;
                }
            },
            {
                data: 'outcomeAll',
                render:function (data, type, row, meta) {
                    var methods = [];

                    //if (data) {
                        //$.each(data, function(index, value) {
                            if(data[0].title){
                                methods.push(data[0].title); }
                        //});
                    //}

                    return methods.join('\n');
                }
            },
            {
                data: 'conditions',
                render:function (data, type, row, meta) {
                    var methods = [];

                    if (data) {
                        $.each(data, function(index, value) {
                            methods.push(value.name);
                        });
                    }

                    return methods.join(', \n');
                }
            },
            {
                data: 'drugs',
                render:function (data, type, row, meta) {
                    var methods = [];

                    if (data) {
                        $.each(data, function(index, value) {
                            if(value.name){
                                if(value.name.toLowerCase().includes("placebo") || value.name.toLowerCase() == "placebo"){

                                }
                                else{
                                    drugName = value.name;
                                    drugName = drugName.charAt(0).toUpperCase() + drugName.substring(1);
                                    methods.push(drugName);
                                }
                            }
                        });
                    }
                    return methods.join(', \n');
                }
            },
            {
                data: 'outcomeAll',
                render:function (data, type, row, meta) {
                    var methods = [];

                    //if (data) {
                        //$.each(data, function(index, value) {
                            if(data[1]){
                                var count = 1;
                                $.each(data[1], function(index, value) {
                                    if (value.outcome_id == data[0].id && value.classification){
                                        methods.push("<strong>"+data[1][index].classification+"</strong>: "+ value.param_value + " " + value.units + "<br>");
                                    }
                                    else if (value.outcome_id == data[0].id){
                                        methods.push("<strong>Result Group "+ count + "</strong>: "+ value.param_value + " " + value.units + "<br>");
                                        count = count + 1
                                    }
                                });
                            }
                        //});
                    //}

                    return methods.join('\n');
                },
            },

            {
                data: 'outcomeAll',
                render:function (data, type, row, meta) {
                    var methods = [];

                            if(data[2]){
                                $.each(data[2], function(index, value) {
                                    if (value.outcome_id == data[0].id && value.p_value){
                                        if(value.groups_description){
                                            methods.push(value.p_value + '<span data-toggle="tooltip" title="'+ value.groups_description +'" class="glyphicon glyphicon-info-sign" aria-hidden="true"></span><br>');
                                        }
                                        else{
                                            methods.push(value.p_value);
                                        }


                                    }
                                });
                            }

                    return methods.join('\n');
                }
            },
            {
                data: 'studies',
                render:function (data, type, row, meta) {
                    var methods = []
                    if (data) {
                        var startDate = new Date(data["start_date"]*1000)
                        var endDate = new Date(data["completion_date"]*1000)
                        methods.push($.datepicker.formatDate('M yy',startDate)+" - "+$.datepicker.formatDate('M yy',endDate))
                        }
                return methods.join(',');
                }
            },
            {
                data: 'studies',
                render:function (data, type, row, meta) {
                    var methods = []
                    if (data) {
                        if (data.hasOwnProperty("phase")){
                            methods.push(data["phase"])
                            }
                        }
                return methods.join(',')
                }
            }
        ],
        "aoColumnDefs": [ {},{},{},{},{ "width": "30%"},{},{},{} ]
    });
});

$.urlParam = function(name){
	var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
	return results[1] || 0;
}
