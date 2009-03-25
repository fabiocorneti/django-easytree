from problem_example.models import Example, SubClassedExample
from django.contrib import admin

class ExampleAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'title')
    list_editable = ('title',)
    ordering = ('title',)
 
class SubClassedExampleAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'title')
    list_editable = ('title',)
    ordering = ('title',)

admin.site.register(Example, ExampleAdmin)
admin.site.register(SubClassedExample, SubClassedExampleAdmin)
