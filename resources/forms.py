from django import forms

from resources.models import Definition, help_category_choices

class ResourceForm(forms.ModelForm):
    """Form for Resources"""
    class Meta(object):
        widgets = {
            'resource_name': forms.Textarea(attrs={'rows': 1}),
            'resource_website': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ResourceTypeForm(forms.ModelForm):
    """Form for Resource Types"""
    class Meta(object):
        widgets = {
            'resource_type_name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ResourceSubtypeForm(forms.ModelForm):
    """Form for Resource Subtypes"""
    class Meta(object):
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class DefinitionForm(forms.ModelForm):
    """Form for Definitions"""

    class Meta(object):
        model = Definition
        fields = ('order_numbers_already_assigned',)
        widgets = {
            'term': forms.Textarea(attrs={'rows': 1, 'cols': 50}),
            'definition': forms.Textarea(attrs={'rows': 5, 'cols': 50}),
        }

    def __init__(self, *args, **kwargs):
        super(DefinitionForm, self).__init__(*args, **kwargs)
        queryset = Definition.objects.all().order_by('help_category', '-help_order')

        current_list = []
        dict_category_orders = {}
        previous_help_category = ''
        for each in queryset:
            if len(each.help_category) > 0 and each.help_order > 0 and each.help_order is not None:
                if each.help_category != previous_help_category:
                    current_list = []
                if each.help_category in dict_category_orders.keys():
                    current_list = dict_category_orders.get(each.help_category)

                current_list.append(each.help_order)
                dict_category_orders[each.help_category] = current_list

        # print("dict ", dict_category_orders)
        category_string = ''
        this_list_string = ''
        for key, value in dict_category_orders.items():
            try:
                this_list_string = ', '.join(map(str, value))
            except:
                this_list_string = ''
            if len(category_string) == 0:
                category_string = category_string + 'Listed by Source (read only):\n\n' + key + ': ' + this_list_string
            else:
                category_string = category_string + '\n' + key + ': ' + this_list_string

        self.fields['order_numbers_already_assigned'].initial = category_string

    number_cats = len(help_category_choices)
    order_numbers_already_assigned = forms.CharField(
        widget=forms.Textarea(
            attrs={'rows': number_cats+2, 'cols': 75, 'readonly': 'readonly'}
        )
    )
