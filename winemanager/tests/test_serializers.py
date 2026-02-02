from django.test import TestCase
from decimal import Decimal
from winemanager.models import Wine, Bottle, Store
from winemanager.serializers import WineSerializer, BottleSerializer, StoreSerializer


class WineSerializerTests(TestCase):
    """Test cases for WineSerializer"""

    def setUp(self):
        """Create test data"""
        self.wine_data = {
            "name": "Test Wine",
            "region": "Napa Valley",
            "country": "US",
            "vintage": 2020,
            "grape_varieties": "Cabernet Sauvignon",
            "wine_type": "red",
            "rating": 4.5,
            "notes": "Great wine"
        }
        self.wine = Wine.objects.create(**self.wine_data)

    def test_wine_serialization_all_fields(self):
        """Test serializing wine with all fields"""
        serializer = WineSerializer(instance=self.wine)
        data = serializer.data
        
        self.assertEqual(data["name"], "Test Wine")
        self.assertEqual(data["region"], "Napa Valley")
        self.assertEqual(data["country"], "US")
        self.assertEqual(data["vintage"], 2020)
        self.assertEqual(data["grape_varieties"], "Cabernet Sauvignon")
        self.assertEqual(data["wine_type"], "red")
        self.assertEqual(float(data["rating"]), 4.5)
        self.assertEqual(data["notes"], "Great wine")

    def test_wine_serialization_with_annotations(self):
        """Test serializing wine with bottle_count and in_stock_count annotations"""
        # Create bottles
        Bottle.objects.create(wine=self.wine)
        Bottle.objects.create(wine=self.wine, consumed_at="2024-01-01")
        
        # Need to get queryset with annotations
        from django.db.models import Count, Q
        wine_with_annotations = Wine.objects.annotate(
            bottle_count=Count("bottle", distinct=True),
            in_stock_count=Count("bottle", filter=Q(bottle__consumed_at__isnull=True), distinct=True)
        ).get(id=self.wine.id)
        
        serializer = WineSerializer(instance=wine_with_annotations)
        data = serializer.data
        
        self.assertIn("bottle_count", data)
        self.assertIn("in_stock_count", data)
        self.assertEqual(data["bottle_count"], 2)
        self.assertEqual(data["in_stock_count"], 1)

    def test_wine_deserialization_valid(self):
        """Test deserializing valid wine data"""
        data = {
            "name": "New Wine",
            "country": "IT",
            "vintage": 2019,
            "rating": 3.5
        }
        serializer = WineSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        wine = serializer.save()
        
        self.assertEqual(wine.name, "New Wine")
        self.assertEqual(str(wine.country), "IT")
        self.assertEqual(wine.vintage, 2019)
        self.assertEqual(wine.rating, Decimal("3.5"))

    def test_wine_rating_validation_valid(self):
        """Test rating validation accepts valid values"""
        valid_ratings = [0.0, 2.5, 5.0, None]
        for rating in valid_ratings:
            data = {"name": "Test", "rating": rating}
            serializer = WineSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Rating {rating} should be valid")

    def test_wine_rating_validation_below_min(self):
        """Test rating validation rejects values below 0.0"""
        data = {"name": "Test", "rating": -0.1}
        serializer = WineSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("rating", serializer.errors)

    def test_wine_rating_validation_above_max(self):
        """Test rating validation rejects values above 5.0"""
        data = {"name": "Test", "rating": 5.1}
        serializer = WineSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("rating", serializer.errors)

    def test_wine_read_only_fields(self):
        """Test that bottle_count and in_stock_count are read-only"""
        data = {
            "name": "Test",
            "bottle_count": 999,
            "in_stock_count": 888
        }
        serializer = WineSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        wine = serializer.save()
        
        # These fields should not be set from input data
        # They should only come from annotations
        from django.db.models import Count, Q
        wine_with_annotations = Wine.objects.annotate(
            bottle_count=Count("bottle", distinct=True),
            in_stock_count=Count("bottle", filter=Q(bottle__consumed_at__isnull=True), distinct=True)
        ).get(id=wine.id)
        
        self.assertEqual(wine_with_annotations.bottle_count, 0)
        self.assertEqual(wine_with_annotations.in_stock_count, 0)

    def test_wine_nullable_fields_serialization(self):
        """Test serializing wine with nullable fields as None"""
        wine = Wine.objects.create(name="Minimal Wine")
        serializer = WineSerializer(instance=wine)
        data = serializer.data
        
        self.assertIsNone(data["region"])
        self.assertIsNone(data["country"])
        self.assertIsNone(data["vintage"])
        self.assertIsNone(data["grape_varieties"])
        self.assertIsNone(data["wine_type"])
        self.assertIsNone(data["rating"])


class BottleSerializerTests(TestCase):
    """Test cases for BottleSerializer"""

    def setUp(self):
        """Create test data"""
        self.wine = Wine.objects.create(name="Test Wine", vintage=2020)
        self.store = Store.objects.create(name="Test Store")

    def test_bottle_serialization_with_nested_store(self):
        """Test serializing bottle with nested store"""
        from datetime import date
        bottle = Bottle.objects.create(
            wine=self.wine,
            purchase_date=date(2024, 1, 15),
            price=Decimal("45.99"),
            store=self.store
        )
        serializer = BottleSerializer(instance=bottle)
        data = serializer.data
        
        self.assertEqual(data["wine"], self.wine.id)
        self.assertEqual(data["purchase_date"], "2024-01-15")
        self.assertEqual(float(data["price"]), 45.99)
        self.assertIsNotNone(data["store"])
        self.assertEqual(data["store"]["name"], "Test Store")

    def test_bottle_serialization_without_store(self):
        """Test serializing bottle without store"""
        bottle = Bottle.objects.create(wine=self.wine)
        serializer = BottleSerializer(instance=bottle)
        data = serializer.data
        
        self.assertEqual(data["wine"], self.wine.id)
        self.assertIsNone(data["store"])
        self.assertIsNone(data["purchase_date"])
        self.assertIsNone(data["price"])
        self.assertIsNone(data["consumed_at"])

    def test_bottle_deserialization_valid(self):
        """Test deserializing valid bottle data"""
        from datetime import date
        data = {
            "wine": self.wine.id,
            "purchase_date": "2024-01-15",
            "price": "45.99",
            "store": self.store.id
        }
        serializer = BottleSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        bottle = serializer.save()
        
        self.assertEqual(bottle.wine, self.wine)
        self.assertEqual(bottle.purchase_date, date(2024, 1, 15))
        self.assertEqual(bottle.price, Decimal("45.99"))
        self.assertEqual(bottle.store, self.store)

    def test_bottle_store_read_only(self):
        """Test that store is serialized as read-only nested object"""
        bottle = Bottle.objects.create(wine=self.wine, store=self.store)
        serializer = BottleSerializer(instance=bottle)
        data = serializer.data
        
        # Store should be a nested object, not just an ID
        self.assertIsInstance(data["store"], dict)
        self.assertIn("name", data["store"])

    def test_bottle_all_fields_present(self):
        """Test that all fields are present in serialization"""
        bottle = Bottle.objects.create(wine=self.wine)
        serializer = BottleSerializer(instance=bottle)
        data = serializer.data
        
        expected_fields = ["id", "wine", "purchase_date", "price", "store", "consumed_at"]
        for field in expected_fields:
            self.assertIn(field, data)


class StoreSerializerTests(TestCase):
    """Test cases for StoreSerializer"""

    def test_store_serialization(self):
        """Test serializing store"""
        store = Store.objects.create(name="Wine Warehouse")
        serializer = StoreSerializer(instance=store)
        data = serializer.data
        
        self.assertEqual(data["name"], "Wine Warehouse")
        self.assertIn("id", data)

    def test_store_deserialization(self):
        """Test deserializing store data"""
        data = {"name": "New Store"}
        serializer = StoreSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        store = serializer.save()
        
        self.assertEqual(store.name, "New Store")
