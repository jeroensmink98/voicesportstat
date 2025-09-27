Got it. Here’s a **self-contained refactor plan written for an AI code agent** so it can perform the restructuring. It includes the goals, steps, and final target structure, with example code snippets.

---

# 🛠 Refactor Plan for FastAPI App

## 🎯 Goal

* Reduce size of `main.py`
* Follow FastAPI best practices
* Organize code into **routes**, **services**, and **models**
* Prepare for future database support
* App should still run with:

  ```bash
  uv run fastapi dev
  ```

---

## 📂 Target Project Structure

```
project/
│── app/
│   │── __init__.py
│   │── main.py
│   │── config.py
│   │
│   ├── routes/
│   │   │── __init__.py
│   │   │── users.py
│   │   │── items.py
│   │
│   ├── services/
│   │   │── __init__.py
│   │   │── users_service.py
│   │   │── items_service.py
│   │
│   ├── models/
│   │   │── __init__.py
│   │   │── users.py
│   │   │── items.py
│   │
│   └── tests/
│       │── test_users.py
│       │── test_items.py
│
│── README.md
│── .env
```

---

## 📄 File Responsibilities

### `main.py`

Minimal entrypoint:

```python
from fastapi import FastAPI
from app.routes import users, items

app = FastAPI(title="My FastAPI App")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(items.router, prefix="/items", tags=["items"])
```

---

### `routes/users.py`

Handles HTTP only:

```python
from fastapi import APIRouter
from app.models.users import UserCreate, UserResponse
from app.services.users_service import create_user, list_users

router = APIRouter()

@router.post("/", response_model=UserResponse)
def register_user(user: UserCreate):
    return create_user(user)

@router.get("/", response_model=list[UserResponse])
def get_users():
    return list_users()
```

---

### `services/users_service.py`

Business logic (in-memory store for now):

```python
from app.models.users import UserCreate, UserResponse

_fake_users: list[UserResponse] = []
_id_counter = 1

def create_user(user: UserCreate) -> UserResponse:
    global _id_counter
    new_user = UserResponse(id=_id_counter, name=user.name, email=user.email)
    _fake_users.append(new_user)
    _id_counter += 1
    return new_user

def list_users() -> list[UserResponse]:
    return _fake_users
```

---

### `models/users.py`

Pydantic models for validation:

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
```

---

### `routes/items.py` (example stub)

```python
from fastapi import APIRouter
from app.models.items import ItemCreate, ItemResponse
from app.services.items_service import create_item, list_items

router = APIRouter()

@router.post("/", response_model=ItemResponse)
def add_item(item: ItemCreate):
    return create_item(item)

@router.get("/", response_model=list[ItemResponse])
def get_items():
    return list_items()
```

---

### `services/items_service.py`

```python
from app.models.items import ItemCreate, ItemResponse

_fake_items: list[ItemResponse] = []
_id_counter = 1

def create_item(item: ItemCreate) -> ItemResponse:
    global _id_counter
    new_item = ItemResponse(id=_id_counter, name=item.name)
    _fake_items.append(new_item)
    _id_counter += 1
    return new_item

def list_items() -> list[ItemResponse]:
    return _fake_items
```

---

### `models/items.py`

```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str

class ItemResponse(BaseModel):
    id: int
    name: str
```

---

### `tests/test_users.py`

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"

def test_list_users():
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## ✅ Expected Outcome

* `main.py` is now **tiny** and only wires routers.
* Routes only handle HTTP concerns.
* Services encapsulate logic, making it easier to test.
* Models validate data in and out.
* Tests ensure everything works after the refactor.

---

Do you also want me to include a **requirements.txt** file (with FastAPI, Uvicorn, etc.) so the agent knows exactly which deps to install?
