import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Avg
from django.http import HttpResponse, JsonResponse, Http404
from django.forms import modelformset_factory
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Coffee, CoffeeBag, Brew, BrewingMethod, Water, Pouring, Roaster, Descriptor
from .forms import BrewForm, BrewRatingForm


def index(request):
    today = datetime.date.today()
    bags = CoffeeBag.objects.select_related(
        'coffee__roaster'
    ).filter(status=CoffeeBag.NOT_FINISHED).order_by('-purchase_date')

    brews = Brew.objects.select_related(
        'coffee_bag__coffee__roast_profile',
        'method',
        'water',
        'barista',
        ).order_by('-datetime')[:20]
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
        'ajax_list': True,
    })


def brew_list_page(request):
    offset = request.GET.get('offset', '')
    if offset.isdigit():
        offset = int(offset)
    else:
        return JsonResponse({'error': 'invalid offset'})

    page_size = 50
    brews = Brew.objects.select_related(
        'coffee_bag__coffee__roast_profile',
        'method',
        'water',
        'barista',
    ).order_by('-datetime')[offset:offset+page_size]

    return JsonResponse({'brews': [brew.get_json_dict() for brew in brews]})


def all_bags(request):
    bags = CoffeeBag.objects.select_related('coffee__roaster').order_by('-purchase_date')

    return render(request, 'coffee/all_coffee.html', {
        'bags': bags,
    })


def search(request):
    query = request.GET.get('query', '')
    query = query.strip()

    if query:
        bags = CoffeeBag.objects.select_related('coffee__roaster').filter(coffee__name__icontains=query).order_by('-purchase_date')
    else:
        bags = []

    return render(request, 'coffee/search.html', {
        'bags': bags,
        'query': query,
    })


def brew_details(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)

    return render(request, 'coffee/brew_details.html', {
        'brew': brew,
    })


@login_required
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
        if best_brew.grinder is not None:
            brew.grinder = best_brew.grinder

    return brew_form(request, brew)


@login_required
def create_brew(request):
    water = None

    if Water.objects.count() > 0:
        water = Water.objects.all()[0]

    brew = Brew.get_default()
    brew.water = water

    return brew_form(request, brew)


@login_required
def edit_brew(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)
    return brew_form(request, brew)


@login_required
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


@login_required
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
    brews = bag.brew_set.select_related(
        'coffee_bag__coffee__roast_profile',
        'method',
        'water',
        'barista',
    ).all().order_by('-datetime')

    max_rating = None
    best_brew = None

    for brew in brews:
        if max_rating is None or brew.rating > max_rating:
            max_rating = brew.rating

    other_bags = bag.coffee.coffeebag_set.exclude(id=bag_id)
    all_descriptors = Descriptor.objects.filter(brew__coffee_bag__coffee=bag.coffee).distinct()
    if other_bags:
        bag_descriptors = Descriptor.objects.filter(brew__coffee_bag=bag).distinct()
    else:
        bag_descriptors = []

    return render(request, 'coffee/coffee_bag.html', {
        'bag': bag,
        'brews': brews,
        'max_rating': max_rating,
        'hide_coffee': True,
        'all_descriptors': all_descriptors,
        'bag_descriptors': bag_descriptors,
        'other_bags': other_bags,
    })


def object_related_brews(request, heading, brews, extra_context=None):
    brews = brews.select_related(
        'coffee_bag__coffee__roast_profile',
        'method',
        'water',
        'barista',
    ).order_by('-datetime')

    max_rating = None

    for brew in brews:
        if max_rating is None or brew.rating > max_rating:
            max_rating = brew.rating

    context = {
        'heading': heading,
        'brews': brews,
        'max_rating': max_rating,
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, 'coffee/object_related_brews.html', context)


def roaster_list(request):
    roasters = Roaster.objects.all().annotate(
        count=Count('coffee__coffeebag__brew'), avg_rating=Avg('coffee__coffeebag__brew__rating')
    ).order_by('-count')

    return render(request, 'coffee/roaster_list.html', {
        'roasters': roasters,
    })


def roaster(request, roaster_id):
    roaster = get_object_or_404(Roaster, id=roaster_id)
    brews = Brew.objects.filter(coffee_bag__coffee__roaster=roaster)

    return object_related_brews(request, roaster.name, brews, {
        'object_list_name': 'Обжарщики',
        'object_list_url': reverse('coffee:roasters'),
        'object_url': roaster.get_absolute_url(),
    })


def method_list(request):
    methods = BrewingMethod.objects.all().annotate(
        count=Count('brew'), avg_rating=Avg('brew__rating')
    ).order_by('-count')

    return render(request, 'coffee/method_list.html', {
        'methods': methods,
    })


def method_details(request, method_id):
    method = get_object_or_404(BrewingMethod, id=method_id)
    return object_related_brews(request, method.name, method.brew_set.all(), {
        'object_list_name': 'Способы заваривания',
        'object_list_url': reverse('coffee:methods'),
        'object_url': method.get_absolute_url(),
        'hide_method': True,
    })


def descriptor_list(request):
    descriptors = Descriptor.objects.annotate(count=Count('brew'))

    return render(request, 'coffee/descriptor_list.html', {
        'descriptors': descriptors,
    })


def descriptor(request, descriptor_id):
    descriptor = get_object_or_404(Descriptor, id=descriptor_id)
    return object_related_brews(request, descriptor.name, descriptor.brew_set.all(), {
        'object_list_name': 'Ноты',
        'object_list_url': reverse('coffee:notes'),
        'object_url': descriptor.get_absolute_url(),
    })


def water_list(request):
    waters = Water.objects.all().annotate(
        count=Count('brew'), avg_rating=Avg('brew__rating')
    ).order_by('-avg_rating')

    return render(request, 'coffee/water_list.html', {
        'waters': waters,
    })


def water_details(request, water_id):
    water = get_object_or_404(Water, id=water_id)
    return object_related_brews(request, water.name, water.brew_set.all(), {
        'object_list_name': 'Вода',
        'object_list_url': reverse('coffee:waters'),
        'object_url': water.get_absolute_url(),
        'hide_water': True
    })


def brews_by_rating_value(request, rating_value):
    rating_value = int(rating_value)
    if rating_value < 1 or rating_value > 10:
        raise Http404

    brews = Brew.objects.filter(rating=rating_value)
    return object_related_brews(
        request,
        'Оценка {}/10'.format(rating_value),
        brews,
        {
            'object_list_name': 'Статистика',
            'object_list_url': reverse('coffee:stats'),
            'object_url': '',
        }
    )


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
    brews_by_rating = dict((_x, 0) for _x in range(1, 11))

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
            if brew.rating in brews_by_rating:
                brews_by_rating[brew.rating] += 1

        if brew.water_volume is not None:
            consumed_water += brew.water_volume

    avg_rating /= rated_brews
    ratings.sort()

    unexpired_coffee_weight = sum(bag_weight.values())

    french_presses = unexpired_coffee_weight // 25
    harios = unexpired_coffee_weight // 14
    aeropresses = unexpired_coffee_weight // 15

    consumption_rate = sum(coffee_weight_by_day.values()) / len(coffee_weight_by_day)

    return render(request, 'coffee/stats.html', {
        'total_brews': total_brews,
        'consumed_coffee_weight': consumed_coffee_weight / 1000,
        'unexpired_coffee_weight': unexpired_coffee_weight,
        'french_presses_remaining': french_presses,
        'harios_remaining': harios,
        'aeropresses_remaining': aeropresses,
        'avg_rating': avg_rating,
        'consumed_water': consumed_water / 1000,
        'consumption_rate': consumption_rate,
        'brews_by_rating': sorted(
            brews_by_rating.items(),
            key=lambda item: item[0],
            reverse=True
        ),
    })
