from django.core.management.base import BaseCommand
from .data import run


class Command(BaseCommand):
    help = "Seed the database with test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            # Add clearing logic here if needed

        run()
        self.stdout.write(self.style.SUCCESS("Successfully seeded database"))
