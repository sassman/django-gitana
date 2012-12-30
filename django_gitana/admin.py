# -*- coding: utf8 -*-

from django.contrib import admin
import django.contrib.admin as a
from django_gitana.models import Repository, UserKey
from django.contrib.auth.models import User

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.0"
__license__ = "GNU Lesser General Public License"
__package__ = "django_gitana"

class RepositoryAdmin(admin.ModelAdmin):

    list_display = ('account', 'repository_name', 'full_url', 'git_remote_add')
    search_fields = ('account__username', 'slug')
    ordering = ('account__username', 'slug')
    prepopulated_fields = {'slug': ('name', )}

class UserKeyAdmin(admin.ModelAdmin):

    list_display = ('user', 'comment')

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.has_perm('gitana.my_add_user_key') or super(UserKeyAdmin, self).has_add_permission(request)

    def has_change_permission(self, request, object=None):
        if request.user.is_superuser or super(UserKeyAdmin, self).has_change_permission(request, obj=object):
            return True

        return request.user.has_perm('gitana.my_change_user_key') and (object and object.user == request.user) or (not object)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser or super(UserKeyAdmin, self).has_delete_permission(request, obj=obj):
            return True

        return request.user.has_perm('gitana.my_delete_user_key') and obj and obj.user == request.user

    def queryset(self, request):
        qs = super(UserKeyAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user = request.user)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if not request.user.is_superuser and db_field.name == 'user':
            kwargs['queryset'] = User.objects.filter(id = request.user.id)
        return super(UserKeyAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

a.site.register(Repository, RepositoryAdmin)
a.site.register(UserKey, UserKeyAdmin)