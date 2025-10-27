from django.urls import path, include

urlpatterns = [
    path('api/listas/', include('precios.urls'))
]
