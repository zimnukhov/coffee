import datetime
from django.shortcuts import render
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
