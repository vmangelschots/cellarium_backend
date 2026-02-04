from django.contrib import admin
from .models import Wine, Bottle, Store, Region

# Register your models here.
admin.site.register(Wine)
admin.site.register(Bottle)
admin.site.register(Store)
admin.site.register(Region)