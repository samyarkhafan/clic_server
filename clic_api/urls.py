from . import views
from django.urls import path


urlpatterns = [
    path('',views.getRoutes),
    path('rooms/',views.rooms),
    path("rooms/<int:pk>/",views.room),
    path("frequests/",views.frequests),
    path("frequests/<int:pk>/",views.frequest),
    path("uploads/",views.uploads),
    path("uploads/<int:pk>/",views.upload),
    path("uploads/download/<str:rname>/<str:dname>/",views.uploadDownload),
]
