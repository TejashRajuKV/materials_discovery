# System architecture

```
React (Vite, :5173) ──/api──▶ Express (:3000) ──┬─▶ SQLite (database/materials.db)
                                                └─▶ Python ML engine (subprocess: python ml/main.py <cmd>)
```

- **ML code never lives in Express.** Node talks to Python through `backend/services/pythonService.js`,
  which spawns `ml/main.py`, sends JSON on stdin, and parses the one JSON document on stdout
  (errors are `{error, message}`; 400/503/504 mapping happens in the bridge). A timeout kills runaways.
- Discovery is **asynchronous**: `POST /api/discovery` stores a `running` job and returns `202`; the
  UI polls `GET /api/discovery/:id` until `completed`/`failed`.
- Each ML call pays Python start-up + model load (~2–5 s). Fine for the MVP; when it hurts, turn
  `ml/main.py` into a long-lived service behind the same `pythonService.js` interface.
- Vite proxies `/api` to the backend in development; `npm run build` emits `dist/`.
