import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.forms import modelformset_factory
from .models import Coffee, CoffeeBag, Brew, BrewingMethod, Water, Pouring, Roaster
from .forms import BrewForm, BrewRatingForm


def index(request):
    today = datetime.date.today()
    bags = CoffeeBag.objects.select_related('coffee__roaster').filter(end_date__isnull=True).order_by('-purchase_date')

    brews = Brew.objects.select_related('coffee_bag', 'coffee_bag__coffee', 'method', 'water', 'filter', 'barista').order_by('-datetime')
    coffee_params = {}
    show_roast_profile = set()

    for brew in brews:
        coffee_name = brew.coffee_bag.coffee.name
        roast_profile = brew.coffee_bag.coffee.roast_profile_id
        if coffee_params.get(coffee_name, roast_profile) != roast_profile:
            show_roast_profile.add(brew.coffee_bag.coffee_id)

        coffee_params[coffee_name] = roast_profile

    for brew in brews:
        brew.show_roast_profile = brew.coffee_bag.coffee_id in show_roast_profile

    return render(request, 'coffee/index.html', {
        'bags': bags,
        'brews': brews,
    })


def brew_details(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)

    return render(request, 'coffee/brew_details.html', {
        'brew': brew,
    })


def create_brew_for_bag(request, bag_id):
    bag = get_object_or_404(CoffeeBag, id=bag_id)
    brews = bag.brew_set.select_related('coffee_bag', 'method').filter(rating__isnull=False).order_by('-rating')

    brew = Brew.get_default()
    brew.coffee_bag = bag

    if len(brews) > 0:
        best_brew = brews[0]
        brew.grinder_setting = best_brew.grinder_setting
        brew.method = best_brew.method
        brew.temperature = best_brew.temperature
        brew.coffee_weight = best_brew.coffee_weight
        brew.bloom = best_brew.bloom
        brew.water = best_brew.water

    return brew_form(request, brew)


def create_brew(request):
    water = None

    if Water.objects.count() > 0:
        water = Water.objects.all()[0]

    brew = Brew.get_default()
    brew.water = water

    return brew_form(request, brew)


def edit_brew(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)
    return brew_form(request, brew)


def copy_brew(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)
    brew.id = None
    brew.rating = None
    brew.datetime = datetime.datetime.now()
    return brew_form(request, brew)


def brew_form(request, brew):
    PouringFormset = modelformset_factory(Pouring, extra=0, fields=('volume', 'wait_time'), can_delete=True)

    if brew.id:
        pouring_set = brew.pouring_set.all()
    else:
        pouring_set = Pouring.objects.none()

    if request.method == 'POST':
        form = BrewForm(request.POST, instance=brew)
        formset = PouringFormset(request.POST, queryset=pouring_set)

        if form.is_valid() and formset.is_valid():
            brew = form.save()
            next_order = 0
            for form in formset:
                if form.cleaned_data.get('DELETE') and form.instance.pk:
                    form.instance.delete()
                else:
                    if not form.cleaned_data.get('volume'):
                        continue
                    pouring = form.save(commit=False)
                    pouring.brew = brew
                    pouring.order = next_order
                    next_order += 1
                    pouring.save()

            return redirect(brew)
    else:
        form = BrewForm(instance=brew)
        formset = PouringFormset(queryset=pouring_set)

    return render(request, 'coffee/edit_brew.html', {
        'form': form,
        'pouring_formset': formset,
    })


def rate_brew(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)

    form = BrewRatingForm(request.POST, instance=brew)

    if not form.is_valid():
        return HttpResponse(400)

    brew = form.save()
    return HttpResponse("ok")


def coffee_details(request, coffee_id):
    coffee = get_object_or_404(Coffee, id=coffee_id)
    bag_count = coffee.coffeebag_set.count()

    brews = Brew.objects.filter(coffee_bag__coffee=coffee).order_by('-datetime')

    return render(request, 'coffee/coffee_details.html', {
        'coffee': coffee,
        'bag_count': bag_count,
        'brews': brews,
        'show_date_only_name': True,
    })


def coffee_bag(request, bag_id):
    bag = get_object_or_404(CoffeeBag, id=bag_id)
    brews = bag.brew_set.select_related('coffee_bag', 'method').all().order_by('-datetime')

    max_rating = None
    best_brew = None

    for brew in brews:
        if max_rating is None or brew.rating > max_rating:
            max_rating = brew.rating

    return render(request, 'coffee/coffee_bag.html', {
        'bag': bag,
        'brews': brews,
        'max_rating': max_rating,
        'hide_coffee': True,
    })


def roaster(request, roaster_id):
    roaster = get_object_or_404(Roaster, id=roaster_id)
    brews = Brew.objects.filter(coffee_bag__coffee__roaster=roaster).order_by('-datetime')

    return render(request, 'coffee/roaster.html', {
        'roaster': roaster,
        'brews': brews,
    })


def method_details(request, method_id):
    method = get_object_or_404(BrewingMethod, id=method_id)
    brews = method.brew_set.select_related('coffee_bag').all().order_by('-datetime')

    max_rating = None
    best_brew = None

    for brew in brews:
        if max_rating is None or brew.rating > max_rating:
            max_rating = brew.rating

    return render(request, 'coffee/method.html', {
        'method': method,
        'brews': brews,
        'max_rating': max_rating,
        'hide_method': True,
    })


def stats(request):
    total_brews = 0
    consumed_coffee_weight = 0
    consumed_water = 0
    avg_rating = 0.0

    expire_day = datetime.date.today() - datetime.timedelta(days=60)

    bag_weight = {}

    for bag in CoffeeBag.objects.filter(weight__isnull=False):

        if bag.roast_date is not None:
            expired = bag.roast_date < expire_day
        else:
            expired = bag.purchase_date < expire_day

        if not expired:
            bag_weight[bag.id] = bag.weight

    rated_brews = 0
    ratings = []
    coffee_weight_by_day = {}

    for brew in Brew.objects.all():
        total_brews += 1

        if brew.coffee_weight:
            consumed_coffee_weight += brew.coffee_weight

            if brew.coffee_bag_id in bag_weight:
                bag_weight[brew.coffee_bag_id] -= brew.coffee_weight

            coffee_weight_by_day.setdefault(brew.datetime.date(), 0)
            coffee_weight_by_day[brew.datetime.date()] += brew.coffee_weight

        if brew.rating is not None:
            rated_brews += 1
            avg_rating += brew.rating
            ratings.append(brew.rating)

        if brew.water_volume is not None:
            consumed_water += brew.water_volume

    avg_rating /= rated_brews
    ratings.sort()
    median_rating = ratings[len(ratings) // 2]

    unexpired_coffee_weight = sum(bag_weight.values())

    french_presses = unexpired_coffee_weight // 25
    harios = unexpired_coffee_weight // 14
    aeropresses = unexpired_coffee_weight // 15

    consumption_rate = sum(coffee_weight_by_day.values()) / len(coffee_weight_by_day)

    return render(request, 'coffee/stats.html', {
        'total_brews': total_brews,
        'consumed_coffee_weight': consumed_coffee_weight,
        'unexpired_coffee_weight': unexpired_coffee_weight,
        'french_presses_remaining': french_presses,
        'harios_remaining': harios,
        'aeropresses_remaining': aeropresses,
        'avg_rating': avg_rating,
        'median_rating': median_rating,
        'consumed_water': consumed_water,
        'consumption_rate': consumption_rate,
    })
