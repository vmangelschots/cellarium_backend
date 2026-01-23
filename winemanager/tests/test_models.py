from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from winemanager.models import Wine, Bottle, Store


class WineModelTests(TestCase):
    """Test cases for Wine model"""

    def test_wine_creation_all_fields(self):
        """Test creating a wine with all fields"""
        wine = Wine.objects.create(
            name="Chateau Margaux 2015",
            region="Bordeaux",
            country="France",
            vintage=2015,
            grape_varieties="Cabernet Sauvignon, Merlot",
            rating=4.8,
            wine_type="red",
            notes="Exceptional vintage"
        )
        self.assertEqual(wine.name, "Chateau Margaux 2015")
        self.assertEqual(wine.region, "Bordeaux")
        self.assertEqual(wine.country, "France")
        self.assertEqual(wine.vintage, 2015)
        self.assertEqual(wine.grape_varieties, "Cabernet Sauvignon, Merlot")
        self.assertEqual(wine.rating, Decimal("4.8"))
        self.assertEqual(wine.wine_type, "red")
        self.assertEqual(wine.notes, "Exceptional vintage")

    def test_wine_creation_minimal(self):
        """Test creating a wine with only required fields (name)"""
        wine = Wine.objects.create(name="Simple Wine")
        self.assertEqual(wine.name, "Simple Wine")
        self.assertIsNone(wine.region)
        self.assertIsNone(wine.country)
        self.assertIsNone(wine.vintage)
        self.assertIsNone(wine.grape_varieties)
        self.assertIsNone(wine.rating)
        self.assertIsNone(wine.wine_type)
        self.assertEqual(wine.notes, "")

    def test_wine_str_with_vintage(self):
        """Test __str__ method with vintage"""
        wine = Wine.objects.create(name="Test Wine", vintage=2020)
        self.assertEqual(str(wine), "Test Wine (2020)")

    def test_wine_str_without_vintage(self):
        """Test __str__ method without vintage"""
        wine = Wine.objects.create(name="Test Wine")
        self.assertEqual(str(wine), "Test Wine")

    def test_wine_rating_valid_min(self):
        """Test wine with minimum valid rating (0.0)"""
        wine = Wine.objects.create(name="Test Wine", rating=0.0)
        wine.full_clean()
        self.assertEqual(wine.rating, Decimal("0.0"))

    def test_wine_rating_valid_max(self):
        """Test wine with maximum valid rating (5.0)"""
        wine = Wine.objects.create(name="Test Wine", rating=5.0)
        wine.full_clean()
        self.assertEqual(wine.rating, Decimal("5.0"))

    def test_wine_rating_valid_middle(self):
        """Test wine with middle range rating"""
        wine = Wine.objects.create(name="Test Wine", rating=2.5)
        wine.full_clean()
        self.assertEqual(wine.rating, Decimal("2.5"))

    def test_wine_rating_invalid_negative(self):
        """Test wine with invalid negative rating"""
        wine = Wine.objects.create(name="Test Wine", rating=-0.1)
        with self.assertRaises(ValidationError):
            wine.full_clean()

    def test_wine_rating_invalid_above_max(self):
        """Test wine with rating above maximum"""
        wine = Wine.objects.create(name="Test Wine", rating=5.1)
        with self.assertRaises(ValidationError):
            wine.full_clean()

    def test_wine_type_choices(self):
        """Test valid wine type choices"""
        valid_types = ["red", "white", "rosé", "sparkling"]
        for wine_type in valid_types:
            wine = Wine.objects.create(name=f"Test {wine_type}", wine_type=wine_type)
            self.assertEqual(wine.wine_type, wine_type)

    def test_wine_nullable_fields(self):
        """Test that nullable fields can be None"""
        wine = Wine.objects.create(
            name="Test Wine",
            region=None,
            country=None,
            vintage=None,
            grape_varieties=None,
            rating=None,
            wine_type=None
        )
        self.assertIsNone(wine.region)
        self.assertIsNone(wine.country)
        self.assertIsNone(wine.vintage)
        self.assertIsNone(wine.grape_varieties)
        self.assertIsNone(wine.rating)
        self.assertIsNone(wine.wine_type)

    def test_wine_image_upload_path(self):
        """Test that image field accepts a path"""
        wine = Wine.objects.create(name="Test Wine", image="wines/2024/01/15/test.jpg")
        self.assertEqual(wine.image, "wines/2024/01/15/test.jpg")


class BottleModelTests(TestCase):
    """Test cases for Bottle model"""

    def setUp(self):
        """Create test data for bottle tests"""
        self.wine = Wine.objects.create(name="Test Wine", vintage=2020)
        self.store = Store.objects.create(name="Test Store")

    def test_bottle_creation_with_wine(self):
        """Test creating a bottle with required wine field"""
        bottle = Bottle.objects.create(wine=self.wine)
        self.assertEqual(bottle.wine, self.wine)
        self.assertIsNone(bottle.purchase_date)
        self.assertIsNone(bottle.price)
        self.assertIsNone(bottle.store)
        self.assertIsNone(bottle.consumed_at)

    def test_bottle_with_all_fields(self):
        """Test creating a bottle with all fields"""
        from datetime import date
        bottle = Bottle.objects.create(
            wine=self.wine,
            purchase_date=date(2024, 1, 15),
            price=Decimal("45.99"),
            store=self.store,
            consumed_at=date(2024, 12, 25)
        )
        self.assertEqual(bottle.wine, self.wine)
        self.assertEqual(bottle.purchase_date, date(2024, 1, 15))
        self.assertEqual(bottle.price, Decimal("45.99"))
        self.assertEqual(bottle.store, self.store)
        self.assertEqual(bottle.consumed_at, date(2024, 12, 25))

    def test_bottle_str_method(self):
        """Test __str__ method returns wine name"""
        bottle = Bottle.objects.create(wine=self.wine)
        self.assertEqual(str(bottle), "Test Wine")

    def test_bottle_wine_cascade_delete(self):
        """Test that deleting wine cascades to bottles"""
        bottle = Bottle.objects.create(wine=self.wine)
        bottle_id = bottle.id
        self.wine.delete()
        self.assertFalse(Bottle.objects.filter(id=bottle_id).exists())

    def test_bottle_store_set_null(self):
        """Test that deleting store sets bottle.store to NULL"""
        bottle = Bottle.objects.create(wine=self.wine, store=self.store)
        self.store.delete()
        bottle.refresh_from_db()
        self.assertIsNone(bottle.store)

    def test_bottle_consumed_at_default_null(self):
        """Test that consumed_at defaults to NULL"""
        bottle = Bottle.objects.create(wine=self.wine)
        self.assertIsNone(bottle.consumed_at)

    def test_bottle_price_precision(self):
        """Test price field decimal precision"""
        bottle = Bottle.objects.create(wine=self.wine, price=Decimal("1234.56"))
        self.assertEqual(bottle.price, Decimal("1234.56"))

    def test_bottle_purchase_date_nullable(self):
        """Test that purchase_date can be null"""
        bottle = Bottle.objects.create(wine=self.wine, purchase_date=None)
        self.assertIsNone(bottle.purchase_date)

    def test_bottle_foreign_key_required(self):
        """Test that wine foreign key is required"""
        with self.assertRaises((ValueError, ValidationError)):
            Bottle.objects.create(wine=None)

    def test_bottle_consumed_workflow(self):
        """Test complete consume workflow"""
        from datetime import date
        bottle = Bottle.objects.create(wine=self.wine)
        self.assertIsNone(bottle.consumed_at)
        
        # Consume the bottle
        bottle.consumed_at = date.today()
        bottle.save()
        bottle.refresh_from_db()
        self.assertEqual(bottle.consumed_at, date.today())
        
        # Undo consume
        bottle.consumed_at = None
        bottle.save()
        bottle.refresh_from_db()
        self.assertIsNone(bottle.consumed_at)


class StoreModelTests(TestCase):
    """Test cases for Store model"""

    def test_store_creation(self):
        """Test creating a store"""
        store = Store.objects.create(name="Wine Warehouse")
        self.assertEqual(store.name, "Wine Warehouse")

    def test_store_str_method(self):
        """Test __str__ method returns name"""
        store = Store.objects.create(name="Test Store")
        self.assertEqual(str(store), "Test Store")

    def test_store_name_max_length(self):
        """Test store name max length"""
        long_name = "A" * 200
        store = Store.objects.create(name=long_name)
        self.assertEqual(store.name, long_name)


class RelatedModelsTests(TestCase):
    """Test cases for model relationships"""

    def setUp(self):
        """Create test data"""
        self.wine = Wine.objects.create(name="Test Wine", vintage=2020)
        self.store = Store.objects.create(name="Test Store")

    def test_wine_multiple_bottles(self):
        """Test wine can have multiple bottles"""
        bottle1 = Bottle.objects.create(wine=self.wine)
        bottle2 = Bottle.objects.create(wine=self.wine)
        bottle3 = Bottle.objects.create(wine=self.wine)
        
        wine_bottles = Bottle.objects.filter(wine=self.wine)
        self.assertEqual(wine_bottles.count(), 3)
        self.assertIn(bottle1, wine_bottles)
        self.assertIn(bottle2, wine_bottles)
        self.assertIn(bottle3, wine_bottles)

    def test_store_multiple_bottles(self):
        """Test store can have multiple bottles"""
        wine2 = Wine.objects.create(name="Another Wine")
        bottle1 = Bottle.objects.create(wine=self.wine, store=self.store)
        bottle2 = Bottle.objects.create(wine=wine2, store=self.store)
        
        store_bottles = Bottle.objects.filter(store=self.store)
        self.assertEqual(store_bottles.count(), 2)
        self.assertIn(bottle1, store_bottles)
        self.assertIn(bottle2, store_bottles)

    def test_bottle_count_accuracy(self):
        """Test accurate bottle counting"""
        # Create bottles
        Bottle.objects.create(wine=self.wine)
        Bottle.objects.create(wine=self.wine)
        
        count = Bottle.objects.filter(wine=self.wine).count()
        self.assertEqual(count, 2)
