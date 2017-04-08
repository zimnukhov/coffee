import datetime
from django.shortcuts import render, get_object_or_404
from .models import Coffee, CoffeeBag, Brew


def index(request):
    today = datetime.date.today()
    bags = CoffeeBag.objects.select_related('coffee__roaster').filter(end_date__isnull=True)


    brews = Brew.objects.select_related('coffee_bag', 'method').filter(
        datetime__gt=datetime.datetime.now() - datetime.timedelta(days=7)
    ).order_by('-datetime')

    return render(request, 'coffee/index.html', {
        'bags': bags,
        'brews': brews,
    })


def brew_details(request, brew_id):
    brew = get_object_or_404(Brew, id=brew_id)

    return render(request, 'coffee/brew_details.html', {
        'brew': brew,
    })
