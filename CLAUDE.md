# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend application for the Classical Album Management system. This API provides endpoints for managing classical music composers and their albums.

## Development Commands

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Database Setup

```bash
# Make sure MySQL container is running
cd ../db && docker-compose up -d && cd ../api

# Tables are created automatically when the server starts
# Or manually create tables:
python -c "from app.database import engine, Base; from app.models import Composer; Base.metadata.create_all(bind=engine)"

# Load initial composer data
docker exec -i mysql-container mysql -u myuser -p{password} mydata < scripts/init_composers.sql
```

### Running the Server

```bash
# Development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing

```bash
# Visit interactive API docs
open http://localhost:8000/docs

# Or test with curl
curl http://localhost:8000/api/composers/
curl -X POST http://localhost:8000/api/composers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Gustav Mahler", "short_name": "Mahler", "birth_year": 1860, "death_year": 1911, "nationality": "Austrian"}'
```

## Project Structure

```
api/
├── main.py                    # FastAPI app entry point, CORS config
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (DATABASE_URL)
├── .env.example              # Environment template
├── .gitignore                # Git ignore patterns
├── README.md                 # Detailed API documentation
├── app/
│   ├── __init__.py
│   ├── database.py           # SQLAlchemy engine, session, Base
│   ├── models.py             # Database models (Composer)
│   ├── schemas.py            # Pydantic schemas for validation
│   └── routers/
│       ├── __init__.py
│       └── composers.py      # Composer CRUD endpoints
└── scripts/
    └── init_composers.sql    # Initial data for 11 famous composers
```

## Architecture

### Tech Stack

- **FastAPI** 0.115.5 - Modern async web framework
- **SQLAlchemy** 2.0.36 - ORM for database operations
- **Pydantic** 2.10.3 - Data validation using Python type hints
- **PyMySQL** 1.1.1 - MySQL driver
- **Uvicorn** 0.32.1 - ASGI server

### Database Connection

Connection managed through SQLAlchemy:
- **Engine**: Created from `DATABASE_URL` environment variable
- **Session**: Scoped session with dependency injection
- **Base**: Declarative base for all models

Connection string format:
```
DATABASE_URL=mysql+pymysql://user:password@host:port/database
```

### Application Layers

1. **Models** (`app/models.py`):
   - SQLAlchemy ORM models
   - Define database schema
   - Table: `composers` with fields: id, name, short_name, birth_year, death_year, nationality

2. **Schemas** (`app/schemas.py`):
   - Pydantic models for request/response validation
   - `ComposerCreate`: For POST requests
   - `ComposerUpdate`: For PUT requests (partial updates)
   - `ComposerResponse`: For GET responses (includes ID)

3. **Routers** (`app/routers/composers.py`):
   - API endpoints grouped by resource
   - Dependency injection for database sessions
   - CRUD operations: Create, Read, Read All, Update, Delete

4. **Main** (`main.py`):
   - FastAPI app initialization
   - CORS middleware configuration
   - Router registration
   - Database table creation on startup

### API Endpoints

**Base URL**: `http://localhost:8000`

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | `/` | Root endpoint | - | API info |
| GET | `/health` | Health check | - | Status |
| POST | `/api/composers/` | Create composer | ComposerCreate | ComposerResponse |
| GET | `/api/composers/` | List composers | Query: skip, limit | List[ComposerResponse] |
| GET | `/api/composers/{id}` | Get composer | - | ComposerResponse |
| PUT | `/api/composers/{id}` | Update composer | ComposerUpdate | ComposerResponse |
| DELETE | `/api/composers/{id}` | Delete composer | - | 204 No Content |

### CORS Configuration

Configured to allow requests from Next.js frontend:
- Origin: `http://localhost:3000`
- Credentials: Allowed
- Methods: All
- Headers: All

To add more origins, edit `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    ...
)
```

### Database Models

**Composer Model** (`app/models.py`):
```python
class Composer(Base):
    __tablename__ = "composers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)           # Full name in English
    short_name = Column(String(50), nullable=True)       # Nickname
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)
    nationality = Column(String(50), nullable=True)
```

### Initial Data

The `scripts/init_composers.sql` includes 11 famous classical composers:
- Johann Sebastian Bach (German, 1685-1750)
- Antonio Vivaldi (Italian, 1678-1741)
- George Frideric Handel (German-British, 1685-1759)
- Ludwig van Beethoven (German, 1770-1827)
- Wolfgang Amadeus Mozart (Austrian, 1756-1791)
- Franz Schubert (Austrian, 1797-1828)
- Frédéric Chopin (Polish-French, 1810-1849)
- Johannes Brahms (German, 1833-1897)
- Felix Mendelssohn (German, 1809-1847)
- Pyotr Ilyich Tchaikovsky (Russian, 1840-1893)
- Sergei Rachmaninoff (Russian, 1873-1943)

## Common Development Tasks

### Adding a New Model

1. Define model in `app/models.py`:
```python
class Album(Base):
    __tablename__ = "albums"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    composer_id = Column(Integer, ForeignKey("composers.id"))
```

2. Create schemas in `app/schemas.py`
3. Create router in `app/routers/albums.py`
4. Register router in `main.py`:
```python
from app.routers import albums
app.include_router(albums.router, prefix="/api")
```

### Database Migrations

Currently using `Base.metadata.create_all()` for development. For production, consider:
- **Alembic**: SQLAlchemy migration tool
- Tracks schema changes over time
- Allows rollback of migrations

### Environment Variables

`.env` file (not committed to git):
```
DATABASE_URL=mysql+pymysql://user:password@host:port/database
```

Load with:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Dependency Injection

Database session injected into endpoints:
```python
@router.get("/composers/")
def get_composers(db: Session = Depends(get_db)):
    # db session is automatically created and closed
    return db.query(Composer).all()
```

## Error Handling

HTTP error responses:
- **404**: Resource not found (`HTTPException(status_code=404)`)
- **422**: Validation error (automatic from Pydantic)
- **500**: Internal server error

Example:
```python
if not composer:
    raise HTTPException(status_code=404, detail="Composer not found")
```

## Interactive Documentation

FastAPI automatically generates interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

Use `/docs` to test endpoints directly in the browser.

## Security Considerations

### Current Setup (Development)
- No authentication required
- CORS enabled for localhost:3000
- Database credentials in `.env` file

### Production Recommendations
- Add authentication (JWT tokens, OAuth2)
- Use environment-specific CORS origins
- Store secrets in secure vault (not .env)
- Enable HTTPS
- Rate limiting middleware
- Input sanitization
- SQL injection protection (SQLAlchemy handles this)

## Troubleshooting

### Database Connection Errors
```bash
# Check if MySQL is running
docker ps | grep mysql

# Test connection
docker exec -it mysql-container mysql -u myuser -p
```

### Import Errors
```bash
# Make sure you're in api/ directory
cd /Users/jmac/Documents/dev/alpaii/api

# Check PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Testing Strategy

### Manual Testing
- Use `/docs` for interactive testing
- Use curl commands for automation
- Check database state directly with MySQL client

### Future: Automated Tests
Consider adding:
- **pytest** for unit tests
- **httpx** for API integration tests
- **pytest-asyncio** for async test support

Example test structure:
```python
def test_create_composer():
    response = client.post("/api/composers/", json={...})
    assert response.status_code == 201
```

## Integration with Frontend

The Next.js frontend (`/web`) can consume this API:

```typescript
// Example fetch in Next.js
const response = await fetch('http://localhost:8000/api/composers/');
const composers = await response.json();
```

For production, configure:
- Reverse proxy (nginx)
- Same domain for API and frontend
- Environment-based API URLs
