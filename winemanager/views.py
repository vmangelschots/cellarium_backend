from rest_framework import viewsets
from .models import Wine
from .serializers import WineSerializer

class WineViewSet(viewsets.ModelViewSet):
    queryset = Wine.objects.all().order_by('-id')
    serializer_class = WineSerializer