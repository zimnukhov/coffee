from django.db import models


class Roaster(models.Model):
    name = models.Charfield(max_length=512)

    def __str__(self):
        return self.name


class Coffee(models.Model):
    name = models.Charfield(max_length=512)
    roaster = models.ForeignKey(Roaster)
    purchased = models.DatetimeField()
    ended = models.DatetimeField(blank=True, null=True)
    found_descriptors = models.ManyToManyField(Descriptor)

    def __str__(self):
        return self.name


class BrewingMethod(models.Model):
    name = models.Charfield(max_length=512)

    def __str__(self):
        return self.name


class Brew(models.Model):
    datetime = models.DatetimeField()
    coffee = models.ForeignKey(Coffee)
    grinder_setting = models.IntegerField()
    method = models.ForeignKey(BrewingMethod)
    temperature = models.IntegerField(blank=True, null=True)
    found_descriptors = models.ManyToManyField(Descriptor)

    def __str__(self):
        return self.datetime.strftime('%Y-%m-%d %H:%M')


class Descriptor(models.Model):
    name = models.Charfield(max_length=512)

    def __str__(self):
        return self.name
