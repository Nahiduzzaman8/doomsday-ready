# Doomsday Ready — Tasks

How this file works:
- Do **one task per session**, in order. Each task builds on the one before it.
- A task is finished only when **every** "Done when" item is true.
- "Spec" points to the section of `docs/ARCHITECTURE.md` to follow.
- At the end of each task, follow "End of every task" in `CLAUDE.md`, then stop.

Overview:
| # | Task | Part |
|---|---|---|
| 1 | Backend skeleton + database | Backend |
| 2 | Error handling | Backend |
| 3 | Movie model | Backend |
| 4 | Movie endpoints + cycle check | Backend · Feature 1 |
| 5 | Rewatch order endpoint | Backend · Feature 1 |
| 6 | Cinema model + endpoints | Backend · Feature 2 |
| 7 | Booking quote endpoint | Backend · Feature 2 |
| 8 | Seed command | Backend |
| 9 | Frontend skeleton | Frontend |
| 10 | Movies view | Frontend · Feature 3 |
| 11 | Rewatch Plan view | Frontend · Feature 3 |
| 12 | Booking view | Frontend · Feature 3 |
| 13 | Full Docker setup | Infra · Bonus |
| 14 | README | Docs · Bonus |
| 15 | Final check | All |
| 16 | Submission (done by me, not Claude Code) | — |

---

## Task 1 — Backend skeleton + database
**Spec:** §1 Folder structure, §9 Configuration, §10 (db service only)

**Do**
- From `backend/`: `django-admin startproject config .`
- `movies/` and `cinemas/` folders already exist (they contain the algorithms and their tests),
  so **do not run `startapp`**. Add these files by hand to each app:
  `apps.py`, `models.py` (empty for now), `admin.py`, `migrations/__init__.py`.
- **Do not create `tests.py`**. It would clash with the existing `tests/` package.
- `requirements.txt` with pinned versions: Django 5.2.x (≥ 5.2.8, for Python 3.14), djangorestframework 3.x, psycopg[binary] 3.x, gunicorn (latest of each).
- `config/settings.py`: read everything from environment variables (§9). Use PostgreSQL.
  Set `APPEND_SLASH = False`, `TIME_ZONE = "UTC"`, `USE_TZ = True`. Add `django.contrib.postgres`,
  `rest_framework`, `movies`, `cinemas` to `INSTALLED_APPS`. JSON renderer only, plus the browsable
  renderer when `DEBUG` is on.
- Root `docker-compose.yml` with **only the `db` service** (§10). Task 13 adds the rest.
- Root `.env.example` (§9) and `.gitignore` (Python, Node, `.env`, `__pycache__`, `.venv`, `node_modules`, `dist`).

**Done when**
- [ ] `docker compose up -d db` starts Postgres, and the healthcheck shows healthy.
- [ ] `python manage.py check` shows no issues.
- [ ] `python manage.py test` finds and passes the **15** existing algorithm tests (9 graph + 6 bundles).
- [ ] `graph.py`, `bundles.py` and their tests are unchanged.

---

## Task 2 — Error handling
**Spec:** §7 Errors

**Do**
- `config/exceptions.py`: `CircularDependency` (409), `AlreadyExists` (409), and `api_exception_handler`.
- Register it in `REST_FRAMEWORK["EXCEPTION_HANDLER"]`.
- `config/views.py`: JSON `handler404` and `handler500`; register both in `config/urls.py`.
- `config/urls.py`: mount `/api/` routes. The apps have no routes yet, so add a tiny test-only view if
  you need something to hit in tests (inside the test module, not in production URLs).

**Done when** tests prove each case returns the exact error shape:
- [ ] `ValidationError` → 400 `VALIDATION_ERROR` with field errors in `details`
- [ ] broken JSON body → 400 `VALIDATION_ERROR`
- [ ] `NotFound` / `Http404` → 404 `NOT_FOUND`
- [ ] unknown URL such as `/api/nope` → 404 `NOT_FOUND` (JSON, not HTML)
- [ ] wrong method → 405 `METHOD_NOT_ALLOWED`
- [ ] `CircularDependency` → 409 `CIRCULAR_DEPENDENCY`
- [ ] `AlreadyExists` → 409 `ALREADY_EXISTS`
- [ ] unexpected exception → 500 `INTERNAL_ERROR`, no stack trace in the body
- [ ] all earlier tests still pass

---

## Task 3 — Movie model
**Spec:** §3 Data model (Movie)

**Do**
- `movies/models.py`: `Movie` exactly as in §3, with all 3 constraints and `ordering`.
- `python manage.py makemigrations movies`
- Register `Movie` in `admin.py` (simple list display).

**Done when**
- [ ] migration created and `python manage.py migrate` works
- [ ] model tests: two titles that differ only in letter case → `IntegrityError`
- [ ] model tests: runtime 0 or 301 → `IntegrityError`; release year 1899 or 2101 → `IntegrityError`
- [ ] model tests: adding Iron Man as a prerequisite of The Avengers does **not** make The Avengers a prerequisite of Iron Man (one-way link)
- [ ] all earlier tests still pass

---

## Task 4 — Movie endpoints + cycle check
**Spec:** §4 Movie input, §5 `load_graph` / `create_movie` / `update_movie` / `_apply_prerequisites`, §6 Movie endpoints

**Do**
- `movies/serializers.py`: input validation (§4) and the movie object output (§6).
- `movies/services.py`: `load_graph`, `create_movie`, `update_movie`, `_apply_prerequisites`.
  The cycle check **must** call `graph.creates_cycle`.
- `movies/views.py` + `movies/urls.py`: `POST`/`GET /api/movies`, `GET`/`PATCH /api/movies/<id>`.

**Done when** API tests in `movies/tests/test_api.py` cover:
- [ ] create without prerequisites → 201 and the exact movie object
- [ ] create with prerequisites → 201, prerequisites saved
- [ ] list → 200, ordered by `(release_year, title)`
- [ ] get one → 200; unknown id → 404 `NOT_FOUND`
- [ ] PATCH `{"watched": true}` only → 200, other fields unchanged
- [ ] PATCH `prerequisites` → replaced; PATCH `[]` → cleared; PATCH without the field → unchanged
- [ ] duplicate title, also with different letter case → 409 `ALREADY_EXISTS` (on create and on PATCH)
- [ ] PATCH a movie with its own unchanged title → 200 (not a duplicate)
- [ ] runtime 0 / 301, year 1899 / 2101, empty title, `"126"` as a string, `2.5` → 400 `VALIDATION_ERROR`
- [ ] unknown prerequisite id → 400, the missing id appears in `details`
- [ ] duplicate ids `[1, 1]` → saved once
- [ ] a movie as its own prerequisite → 409 `CIRCULAR_DEPENDENCY`
- [ ] **brief example:** Endgame as a prerequisite of Iron Man → 409 `CIRCULAR_DEPENDENCY`
- [ ] after any 409, the movie's old prerequisites are still exactly the same
- [ ] `load_graph` returns every movie id, with prerequisite lists sorted by `(release_year, title)`
- [ ] all earlier tests still pass

---

## Task 5 — Rewatch order endpoint
**Spec:** §5 `get_rewatch_plan`, §6 rewatch plan example

**Do**
- `services.get_rewatch_plan`: must call `graph.rewatch_order` and keep its order.
- View + URL: `GET /api/movies/<id>/rewatch-order`.

**Done when** tests (using the brief's 8 movies, created in the test setup) cover:
- [ ] **brief example:** Doomsday → 7 movies, each exactly once, each after all its prerequisites;
      exact order: Iron Man, The First Avenger, The Avengers, Civil War, Ragnarok, Infinity War, Endgame
- [ ] **brief example:** Civil War → Iron Man and The First Avenger first (any order), then The Avengers
- [ ] **brief example:** Ragnarok → `movies: []`, `total_count: 0`, `watched_count: 0`, `unwatched_runtime_minutes: 0`
- [ ] the target is never in its own list
- [ ] mark Iron Man, The First Avenger, The Avengers, Civil War as watched → Doomsday gives
      `total_count` 7, `watched_count` 4, `unwatched_runtime_minutes` **460**
- [ ] unknown id → 404 `NOT_FOUND`
- [ ] all earlier tests still pass

---

## Task 6 — Cinema model + endpoints
**Spec:** §3 Cinema, §4 Cinema input, §5 `create_cinema`, §6 Cinema endpoints

**Do**
- `cinemas/models.py` + migration, `admin.py`.
- `cinemas/serializers.py`, `cinemas/services.py` (`create_cinema`), views, urls.
- `POST /api/cinemas`, `GET /api/cinemas`.

**Done when** tests cover:
- [ ] create → 201, and `bundle_sizes` comes back sorted (`[5, 2]` is saved as `[2, 5]`)
- [ ] list → 200, ordered by name
- [ ] duplicate name, also with different letter case → 409 `ALREADY_EXISTS`
- [ ] `bundle_sizes` errors → 400 `VALIDATION_ERROR`: `[]`, 11 sizes, `[0]`, `[501]`, `[2, 2]`, `["2"]`, missing field
- [ ] empty name → 400
- [ ] all earlier tests still pass

---

## Task 7 — Booking quote endpoint
**Spec:** §4 `groupSize`, §5 `get_booking_quote`, §6 booking examples

**Do**
- `services.get_booking_quote`: must call `bundles.fewest_bundles`.
- View + URL: `GET /api/cinemas/<id>/booking?groupSize=N`.

**Done when** tests cover (exact JSON bodies):
- [ ] **brief example:** `[1, 3, 4]`, 6 → `total_bundles` 2, bundles `[{size: 3, count: 2}]`
- [ ] **brief example:** `[2, 5]`, 11 → 4, `[{5, 1}, {2, 3}]`
- [ ] **brief example:** `[6, 9, 20]`, 44 → 4, `[{20, 1}, {9, 2}, {6, 1}]`
- [ ] **brief example:** `[4, 6]`, 7 → 200, `possible: false`, `total_bundles: null`, `bundles: []`, message present
- [ ] `groupSize` 1 and 10000 accepted
- [ ] `groupSize` missing, empty, `abc`, `2.5`, `0`, `10001` → 400 `VALIDATION_ERROR`
- [ ] unknown cinema → 404 `NOT_FOUND`
- [ ] all earlier tests still pass

---

## Task 8 — Seed command
**Spec:** §11 Seed data

**Do**
- `movies/management/commands/seed.py` (with the `management/` and `commands/` `__init__.py` files).
- Movies only if the movie table is empty; cinemas only if the cinema table is empty. Use one transaction.

**Done when** `movies/tests/test_seed.py` covers:
- [ ] on an empty database → 8 movies, 4 cinemas, prerequisites exactly as in §11
- [ ] run twice → still 8 movies and 4 cinemas
- [ ] mark a movie watched, run seed again → it is still watched (user data never overwritten)
- [ ] after seeding, the Doomsday rewatch order returns 7 movies
- [ ] all earlier tests still pass
- [ ] manual: `python manage.py seed`, then http://localhost:8000/api/movies shows 8 movies

---

## Task 9 — Frontend skeleton
**Spec:** §8 Rules, `api.js`, `format.js`, Dev proxy

**Do**
- From the repo root: `npm create vite@latest frontend -- --template react` (JavaScript).
- Remove the Vite demo content (logos, counter, demo CSS).
- `vite.config.js` with the `/api` proxy.
- `src/api.js` (all 7 functions + `request()` helper), `src/format.js`, `src/components/ErrorMessage.jsx`.
- `src/App.jsx`: header "Doomsday Ready" + 3 tabs. Each tab shows a placeholder line for now.
- `src/styles.css`: base layout, tabs, buttons, tables, forms, error box.

**Done when**
- [ ] `npm run build` succeeds
- [ ] `npm run dev` shows the header and 3 working tabs
- [ ] `formatMinutes` and `formatBundles` return exactly the values in the §8 table
      (check with a quick `node` one-liner; no test framework needed)
- [ ] no Vite demo files or text left

---

## Task 10 — Movies view
**Spec:** §8 View 1

**Done when** (check by hand in the browser, with the backend running and seeded):
- [ ] the table shows all 8 movies with year, runtime (`2 h 6 min`), watched tick and prerequisite titles
- [ ] adding a new movie with prerequisites works, and it appears in the table
- [ ] ticking watched in the table saves (still ticked after a page reload)
- [ ] Edit → change prerequisites → Save works; Cancel discards
- [ ] setting Endgame as a prerequisite of Iron Man shows the circular-dependency message under the row, and nothing changes
- [ ] duplicate title shows the "already exists" message
- [ ] loading and empty states appear (stop the backend to see the "Cannot reach the server." error)
- [ ] `npm run build` succeeds; no `console.log`

---

## Task 11 — Rewatch Plan view
**Spec:** §8 View 2

**Done when** (browser):
- [ ] before picking a movie: "Pick a movie to see what to watch first."
- [ ] Doomsday → 7 movies, numbered, in the API order
- [ ] tick the first 4 → "4 of 7 watched", progress bar at 4/7, "Remaining: 7 h 40 min"
- [ ] watched items look faded or struck through
- [ ] Thor: Ragnarok → "Nothing to watch first — you're ready!"
- [ ] all ticked → "All caught up — you're ready!"
- [ ] `npm run build` succeeds

---

## Task 12 — Booking view
**Spec:** §8 View 3

**Done when** (browser):
- [ ] Cinema Alpha, 6 → "✅ 2 bundles: 3 × 2"
- [ ] Cinema Bravo, 11 → "✅ 4 bundles: 5 × 1, 2 × 3"
- [ ] Cinema Charlie, 44 → "✅ 4 bundles: 20 × 1, 9 × 2, 6 × 1"
- [ ] Cinema Delta, 7 → "❌ Not possible — …"
- [ ] group size 0 or 10001 is stopped by the input check; and if the API is called anyway, its error message is shown
- [ ] changing the cinema or group size clears the old result
- [ ] add cinema "Test Hall" with "5, 2" → appears in the dropdown, selected, with sizes 2, 5
- [ ] `npm run build` succeeds

---

## Task 13 — Full Docker setup
**Spec:** §10 Docker

**Do**
- `backend/Dockerfile`, `backend/entrypoint.sh` (executable), `backend/.dockerignore`.
- `frontend/Dockerfile` (multi-stage), `frontend/nginx.conf`, `frontend/.dockerignore`.
- Extend `docker-compose.yml` with `backend` and `frontend`. Every env value has a default.

**Done when**
- [ ] `docker compose down -v && docker compose up --build` works with **no** `.env` file
- [ ] http://localhost:3000 opens the app with the seeded data
- [ ] http://localhost:3000/api/movies returns JSON through nginx
- [ ] restarting (`docker compose restart backend`) keeps watched ticks
- [ ] `docker compose down -v` then `up` restores the original sample data

---

## Task 14 — README
**Do** — write `README.md` in simple, clear English with these sections:
1. What it is (2–3 lines) + screenshot placeholders for the 3 views
2. Quick start with Docker (one command) and local development
3. API summary (endpoint table + one example each)
4. Data model (copy the mermaid diagram from ARCHITECTURE.md §3)
5. How the algorithms work, in plain words, with complexity:
   - cycle check: walk from the new prerequisites; reaching the movie means a cycle. O(V + E)
   - rewatch order: iterative post-order DFS. O(V + E)
   - booking: unbounded coin-change DP. O(group size × number of sizes)
6. Assumptions (copy ARCHITECTURE.md §13)
7. How AI was used: honest and specific (see PROMPTS.md for the wording), with a marked placeholder for my own words
8. Testing: how to run, what is covered
9. What I would improve with more time (3–5 bullets)

**Done when**
- [ ] someone who has never seen the project can run it using only the README
- [ ] the mermaid diagram renders on GitHub
- [ ] every command in the README was actually run and works

---

## Task 15 — Final check
**Do**
- Compare every endpoint, JSON field, status code and error code in ARCHITECTURE.md with the real
  code. List any mismatch, then fix it.
- Remove dead code, debug prints, `console.log`, unused imports, files and dependencies.

**Done when**
- [ ] `python manage.py test`: all tests pass
- [ ] `npm run build` succeeds
- [ ] fresh clone into a new folder → `docker compose up --build` → every brief example works by hand:
      3 rewatch examples, the Endgame → Iron Man 409, and the 4 booking examples

---

## Task 16 — Submission (me, not Claude Code)
- [ ] push to GitHub; make the repo public (or share access, if the form asks for that)
- [ ] open the repo link in a private browser window to make sure it is visible
- [ ] check the README renders, including the diagram
- [ ] submit the link through the Google Form that came with the challenge
