from django.conf import settings
#from django.conf.urls.static import static
from django.urls import path
from .views import buscar_contrato, generar_documento_view, servir_archivo_media, buscar_por_proveedor, buscar_pedido, \
    buscar_orden
from django.views.generic import RedirectView

urlpatterns = [
    path("", buscar_contrato, name="buscar_contrato"),
    path("generar-documento/", generar_documento_view, name="generar_documento"),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
    path('buscar-por-proveedor/', buscar_por_proveedor, name='buscar_por_proveedor'),
    path("buscar-pedido/", buscar_pedido, name="buscar_pedido"),
path("buscar-orden/", buscar_orden, name="buscar_orden"),
]

 # Solo añadir la ruta de `media/` si estamos en producción
if not settings.DEBUG:
    urlpatterns += [
        path("media/<path:path>", servir_archivo_media, name="servir_archivo_media"),
        path("buscar-proveedor/", buscar_por_proveedor, name="buscar_por_proveedor"),
        path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
        path("buscar-pedido/", buscar_pedido, name="buscar_pedido"),
        path("buscar-orden/", buscar_orden, name="buscar_orden"),
    ]