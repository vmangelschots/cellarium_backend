from rest_framework.test import APITestCase
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
from datetime import date
from winemanager.models import Wine, Bottle, Store


class ComplexWorkflowTests(APITestCase):
    """Test cases for complex workflows integrating multiple models"""

    def test_wine_bottle_consume_workflow(self):
        """Test complete workflow: create wine -> bottles -> consume -> verify counts"""
        # Create wine
        wine_data = {"name": "Workflow Wine", "vintage": 2020}
        wine_response = self.client.post(reverse('wine-list'), wine_data, format='json')
        wine_id = wine_response.data['id']
        
        # Create bottles
        bottle1_data = {"wine": wine_id, "price": "40.00"}
        bottle2_data = {"wine": wine_id, "price": "45.00"}
        bottle3_data = {"wine": wine_id, "price": "50.00"}
        
        bottle1_response = self.client.post(reverse('bottle-list'), bottle1_data, format='json')
        bottle2_response = self.client.post(reverse('bottle-list'), bottle2_data, format='json')
        bottle3_response = self.client.post(reverse('bottle-list'), bottle3_data, format='json')
        
        # Verify all created
        self.assertEqual(bottle1_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(bottle2_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(bottle3_response.status_code, status.HTTP_201_CREATED)
        
        # Check wine has 3 bottles, all in stock
        wine_detail = self.client.get(reverse('wine-detail', kwargs={'pk': wine_id}))
        self.assertEqual(wine_detail.data['bottle_count'], 3)
        self.assertEqual(wine_detail.data['in_stock_count'], 3)
        
        # Consume one bottle
        bottle1_id = bottle1_response.data['id']
        consume_response = self.client.post(reverse('bottle-consume', kwargs={'pk': bottle1_id}))
        self.assertEqual(consume_response.status_code, status.HTTP_200_OK)
        
        # Check wine now has 2 in stock
        wine_detail = self.client.get(reverse('wine-detail', kwargs={'pk': wine_id}))
        self.assertEqual(wine_detail.data['bottle_count'], 3)
        self.assertEqual(wine_detail.data['in_stock_count'], 2)
        
        # Undo consume
        undo_response = self.client.post(reverse('bottle-undo-consume', kwargs={'pk': bottle1_id}))
        self.assertEqual(undo_response.status_code, status.HTTP_200_OK)
        
        # Check wine has 3 in stock again
        wine_detail = self.client.get(reverse('wine-detail', kwargs={'pk': wine_id}))
        self.assertEqual(wine_detail.data['bottle_count'], 3)
        self.assertEqual(wine_detail.data['in_stock_count'], 3)

    def test_bottle_counts_update_on_consume(self):
        """Test that bottle counts update correctly when consuming"""
        wine = Wine.objects.create(name="Count Test Wine")
        bottle1 = Bottle.objects.create(wine=wine)
        bottle2 = Bottle.objects.create(wine=wine)
        
        # Initially both in stock
        wine_url = reverse('wine-detail', kwargs={'pk': wine.id})
        response = self.client.get(wine_url)
        self.assertEqual(response.data['bottle_count'], 2)
        self.assertEqual(response.data['in_stock_count'], 2)
        
        # Consume one
        self.client.post(reverse('bottle-consume', kwargs={'pk': bottle1.id}))
        response = self.client.get(wine_url)
        self.assertEqual(response.data['bottle_count'], 2)
        self.assertEqual(response.data['in_stock_count'], 1)
        
        # Consume another
        self.client.post(reverse('bottle-consume', kwargs={'pk': bottle2.id}))
        response = self.client.get(wine_url)
        self.assertEqual(response.data['bottle_count'], 2)
        self.assertEqual(response.data['in_stock_count'], 0)

    def test_in_stock_count_accuracy(self):
        """Test in_stock_count accuracy with mixed consumed/unconsumed bottles"""
        wine = Wine.objects.create(name="Stock Test")
        
        # Create 5 bottles
        bottles = [Bottle.objects.create(wine=wine) for _ in range(5)]
        
        # Consume 3 of them
        for bottle in bottles[:3]:
            bottle.consumed_at = date.today()
            bottle.save()
        
        # Check counts
        wine_url = reverse('wine-detail', kwargs={'pk': wine.id})
        response = self.client.get(wine_url)
        self.assertEqual(response.data['bottle_count'], 5)
        self.assertEqual(response.data['in_stock_count'], 2)


class CascadeDeleteTests(TestCase):
    """Test cases for cascade and SET_NULL deletion behavior"""

    def test_wine_deletion_cascades_bottles(self):
        """Test that deleting wine cascades to bottles"""
        wine = Wine.objects.create(name="Cascade Wine")
        bottle1 = Bottle.objects.create(wine=wine)
        bottle2 = Bottle.objects.create(wine=wine)
        
        bottle1_id = bottle1.id
        bottle2_id = bottle2.id
        
        # Delete wine
        wine.delete()
        
        # Bottles should be deleted
        self.assertFalse(Bottle.objects.filter(id=bottle1_id).exists())
        self.assertFalse(Bottle.objects.filter(id=bottle2_id).exists())

    def test_store_deletion_nullifies_bottles(self):
        """Test that deleting store sets bottle.store to NULL"""
        wine = Wine.objects.create(name="Store Test Wine")
        store = Store.objects.create(name="Test Store")
        bottle = Bottle.objects.create(wine=wine, store=store)
        
        bottle_id = bottle.id
        
        # Delete store
        store.delete()
        
        # Bottle should still exist with NULL store
        self.assertTrue(Bottle.objects.filter(id=bottle_id).exists())
        bottle.refresh_from_db()
        self.assertIsNone(bottle.store)


class MultipleBottleTests(APITestCase):
    """Test cases for multiple bottles of same wine"""

    def test_multiple_bottles_same_wine(self):
        """Test wine can have multiple bottles tracked correctly"""
        wine = Wine.objects.create(name="Multi Bottle Wine")
        store1 = Store.objects.create(name="Store 1")
        store2 = Store.objects.create(name="Store 2")
        
        # Create bottles from different stores, different prices
        Bottle.objects.create(wine=wine, store=store1, price=Decimal("40.00"))
        Bottle.objects.create(wine=wine, store=store2, price=Decimal("45.00"))
        Bottle.objects.create(wine=wine, store=store1, price=Decimal("42.00"))
        
        # Get wine details
        wine_url = reverse('wine-detail', kwargs={'pk': wine.id})
        response = self.client.get(wine_url)
        
        self.assertEqual(response.data['bottle_count'], 3)
        self.assertEqual(response.data['in_stock_count'], 3)
        
        # Filter bottles by wine
        bottles_response = self.client.get(reverse('bottle-list'), {'wine': wine.id})
        self.assertEqual(len(bottles_response.data), 3)

    def test_consume_multiple_bottles_count(self):
        """Test consuming multiple bottles updates counts correctly"""
        wine = Wine.objects.create(name="Consume Multi Wine")
        bottles = [Bottle.objects.create(wine=wine) for _ in range(4)]
        
        # Consume 2 bottles
        for bottle in bottles[:2]:
            self.client.post(reverse('bottle-consume', kwargs={'pk': bottle.id}))
        
        # Check counts
        wine_url = reverse('wine-detail', kwargs={'pk': wine.id})
        response = self.client.get(wine_url)
        self.assertEqual(response.data['bottle_count'], 4)
        self.assertEqual(response.data['in_stock_count'], 2)


class SearchOrderingIntegrationTests(APITestCase):
    """Test cases for search and ordering integration"""

    def test_search_with_bottle_count_ordering(self):
        """Test combining search with bottle_count ordering"""
        # Create wines with different bottle counts
        wine1 = Wine.objects.create(name="French Bordeaux", country="FR")
        wine2 = Wine.objects.create(name="French Burgundy", country="FR")
        wine3 = Wine.objects.create(name="Italian Chianti", country="IT")
        
        # Different bottle counts
        Bottle.objects.create(wine=wine1)
        Bottle.objects.create(wine=wine2)
        Bottle.objects.create(wine=wine2)
        
        # Search for French wines ordered by bottle count
        response = self.client.get(reverse('wine-list'), {
            'search': 'French',
            'ordering': 'bottle_count'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should get 2 French wines
        self.assertEqual(len(response.data), 2)

    def test_filter_and_count_consistency(self):
        """Test that filtering and counts are consistent"""
        wine1 = Wine.objects.create(name="Wine 1")
        wine2 = Wine.objects.create(name="Wine 2")
        
        # Create bottles
        Bottle.objects.create(wine=wine1)
        Bottle.objects.create(wine=wine1)
        Bottle.objects.create(wine=wine2)
        
        # Filter bottles by wine1
        response = self.client.get(reverse('bottle-list'), {'wine': wine1.id})
        self.assertEqual(len(response.data), 2)
        
        # Check wine1 bottle count
        wine_response = self.client.get(reverse('wine-detail', kwargs={'pk': wine1.id}))
        self.assertEqual(wine_response.data['bottle_count'], 2)

    def test_concurrent_bottle_operations(self):
        """Test multiple bottle operations maintain data consistency"""
        wine = Wine.objects.create(name="Concurrent Test Wine")
        
        # Create multiple bottles
        bottles = [Bottle.objects.create(wine=wine) for _ in range(3)]
        
        # Perform various operations
        self.client.post(reverse('bottle-consume', kwargs={'pk': bottles[0].id}))
        self.client.post(reverse('bottle-consume', kwargs={'pk': bottles[1].id}))
        self.client.post(reverse('bottle-undo-consume', kwargs={'pk': bottles[0].id}))
        
        # Verify final state
        wine_response = self.client.get(reverse('wine-detail', kwargs={'pk': wine.id}))
        self.assertEqual(wine_response.data['bottle_count'], 3)
        self.assertEqual(wine_response.data['in_stock_count'], 2)
        
        # Verify individual bottles
        bottles[0].refresh_from_db()
        bottles[1].refresh_from_db()
        bottles[2].refresh_from_db()
        
        self.assertIsNone(bottles[0].consumed_at)  # Was undone
        self.assertIsNotNone(bottles[1].consumed_at)  # Still consumed
        self.assertIsNone(bottles[2].consumed_at)  # Never consumed
