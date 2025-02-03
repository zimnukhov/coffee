import os
import datetime
from io import BytesIO
from PIL import Image
from django.db import models
from django.urls import reverse
from django.core.files.base import ContentFile
from .utils import get_time_display


class City(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'cities'


class Roaster(models.Model):
    name = models.CharField(max_length=512)
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('coffee:roaster-details', args=[self.id])


class RoastProfile(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name


class Grinder(models.Model):
    SIMPLE = 0
    AERGRIND = 1

    name = models.CharField(max_length=512)
    comment = models.TextField(null=True, blank=True)
    default = models.BooleanField(default=False)
    adjust_type = models.IntegerField(choices=(
        (SIMPLE, "Simple"),
        (AERGRIND, "Aergrind"),
    ), default=SIMPLE)

    def get_setting_display(self, value):
        if self.adjust_type == self.AERGRIND:
            return '%d,%d' % (value / 12, value % 12)

        return str(value)

    def __str__(self):
        return self.name


class Coffee(models.Model):
    WASHED = 1
    DRY = 2
    HONEY = 3

    name = models.CharField(max_length=512)
    short_name = models.CharField(max_length=32, blank=True, null=True)
    processing = models.IntegerField(choices=(
        (WASHED, "Washed"),
        (DRY, "Dry"),
        (HONEY, "Honey"),
    ), blank=True, null=True)
    roaster = models.ForeignKey(Roaster, on_delete=models.CASCADE)
    roast_profile = models.ForeignKey(RoastProfile, blank=True, null=True, on_delete=models.CASCADE)
    roaster_comment = models.TextField(null=True, blank=True)
    descriptors = models.ManyToManyField('Descriptor', blank=True)

    def get_absolute_url(self):
        return reverse('coffee:coffee-details', args=[self.id])

    def __str__(self):
        result = self.name
        if self.roast_profile:
            result += ' ' + self.roast_profile.name
        return result

    def get_short_name(self):
        if self.short_name:
            return self.short_name
        return self.name


class CoffeeBag(models.Model):
    NOT_FINISHED = 0
    FINISHED = 1
    THROWN_AWAY = 2
    GIVEN_AWAY = 3
    LOST = 4

    coffee = models.ForeignKey(Coffee, on_delete=models.CASCADE)
    weight = models.IntegerField(blank=True, null=True)
    roast_date = models.DateField(blank=True, null=True)
    purchase_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.IntegerField(choices=(
        (NOT_FINISHED, 'Not finished'),
        (FINISHED, 'Finished'),
        (THROWN_AWAY, 'Thrown away'),
        (GIVEN_AWAY, 'Given away'),
        (LOST, 'Lost'),
    ), default=NOT_FINISHED)
    roaster_comment = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='bags/full/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='bags/thumbs/', blank=True, null=True)

    _original_image = None

    def __init__(self, *args, **kwargs):
        super(CoffeeBag, self).__init__(*args, **kwargs)
        self._original_image = self.image

    def __str__(self):
        name = '{} ({})'.format(self.coffee, self.coffee.roaster.name)
        if self.roast_date is not None:
            name += ' ' + self.roast_date.strftime('%Y-%m-%d')
        return name

    def get_absolute_url(self):
        return reverse('coffee:bag-details', args=[self.id])

    def get_weight_display(self):
        if self.weight is None:
            return ''
        return '{}g'.format(self.weight)

    def get_date_only_name(self):
        if self.roast_date is None:
            return 'Purchased on ' + self.purchase_date.strftime('%Y-%m-%d')
        else:
            return 'Roasted on ' + self.roast_date.strftime('%Y-%m-%d')

    def save(self, *args, **kwargs):
        if self.image:
            image_changed = False
            if self._original_image:
                if self._original_image.size != self.image.size:
                    image_changed = True
                else:
                    data1 = self._original_image.file.read()
                    self.image.file.seek(0)
                    data2 = self.image.file.read()
                    self._original_image.file.seek(0)
                    if data1 != data2:
                        image_changed = True
            else:
                image_changed = True

            if image_changed:
                thumb_size = (130, 170)
                image = Image.open(BytesIO(self.image.read()))
                image.thumbnail(thumb_size, Image.ANTIALIAS)

                thumb_stream = BytesIO()
                image.save(thumb_stream, 'jpeg', quality=95)

                thumb_stream.seek(0)

                uploaded_file = ContentFile(thumb_stream.read())

                self.thumbnail.save(
                    os.path.basename(self.image.name),
                    uploaded_file,
                    save=False,
                )
        else:
            self.thumbnail = None
        super(CoffeeBag, self).save(*args, **kwargs)


class BagPicture(models.Model):
    bag = models.ForeignKey(CoffeeBag, related_name='extra_pictures', on_delete=models.CASCADE)
    comment = models.CharField(max_length=512, blank=True, null=True)
    image = models.ImageField(upload_to='bags/full/')
    thumbnail = models.ImageField(upload_to='bags/thumbs/', blank=True, null=True)

    def __str__(self):
        name = str(self.bag)
        if self.comment:
            name += ' ' + self.comment
        return name

    def save(self, *args, **kwargs):
        thumb_size = (100, 100)
        image = Image.open(BytesIO(self.image.read()))
        image.thumbnail(thumb_size, Image.ANTIALIAS)

        thumb_stream = BytesIO()
        image.save(thumb_stream, 'jpeg', quality=95)

        thumb_stream.seek(0)

        uploaded_file = ContentFile(thumb_stream.read())

        self.thumbnail.save(
            os.path.basename(self.image.name),
            uploaded_file,
            save=False,
        )
        super(BagPicture, self).save(*args, **kwargs)


class Water(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('coffee:water', args=[self.id])


class BrewingMethod(models.Model):
    name = models.CharField(max_length=512)
    default_filter = models.ForeignKey('Filter', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('coffee:brewing-method', args=[self.id])


class Filter(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=256)
    default_barista = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class BrewQuerySet(models.QuerySet):

    _aggregation_data_loaded = False
    max_rating = None
    total_weight = None
    def _calc_aggregation_data(self):
        max_rating = None
        total_weight = 0

        for brew in self:
            if brew.coffee_weight is not None:
                total_weight += brew.coffee_weight
            if brew.rating is not None and (max_rating is None or brew.rating > max_rating):
                max_rating = brew.rating

        self._aggregation_data_loaded = True
        self.max_rating = max_rating
        self.total_weight = total_weight

    def get_total_weight(self):
        if not self._aggregation_data_loaded:
            self._calc_aggregation_data()

        return self.total_weight

    def get_max_rating(self):
        if not self._aggregation_data_loaded:
            self._calc_aggregation_data()

        return self.max_rating


class Brew(models.Model):
    BLOOM_UNKNOWN = 0
    BLOOM = 1
    NO_BLOOM = 2
    RATING_MAX = 10

    UNDER_EXTRACTED = -1
    BALANCED = 0
    OVER_EXTRACTED = 1
    extraction_symbols = {
        UNDER_EXTRACTED: '&darr;',
        BALANCED: '&check;',
        OVER_EXTRACTED: '&uarr;',
    }

    objects = BrewQuerySet.as_manager()

    datetime = models.DateTimeField()
    coffee_bag = models.ForeignKey(CoffeeBag, on_delete=models.CASCADE)
    barista = models.ForeignKey(Person, blank=True, null=True, on_delete=models.CASCADE)
    grinder = models.ForeignKey(Grinder, blank=True, null=True, on_delete=models.CASCADE)
    grinder_setting = models.IntegerField()
    method = models.ForeignKey(BrewingMethod, on_delete=models.CASCADE)
    temperature = models.IntegerField(blank=True, null=True)
    coffee_weight = models.IntegerField(blank=True, null=True)
    water_volume = models.IntegerField(blank=True, null=True)
    result_volume = models.IntegerField(blank=True, null=True)
    water = models.ForeignKey(Water, blank=True, null=True, on_delete=models.CASCADE)
    water_tds = models.IntegerField(blank=True, null=True)
    brew_time = models.IntegerField(blank=True, null=True)
    bloom = models.SmallIntegerField(choices=(
        (BLOOM_UNKNOWN, 'Unknown'),
        (BLOOM, 'Bloom'),
        (NO_BLOOM, 'No bloom'),
    ), default=0)
    filter = models.ForeignKey(Filter, blank=True, null=True, on_delete=models.CASCADE)
    found_descriptors = models.ManyToManyField('Descriptor', blank=True)
    extraction = models.SmallIntegerField(blank=True, null=True, choices=(
        (UNDER_EXTRACTED, 'Недоэкстрагирован'),
        (BALANCED, 'Сбалансирован'),
        (OVER_EXTRACTED, 'Переэкстрагирован'),
    ))
    rating = models.SmallIntegerField(blank=True, null=True, choices=((i, i) for i in range(1, 11)))
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return '{} {} - {}'.format(
            self.datetime.strftime('%Y-%m-%d %H:%M'),
            self.coffee_bag.coffee.name,
            self.method.name,
        )

    def get_absolute_url(self):
        return reverse('coffee:brew-details', args=[self.id])

    def get_grinder_setting_display(self):
        if self.grinder_setting is None:
            return ''

        if self.grinder is None:
            return str(self.grinder_setting)

        return self.grinder.get_setting_display(self.grinder_setting)

    def get_rating_display(self):
        return '{}/10'.format(self.rating)

    def get_coffee_weight_display(self):
        if not self.coffee_weight:
            return ''
        return '{}g'.format(self.coffee_weight)

    def get_brew_time_display(self):
        if self.brew_time is None:
            return ''
        return get_time_display(self.brew_time)

    def get_rating_stars(self):
        stars = [False] * self.RATING_MAX

        if self.rating is not None:
            for i in range(min(self.rating, self.RATING_MAX)):
                stars[i] = True

        return stars

    def get_json_dict(self):
        return {
            'url': self.get_absolute_url(),
            'datetime': self.datetime.strftime('%Y-%m-%d %H:%M'),
            'barista': self.barista.name,
            'bag': self.coffee_bag.coffee.name,
            'bag_url': self.coffee_bag.get_absolute_url(),
            'method': self.method.name,
            'method_url': self.method.get_absolute_url(),
            'temperature': self.temperature,
            'grinder_setting': self.get_grinder_setting_display(),
            'water': self.water.name,
            'water_url': self.water.get_absolute_url(),
            'water_tds': self.water_tds,
            'coffee_weight': self.coffee_weight,
            'brew_time': self.get_brew_time_display(),
            'extraction_display': self.get_extraction_display(),
            'extraction_symbol': self.get_extraction_symbol(),
            'rating': self.rating,
        }

    @classmethod
    def get_default(cls):
        barista = None

        default_baristas = Person.objects.filter(default_barista=True)
        if len(default_baristas) > 0:
            barista = default_baristas[0]

        grinder = None

        default_grinders = Grinder.objects.filter(default=True)
        if len(default_grinders) > 0:
            grinder = default_grinders[0]

        return cls(
            datetime=datetime.datetime.now(),
            grinder_setting=14,
            temperature=92,
            coffee_weight=15,
            bloom=cls.BLOOM,
            barista=barista,
            grinder=grinder,
        )

    def extraction_is_set(self):
        return self.extraction is not None

    def get_extraction_symbol(self):
        return self.extraction_symbols.get(self.extraction, '')


class Pouring(models.Model):
    brew = models.ForeignKey(Brew, on_delete=models.CASCADE)
    volume = models.IntegerField()
    order = models.IntegerField(default=0)
    wait_time = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return '%sml' % self.volume

    class Meta:
        ordering = ['order']


class Descriptor(models.Model):
    name = models.CharField(max_length=512)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('coffee:note-details', args=[self.id])

    class Meta:
        ordering = ['name']
