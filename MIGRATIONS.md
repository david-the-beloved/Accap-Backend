Baseline table added: `UserBookBaseline`

What changed

- Added `UserBookBaseline` table to store per-user, per-book baseline info
  (book_version, baseline_page, baseline_chapter).
- Server now stores baselines via `create_baseline(...)` instead of creating
  synthetic "yesterday" DailyLog rows.
- Weekly goal logic removed; goals are daily-only.

Applying changes

- If you run the backend normally, `SQLModel.metadata.create_all(engine)` will
  create the new table automatically on startup. Restart the backend to apply.

Commands (from repository root):

PowerShell

```powershell
# activate venv if needed
& ".\.venv\Scripts\Activate.ps1"
cd backend
# ensure environment variables are set in backend/.env
uvicorn app.main:app --reload --port 8000
```

Notes

- If you use Alembic or a migration system, create an explicit migration to add
  the `user_book_baseline` table instead of relying on `create_all`.
- The scheduler and accountability logic now consult stored baselines when no
  prior DailyLog exists for a user.
