from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WineViewSet,BottleViewSet, StoreViewSet


router = DefaultRouter()
router.register(r'wines', WineViewSet, basename='wine')
router.register(r'bottles', BottleViewSet)
router.register(r'stores', StoreViewSet)

urlpatterns = [
    path('', include(router.urls)),

]
