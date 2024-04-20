"""
URL configuration for ms_brd project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from webird import views as webird_views
from pic import views as pic_views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', webird_views.index),
    path('admin/login/', webird_views.login),
    path('admin/register/', webird_views.register),
    path('logout/', webird_views.logout),
    path('records/', webird_views.records),
    path('records/<int:record_id>/', webird_views.records_edit, name='record_id'),
    path('records_visualized/', webird_views.visualized_record),
    path('species/', webird_views.bird_species),
    # path('location/', views.location),
    path('location/<str:page_name>/', webird_views.location_view, name='location_page'),
    path('species/<str:species_name>/', webird_views.species_view, name='species_name'),
    path('classes/<str:bird_class_name>/', webird_views.classes_view, name='bird_class_name'),
    path('species/refresh/<int:bird_id>/', webird_views.refresh_distribution_graph_button, name='bird_id'),
    path('add/', webird_views.add_record),
    path('ebird_add_verify/', webird_views.add_record_ebird_verify),
    path('ebird_add_verify/upload/', webird_views.add_record_ebird_upload),
    path('add_birdinfo_csv_verify/', webird_views.add_birdinfo_csv_verify),
    path('add_birdinfo_csv_verify/upload/', webird_views.add_birdinfo_csv_upload),
    # path('add_dev/', webird_views.add_record_dev),
    path('gallery/', webird_views.gallery),
    path('gallery_add/', webird_views.add_img),
    path('img/add/', pic_views.upload_image),
    path('img/add/receive/', pic_views.receive_img),
    path('img/show/', pic_views.image_list),
    path('404/', webird_views.error_404),
    path('add_birdinfo/', webird_views.add_birdinfo),
    path('add_location/', webird_views.add_location),
    path('about/', webird_views.blogs_view),
    path('management/', webird_views.management),
    path('api/species-distribution/', webird_views.record_api),
    path('api/record_get_csv/<str:arg>', webird_views.record_get_csv, name='arg'),
    # path('tmp/', webird_views.tmp),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# handler404 = webird_views.error_404
