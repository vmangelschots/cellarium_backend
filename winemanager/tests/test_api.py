from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from datetime import date
from winemanager.models import Wine, Bottle, Store


class WineAPICRUDTests(APITestCase):
    """Test cases for Wine API CRUD operations"""

    def setUp(self):
        """Create test data"""
        self.wine = Wine.objects.create(
            name="Test Wine",
            region="Bordeaux",
            country="FR",
            vintage=2020,
            grape_varieties="Cabernet Sauvignon",
            wine_type="red",
            rating=4.5
        )
        self.list_url = reverse('wine-list')
        self.detail_url = reverse('wine-detail', kwargs={'pk': self.wine.pk})

    def test_list_wines_empty(self):
        """Test listing wines when database is empty"""
        Wine.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_wines_with_data(self):
        """Test listing wines with data"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_wine_valid(self):
        """Test creating wine with valid data"""
        data = {
            "name": "New Wine",
            "region": "Tuscany",
            "country": "IT",
            "vintage": 2019,
            "grape_varieties": "Sangiovese",
            "wine_type": "red",
            "rating": 4.0,
            "notes": "Excellent"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Wine.objects.count(), 2)
        self.assertEqual(response.data['name'], "New Wine")
        self.assertEqual(response.data['country'], "IT")

    def test_create_wine_minimal(self):
        """Test creating wine with only required fields"""
        data = {"name": "Minimal Wine"}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Minimal Wine")

    def test_create_wine_invalid_rating(self):
        """Test creating wine with invalid rating returns 400"""
        data = {"name": "Test", "rating": 5.5}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rating', response.data)

    def test_retrieve_wine_exists(self):
        """Test retrieving a wine that exists"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Wine")
        self.assertEqual(response.data['country'], "FR")

    def test_retrieve_wine_not_found(self):
        """Test retrieving a wine that doesn't exist returns 404"""
        url = reverse('wine-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_wine_put(self):
        """Test full update of wine with PUT"""
        data = {
            "name": "Updated Wine",
            "region": "Napa",
            "country": "US",
            "vintage": 2021,
            "grape_varieties": "Merlot",
            "wine_type": "red",
            "rating": 3.5,
            "notes": "Updated"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wine.refresh_from_db()
        self.assertEqual(self.wine.name, "Updated Wine")
        self.assertEqual(str(self.wine.country), "US")

    def test_update_wine_patch(self):
        """Test partial update of wine with PATCH"""
        data = {"name": "Patched Wine", "rating": 5.0}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wine.refresh_from_db()
        self.assertEqual(self.wine.name, "Patched Wine")
        self.assertEqual(self.wine.rating, Decimal("5.0"))
        self.assertEqual(str(self.wine.country), "FR")  # Unchanged

    def test_delete_wine(self):
        """Test deleting a wine"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Wine.objects.filter(pk=self.wine.pk).exists())

    def test_wine_annotations_bottle_count(self):
        """Test that bottle_count annotation is present"""
        Bottle.objects.create(wine=self.wine)
        Bottle.objects.create(wine=self.wine)
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('bottle_count', response.data)
        self.assertEqual(response.data['bottle_count'], 2)

    def test_wine_annotations_in_stock_count(self):
        """Test that in_stock_count annotation is accurate"""
        Bottle.objects.create(wine=self.wine)
        Bottle.objects.create(wine=self.wine, consumed_at=date.today())
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('in_stock_count', response.data)
        self.assertEqual(response.data['in_stock_count'], 1)


class WineSearchFilterTests(APITestCase):
    """Test cases for Wine search and filtering"""

    def setUp(self):
        """Create test wines"""
        Wine.objects.create(name="Bordeaux Supreme", country="FR", region="Bordeaux")
        Wine.objects.create(name="Chianti Classico", country="IT", region="Tuscany")
        Wine.objects.create(name="Napa Cabernet", country="US", region="Napa Valley", grape_varieties="Cabernet Sauvignon")
        self.list_url = reverse('wine-list')

    def test_search_by_name(self):
        """Test searching wines by name"""
        response = self.client.get(self.list_url, {'search': 'Bordeaux'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Bordeaux Supreme")

    def test_search_by_country(self):
        """Test searching wines by country"""
        response = self.client.get(self.list_url, {'search': 'IT'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Chianti Classico")

    def test_search_by_region(self):
        """Test searching wines by region"""
        response = self.client.get(self.list_url, {'search': 'Napa'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Napa Cabernet")

    def test_search_by_grape_varieties(self):
        """Test searching wines by grape varieties"""
        response = self.client.get(self.list_url, {'search': 'Cabernet'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['grape_varieties'], "Cabernet Sauvignon")

    def test_search_multiple_fields(self):
        """Test that search works across multiple fields"""
        response = self.client.get(self.list_url, {'search': 'Tuscany'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_case_insensitive(self):
        """Test that search is case insensitive"""
        response = self.client.get(self.list_url, {'search': 'bordeaux'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class WineOrderingTests(APITestCase):
    """Test cases for Wine ordering"""

    def setUp(self):
        """Create test wines"""
        self.wine_a = Wine.objects.create(name="A Wine", vintage=2018)
        self.wine_z = Wine.objects.create(name="Z Wine", vintage=2022)
        self.wine_m = Wine.objects.create(name="M Wine", vintage=2020)
        
        # Create bottles for ordering tests
        Bottle.objects.create(wine=self.wine_a)
        Bottle.objects.create(wine=self.wine_a)
        Bottle.objects.create(wine=self.wine_z)
        
        self.list_url = reverse('wine-list')

    def test_order_by_name(self):
        """Test ordering wines by name ascending"""
        response = self.client.get(self.list_url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [wine['name'] for wine in response.data]
        self.assertEqual(names[0], "A Wine")
        self.assertEqual(names[-1], "Z Wine")

    def test_order_by_vintage(self):
        """Test ordering wines by vintage"""
        response = self.client.get(self.list_url, {'ordering': 'vintage'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vintages = [wine['vintage'] for wine in response.data]
        self.assertEqual(vintages[0], 2018)
        self.assertEqual(vintages[-1], 2022)

    def test_order_by_bottle_count(self):
        """Test ordering wines by bottle_count"""
        response = self.client.get(self.list_url, {'ordering': 'bottle_count'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # wine_m has 0 bottles, wine_z has 1, wine_a has 2
        self.assertLessEqual(response.data[0]['bottle_count'], response.data[-1]['bottle_count'])

    def test_order_by_in_stock_count(self):
        """Test ordering wines by in_stock_count"""
        response = self.client.get(self.list_url, {'ordering': 'in_stock_count'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data)

    def test_order_descending(self):
        """Test ordering wines descending"""
        response = self.client.get(self.list_url, {'ordering': '-name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [wine['name'] for wine in response.data]
        self.assertEqual(names[0], "Z Wine")
        self.assertEqual(names[-1], "A Wine")


class BottleAPICRUDTests(APITestCase):
    """Test cases for Bottle API CRUD operations"""

    def setUp(self):
        """Create test data"""
        self.wine = Wine.objects.create(name="Test Wine", vintage=2020)
        self.store = Store.objects.create(name="Test Store")
        self.bottle = Bottle.objects.create(wine=self.wine, price=Decimal("45.99"))
        
        self.list_url = reverse('bottle-list')
        self.detail_url = reverse('bottle-detail', kwargs={'pk': self.bottle.pk})

    def test_list_bottles(self):
        """Test listing bottles"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_bottle(self):
        """Test creating a bottle"""
        data = {
            "wine": self.wine.id,
            "purchase_date": "2024-01-15",
            "price": "55.00"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bottle.objects.count(), 2)

    def test_create_bottle_with_store(self):
        """Test creating a bottle with store"""
        data = {
            "wine": self.wine.id,
            "store": self.store.id,
            "price": "60.00"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_bottle(self):
        """Test retrieving a bottle"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['wine'], self.wine.id)

    def test_update_bottle(self):
        """Test updating a bottle"""
        data = {
            "wine": self.wine.id,
            "price": "50.00"
        }
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bottle.refresh_from_db()
        self.assertEqual(self.bottle.price, Decimal("50.00"))

    def test_delete_bottle(self):
        """Test deleting a bottle"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Bottle.objects.filter(pk=self.bottle.pk).exists())

    def test_filter_bottles_by_wine(self):
        """Test filtering bottles by wine"""
        wine2 = Wine.objects.create(name="Another Wine")
        Bottle.objects.create(wine=wine2)
        
        response = self.client.get(self.list_url, {'wine': self.wine.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for bottle in response.data:
            self.assertEqual(bottle['wine'], self.wine.id)

    def test_bottle_ordering(self):
        """Test that bottles are ordered by -id"""
        bottle2 = Bottle.objects.create(wine=self.wine)
        bottle3 = Bottle.objects.create(wine=self.wine)
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Most recent should be first
        self.assertEqual(response.data[0]['id'], bottle3.id)


class BottleCustomActionsTests(APITestCase):
    """Test cases for Bottle custom actions (consume, undo_consume)"""

    def setUp(self):
        """Create test data"""
        self.wine = Wine.objects.create(name="Test Wine")
        self.bottle = Bottle.objects.create(wine=self.wine)
        self.consume_url = reverse('bottle-consume', kwargs={'pk': self.bottle.pk})
        self.undo_consume_url = reverse('bottle-undo-consume', kwargs={'pk': self.bottle.pk})

    def test_consume_bottle_success(self):
        """Test consuming a bottle successfully"""
        response = self.client.post(self.consume_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bottle.refresh_from_db()
        self.assertIsNotNone(self.bottle.consumed_at)

    def test_consume_bottle_sets_date(self):
        """Test that consuming sets consumed_at to today"""
        response = self.client.post(self.consume_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bottle.refresh_from_db()
        self.assertEqual(self.bottle.consumed_at, date.today())

    def test_consume_bottle_idempotent(self):
        """Test that consuming already consumed bottle is idempotent"""
        # Consume once
        self.client.post(self.consume_url)
        self.bottle.refresh_from_db()
        first_date = self.bottle.consumed_at
        
        # Consume again
        response = self.client.post(self.consume_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bottle.refresh_from_db()
        self.assertEqual(self.bottle.consumed_at, first_date)

    def test_consume_bottle_not_found(self):
        """Test consuming non-existent bottle returns 404"""
        url = reverse('bottle-consume', kwargs={'pk': 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_undo_consume_success(self):
        """Test undo consume successfully"""
        # First consume
        self.bottle.consumed_at = date.today()
        self.bottle.save()
        
        # Then undo
        response = self.client.post(self.undo_consume_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bottle.refresh_from_db()
        self.assertIsNone(self.bottle.consumed_at)

    def test_undo_consume_clears_date(self):
        """Test that undo consume clears consumed_at"""
        self.bottle.consumed_at = date.today()
        self.bottle.save()
        
        self.client.post(self.undo_consume_url)
        self.bottle.refresh_from_db()
        self.assertIsNone(self.bottle.consumed_at)

    def test_undo_consume_idempotent(self):
        """Test that undo consume on unconsumed bottle is idempotent"""
        self.assertIsNone(self.bottle.consumed_at)
        
        response = self.client.post(self.undo_consume_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bottle.refresh_from_db()
        self.assertIsNone(self.bottle.consumed_at)

    def test_undo_consume_not_found(self):
        """Test undo consume on non-existent bottle returns 404"""
        url = reverse('bottle-undo-consume', kwargs={'pk': 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StoreAPICRUDTests(APITestCase):
    """Test cases for Store API CRUD operations"""

    def setUp(self):
        """Create test data"""
        self.store = Store.objects.create(name="Test Store")
        self.list_url = reverse('store-list')
        self.detail_url = reverse('store-detail', kwargs={'pk': self.store.pk})

    def test_list_stores(self):
        """Test listing stores"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_store(self):
        """Test creating a store"""
        data = {"name": "New Store"}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Store.objects.count(), 2)

    def test_retrieve_store(self):
        """Test retrieving a store"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Store")

    def test_update_store(self):
        """Test updating a store"""
        data = {"name": "Updated Store"}
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.store.refresh_from_db()
        self.assertEqual(self.store.name, "Updated Store")

    def test_delete_store(self):
        """Test deleting a store"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Store.objects.filter(pk=self.store.pk).exists())

    def test_store_ordering(self):
        """Test that stores are ordered by -id"""
        store2 = Store.objects.create(name="Store 2")
        store3 = Store.objects.create(name="Store 3")
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Most recent should be first
        self.assertEqual(response.data[0]['id'], store3.id)
