from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import ecommerce_app_enlog.websocket_urls as app_urls

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(
            app_urls.websocket_urlpatterns
        )
    ),
})
