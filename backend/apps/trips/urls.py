from django.urls import path

from apps.trips import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("trips/plan/", views.plan_trip, name="trip-plan"),
    path("trips/", views.trip_list, name="trip-list"),
    path("trips/<uuid:trip_id>/", views.trip_detail, name="trip-detail"),
    path("geocode/", views.geocode_suggest, name="geocode-suggest"),
]
