import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Avg
from django.http import HttpResponse, JsonResponse, Http404
from django.forms import modelformset_factory
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Coffee, CoffeeBag, Brew, BrewingMethod, Water, Pouring, Roaster, Descriptor
from .forms import BrewForm, BrewRatingForm, CoffeeBagForm


MAX_BREWS_HTML = getattr(settings, 'COFFEE_MAX_BREWS_HTML', 20)
MAX_BREWS_AJAX = getattr(settings, 'COFFEE_MAX_BREWS_AJAX', 50)


def get_brew_list_order(request):
    order = request.GET.get('sort', '')
    order_dir = ''
    if order.startswith('-'):
        order_dir = '-'
        order = order[1:]

    if order not in (
        'datetime', 'barista', 'bag', 'method',
        'temperature', 'grinder_setting', 'water',
        'coffee_weight', 'brew_time', 'rating'
    ):
        return '-datetime'

    return order_dir + order


def index(request):
    today = datetime.date.today()
    bags = CoffeeBag.objects.select_related(
        'coffee__roaster'
    ).filter(status=CoffeeBag.NOT_FINISHED).order_by('-purchase_date')

    order = get_brew_list_order(request)

    brews = Brew.objects.select_related(
        'coffee_bag__coffee__roast_profile',
        'method',
        'water',
        'barista',
        'grinder',
        ).order_by(get_brew_list_order(request))[:MAX_BREWS_HTML]
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
        'order': order,
        'ajax_url': reverse('coffee:brew-list-json'),
        'ajax_list': True,
    })


def brew_list_page(request):
    offset = request.GET.get('offset', '')
    if offset.isdigit():
        offset = int(offset)
    else:
        return JsonResponse({'error': 'invalid offset'})

    page_size = MAX_BREWS_AJAX
    brews = Brew.objects.select_related(
        'coffee_bag__coffee__roast_profile',
        'method',
        'water',
        'barista',
        'grinder',
    ).order_by(get_brew_list_order(request))[offset:offset+page_size]

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


def coffee_bag_form(request, bag, action):
    if request.method == 'POST':
        form = CoffeeBagForm(request.POST, request.FILES, instance=bag)

        if form.is_valid():
            bag = form.save()

            return redirect(bag)
    else:
        form = CoffeeBagForm(instance=bag)

    return render(request, 'coffee/edit_coffee_bag.html', {
        'form': form,
        'bag': bag,
        'action': action,
    })


@login_required
def edit_coffee_bag(request, bag_id):
    bag = get_object_or_404(CoffeeBag, id=bag_id)

    return coffee_bag_form(request, bag, 'edit')


@login_required
def copy_coffee_bag(request, bag_id):
    bag = get_object_or_404(CoffeeBag, id=bag_id)
    new_bag = CoffeeBag()
    new_bag.coffee = bag.coffee
    new_bag.weight = bag.weight
    new_bag.status = CoffeeBag.NOT_FINISHED
    new_bag.purchase_date = datetime.date.today()

    return coffee_bag_form(request, new_bag, 'copy')


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
    order = get_brew_list_order(request)

    brews = bag.brew_set.select_related(
        'coffee_bag__coffee__roast_profile',
        'method',
        'water',
        'barista',
    ).all().order_by(order)

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
        'order': order,
    })


def object_related_brews(request, heading, brews, extra_context=None):
    order = get_brew_list_order(request)

    brews = brews.select_related(
        'coffee_bag__coffee__roast_profile',
        'method',
        'water',
        'barista',
    ).order_by(order)

    if request.GET.get('json'):
        offset = request.GET.get('offset', 0)
        if not offset.isdigit():
            return JsonResponse({'error': 'invalid offset'})

        offset = int(offset)

        brews = brews[offset:offset + MAX_BREWS_AJAX]

        return JsonResponse({'brews': [brew.get_json_dict() for brew in brews]})
    else:
        brews = brews[:MAX_BREWS_HTML]

    context = {
        'heading': heading,
        'brews': brews,
        'order': order,
        'ajax_list': True,
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, 'coffee/object_related_brews.html', context)


def roaster_list(request):
    roasters = Roaster.objects.all().annotate(
        count=Count('coffee__coffeebag__brew'), avg_rating=Avg('coffee__coffeebag__brew__rating')
    ).order_by('-count')

    recent_ratings = {}

    for brew in Brew.objects.select_related('coffee_bag__coffee').filter(rating__isnull=False).order_by("-datetime")[:100]:
        recent_ratings.setdefault(brew.coffee_bag.coffee.roaster_id, {'rating': 0, 'count': 0})
        recent_ratings[brew.coffee_bag.coffee.roaster_id]['rating'] += brew.rating
        recent_ratings[brew.coffee_bag.coffee.roaster_id]['count'] += 1

    for roaster in roasters:
        recent = recent_ratings.get(roaster.id)
        if recent:
            roaster.recent_rating = recent['rating'] / recent['count']

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
    descriptors = Descriptor.objects.annotate(count=Count('brew')).order_by('-count', 'name')

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

    recent_ratings = {}

    for brew in Brew.objects.filter(rating__isnull=False).order_by("-datetime")[:100]:
        recent_ratings.setdefault(brew.water_id, {'rating': 0, 'count': 0})
        recent_ratings[brew.water_id]['rating'] += brew.rating
        recent_ratings[brew.water_id]['count'] += 1

    for water in waters:
        recent = recent_ratings.get(water.id)
        if recent:
            water.recent_rating = recent['rating'] / recent['count']

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


def get_stats_for_brews(brews, calc_unexpired=True):
    total_brews = 0
    rated_brews = 0
    avg_rating = 0
    consumed_water = 0
    consumed_coffee_weight = 0
    coffee_weight_by_day = {}
    brews_by_rating = dict((_x, 0) for _x in range(1, 11))

    expire_day = datetime.date.today() - datetime.timedelta(days=60)

    bag_weight = {}

    if calc_unexpired:
        for bag in CoffeeBag.objects.filter(weight__isnull=False, status=CoffeeBag.NOT_FINISHED):
            if bag.roast_date is not None:
                expired = bag.roast_date < expire_day
            else:
                expired = bag.purchase_date < expire_day

            if not expired:
                bag_weight[bag.id] = bag.weight

    for brew in brews:
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
            if brew.rating in brews_by_rating:
                brews_by_rating[brew.rating] += 1

        if brew.water_volume is not None:
            consumed_water += brew.water_volume

    if rated_brews > 0:
        avg_rating /= rated_brews
    else:
        avg_rating = 0.0

    if len(coffee_weight_by_day) > 0:
        consumption_rate = sum(coffee_weight_by_day.values()) / len(coffee_weight_by_day)
    else:
        consumption_rate = 0.0

    unexpired_coffee_weight = sum(bag_weight.values())

    return {
        'brews': total_brews,
        'avg_rating': avg_rating,
        'brews_by_rating': brews_by_rating,
        'consumed_coffee_weight': consumed_coffee_weight / 1000,
        'consumed_water': consumed_water / 1000,
        'consumption_rate': consumption_rate,
        'unexpired_coffee_weight': unexpired_coffee_weight,
    }


def stats(request):
    total_stats = get_stats_for_brews(Brew.objects.all())
    last100_stats = get_stats_for_brews(
        Brew.objects.all().order_by('-datetime')[:100],
        calc_unexpired=False
    )
    last_week_stats = get_stats_for_brews(
        Brew.objects.filter(datetime__gt=datetime.date.today() - datetime.timedelta(days=6)),
        calc_unexpired=False
    )

    brews_by_rating = [
        (
            rating,
            total_stats['brews_by_rating'][rating],
            last100_stats['brews_by_rating'][rating],
            last_week_stats['brews_by_rating'][rating],
        ) for rating in range(10, 0, -1)
    ]

    days_left = int(total_stats['unexpired_coffee_weight'] / last100_stats['consumption_rate'])

    return render(request, 'coffee/stats.html', {
        'total_stats': total_stats,
        'last100_stats': last100_stats,
        'last_week_stats': last_week_stats,
        'brews_by_rating': brews_by_rating,
        'unexpired_coffee_weight': total_stats['unexpired_coffee_weight'],
        'days_left': days_left,
    })
