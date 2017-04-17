import datetime
from django.shortcuts import render, redirect, get_object_or_404
from .models import Coffee, CoffeeBag, Brew, BrewingMethod
from .forms import BrewForm


def index(request):
    today = datetime.date.today()
    bags = CoffeeBag.objects.select_related('coffee__roaster').filter(end_date__isnull=True)


    brews = Brew.objects.select_related('coffee_bag', 'method').order_by('-datetime')

    return render(request, 'coffee/index.html', {
        'bags': bags,
        'brews': brews,
    })


def brew_details(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)

    return render(request, 'coffee/brew_details.html', {
        'brew': brew,
    })


def create_brew(request):
    brew = Brew(
        datetime=datetime.datetime.now(),
        grinder_setting=15,
        temperature=92,
        coffee_weight=15,
        bloom=Brew.BLOOM,
    )
    return brew_form(request, brew)


def edit_brew(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)
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
