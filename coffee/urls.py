from django.urls import re_path
from . import views


app_name = 'coffee'

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'brews.json$', views.brew_list_page, name='brew-list-json'),
    re_path(r'^search/?$', views.search, name='search'),
    re_path(r'^bags/?$', views.all_bags, name='all-bags'),
    re_path(r'^brew/(\d+)/?$', views.brew_details, name='brew-details'),
    re_path(r'^brew/(\d+)/edit/?$', views.edit_brew, name='brew-edit'),
    re_path(r'^brew/(\d+)/copy/?$', views.copy_brew, name='brew-copy'),
    re_path(r'^brew/(\d+)/rate/?$', views.rate_brew, name='brew-rate'),
    re_path(r'^brew/add/?$', views.create_brew, name='brew-create'),
    re_path(r'^bags/(\d+)/?$', views.coffee_bag, name='bag-details'),
    re_path(r'^bags/(\d+)/add/?$', views.create_brew_for_bag, name='brew-create-for-bag'),
    re_path(r'^bags/(\d+)/edit/?$', views.edit_coffee_bag, name='bag-edit'),
    re_path(r'^bags/(\d+)/copy/?$', views.copy_coffee_bag, name='bag-copy'),
    re_path(r'^coffee/(\d+)/?$', views.coffee_details, name='coffee-details'),
    re_path(r'^roasters/?$', views.roaster_list, name='roasters'),
    re_path(r'^roasters/(\d+)/?$', views.roaster, name='roaster-details'),
    re_path(r'^methods/?$', views.method_list, name='methods'),
    re_path(r'^methods/(\d+)/?$', views.method_details, name='brewing-method'),
    re_path(r'^water/?$', views.water_list, name='waters'),
    re_path(r'^water/(\d+)/?$', views.water_details, name='water'),
    re_path(r'^notes/?$', views.descriptor_list, name='notes'),
    re_path(r'^notes/(\d+)/?$', views.descriptor, name='note-details'),
    re_path(r'^rating/(\d+)/?$', views.brews_by_rating_value, name='brews-by-rating-value'),
    re_path(r'^stats/?$', views.stats, name='stats'),
]
