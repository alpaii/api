# Classical Album Management API

FastAPI backend for managing classical music composers and albums.

## Setup

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
# The database should already be running in Docker
```

### 3. Initialize Database

The database tables will be created automatically when you start the server.

To load initial composer data:

```bash
# Make sure MySQL container is running
cd ../db && docker-compose up -d && cd ../api

# Load initial data
mysql -h localhost -u myuser -p mydata < scripts/init_composers.sql
# Or use Docker:
docker exec -i mysql-container mysql -u myuser -pmypassword mydata < scripts/init_composers.sql
```

### 4. Run Development Server

```bash
# From api/ directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Project Structure

```
api/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── .env.example           # Environment template
├── app/
│   ├── __init__.py
│   ├── database.py        # Database connection and session
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas for validation
│   └── routers/
│       ├── __init__.py
│       └── composers.py   # Composer CRUD endpoints
└── scripts/
    └── init_composers.sql # Initial data for composers
```

## API Endpoints

### Composers

- `POST /api/composers/` - Create a new composer
- `GET /api/composers/` - Get all composers (with pagination)
- `GET /api/composers/{id}` - Get a specific composer
- `PUT /api/composers/{id}` - Update a composer
- `DELETE /api/composers/{id}` - Delete a composer

### Example Requests

**Create Composer:**
```bash
curl -X POST "http://localhost:8000/api/composers/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gustav Mahler",
    "short_name": "Mahler",
    "birth_year": 1860,
    "death_year": 1911,
    "nationality": "Austrian"
  }'
```

**Get All Composers:**
```bash
curl "http://localhost:8000/api/composers/"
```

**Get Composer by ID:**
```bash
curl "http://localhost:8000/api/composers/1"
```

**Update Composer:**
```bash
curl -X PUT "http://localhost:8000/api/composers/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nationality": "German"
  }'
```

**Delete Composer:**
```bash
curl -X DELETE "http://localhost:8000/api/composers/1"
```

## Database Schema

### Composers Table

| Field | Type | Description |
|-------|------|-------------|
| id | INT | Primary key (auto-increment) |
| name | VARCHAR(100) | Full name in English |
| short_name | VARCHAR(50) | Short name or nickname |
| birth_year | INT | Year of birth |
| death_year | INT | Year of death |
| nationality | VARCHAR(50) | Country of origin |

## Development

### Database Connection

The application uses SQLAlchemy with MySQL connector (PyMySQL).

Connection string format:
```
DATABASE_URL=mysql+pymysql://user:password@host:port/database
```

### CORS Configuration

CORS is configured to allow requests from the Next.js frontend running on `http://localhost:3000`.

To modify allowed origins, edit `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add more origins here
    ...
)
```

## Testing

Visit http://localhost:8000/docs for interactive API documentation where you can test all endpoints.
