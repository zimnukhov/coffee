from django.contrib import admin
from .models import (
    Roaster, RoastProfile, Coffee, CoffeeBag, Water, BrewingMethod, Brew,
    Descriptor, Filter, Person, BagPicture, City, Grinder
)


class CoffeeBagAdmin(admin.ModelAdmin):
    exclude = ['thumbnail']


class BagPictureAdmin(admin.ModelAdmin):
    exclude = ['thumbnail']


admin.site.register(City)
admin.site.register(Roaster)
admin.site.register(RoastProfile)
admin.site.register(Coffee)
admin.site.register(CoffeeBag, CoffeeBagAdmin)
admin.site.register(Water)
admin.site.register(BrewingMethod)
admin.site.register(Brew)
admin.site.register(Descriptor)
admin.site.register(Filter)
admin.site.register(Person)
admin.site.register(BagPicture, BagPictureAdmin)
admin.site.register(Grinder)
