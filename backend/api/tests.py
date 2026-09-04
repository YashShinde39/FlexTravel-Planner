from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ItineraryOptionsAPITest(APITestCase):
    def test_itinerary_options_returns_three_items(self):
        response = self.client.get(reverse("itinerary-options"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("itineraries", response.data)
        self.assertEqual(len(response.data["itineraries"]), 3)
