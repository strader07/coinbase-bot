
from django.urls import path, re_path
from django.conf.urls import url
from app import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    # path('tradestatus-update/', views.update_tradestatus, name='update_tradestatus'),
    path('execute/', views.run_trade, name='run_trade'),
    path('update-account/', views.update_account, name='update_account'),
    path('update-totalbalance/', views.update_balance, name='update_balance'),
    path('tradecurrency-update/', views.update_tradecurrency, name='update_tradecurrency'),

    path('portfolio/', views.get_portfolio, name='get_portfolio'),
    path('portfolio/new/', views.new_portfolio, name='new_portfolio'),
    url(r'^portfolio/edit/(?P<pk>.*)$', views.edit_portfolio, name='edit_portfolio'),
    url(r'^portfolio/del/(?P<pk>.*)$', views.del_portfolio, name='del_portfolio'),
    path('portfolio/delall/', views.delete_portfolios, name='delete_portfolios'),

    path('bot/', views.get_bots, name='get_bots'),
    path('bot/new/', views.new_bot, name='new_bot'),
    url(r'^bot/edit/(?P<pk>.*)$', views.edit_bot, name='edit_bot'),
    url(r'^bot/del/(?P<pk>.*)$', views.del_bot, name='del_bot'),
    path('bot/delall/', views.delete_bots, name='delete_bots'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
