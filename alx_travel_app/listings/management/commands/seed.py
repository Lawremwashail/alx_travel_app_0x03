from django.core.management.base import BaseCommand
from listings.models import Listing

class Command(BaseCommand):
    help = "Seed the database with sample listings data"

    def handle(self, *args, **kwargs):
        sample_listings = [
            {"title": "Beachside Bungalow", "description": "Relaxing bungalow by the sea.", "location": "Mombasa", "price_per_night": 120.00},
            {"title": "Mountain Retreat", "description": "Peaceful cabin with scenic views.", "location": "Mt. Kenya", "price_per_night": 95.00},
            {"title": "City Apartment", "description": "Modern apartment in the city center.", "location": "Nairobi", "price_per_night": 80.00},
        ]

        for data in sample_listings:
            Listing.objects.get_or_create(**data)

        self.stdout.write(self.style.SUCCESS("Successfully seeded the database with listings!"))

