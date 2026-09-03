# Flower Billing App — Backend (FastAPI + JWT + MySQL)

This is the **user auth / JWT part** of the flower billing app (for farmers selling
products like rose, leaves, etc.). Billing/product modules can be added later on
top of this same structure (`app/models`, `app/schemas`, `app/routers`).

## Folder structure

```
flower_billing_app/
├── app/
│   ├── main.py                 # FastAPI app entrypoint
│   ├── config.py                # reads .env (DB + JWT settings)
│   ├── database.py              # SQLAlchemy engine/session
│   ├── models/
│   │   └── user.py              # User table
│   ├── schemas/
│   │   └── user.py              # Pydantic request/response models
│   ├── auth/
│   │   ├── jwt_handler.py       # create/verify JWT tokens
│   │   └── dependencies.py      # get_current_user (protects routes)
│   └── routers/
│       └── auth.py              # /auth/register, /auth/login, /auth/me
├── requirements.txt
├── .env                          # DB + JWT secrets (edit this)
└── README.md
```

## Step 1 — Open in PyCharm

1. Unzip the project, open the `flower_billing_app` folder in PyCharm as a project.
2. `File > Settings > Project > Python Interpreter` → click gear → **Add Interpreter**
   → **New Virtualenv Environment** (creates a `venv` for this project only).
3. Open the PyCharm **Terminal** tab (bottom) — it will already be inside the venv.

## Step 2 — Install dependencies

In the PyCharm terminal:

```bash
pip install -r requirements.txt
```

## Step 3 — Create the MySQL database

Open MySQL Workbench / CLI and run:

```sql
CREATE DATABASE flower_billing_db CHARACTER SET utf8mb4;
```

You don't need to create the `users` table manually — `Base.metadata.create_all()`
in `main.py` creates it automatically the first time the app starts.

## Step 4 — Edit `.env`

```
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=flower_billing_db

SECRET_KEY=change_this_to_a_long_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Generate a strong `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 5 — Run the server

```bash
uvicorn app.main:app --reload
```

Or in PyCharm: right-click `main.py` → doesn't work directly for uvicorn apps, so
instead create a **Run Configuration**:
- Run > Edit Configurations > + > Python
- Module name: `uvicorn`
- Parameters: `app.main:app --reload`
- Working directory: project root

Then open: **http://127.0.0.1:8000/docs** — interactive Swagger UI.

## Step 6 — Test it

1. **Register** — `POST /auth/register`
   ```json
   {
     "username": "farmer1",
     "email": "farmer1@example.com",
     "password": "secret123",
     "full_name": "Ravi Kumar"
   }
   ```

2. **Login** — `POST /auth/login` (form-data, not JSON — Swagger UI handles this
   automatically since it uses `OAuth2PasswordRequestForm`)
   - `username`: farmer1
   - `password`: secret123
   - Response: `{ "access_token": "...", "token_type": "bearer" }`

3. **Authorize** — click the **Authorize** button (top-right of `/docs`), paste the
   token, and now you can call protected routes.

4. **Get current user** — `GET /auth/me` (requires the token) → returns your user data.

## Next step (billing module)

Once this auth layer is confirmed working, add:
- `app/models/product.py` (e.g. Rose, Leaves — with `price_per_unit`, `stock_qty`)
- `app/models/invoice.py` / `invoice_item.py` (billing header + line items, linked
  to the farmer/user who created it)
- `app/routers/products.py`, `app/routers/billing.py`
- Protect those routes with `Depends(get_current_user)` the same way `/auth/me` is
  protected.

Say the word and I'll build that part next, using this same folder structure.

             LOGIN
               │
               ▼
       ┌─────────────────┐
       │ Access Token    │───► /auth/me
       │ 60 minutes      │
       └─────────────────┘
               │
          expires
               │
               ▼
       ┌─────────────────┐
       │ Refresh Token   │
       │ 7 days          │
       └─────────────────┘
               │
               ▼
        POST /auth/refresh
               │
               ▼
       New Access Token