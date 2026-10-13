# Running and operating the engine

## Two ways to run the ML engine

- **Per-call (default).** The backend starts `python ml/main.py <command>` for each request. Simple, but
  every predict call loads the band-gap model (over 1 GB), about 6–7 s each time.
- **Resident service.** `python ml/service.py` loads each model once and serves the same commands over
  HTTP on 127.0.0.1:8001. Start it, then point the backend at it:

  ```bash
  python ml/service.py
  ML_SERVICE_URL=http://127.0.0.1:8001 npm run dev:backend
  ```

  Predict calls then take about 0.5 s after the first load. Discovery runs in about 30 s on the warm service.
  Both modes give the same results and error codes.

The interpreter is chosen in `scripts/python-bin.js`: `PYTHON_BIN` if set, then the project `.venv`.

## Memory

The band-gap model is 0.75 GB on disk, since its forests have minimum leaf 5. Loading can still fail with a
`MemoryError` when other applications use most of the machine's commit limit. In that case, close other
applications, or run the resident service so the model is loaded only once.

## Backups

```bash
node scripts/backup-db.js            # writes database/backups/materials-<time>.db, keeps the newest 14
node scripts/backup-db.js --keep 30
```

Backups use `VACUUM INTO`, which copies a consistent snapshot even while the server is running.
`database/backups/` is git-ignored.

## Discovery results

`GET /api/discovery/:id/export.csv` downloads a job's candidates as CSV. The candidates page has a link.
