$(document).ready(function() {
    window.TABLE = $('#adverse_events').DataTable({
        dom: 'B<"row">lfrtip',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        iDisplayLength: 50,
        deferRender: true,
        ajax: {
            url: '/drugtrials_ajax/',
            data: {
                call: 'fetch_adverse_events_data',
                csrfmiddlewaretoken: window.COOKIES.csrfmiddlewaretoken
            },
            type: 'POST',
            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        },
        columns: [
            {
                data: 'view',
                sortable:false,
                width: "10%",
                render:function (data, type, row, meta) {
                    return '<a class="btn btn-primary" href="' + data + '">View</a>';
                }
            },
            {
                data: 'compound',
                render:function (data, type, row, meta) {
                    return '<a href="/compounds/' + data.id + '">' + data.name + '</a>';
                }
            },
            {
                data: 'event',
                render:function (data, type, row, meta) {
                    return '<a href="https://en.wikipedia.org/wiki/' + data.lower+ '">' + data.name + '</a>';
                }
            },
            {data: 'number_of_reports'},
            {data: 'normalized_reports'},
            {data: 'estimated_usage'},
            {data: 'organ'},
            {
                data: 'black_box_warning',
                render:function (data, type, row, meta) {
                    if (data) {
                        return '<span title="This compound has a Black Box Warning" class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>'
                    }
                    return '';
                }
            },
            {
                data: 'logp',
                visible: false,
                searchable: true,
            },
            {
                data: 'alogp',
                visible: false,
                searchable: true,
            },
            // {data: 'project', visible: false, searchable: true},
        ],
        "order": [[ 1, "asc" ], [ 3, "desc"]]
    });
});
