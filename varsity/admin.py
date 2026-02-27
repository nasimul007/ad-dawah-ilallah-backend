from django.contrib import admin
from .models import Varsity, PrintingPoint, Printer

@admin.register(Varsity)
class VarsityAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(PrintingPoint)
class PrintingPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'varsity')
    list_filter = ('varsity',)

@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'printing_point', 'connected_user')
    list_filter = ('printing_point__varsity',)
