from rest_framework import viewsets
from rest_framework.decorators import action
from .models import Wine, Bottle, Store, Region
from .serializers import WineSerializer, BottleSerializer, StoreSerializer, RegionSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q

class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "country"]
    ordering_fields = ["name", "country", "wine_count"]
    ordering = ["country", "name"]
    
    def get_queryset(self):
        return Region.objects.annotate(
            wine_count=Count('wines', distinct=True)
        )

class WineViewSet(viewsets.ModelViewSet):
    
    serializer_class = WineSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "country", "region__name", "grape_varieties", "wine_type"]
    ordering_fields = ["name", "vintage", "country", "bottle_count", "in_stock_count"]
    ordering = ["name"]
    def get_queryset(self):
        return (
                    Wine.objects.all()
                    .annotate(
                        bottle_count=Count("bottle", distinct=True),
                        in_stock_count=Count("bottle", filter=Q(bottle__consumed_at__isnull=True), distinct=True),
                )
            )
class BottleViewSet(viewsets.ModelViewSet):
    queryset = Bottle.objects.all().order_by('-id')
    serializer_class = BottleSerializer
    filter_backends = [DjangoFilterBackend]

    # Allow /api/bottles/?wine=1
    filterset_fields = ["wine"]
    @action(detail=True, methods=['post'])
    def consume(self, request, pk=None):
        bottle = self.get_object()
                # idempotent: if already consumed, just return current state
        if bottle.consumed_at is None:
            bottle.consumed_at = timezone.localdate()
            bottle.save(update_fields=["consumed_at"])

        return Response(self.get_serializer(bottle).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def undo_consume(self, request, pk=None):
        bottle = self.get_object()
              
        if bottle.consumed_at is not None:
            bottle.consumed_at = None
            bottle.save(update_fields=["consumed_at"])

        return Response(self.get_serializer(bottle).data, status=status.HTTP_200_OK)
class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all().order_by('-id')
    serializer_class = StoreSerializer