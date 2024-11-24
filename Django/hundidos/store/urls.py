from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name="store"),
    path('category/<slug:category_slug>/', views.store, name="products_by_category"),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name="product_detail"),
    path('search/', views.search, name='search'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('ships', views.product_list, name='product_list'),
    path('edit_ship/<int:ship_id>/', views.edit_ship, name='edit_ship'),
    path('delete_ship/<int:ship_id>/', views.delete_ship, name='delete_ship'),
    path('create_ship/', views.create_ship, name='create_ship'),

]
