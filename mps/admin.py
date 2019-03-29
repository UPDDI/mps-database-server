from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from .forms import MyUserChangeForm

from django.utils.safestring import mark_safe


class MyUserAdmin(UserAdmin):
    """Revised User Admin interface"""
    save_on_top = True
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'all_groups',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
        'last_login'
    )
    form = MyUserChangeForm

    def get_queryset(self, request):
        qs = super(MyUserAdmin, self).get_queryset(request)
        qs = qs.prefetch_related(
            'groups',
        )
        return qs

    @mark_safe
    def all_groups(self, obj):
        contents = ''
        trigger = ''
        queryset = obj.groups.all()
        count = queryset.count()
        if count:
            contents = '<br>'.join([group.name for group in queryset.order_by('name')])
            trigger = '<a href="javascript:void(0)" onclick=$("#groups_{0}").toggle()>Show/Hide Groups ({1})</a>'.format(obj.pk, count)
        return '{0}<div hidden id="groups_{1}">{2}</div>'.format(trigger, obj.pk, contents)

    all_groups.allow_tags = True

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)


class MyGroupAdmin(GroupAdmin):
    """Revised Group Admin interface"""
    save_on_top = True
    list_display = (
        'name',
        'all_users'
    )

    def get_queryset(self, request):
        qs = super(MyGroupAdmin, self).get_queryset(request)
        qs = qs.prefetch_related(
            'user_set',
        )
        return qs

    @mark_safe
    def all_users(self, obj):
        contents = ''
        trigger = ''
        queryset = obj.user_set.all()
        count = queryset.count()
        if count:
            contents = '<br>'.join([' '.join([user.first_name, user.last_name]) for user in queryset.order_by('username')])
            trigger = '<a href="javascript:void(0)" onclick=$("#users_{0}").toggle()>Show/Hide Users ({1})</a>'.format(obj.pk, count)
        return '{0}<div hidden id="users_{1}">{2}</div>'.format(trigger, obj.pk, contents)

    all_users.allow_tags = True

admin.site.unregister(Group)
admin.site.register(Group, MyGroupAdmin)
