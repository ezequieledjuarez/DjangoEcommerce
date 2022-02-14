from django.contrib import admin
from .models import (
    Product,
    Order,
    OrderItem, 
    ColorVariation, 
    SizeVariation,
    Address,
    Payment)

class AddressAdmin(admin.ModelAdmin):
    list_display=[
        'direccion_1',
        'direccion_2',
        'codigo_postal',
        'ciudad',
        'tipo_de_direccion',
    ]

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ColorVariation)
admin.site.register(SizeVariation)
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment)

