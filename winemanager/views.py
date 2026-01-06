from rest_framework import viewsets
from rest_framework.decorators import action
from .models import Wine, Bottle, Store
from .serializers import WineSerializer, BottleSerializer, StoreSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q

class WineViewSet(viewsets.ModelViewSet):
    queryset = Wine.objects.all() 
    serializer_class = WineSerializer

    def get_queryset(self):
        return (
                    Wine.objects.all()
                    .annotate(
                        bottle_count=Count("bottle", distinct=True),
                        in_stock_count=Count("bottle", filter=Q(bottle__consumed_at__isnull=True), distinct=True),
                )
                .order_by("name")
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