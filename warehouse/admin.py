from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import WeaponCategory, Supplier, Weapon, Ammunition


@admin.register(WeaponCategory)
class WeaponCategoryAdmin(ImportExportModelAdmin):
    list_display = ['code', 'name']


@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    list_display = ['name', 'country']


@admin.register(Weapon)
class WeaponAdmin(ImportExportModelAdmin):
    list_display = ['model', 'name', 'category', 'quantity', 'critical_threshold', 'status']
    list_filter = ['category', 'supplier']
    search_fields = ['model', 'name']

    def status(self, obj):
        if obj.quantity == 0:
            return "НЕТ НА СКЛАДЕ"
        elif obj.quantity <= obj.critical_threshold:
            return "КРИТИЧЕСКИ МАЛО"
        else:
            return "В наличии"
    status.short_description = "Статус"


@admin.register(Ammunition)
class AmmunitionAdmin(ImportExportModelAdmin):
    list_display = ['name', 'quantity', 'monthly_incoming', 'monthly_outgoing', 'critical_threshold']