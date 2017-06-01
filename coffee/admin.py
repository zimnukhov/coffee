from django.contrib import admin
from .models import (
    Roaster, RoastProfile, Coffee, CoffeeBag, Water, BrewingMethod, Brew,
    Descriptor, Filter
)


admin.site.register(Roaster)
admin.site.register(RoastProfile)
admin.site.register(Coffee)
admin.site.register(CoffeeBag)
admin.site.register(Water)
admin.site.register(BrewingMethod)
admin.site.register(Brew)
admin.site.register(Descriptor)
admin.site.register(Filter)
