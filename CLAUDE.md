# Doomsday Ready

Small full-stack app for MCU fans:
1. **Movies + rewatch order:** track movies and their prerequisites; given a target movie, list everything
   to watch first in a valid order; block circular dependencies.
2. **Cinemas + booking:** find the fewest seat bundles that add up to exactly a group size.
3. **React UI** with three views: Movies, Rewatch Plan, Booking.

This is an internship assessment. The code will be read by reviewers, so it must be simple,
clean, correct and easy to follow.

## Read first
- `docs/ARCHITECTURE.md`: the build spec. Follow it exactly: names, URLs, JSON fields, status codes, error codes.
- `docs/TASKS.md`: the task list. Work on one task at a time.
- `docs/DECISIONS.md`: why things are designed this way. Read it only if you need the reason.

If ARCHITECTURE.md and DECISIONS.md disagree, ARCHITECTURE.md wins.

## Stack
- Backend: Python 3.12+ (my machine has 3.14), Django 5.2 LTS (≥ 5.2.8), Django REST Framework 3, PostgreSQL 16 (`psycopg` 3)
- Frontend: React 18 + Vite, plain JavaScript
- Infra: Docker Compose (`db`, `backend`, `frontend`)

## Hard rules
1. **Do not change** `backend/movies/graph.py`, `backend/cinemas/bundles.py`, `test_graph.py` or `test_bundles.py`.
   They hold the core algorithms and are already tested. Call them from `services.py`.
   If you think one of them is wrong, stop and tell me.
2. **Never add a library that solves Feature 1 or 2** (networkx, graphlib, toposort, any DP/solver package).
3. **Do not add** packages, endpoints, fields or features that are not in ARCHITECTURE.md without asking me first.
4. **Every error** uses the shape `{"error": {"code", "message", "details"}}` from ARCHITECTURE.md §7.
5. **Tests must pass** at the end of every task. Never delete, skip or weaken a test to make it pass.
6. **One task per session.** Finish it, run the tests, show me the output, suggest a commit message, then stop.
   Do not start the next task by yourself.
7. **Never run `git commit` or `git push`.** I review and commit myself.
8. **If something is unclear,** choose the simplest option that fits ARCHITECTURE.md, tell me what you chose,
   and add it to the Assumptions list (ARCHITECTURE.md §13).
9. **Do not ask me** for things you can find in the repo. Read the files first.

## Code style
- Code should look human-written: short functions, clear names, no clever tricks.
- Comments only where the *why* is not obvious. No comments that just repeat the code.
- No debug prints, no `console.log`, no commented-out code, no TODOs left behind.
- Python: PEP 8, type hints on service functions, f-strings.
- Business logic lives in `services.py`. Views stay thin. Serializers only validate and shape data.
- React: function components and hooks. API calls only in `src/api.js`. One view per file in `src/views/`.
- Keep the CSS small. Use one file: `src/styles.css`.

## Commands
```bash
# Database only (needed for local backend and tests)
docker compose up -d db

# Backend (from backend/)
python manage.py migrate
python manage.py seed
python manage.py runserver          # http://localhost:8000
python manage.py test               # all backend tests

# Frontend (from frontend/)
npm install
npm run dev                         # http://localhost:5173 (proxies /api to :8000)
npm run build                       # must succeed before a frontend task is done

# Everything
docker compose up --build           # http://localhost:3000
docker compose down -v              # stop and delete all data
```

## End of every task
1. Run `python manage.py test` (and `npm run build` if frontend files changed).
2. Show me the test output.
3. List the files you created or changed, one line each.
4. Suggest a commit message in this form: `feat: add movie CRUD endpoints` (or `fix:`, `test:`, `docs:`, `chore:`).
5. Stop and wait.
