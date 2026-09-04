from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def itinerary_options(_request):
    itineraries = [
        {
            "id": 1,
            "title": "Cultural City Escape",
            "duration_days": 4,
            "budget_usd": 950,
            "highlights": ["Museum district", "Local food tour", "Historic old town"],
        },
        {
            "id": 2,
            "title": "Coastal Relaxation Retreat",
            "duration_days": 6,
            "budget_usd": 1350,
            "highlights": ["Beachfront stay", "Sunset cruise", "Spa day"],
        },
        {
            "id": 3,
            "title": "Mountain Adventure Loop",
            "duration_days": 5,
            "budget_usd": 1125,
            "highlights": ["Guided hike", "Scenic train", "Lake kayaking"],
        },
    ]
    return Response({"itineraries": itineraries})
