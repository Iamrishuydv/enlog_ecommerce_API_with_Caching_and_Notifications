from django.contrib import admin

# Register your models here.
from .models import Category, Product, User

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Product)
