from django.contrib import admin
from .models import PrintOrder, Print

class PrintInline(admin.TabularInline):
    model = Print
    extra = 0
    readonly_fields = ('file_url',)

@admin.register(PrintOrder)
class PrintOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'printer', 'status', 'created_at')
    list_filter = ('status', 'printer', 'created_at')
    search_fields = ('name', 'user__username', 'user__full_name')
    inlines = [PrintInline]

@admin.register(Print)
class PrintAdmin(admin.ModelAdmin):
    list_display = ('name', 'print_order', 'copies', 'cost')
    list_filter = ('print_order__printer',)
