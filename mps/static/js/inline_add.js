// THIS FILE NEEDS TO BE REFACTORED
$(document).ready(function () {
    // Note that this requires certain class name, add name, inlines name
    // Note that the selector that selects TABLES (not divs) with the name inlines
    var inlines = $('.inlines');
    var default_rows = {};

    // For each inline
    inlines.each(function() {
        var title = $(this).find('.inline')[0].id.split('-')[0];
        var set_title = this.id.split('-')[0];

        default_rows[set_title] = $(this).find('.inline:last').clone();

        $('#add_button-'+set_title).click(function() {
            var current_set_title = this.id.split('-').slice(1).join('-');
            var current_title = $('#'+current_set_title+'-group').find('.inline')[0].id.split('-')[0];

            var add = default_rows[current_set_title].html();

            var next_id = $('#'+current_set_title+'-group').find('.inline').length;
            var tag = '<tr class="inline" id="' + current_title + '-' + next_id + '">';
            // Use a regular expression to replace all the places where ID is needed
            // In case the RegExp looks a little obfuscated, it means to replace any number of digits that fall between two hyphens
            // TODO is this irresponsible?
            $(tag).appendTo($('#'+current_set_title+'-group')).html(add.replace(/\-\d+\-/g,'-'+ next_id +'-'));
            next_id += 1;
            // Set the hidden TOTAL_FORMS to be incremented, otherwise won't bother reading other inline
            $('#id_'+current_set_title+'-TOTAL_FORMS').val(""+next_id);
            $("select").each(function(i, obj) {
                if(!$(obj).parent().hasClass("no-selectize") && !$(obj).hasClass('no-selectize')) {
                    $(obj).not('.selectized').selectize({
                        diacritics: true
                    });
                }
            });
        });
    });

    // This selector will check all items with DELETE in the name, including newly created ones
    $("body").on("click", ".inline td input[id$=-DELETE]", function(event) {
        // Use a regex to get the desired ID number
        // var thenum = thestring.match(/\d+$/)[0];
        var id = parseInt(event.target.id.match(/\d+/)[0]);

        var current_set_title = this.id.split('_').slice(1).join('_').split('-')[0];
        var current_title = $('#'+current_set_title+'-group').find('.inline')[0].id.split('-')[0];

        // Exit the function if this is an update page (if it has an original, it already exists)
        if ($('#' + current_title + '-' + id + ' .original')[0]) {
            return;
        }

        // Prevent user from removing ALL inlines (can cause unexpected behavior)
        if ($("[id^=id_"+current_set_title+"-][id$=-DELETE]").length < 2) {
            // Uncheck all in current inline
            $("[id^=id_"+current_set_title+"-][id$=-DELETE]").prop('checked', false);
            return;
        }

        // Remove the element
        $('#'+current_title+'-'+id).remove();

        // Need to find way to correctly decrement TOTAL_FORMS and next_id to avoid conflict
        // Rename all greater than deleted, next_id = inlines.length
        current_inlines = $('#' + current_set_title + '-group .inline');
        //console.log(inlines.length + " " + id);
        var next_id = current_inlines.length;

        // Decrease TOTAL_FORMS
        $("#id_" + current_set_title + "-TOTAL_FORMS").val(""+next_id);

        var end = next_id;
        for (var i=id+1; i<=end; i++) {
            var current = $('#' + current_title + '-' + i);

            var add = $('<tr>').html(
                default_rows[current_set_title].clone().html().replace(/\-\d+\-/g,'-'+ (i) +'-')
            );

            // Need to update values before creating the replacement text
            // Add values to input
            $('#'+ current_title + '-' + i + ' input').each(function () {
                $(this).attr("value", this.value);
                add.find('#' + this.id).val(this.value);
                add.find('#' + this.id).attr('value', this.value);
            });
            // Add selected attribute to selected option of each select
            $('#'+ current_title + '-' + i + ' select').each(function (){
                //console.log(this.id);
                $('#' + this.id + ' option[value="' + $(this).val() + '"]').attr("selected", true);
                add.find('#' + this.id).val(this.value);
                add.find('#' + this.id + ' option[value="' + $(this).val() + '"]').attr("selected", true);
            });

            var replacement = add.html().replace(/\-\d+\-/g,'-'+ (i-1) +'-');
            var tag = '<tr class="inline" id="' + current_title + '-' + (i-1) + '">';
            $(tag).appendTo($('#'+current_set_title+'-group')).html(replacement);
            // Remove old
            current.remove();
        }
        $("select").each(function(i, obj) {
            if(!$(obj).parent().hasClass("no-selectize")) {
                $(obj).not('.selectized').selectize({
                    diacritics: true
                });
            }
        });
    });
});
