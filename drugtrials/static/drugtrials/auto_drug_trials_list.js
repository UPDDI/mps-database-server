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
            }
        },
        columns: [
            {
                data: 'nct_id',
                render:function (data, type, row, meta) {
                    return data;
                }
            },
            {
                data: 'studies',
                render:function (data, type, row, meta) {
                    var methods = []

                    if (data) {
                        if (data.hasOwnProperty("brief_title")){
                            methods.push(data["brief_title"])
                            }
                        }
                return methods.join(',')
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

                    return methods.join(',');
                }
            },
            {
                data: 'drugs',
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
                render:function (data, type, row, meta){
                    var methods = []
                    methods.push("Human")
                    return methods.join(',');
                }
            },
            {
                data: 'studies',
                render:function (data, type, row, meta) {
                    var methods = []

                    if (data) {
                        if (data.hasOwnProperty("study_type")){
                            methods.push(data["study_type"])
                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'studies',
                //className: 'none',
                render:function (data, type, row, meta) {
                    var methods = []

                    if (data) {
                        if (data.hasOwnProperty("overall_status")){
                            methods.push(data["overall_status"])
                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'brief_summaries',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = []

                    if (data) {
                        if (data.hasOwnProperty("description")){
                            methods.push(data["description"])
                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'eligibilities',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = []

                    if (data) {
                        if (data.hasOwnProperty("criteria")){
                            methods.push(data["criteria"])
                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'eligibilities',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = []

                    if (data) {
                        if (data.hasOwnProperty("gender")){
                            methods.push(data["gender"])
                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'eligibilities',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = []

                    if (data) {
                        if (data.hasOwnProperty("minimum_age")){
                            methods.push(data["minimum_age"])
                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'eligibilities',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = []

                    if (data) {
                        if (data.hasOwnProperty("maximum_age")){
                            methods.push(data["maximum_age"])
                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'interventions',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = [];

                    if (data) {
                        $.each(data, function(index, value) {
                            methods.push(" " + value.name);
                        });
                    }

                    return methods.join(',');
                }
            },
            {
                data: 'reported_events',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = [];

                    if (data) {
                        $.each(data, function(index, value) {
                            methods.push(" " + value.adverse_event_term);
                        });
                    }

                    return methods.join(',');
                }
            },
            {
                data: 'outcomes',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = [];

                    if (data) {
                        $.each(data, function(index, value) {
                            if(value.outcome_type == "Primary"){
                                methods.push(value.title);
                            }
                        });
                    }

                    return methods.join(',\n');
                }
            },
            {
                data: 'studies',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = []
                    if (data) {
                        if (data.hasOwnProperty("start_date")){
                            var myDate = new Date(data["start_date"]*1000)
                            methods.push($.datepicker.formatDate('M yy',myDate))

                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'studies',
                className: 'none',
                render:function (data, type, row, meta) {
                    var methods = []
                    if (data) {
                        if (data.hasOwnProperty("completion_date")){
                            var myDate = new Date(data["completion_date"]*1000)
                            methods.push($.datepicker.formatDate('M yy',myDate))

                            }
                        }
                return methods.join(',')
                }
            },
            {
                data: 'studies',
                className: 'none',
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
    });
});

$.urlParam = function(name){
	var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
	return results[1] || 0;
}
