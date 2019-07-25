$(document).ready(function () {
    var study_pk = Math.floor(window.location.pathname.split("/")[3]);

    // Crude, for old schema
    if (isNaN(study_pk)) {
        study_pk = Math.floor(window.location.pathname.split("/")[2]);
    }

    // Not currently used
    // var image_container = $('#image_mosaic');
    var filter_table = $('#filter_table');
    var image_table = $('#image_table');

    var contrast = 100;
    var brightness = 100;

    var downloadFilename = '';
    var image_types = ['jpg','jpeg','png','gif','tif','tiff']

    // Perform on image expansion
    var popupDialogData = {};
    var dialogConfirm = $("#image_popup");
    var dialogOptions = {
        resizable: false,
        draggable: false,
        position: {my:"top", at:"top", of:window},
        modal: false,
        closeOnEscape: true,
        autoOpen: false,
        buttons: [
        {
            text: 'Download Unaltered Image',
            // Keep JQuery UI from throwing a hissy fit, with Luke's approval.
            click: function() {}
        },
        {
            text: 'Back',
            click: function() {
               $(this).dialog("close");
            }
        }],
        open: function() {
            $.ui.dialog.prototype.options.open();

            $(this).dialog('option', 'width', $(window).width());
            $(this).dialog('option', 'height', ($(window).height()-$('#floating-sliders').height()-1));

            var iChip = popupDialogData["chip_id"];
            var iPlate = popupDialogData["plate_id"];
            var iWell = popupDialogData["well_id"];
            var iTime = popupDialogData["time"];
            var iMethodKit = popupDialogData["method_kit"];
            var iStainPairings = popupDialogData["stain_pairings"];
            var iTargetAnalyte = popupDialogData["target_analyte"];
            var iSubtarget = popupDialogData["subtarget"];
            var iSampleLocation = popupDialogData["sample_location"];
            var iReplicate = popupDialogData["replicate"];
            var iNotes = popupDialogData["notes"];
            var iFileName = popupDialogData["file_name"];
            var iField = popupDialogData["field"];
            var iFieldDescription = popupDialogData["field_description"];
            var iMagnification = popupDialogData["magnification"];
            var iResolution = popupDialogData["resolution"];
            var iResolutionUnit = popupDialogData["resolution_unit"];
            var iSampleLabel = popupDialogData["sample_label"];
            var iSampleLabelDescription = popupDialogData["sample_label_description"];
            var iWavelength = popupDialogData["wavelength"];
            var iColorMapping = popupDialogData['color_mapping'];
            var iSettingNote = popupDialogData["setting_notes"];
            // Construct Dialog Box Title
            var tempTarget = iTargetAnalyte.split(' | ');
            var tempLabel = iSampleLabel.split(' | ');
            var tempColor = iColorMapping.split(' | ');
            var titleText = "";
            if (tempTarget.length == 1 || tempLabel.length == 1 || tempColor.length == 1){
                titleText = iTargetAnalyte + " ("+iSampleLabel+" | "+iColorMapping.toUpperCase()+")";
            } else {
                try {
                    for (i = 0; i < tempTarget.length; i++) {
                        titleText += tempTarget[i] + " ("+tempLabel[i]+" | "+tempColor[i].toUpperCase()+")";
                        if (i < tempTarget.length-1) {
                            titleText += ", ";
                        }
                    }
                } catch(err) {
                    titleText = iTargetAnalyte + " ("+iSampleLabel+", "+iColorMapping.toUpperCase()+")";
                }
            }

            // Tooltips logic
            var fieldTooltip = '';
            if (iFieldDescription && iFieldDescription != "none") {
                fieldTooltip = ' <span data-toggle="tooltip" title="'+iFieldDescription+'" class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>';
            }
            var sampleLabelTooltip = '';
            if (iSampleLabelDescription && iSampleLabelDescription != "none") {
                sampleLabelTooltip = ' <span data-toggle="tooltip" title="'+iSampleLabelDescription+'" class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>';
            }

            // Check filetype
            var type = '';
            var detailDisplay = '';
            if (image_types.indexOf($.trim(popupDialogData["file_name"].split('.').pop().toLowerCase())) >= 0){
                type = "Image";
                detailDisplay = '<a href="/media/assay_images/'+study_pk+'/'+popupDialogData["file_name"]+'"><div class="thumbnail col-md-12 col-lg-4"><img alt="'+popupDialogData["file_name"]+'" style="filter: contrast('+contrast+'%)  brightness('+brightness+'%);" src="/media/assay_thumbs/'+study_pk+'/thumbnail_'+popupDialogData["file_name"].split(".").slice(0, -1).join('.') +'_600_600.jpg"/></div></a>'
            } else {
                type = "Video";
                var videoName = popupDialogData["file_name"].substr(0, popupDialogData["file_name"].lastIndexOf("."))
                detailDisplay = '<div class="thumbnail col-md-12 col-lg-4"><video style="max-width: 100%; max-height: 100%;" width="600" height="600" controls><source src="/media/assay_images/'+study_pk+'/'+videoName+'.mp4" type="video/mp4"></source></video></div>'
            }

            // Add tooltip to "Download" button and trigger download on click
            downloadFilename = popupDialogData["file_name"];
            $(".ui-dialog").find(".ui-button-text-only:first").html('<a style="text-decoration: none; color: white;" download href="/media/assay_images/'+study_pk+'/'+downloadFilename+'"><span class="ui-button-text">Download Unaltered '+type+' <span data-toggle="tooltip" title="Some '+type+'s are dark and may require\n intensity adjustment to discern details." class="glyphicon glyphicon-info-sign" aria-hidden="true"></span></span></a>');

            $("#myDialogText").html('<div class="row no-padding">'+detailDisplay+'<div class="col-md-12 col-lg-7"><table class="table table-hover table-striped table-bordered table-condensed small">'+
                '<div class="text-center"><label>Note: This '+type.toLowerCase()+' may have been altered to assist with viewing.<br>To perform analysis, please download the unaltered '+type.toLowerCase()+'.</label></div><br>'+
                '<tr><th style="width: 200px;">Chip ID</th><td>'+iChip+'</td></tr>'+
                '<tr><th>Assay Plate ID</th><td>'+iPlate+'</td></tr>'+
                '<tr><th>Assay Well ID</th><td>'+iWell+'</td></tr>'+
                '<tr><th>Time</th><td>'+iTime+'</td></tr>'+
                '<tr><th>Method/Kit</th><td>'+iMethodKit+'</td></tr>'+
                '<tr><th>Target-Stain Pairings</th><td><b>'+iStainPairings+'</td></tr></b>'+
                '<tr><th>Target/Analyte</th><td>'+iTargetAnalyte+'</td></tr>'+
                '<tr><th>Sample Location</th><td>'+iSampleLocation+'</td></tr>'+
                '<tr><th>Notes</th><td>'+iNotes+'</td></tr>'+
                '<tr><th>'+type+' File Name</th><td>'+iFileName+'</td></tr>'+
                '<tr><th>'+type+' Field</th><td>'+iField.split(".")[0]+fieldTooltip+'</td></tr>'+
                '<tr><th>'+type+' Magnification</th><td>'+iMagnification+'x</td></tr>'+
                '<tr><th>'+type+' Resolution</th><td>'+iResolution+" "+iResolutionUnit+'</td></tr>'+
                '<tr><th>'+type+' Sample Label</th><td>'+iSampleLabel+sampleLabelTooltip+'</td></tr>'+
                '<tr><th>'+type+' Wavelength (ex/em nm)</th><td>'+iWavelength+'</td></tr>'+
                '<tr><th>'+type+' Color Mapping</th><td>'+iColorMapping+'</td></tr>'+
                '<tr><th>'+type+' Setting Note</th><td>'+iSettingNote+'</td></tr></table></div></div>');
            $("#ui-id-1")[0].innerHTML = titleText;
        }
    };
    var theDialog = dialogConfirm.dialog(dialogOptions);

    var filter_elements = "";
    for (var i=0; i<tableCols.length; i++) {
        var col = tableCols[i].replace(/\s/g, '').replace(/[,]/g, '');
        filter_elements += "<button aria-pressed='true' style='max-width: 160px; min-height: 80px; white-space: normal; margin-bottom: 1em;' class='hand-cursor col-lg-2 col-md-4 col-sm-6 col-xs-12 btn btn-3d btn-default btn-checkbox active'>"+tableCols[i].toUpperCase()+"<input checked data-column='"+col+"' type=checkbox></button>";
    }
    // for (i=0; i<tableRows.length; i++){
    //     filter_elements += "<tr><th>"+tableRows[i]+"</th><td><input id='"+tableRows[i].split(" ").join("").split(",").join("")+"' type=checkbox></td></tr>";
    // }
    filter_table.html(filter_elements);

    var table_elements = "<thead><tr><td style='font-weight: bold; width: .1%; white-space: nowrap;'>Chip/Well</td>";
    for (i=0; i<tableCols.length; i++) {
        var col = tableCols[i].replace(/\s/g, '').replace(/[,]/g, '');
        table_elements += "<th style='white-space: nowrap;' data-column='" + col + "' class='text-center no-sort'>"+tableCols[i].toUpperCase()+"</th>";
    }
    table_elements += "</tr></thead><tbody>";
    for (i=0; i<tableRows.length; i++) {
        var row = tableRows[i].replace(/\s/g, '').replace(/[,]/g, '');
        table_elements += "<tr data-row='"+row+"'><th class='row-header' style='width: .1%; white-space: nowrap;'><a href='/assays/assaymatrixitem/"+metadata_list[tableRows[i]]+"/'>"+tableRows[i]+"</a></th>";
        for (var j=0; j<tableCols.length; j++) {
            var col = tableCols[j].replace(/\s/g, '').replace(/[,]/g, '');
            // table_elements += "<td class='text-center "+col+row+" "+col+"'></td>";
            table_elements += "<td class='text-center' data-column='" + col + "' data-row='" + row + "'></td>";
        }
        table_elements += "</tr>";
    }
    table_elements += "</tbody>";
    image_table.html(table_elements);

    image_table.on('click', '.image_thumbnail', function () {
        popupDialogData = metadata_list[this.getAttribute("data-pic")];
        dialogConfirm.dialog("open");
    });

    //Checkbox click event
    $("#filter_table").on("click",":checkbox", function() {
        var checkbox = $(this);
        var checkbox_id = $(this).attr('data-column');
        var cls = checkbox_id.split(' ').pop();
        if (checkbox.is(':checked')) {
            image_table.find('th[data-column="'+ cls + '"], td[data-column="'+ cls + '"]').removeClass('hidden');
        } else {
            image_table.find('th[data-column="'+ cls + '"], td[data-column="'+ cls + '"]').addClass('hidden');
        }
        $('.row-header').css('width', '.1%').css('white-space', 'nowrap');

        // Activates Bootstrap tooltips
        $('[data-toggle="tooltip"]').tooltip({container:"body", html: true});
    });

    for (j=0; j<tableCols.length; j++){
        cls = tableCols[j].split(" ").join("").split(",").join("");
        // for (var i=0; i<Object.keys(tableData).length; i++) {
        $.each(orderedStudyImages, function(index, image_id) {
            if (tableData[image_id][1] == cls) {
                var caption = metadata_list[image_id]["target_analyte"] + " (" + metadata_list[image_id]["sample_location"] + "), "
                +metadata_list[image_id]["sample_label"]+", "+metadata_list[image_id]["magnification"]
                +"x at " + metadata_list[image_id]["time"];

                var extension = metadata_list[image_id]["file_name"].split(".").pop().toLowerCase();
                if (['flv', 'avi', 'mp4', 'mov', 'wmv'].indexOf(extension) >= 0){
                    $('[data-column="' + cls + '"][data-row="' + tableData[image_id][0] + '"]').append('<span data-pic="'+image_id
                    +'" style="vertical-align: top; display: inline-block; margin:2px;" class="image_thumbnail"><figure><div style="position: absolute; z-index: 0;"><img alt="'
                    +metadata_list[image_id]["file_name"]+'" style="height: 120px; width: 120px; filter: contrast('+contrast+'%) brightness('+brightness+'%);" src="/media/assay_thumbs/'
                    +study_pk+'/thumbnail_'+metadata_list[image_id]["file_name"].split(".").slice(0, -1).join('.')
                    +'_120_120.jpg"/></div><div onMouseOver="this.style.opacity='+"1"+'" onMouseOut="this.style.opacity='+"0.5"+'" style="position: absolute; z-index: 1; opacity: 0.5;"><img src="/media/assay_images/playbutton.png" style="padding: 30px; filter: invert(1);"/></div><div style="padding-top:120px;"><figcaption style="width: 120px; word-wrap: break-word;" class="caption text-center">'+ caption +'</figcaption></div></figure></span>');
                }
                else {
                    $('[data-column="' + cls + '"][data-row="' + tableData[image_id][0] + '"]').append('<span data-pic="'+image_id
                    +'" style="vertical-align: top; display: inline-block; margin:2px;" class="image_thumbnail"><figure><img alt="'
                    +metadata_list[image_id]["file_name"]+'" style="height: 120px; width: 120px; filter: contrast('+contrast+'%) brightness('+brightness+'%);" src="/media/assay_thumbs/'
                    +study_pk+'/thumbnail_'+metadata_list[image_id]["file_name"].split(".").slice(0, -1).join('.')
                    +'_120_120.jpg"/><figcaption style="width: 120px; word-wrap: break-word;" class="text-center caption">'+ caption +'</figcaption></figure></span>');
                }
            }
        });
    }

    $( function() {
        var handle = $( "#handle-contrast" );
        $( "#slider-contrast" ).slider({
            create: function() {
                handle.text( $( this ).slider( "value" ) + "%" );
            },
            slide: function( event, ui ) {
                handle.text( ui.value + "%");
                adjustContrast(ui.value);
            },
            value: 100,
            min: 0,
            max: 200
        });
    } );

    $( function() {
        var handle = $( "#handle-brightness" );
        $( "#slider-brightness" ).slider({
            create: function() {
                handle.text( $( this ).slider( "value" ) + "%" );
            },
            slide: function( event, ui ) {
                handle.text( ui.value + "%");
                adjustBrightness(ui.value);
            },
            value: 100,
            min: 0,
            max: 500
        });
    } );

    function adjustContrast(newContrast){
        contrast = newContrast;
        $( "img" ).not('img[src$="/static/img/brand.png"]').not('img[src$="/media/assay_images/playbutton.png"]').each(function() {
            $( this ).css( "filter", "contrast("+contrast+"%) brightness("+brightness+"%)");
        });
    }

    function adjustBrightness(newBrightness){
        brightness = newBrightness;
        $( "img" ).not('img[src$="/static/img/brand.png"]').not('img[src$="/media/assay_images/playbutton.png"]').each(function() {
            $( this ).css( "filter", "contrast("+contrast+"%) brightness("+brightness+"%)");
        });
    }

    // Return brightness and contrast to 100%.
    $('#reset-to-default').click(function () {
        adjustBrightness(100);
        adjustContrast(100);
        $('#handle-brightness').text("100%");
        $('#handle-contrast').text("100%");
        $("#slider-brightness").slider( "value", 100 );
        $("#slider-contrast").slider( "value", 100 );
    });

    // Toggle buttons.
    $(".btn-checkbox").on("mouseup", function () {
        var $checkbox = $(this).find(':checkbox');
        $checkbox.trigger("click");
        if ($checkbox.prop('checked')){
            $(this).addClass("active");
        } else {
            $(this).removeClass("active");
        }
        $(this).blur();
        doSearch(true);
    });

    image_table.dataTable({
        // columns: generateColumns(),
        "ordering": true,
        "filter": false,
        "searching": false,
        dom: 'frt',
        fixedHeader: {headerOffset: 50},
        deferRender: true,
        iDisplayLength: -1,
        "aoColumnDefs": [
            {
                "width": "10%",
                "aTargets": [0]
            },
            {
                orderable: false,
                targets: "no-sort"
            }
        ]
    });

    // On keystroke, run search function.
    $('#search-box').keyup(function (e) {
        if(e.keyCode === 8) {
            doSearch(true);
        } else {
            doSearch(false);
        }
    });

    // Filter table based on contents of search textbox.
    // TODO A caption may contain a query, but if a future caption does not, the row will be hidden.
    function doSearch(backspace) {
        var query = $('#search-box').val().toUpperCase();
        var isChip = false;

        // Always make everything visible again
        makeAllVisible();

        for (var i=0; i<tableRows.length; i++) {
            if (tableRows[i].toUpperCase().includes(query)) {
                isChip = true;
                break;
            }
        }

        if (isChip) {
            image_table.find('th').each(function(header_index) {
                if (header_index > tableCols.length - 1) {
                    if ($(this).text().toUpperCase().includes(query)) {
                        $(this).parent().removeClass('hidden');
                    } else {
                        $(this).parent().addClass('hidden');
                    }
                }
            });
        }
        else {
            image_table.find('figcaption').each(function() {
                // var buttonActive = $('#'+$(value).parent().parent().parent().attr("class").split(" ")[2]).prop('checked');
                var current_column = $(this).parent().parent().parent();
                var current_fig = $(this).parent().parent();
                var buttonActive = $('input[data-column="' + current_column.attr("data-column") + '"]').prop('checked');
                if ($(this).text().toUpperCase().includes(query) || $(this).attr("data-text-long").toUpperCase().includes(query)) {
                    if (buttonActive) {
                        current_fig.removeClass('hidden');
                    } else {
                        current_fig.addClass('hidden');
                    }
                } else {
                    current_fig.addClass('hidden');
                }
            });
        }

        hideEmpty();
    }

    // Reveal every row and image.
    function makeAllVisible(){
        image_table.find('figcaption').each(function(index, value) {
            $(value).parent().parent().removeClass('hidden');
        });
        image_table.find('th').each(function(index, value) {
            if (index > tableCols.length - 1){
                $(value).parent().removeClass('hidden');
            }
        });
    }

    // Hide rows that contain no images.
    function hideEmpty() {
        for (i=0; i<tableRows.length; i++) {
            if ($('tr[data-row="'+ tableRows[i] + '"]').height() < 100) {
                $('tr[data-row="'+ tableRows[i] + '"]').addClass('hidden');
            }
        }

        // Adjust fixedHeader
        $($.fn.dataTable.tables(true)).DataTable().fixedHeader.adjust();
    }

    // Center JQuery Dialog Window Title
    $("#ui-id-1").css('text-align', 'center').css('width','100%').css('font-size', '16px');

    // Make JQuery Dialog title bar not blend in with browser UI so strongly
    $(".ui-dialog").find(".ui-widget-header").css('background', 'linear-gradient(#111111, #333333)').css('color', 'white');

    // "Close" and "Download" buttons as Bootstrap buttons
    // $(".ui-dialog").find(".ui-button-text-only").addClass('btn btn-primary').removeClass('ui-state-default');

    // Change caption font-size
    $(".caption").css('font-size', '13px');

    // Collapsible Captions
    var lastX, indexInc, captionEndString = '';
    $(".caption").each(function(i, obj){
        if ($(obj).height() > 54){
            $(obj).attr("data-text-long", $(obj).text());
            lastX = $(obj).attr('data-text-long').lastIndexOf('x');
            indexInc = 2;
            while ($(obj).attr('data-text-long')[lastX-indexInc] != ' '){
                indexInc += 1
            }
            captionEndString = $(obj).attr('data-text-long').substring(lastX-indexInc);
            $(obj).attr("data-text-short", $(obj).attr('data-text-long').substring(0,47-captionEndString.length)+"..."+captionEndString);
            $($(obj).parent())[0].addEventListener("mouseover",function(){
                $(obj).text($(obj).attr('data-text-long'));
            });
            $($(obj).parent())[0].addEventListener("mouseout",function(){
                $(obj).text($(obj).attr('data-text-short'));
            });
            $(obj).text($(obj).attr('data-text-short'));
        } else {
            $(obj).attr("data-text-long", $(obj).text());
        }
    });

    //TODO Unintelligently play with table sizing at different image quantities
    // var mostImages = 0;
    // $("td").each(function(index){
    //     if ($(this).children().length > mostImages){
    //         mostImages = $(this).children().length;
    //     }
    // });
    // console.log(mostImages);
    // console.log(tableCols.length);
    // if (mostImages < 3 && tableCols.length < 4) {
    //     console.log("Shrinking table");
    //     console.log($("#fluid-content").width());
    // }

    // Escape Key closes dialog windows
    $(document).keydown(function(e) {
        // ESCAPE key pressed
        if (e.which == 27) {
            $(theDialog).dialog('close');
        }
    });
});
