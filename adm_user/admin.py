from django.contrib import admin
from .models import Category, Color, Fabric, Print, Product, ProductVariant, ProductImage

# Register your models here.
admin.site.register(Category)
admin.site.register(Color)
admin.site.register(Fabric)
admin.site.register(Print)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)