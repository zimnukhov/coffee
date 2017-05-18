import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Coffee, CoffeeBag, Brew, BrewingMethod, Water
from .forms import BrewForm, BrewRatingForm


def index(request):
    today = datetime.date.today()
    bags = CoffeeBag.objects.select_related('coffee__roaster').filter(end_date__isnull=True).order_by('-purchase_date')

    brews = Brew.objects.select_related('coffee_bag', 'coffee_bag__coffee', 'method', 'water').order_by('-datetime')
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
    else:
        brew.water = water

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
    if request.method == 'POST':
        form = BrewForm(request.POST, instance=brew)
        if form.is_valid():
            brew = form.save()
            return redirect(brew)
    else:
        form = BrewForm(instance=brew)

    return render(request, 'coffee/edit_brew.html', {
        'form': form,
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
    })
