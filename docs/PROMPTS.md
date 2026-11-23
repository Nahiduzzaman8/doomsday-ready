# Doomsday Ready — Prompts for Claude Code (VS Code)

Copy-paste prompts, one per task in `docs/TASKS.md`.
The rules (style, no commits, tests, stop after each task) are already in `CLAUDE.md`, which
Claude Code reads by itself, so the prompts stay short.

---

## Before you start (once)

1. Unzip `doomsday-ready.zip` and open the `doomsday-ready` folder in VS Code.
2. Check you have: Python 3.12+, Node 20+, Docker with the compose plugin (running), Git.
   On Kali / Debian Linux also check:
   ```bash
   docker compose version                 # if "unknown command": sudo apt install docker-compose
   sudo systemctl enable --now docker     # start Docker now and on every boot
   sudo usermod -aG docker $USER          # use docker without sudo, then log out and back in
   docker run --rm hello-world            # must work without sudo
   sudo ss -ltnp | grep 5432              # if Kali's own PostgreSQL is listed:
   sudo systemctl disable --now postgresql   # free port 5432 for the Docker database
   python3 -m venv --help > /dev/null || sudo apt install python3-venv
   ```
3. In the VS Code terminal:
   ```bash
   git init
   git add .
   git commit -m "docs: add planning docs and core algorithms"
   ```
4. Create the Python virtual environment (used from Task 1 on):
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   cd ..
   ```
5. Open Claude Code in VS Code.

## The loop for every task

1. Open a **new** Claude Code chat (keeps it focused on one task).
2. Paste the task's prompt.
3. When it stops: read the changed files and run the tests yourself.
4. Do the **You check** items.
5. Paste the **Review prompt** (bottom of this file) in the same chat. Let it fix what it finds.
6. Commit with the suggested message:
   ```bash
   git add .
   git commit -m "<message>"
   ```
7. Go to the next task.

If something breaks, use the **Fix prompt** (bottom of this file).

---

## Prompt 0 — Read and check (once, before Task 1)
```
Read CLAUDE.md, docs/ARCHITECTURE.md, docs/TASKS.md and docs/DECISIONS.md fully. Also read
backend/movies/graph.py, backend/cinemas/bundles.py and their tests.
Do not write or change any files.
Reply in short:
1. Anything unclear, missing or contradicting itself across these files.
2. Anything you need from me before Task 1.
If there is nothing, reply "Ready for Task 1".
```
**You check:** if it lists problems, paste them to web Claude to fix the docs before going on.

---

## Prompt 1 — Backend skeleton + database
```
Do Task 1 from docs/TASKS.md, following CLAUDE.md and the spec sections it names.
The movies/ and cinemas/ folders already exist: add the app files by hand, do not run startapp,
do not create tests.py. Do not change graph.py, bundles.py or their tests.
I have already created and activated backend/.venv; install requirements into it.
Start the database with docker compose before running the tests.
```
**You check:** `python manage.py test` shows 15 tests OK.

## Prompt 2 — Error handling
```
Do Task 2 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §7 exactly.
Every error must have the shape {"error": {"code", "message", "details"}}.
Write a test for every item in the task's "Done when" list.
```
**You check:** tests OK.

## Prompt 3 — Movie model
```
Do Task 3 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §3 exactly
(field names, symmetrical=False, related_name, the 3 constraints, ordering).
Write a test for every item in the task's "Done when" list.
```
**You check:** a new file in `movies/migrations/`; tests OK.

## Prompt 4 — Movie endpoints + cycle check
```
Do Task 4 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §4, §5 and §6 exactly.
The cycle check must call movies.graph.creates_cycle; do not write your own.
Follow the transaction and lock steps in §5 exactly, and do not lock on a watched-only PATCH.
Write a test for every item in the task's "Done when" list.
```
**You check:** run `python manage.py runserver`, open http://localhost:8000/api/movies → `[]`.

## Prompt 5 — Rewatch order endpoint
```
Do Task 5 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §5 (get_rewatch_plan)
and §6 exactly. It must call movies.graph.rewatch_order and keep its order.
In the tests, create the brief's 8 movies in setUp.
Write a test for every item in the task's "Done when" list.
```
**You check:** the 3 brief rewatch tests and the 460-minute test pass.

## Prompt 6 — Cinema model + endpoints
```
Do Task 6 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §3, §4, §5 (create_cinema)
and §6 exactly. Save bundle_sizes sorted ascending.
Write a test for every item in the task's "Done when" list.
```
**You check:** tests OK.

## Prompt 7 — Booking quote endpoint
```
Do Task 7 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §4 (groupSize),
§5 (get_booking_quote) and §6 exactly. It must call cinemas.bundles.fewest_bundles; do not write
your own. "Not possible" is a 200 response with possible: false.
Write a test for every item in the task's "Done when" list, checking the full JSON body.
```
**You check:** the 4 brief booking tests pass.

## Prompt 8 — Seed command
```
Do Task 8 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §11 exactly
(the exact titles, years, runtimes, prerequisites and cinemas).
Seed only into empty tables, so it never overwrites user data.
Write a test for every item in the task's "Done when" list.
```
**You check:** run `python manage.py seed` twice; http://localhost:8000/api/movies shows 8 movies,
http://localhost:8000/api/cinemas shows 4 cinemas.

## Prompt 9 — Frontend skeleton
```
Do Task 9 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §8 exactly
(Rules, api.js, format.js, Dev proxy). Plain JavaScript, no UI library, no router.
Remove all Vite demo content. Prove formatMinutes and formatBundles return the exact values
in the §8 table with a quick node command, and run npm run build.
```
**You check:** `npm run dev` → open http://localhost:5173 → header + 3 tabs switch.

## Prompt 10 — Movies view
```
Do Task 10 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §8 View 1 exactly,
including loading, error and empty states. Use only functions from src/api.js.
Run npm run build. Then tell me exactly what to click to check every "Done when" item.
```
**You check (backend running + seeded):** every "Done when" item of Task 10, especially
Endgame → Iron Man shows the circular-dependency message.

## Prompt 11 — Rewatch Plan view
```
Do Task 11 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §8 View 2 exactly,
including the exact texts for the empty states. Use a native <progress> element.
Run npm run build. Then tell me exactly what to click to check every "Done when" item.
```
**You check:** Doomsday, tick 4 → "4 of 7 watched", "Remaining: 7 h 40 min"; Ragnarok → "Nothing to watch first — you're ready!"

## Prompt 12 — Booking view
```
Do Task 12 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §8 View 3 exactly.
Run npm run build. Then tell me exactly what to click to check every "Done when" item.
```
**You check:** Alpha 6 → 2 bundles: 3 × 2 · Bravo 11 → 4 bundles: 5 × 1, 2 × 3 ·
Charlie 44 → 4 bundles: 20 × 1, 9 × 2, 6 × 1 · Delta 7 → Not possible.

## Prompt 13 — Full Docker setup
```
Do Task 13 from docs/TASKS.md, following CLAUDE.md and ARCHITECTURE.md §10 exactly.
Extend the existing docker-compose.yml. Every environment value must have a default so it runs
with no .env file. Make entrypoint.sh executable.
Run docker compose down -v, then docker compose up --build, and check http://localhost:3000 and
http://localhost:3000/api/movies. Show me the result.
```
**You check:** stop everything, then run `docker compose down -v` and `docker compose up --build`
yourself → the app works on http://localhost:3000.

## Prompt 14 — README
```
Do Task 14 from docs/TASKS.md. Write README.md in simple, clear English with exactly the
9 sections listed in the task. Copy the mermaid diagram from ARCHITECTURE.md §3 and the
assumptions from §13. Explain the three algorithms in plain words with their complexity.

For "How AI was used", write this honestly:
- The design (requirements, data model, API, algorithms, frontend, Docker) was planned step by step
  with Claude in a web chat and written into docs/DECISIONS.md, ARCHITECTURE.md, TASKS.md and
  PROMPTS.md, which I reviewed and approved.
- The algorithm files backend/movies/graph.py and backend/cinemas/bundles.py, with their tests,
  were written by Claude in that chat; I studied and verified them against the brief's examples.
- The Django, React and Docker code was written with Claude Code in VS Code, one task at a time,
  using the prompts in docs/PROMPTS.md. I ran, tested and reviewed every task before committing.
Then add a clearly marked placeholder "<!-- In my own words: -->" for me to fill in.

Only include commands you have actually run and that work.
```
**You check:** fill the placeholder in your own words. Open the README preview in VS Code.

## Prompt 15 — Final check
```
Do Task 15 from docs/TASKS.md.
1. Go through every endpoint, JSON field, status code and error code in ARCHITECTURE.md and
   compare with the real code. Show me a table: item | spec | code | OK/mismatch. Fix every mismatch.
2. Remove dead code, debug prints, console.log, unused imports, files and dependencies.
3. Run python manage.py test and npm run build, and show the output.
```
**You check:** clone the repo into a new folder, run `docker compose up --build`, and test all
8 brief examples by hand in the browser.

## Task 16 — Submission (you, not Claude Code)
1. Create a GitHub repository (e.g. `doomsday-ready`), then:
   ```bash
   git remote add origin https://github.com/<your-username>/doomsday-ready.git
   git branch -M main
   git push -u origin main
   ```
2. Make it public. Open the link in a private browser window to check it is visible and the README renders.
3. Submit the link through the Google Form that came with the challenge.

---

## Review prompt (after every task, same chat)
```
Review only the files you changed in this task against CLAUDE.md and docs/ARCHITECTURE.md.
List every mismatch or problem: URL, JSON field name, status code, error code, a missing test from
the task's "Done when" list, a broken rule, debug print, unused code, or code that looks
over-complicated. Fix them, run the tests again and show the output.
```

## Fix prompt (when something breaks)
```
This fails:
<paste the full error or describe what you see>
Find the root cause and fix it. Do not change or delete a test unless the test itself is wrong;
if you think it is, explain why first and wait for me.
```

## Understand the algorithms (do this before any interview)
```
Explain backend/movies/graph.py and backend/cinemas/bundles.py to me line by line in very simple
words, using the brief's examples: the Doomsday rewatch order, Endgame → Iron Man (cycle), and
bundles 2 and 5 for 11 people. Then ask me 5 interview-style questions about them, one at a time,
and check each answer before asking the next.
```
