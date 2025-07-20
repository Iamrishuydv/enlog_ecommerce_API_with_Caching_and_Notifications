# 🛒 EnLog E-commerce API

This is a Django REST Framework-based E-commerce API that supports JWT authentication, product browsing, cart management, order placement, real-time order status updates via WebSockets, and Redis-based caching.

---

## 🚀 Features

- User registration & JWT login
- Profile view and update
- Product and category management (Admin-only)
- Add/remove items to cart (with quantity)
- Place orders with real-time status notifications
- Redis caching for product/category listing
- Pagination and filtering support
- Django Channels for WebSocket support

---

## 🛠 Tech Stack

- Python 3.10+
- Django 5.x
- Django REST Framework
- PostgreSQL
- Redis (for caching and WebSocket layer)
- Django Channels
- SimpleJWT

---

## ⚙️ Setup Instructions

### 1. Clone the Repo
```bash
git clone https://github.com/your-username/enlog-ecommerce-api.git
cd enlog-ecommerce-api
```

### 2. Create a Virtual Environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL DB

Update `DATABASES` in `ecommerce/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'enlog_ecom',
        'USER': 'postgres',
        'PASSWORD': 'yourpassword',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

Create the database in PostgreSQL:
```sql
CREATE DATABASE enlog_ecom;
```

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

---

## 🔁 Run the Server

For **development**:
```bash
python manage.py runserver
```

For **WebSocket support** (Django Channels):
```bash
daphne -p 8000 ecommerce.asgi:application
```

---

## 💡 API Endpoints

### Auth
- `POST /api/auth/register/` – Register
- `POST /api/auth/login/` – Login (returns JWT)
- `GET /api/auth/profile/` – View profile
- `PUT /api/auth/profile/` – Update profile

### Products & Categories
- `GET /api/categories/` – List categories
- `GET /api/products/` – List products (supports pagination & filtering)

### Cart
- `GET /api/cart/` – View cart
- `POST /api/cart/add/` – Add product to cart
- `DELETE /api/cart/remove/` – Remove product (by quantity)

### Orders
- `POST /api/orders/place/` – Place order
- `GET /api/orders/` – View order history

### WebSocket
- `ws://<host>:8000/ws/order-status/<user_id>/` – Live order status

---

## 📦 Caching

- Redis is used for caching category and product listings (1 hour timeout).
- Cache is invalidated automatically on create/update/delete.

---

## 🧪 Filtering & Pagination

- Pagination: 10 products per page
- Filter by: `category`, `stock`, `price` (via extension)

Example:
```http
GET /api/products/?category=2&stock=1
```

---

## 📡 WebSocket Order Status

- Use any WebSocket client (e.g., Postman or frontend)
- Connect to: `ws://localhost:8000/ws/order-status/<user_id>/`
- On status change, message is pushed live

---

## 📁 Folder Structure

```
ecommerce/
├── ecommerce/              # Main project config
├── ecommerce_app_enlog/    # Main app (users, products, orders, cart, ws)
├── manage.py
└── requirements.txt
```

---

---

## 🧑‍💻 Author

Created by **Your Name** – [rishuydvatwork@gmail.com](mailto:rishuydvatwork@gmail.com)

---

## 📜 License

MIT License
