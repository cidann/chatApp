from django.contrib import admin
from group.models import User,Message,Group,Membership
# Register your models here.
class DefaultAdmin(admin.ModelAdmin):
    pass

admin.site.register(User,DefaultAdmin)
admin.site.register(Message,DefaultAdmin)
admin.site.register(Group,DefaultAdmin)
admin.site.register(Membership,DefaultAdmin)