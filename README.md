# LinkTrack

A URL shortener with click analytics. Paste a long URL, get a short link, and see how many people used it and when.

**Live demo:** https://linktrack-ljbg.onrender.com

> The demo runs on a free hosting tier, which sleeps after about 15 minutes of inactivity. The first visit after a pause can take 30 to 60 seconds to wake up.

<!-- Add screenshots here, e.g. ![Create page](docs/create.png) -->

## Features

- Create short links from long URLs, with an optional expiry date
- Redirect visitors from the short code to the original URL
- Every visit is recorded (timestamp, referrer, user agent)
- Dashboard with a list of links, click counts, and Active/Expired status
- Per-link stats page with total clicks, last click time, and a clicks-per-day chart
- Delete links (their click history is deleted too)
- Rate limiting, input validation, and consistent error responses

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy, Alembic (migrations) |
| Validation | Pydantic |
| Frontend | HTML, CSS, vanilla JavaScript (Fetch API), Chart.js |
| Testing | pytest, FastAPI TestClient |
| Rate limiting | slowapi |
| Local database | Docker Compose |
| Hosting | Render (app), Neon (PostgreSQL) |

FastAPI serves the frontend as static files, so the whole app is a single deployable service and needs no CORS configuration.

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/links` | Create a short link (`201`; `422` on invalid input; `429` when rate limited) |
| `GET` | `/api/links` | List links with click counts |
| `GET` | `/api/links/{code}/stats` | Total clicks, last click, clicks per day |
| `DELETE` | `/api/links/{code}` | Delete a link and its clicks (`204`) |
| `GET` | `/{code}` | Redirect to the original URL (`302`; `404` unknown; `410` expired or deactivated) |
| `GET` | `/api/health` | Health check |

Interactive API docs are available at `/docs`.

## Data model

- **links**: `id`, `short_code` (unique, indexed), `original_url`, `created_at`, `expires_at` (nullable), `is_active`
- **clicks**: `id`, `link_id` (foreign key, `ON DELETE CASCADE`), `clicked_at`, `referrer`, `user_agent`, with a composite index on `(link_id, clicked_at)`

## Design decisions

- **302 instead of 301 redirects.** A 301 is cached by browsers, so repeat visits would skip the server and never be counted. A 302 makes every visit hit LinkTrack.
- **Collision handling in the database.** Codes are 7 random base62 characters from Python's `secrets` module. The `short_code` column has a unique constraint; the app inserts optimistically and retries on `IntegrityError` (up to 5 times). This is race-safe, unlike check-then-insert.
- **Non-blocking click recording.** Clicks are written in a FastAPI background task with its own database session, so the redirect is not slowed by the analytics write. A failed write never breaks a redirect.
- **404 vs 410.** `404` means the code never existed. `410 Gone` means it existed but has expired or been deactivated. Expired visits are not counted.
- **Aggregation in SQL.** The link list uses a single `LEFT JOIN ... GROUP BY` query (no N+1 queries), and stats use `COUNT` and `GROUP BY date`, backed by the composite index.
- **Input validation.** Only `http` and `https` URLs are accepted (blocking `javascript:` and similar), URLs are capped at 2048 characters, expiry must be in the future, and URLs pointing back at LinkTrack itself are rejected to prevent redirect loops.
- **Rate limiting.** Link creation is limited per IP (default `10/minute`, configurable).
- **Safe error handling.** A global handler returns a generic 500 and logs the details server-side. The frontend escapes all user-provided text before rendering to prevent XSS.
- **Timezone-aware timestamps.** All timestamps are stored in UTC. Clicks-per-day groups by UTC date.

## Project structure

```
linktrack/
├── backend/
│   ├── app/
│   │   ├── main.py          # app setup, static files, router order
│   │   ├── config.py        # environment-based settings
│   │   ├── database.py      # engine and session
│   │   ├── models.py        # Link and Click tables
│   │   ├── schemas.py       # Pydantic validation and responses
│   │   ├── limiter.py       # rate limiter
│   │   ├── routes/          # links API and redirect
│   │   └── services/        # short codes, link logic, click recording, stats
│   ├── alembic/             # database migrations
│   ├── tests/               # pytest suite
│   └── requirements.txt
├── frontend/
│   ├── index.html           # create a link
│   ├── links.html           # list and delete
│   ├── stats.html           # stats and chart
│   ├── css/style.css
│   └── js/                  # api.js, create.js, links.js, stats.js
├── docker-compose.yml       # local PostgreSQL
└── README.md
```

## Run locally

Requires Python 3.10+, Docker, and Git.

```bash
git clone https://github.com/AdithyaVVS/linktrack.git
cd linktrack

# 1. Start PostgreSQL
docker compose up -d

# 2. Set up Python environment
cd backend
python -m venv venv
venv\Scripts\activate          # Windows (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

# 3. Configure environment
# Create backend/.env containing:
# DATABASE_URL=postgresql+psycopg2://linktrack:linktrack@localhost:5432/linktrack

# 4. Create tables and start the server
alembic upgrade head
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 for the app or http://127.0.0.1:8000/docs for the API docs.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | required | PostgreSQL connection string (use the `postgresql+psycopg2://` prefix) |
| `BASE_URL` | `http://127.0.0.1:8000` | Public address, used to build short links (no trailing slash) |
| `CREATE_RATE_LIMIT` | `10/minute` | Rate limit for creating links |

## Tests

Tests run against a separate `linktrack_test` PostgreSQL database, so the real unique constraints, cascades, and queries are exercised.

```bash
docker exec -it linktrack_db psql -U linktrack -d linktrack -c "CREATE DATABASE linktrack_test;"
cd backend
pytest -v
```

The suite (19 tests) covers link creation and validation, collision retry and give-up, redirects (302, 404, 410), click recording, list and stats queries, cascade delete, URL hardening, and rate limiting.

## Deployment

- **App:** Render web service with root directory `backend`, build command `pip install -r requirements.txt`, and start command `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Database:** Neon managed PostgreSQL
- Set `DATABASE_URL` and `BASE_URL` as environment variables on the host

## Possible improvements

- Custom aliases (e.g. `/my-campaign`)
- User accounts so each person sees only their own links
- Redis caching for frequently visited links
- QR code generation
- Show clicks-per-day in the viewer's local timezone
