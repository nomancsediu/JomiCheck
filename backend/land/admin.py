from django.contrib import admin

from . import models

admin.site.site_header = "JomiCheck — Land Records (Synthetic Data)"
admin.site.site_title = "JomiCheck Admin"
admin.site.index_title = "Land record registry"


class KhatianOwnerInline(admin.TabularInline):
    model = models.KhatianOwner
    extra = 0
    autocomplete_fields = ["person"]


class HeirLinkInline(admin.TabularInline):
    model = models.HeirLink
    fk_name = "deceased"
    extra = 0
    autocomplete_fields = ["heir"]


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_bn"]
    search_fields = ["name_en", "name_bn"]


@admin.register(models.Upazila)
class UpazilaAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_bn", "district"]
    list_filter = ["district"]
    search_fields = ["name_en", "name_bn"]


@admin.register(models.Mouza)
class MouzaAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_bn", "jl_no", "upazila"]
    list_filter = ["upazila__district", "upazila"]
    search_fields = ["name_en", "name_bn"]


@admin.register(models.Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_bn", "father_name_en", "religion", "is_minor", "is_deceased"]
    list_filter = ["religion", "gender", "is_minor", "is_deceased", "is_government"]
    search_fields = ["name_en", "name_bn", "nid"]
    inlines = [HeirLinkInline]


@admin.register(models.Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ["dag_no", "mouza", "area_acre", "land_class", "mouza_rate_per_acre"]
    list_filter = ["mouza__upazila__district", "mouza", "land_class"]
    search_fields = ["dag_no", "mouza__name_en"]


@admin.register(models.Khatian)
class KhatianAdmin(admin.ModelAdmin):
    list_display = ["khatian_no", "survey", "record_year", "mouza"]
    list_filter = ["survey", "mouza"]
    search_fields = ["khatian_no"]
    filter_horizontal = ["plots"]
    inlines = [KhatianOwnerInline]


@admin.register(models.Deed)
class DeedAdmin(admin.ModelAdmin):
    list_display = ["deed_no", "deed_type", "registration_date", "plot", "area_acre", "price_bdt", "status"]
    list_filter = ["deed_type", "status", "sub_registry_office"]
    search_fields = ["deed_no", "plot__dag_no"]
    filter_horizontal = ["sellers", "buyers"]
    date_hierarchy = "registration_date"


@admin.register(models.Bainanama)
class BainanamaAdmin(admin.ModelAdmin):
    list_display = ["agreement_no", "plot", "seller", "buyer", "area_acre", "agreement_date", "status"]
    list_filter = ["status", "is_registered"]


@admin.register(models.Mutation)
class MutationAdmin(admin.ModelAdmin):
    list_display = ["case_no", "plot", "new_owner", "application_date", "status"]
    list_filter = ["status"]
    search_fields = ["case_no", "plot__dag_no"]


@admin.register(models.PowerOfAttorney)
class PowerOfAttorneyAdmin(admin.ModelAdmin):
    list_display = ["poa_no", "principal", "attorney", "plot", "scope", "is_registered", "is_revoked"]
    list_filter = ["scope", "is_registered", "is_revoked"]


@admin.register(models.LegalStatus)
class LegalStatusAdmin(admin.ModelAdmin):
    list_display = ["plot", "status_type", "reference_no", "since", "is_active"]
    list_filter = ["status_type", "is_active"]


@admin.register(models.Mortgage)
class MortgageAdmin(admin.ModelAdmin):
    list_display = ["plot", "mortgagor", "lender", "amount_bdt", "registered_on", "is_active"]
    list_filter = ["is_active"]


@admin.register(models.TaxRecord)
class TaxRecordAdmin(admin.ModelAdmin):
    list_display = ["plot", "holding_no", "paid_upto_year", "arrears_bdt"]


@admin.register(models.PurchaseIntent)
class PurchaseIntentAdmin(admin.ModelAdmin):
    list_display = ["plot", "buyer_token", "created_at"]
