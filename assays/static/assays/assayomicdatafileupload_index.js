$(document).ready(function() {

    let table_column_defs = [
    {'targets': [0], 'visible': true,},
    {'targets': [1], 'visible': true,},
    {'targets': [2], 'visible': true,},
    {'targets': [3], 'visible': true,},
    {'targets': [4], 'visible': true,},
    {'targets': [5], 'visible': true,},
    {'targets': [6], 'visible': true,},
    {'targets': [7], 'visible': true,},
    {'targets': [8], 'visible': false,},
    {'targets': [9], 'visible': false,},
    {'targets': [10], 'visible': false,},
    {'targets': [11], 'visible': false,},
    {'targets': [12], 'visible': false,},
    {'targets': [13], 'visible': false,},
    {'targets': [14], 'visible': false,},
    {responsivePriority: 1, targets: 0},
    {responsivePriority: 2, targets: 1},
    {responsivePriority: 3, targets: 2},
    {responsivePriority: 4, targets: 3},
    {responsivePriority: 5, targets: 4},
    {responsivePriority: 6, targets: 6},
    {responsivePriority: 7, targets: 8},

    // none of these for this table.....{'sortable': false, 'targets': [30, 32]},
    //may need the following later - if pursue sorting on these fields
    //https://datatables.net/reference/option/columns.orderDataType
    //https://datatables.net/reference/option/columns.responsivePriority
    //{ 'orderDataType': 'dom-text', 'targets': [ 30 ] },
    //{ 'orderDataType': 'dom-checkbox', 'targets': [ 32 ] },
    ];

    $('#assayomicdatafileuploads').DataTable({
        'iDisplayLength': 25,
        'sDom': '<B<"row">lfrtip>',
        fixedHeader: {headerOffset: 50},
        responsive: true,
        'order': [[4, 'asc']],
        'columnDefs': table_column_defs
    });

});
