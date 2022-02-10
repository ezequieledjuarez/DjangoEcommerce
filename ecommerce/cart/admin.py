from django.contrib import admin
from .models import (
    Product,
    Order,
    OrderItem, 
    ColorVariation, 
    SizeVariation,
    Address)

class AddressAdmin(admin.ModelAdmin):
    list_display=[
        'address_line_1',
        'address_line_2',
        'zip_code',
        'city',
        'address_type',
    ]

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ColorVariation)
admin.site.register(SizeVariation)
admin.site.register(Address, AddressAdmin)

