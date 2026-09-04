from django.urls import path

from .views import itinerary_options

urlpatterns = [
    path("itineraries/", itinerary_options, name="itinerary-options"),
]
