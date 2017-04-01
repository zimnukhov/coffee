from django.contrib import admin
from .models import Roaster, Coffee, CoffeeBag, BrewingMethod, Brew, Descriptor


admin.site.register(Roaster)
admin.site.register(Coffee)
admin.site.register(CoffeeBag)
admin.site.register(BrewingMethod)
admin.site.register(Brew)
admin.site.register(Descriptor)
