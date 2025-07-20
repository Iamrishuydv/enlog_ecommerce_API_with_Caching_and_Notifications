from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import RegisterSerializer, ProfileSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import CartSerializer, OrderSerializer
from .models import Cart, CartItem, Order, OrderItem
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField()
        self.fields['password'] = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email is None or password is None:
            raise serializers.ValidationError("Email and password are required.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs['username'] = user.username
        return super().validate(attrs)



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        cache_key = "category_list"
        data = cache.get(cache_key)
        if data is None:
            serializer = self.get_serializer(self.queryset, many=True)
            data = serializer.data
            cache.set(cache_key, data, timeout=60 * 60)
        return Response(data)





class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        cache_key = "product_list"
        data = cache.get(cache_key)
        if data is None:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = self.get_paginated_response(serializer.data).data
            else:
                serializer = self.get_serializer(queryset, many=True)
                data = serializer.data
            cache.set(cache_key, data, timeout=60 * 60)  # 1 hour
        return Response(data)







class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)

        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = item.quantity + quantity if not created else quantity
        item.save()
        return Response({"message": "Added to cart"}, status=201)

    @action(detail=False, methods=['delete'])
    def remove(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response({"message": "Item not found in cart"}, status=404)

        if item.quantity > quantity:
            item.quantity -= quantity
            item.save()
            return Response({"message": f"Removed {quantity} item(s)"}, status=200)
        else:
            item.delete()
            return Response({"message": "Item removed from cart"}, status=204)



class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def place(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        items = cart.items.all()

        if not items.exists():
            return Response({"message": "Cart is empty"}, status=400)

        # Stock check
        for item in items:
            if item.product.stock < item.quantity:
                return Response(
                    {"message": f"Insufficient stock for {item.product.name}"},
                    status=400
                )

        total = sum(item.product.price * item.quantity for item in items)
        order = Order.objects.create(user=request.user, total_price=total)

        for item in items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            item.product.stock -= item.quantity
            item.product.save()

        cart.items.all().delete()
        return Response(OrderSerializer(order).data, status=201)






def notify_order_status_change(order):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{order.user.id}",
        {
            "type": "send_status_update",
            "data": {
                "order_id": order.id,
                "status": order.status,
                "message": f"Your order is now {order.status.upper()}"
            }
        }
    )
