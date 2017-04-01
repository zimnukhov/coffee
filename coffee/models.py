from django.db import models


class Roaster(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name


class Coffee(models.Model):
    name = models.CharField(max_length=512)
    roaster = models.ForeignKey(Roaster)
    roaster_comment = models.TextField()
    descriptors = models.ManyToManyField('Descriptor', blank=True)

    def __str__(self):
        return self.name


class CoffeeBag(models.Model):
    coffee = models.ForeignKey(Coffee)
    weight = models.IntegerField(blank=True, null=True)
    roast_date = models.DateField(blank=True, null=True)
    purchase_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.coffee.name, self.coffee.roaster.name)

    def get_weight_display(self):
        if self.weight is None:
            return ''
        return '{}g'.format(self.weight)


class BrewingMethod(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name


class Brew(models.Model):
    datetime = models.DateTimeField()
    coffee_bag = models.ForeignKey(CoffeeBag)
    grinder_setting = models.IntegerField()
    method = models.ForeignKey(BrewingMethod)
    temperature = models.IntegerField(blank=True, null=True)
    found_descriptors = models.ManyToManyField('Descriptor')
    rating = models.SmallIntegerField()

    def __str__(self):
        return self.datetime.strftime('%Y-%m-%d %H:%M')


class Descriptor(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name
