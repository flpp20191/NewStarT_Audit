from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Category)
admin.site.register(Subthemes) 
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    search_fields = ['question', 'id']
    list_filter = ["condition__type"]

@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    search_fields = ['question__question', 'id']
    list_filter = ["type"]

admin.site.register(Answer)
admin.site.register(Score)
