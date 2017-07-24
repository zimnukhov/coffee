from django.conf.urls import url
from . import views


app_name = 'coffee'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^search/?$', views.search, name='search'),
    url(r'^bags/?$', views.all_bags, name='all-bags'),
    url(r'^brew/(\d+)/?$', views.brew_details, name='brew-details'),
    url(r'^brew/(\d+)/edit/?$', views.edit_brew, name='brew-edit'),
    url(r'^brew/(\d+)/copy/?$', views.copy_brew, name='brew-copy'),
    url(r'^brew/(\d+)/rate/?$', views.rate_brew, name='brew-rate'),
    url(r'^brew/add/?$', views.create_brew, name='brew-create'),
    url(r'^bag/(\d+)/?$', views.coffee_bag, name='bag-details'),
    url(r'^bag/(\d+)/add/?$', views.create_brew_for_bag, name='brew-create-for-bag'),
    url(r'^method/(\d+)/?$', views.method_details, name='brewing-method'),
    url(r'^coffee/(\d+)/?$', views.coffee_details, name='coffee-details'),
    url(r'^roaster/(\d+)/?$', views.roaster, name='roaster-details'),
    url(r'^stats/?$', views.stats, name='stats'),
]
