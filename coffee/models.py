from django.db import models
from django.urls import reverse


class Roaster(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name


class RoastProfile(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name


class Coffee(models.Model):
    name = models.CharField(max_length=512)
    roaster = models.ForeignKey(Roaster)
    roast_profile = models.ForeignKey(RoastProfile, blank=True, null=True)
    roaster_comment = models.TextField(null=True, blank=True)
    descriptors = models.ManyToManyField('Descriptor', blank=True)

    @models.permalink
    def get_absolute_url(self):
        return ('coffee-details', [self.id])

    def __str__(self):
        result = self.name
        if self.roast_profile:
            result += ' ' + self.roast_profile.name
        return result


class CoffeeBag(models.Model):
    coffee = models.ForeignKey(Coffee)
    weight = models.IntegerField(blank=True, null=True)
    roast_date = models.DateField(blank=True, null=True)
    purchase_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.coffee, self.coffee.roaster.name)

    @models.permalink
    def get_absolute_url(self):
        return ('coffee-bag', [self.id])

    def get_weight_display(self):
        if self.weight is None:
            return ''
        return '{}g'.format(self.weight)


class BrewingMethod(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name


class Brew(models.Model):
    BLOOM_UNKNOWN = 0
    BLOOM = 1
    NO_BLOOM = 2
    RATING_MAX = 10

    datetime = models.DateTimeField()
    coffee_bag = models.ForeignKey(CoffeeBag)
    grinder_setting = models.IntegerField()
    method = models.ForeignKey(BrewingMethod)
    temperature = models.IntegerField(blank=True, null=True)
    coffee_weight = models.IntegerField(blank=True, null=True)
    water_volume = models.IntegerField(blank=True, null=True)
    brew_time = models.IntegerField(blank=True, null=True)
    bloom = models.SmallIntegerField(choices=(
        (BLOOM_UNKNOWN, 'Unknown'),
        (BLOOM, 'Bloom'),
        (NO_BLOOM, 'No bloom'),
    ), default=0)
    found_descriptors = models.ManyToManyField('Descriptor', blank=True)
    rating = models.SmallIntegerField(blank=True, null=True, choices=((i, i) for i in range(1, 11)))

    def __str__(self):
        return '{} {} - {}'.format(
            self.datetime.strftime('%Y-%m-%d %H:%M'),
            self.coffee_bag.coffee.name,
            self.method.name,
        )

    @models.permalink
    def get_absolute_url(self):
        return ('brew-details', [self.id])

    def get_rating_display(self):
        return '{}/10'.format(self.rating)

    def get_coffee_weight_display(self):
        if not self.coffee_weight:
            return ''
        return '{}g'.format(self.coffee_weight)


class Descriptor(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name
