# Setup

Requirements: Node ≥ 18 (developed on 22), Python ≥ 3.10.

```bash
npm install
pip install -r requirements.txt
npm run setup          # synthetic data → preprocess → train → export → seed SQLite
# with your own dataset instead: python3 ml/main.py bootstrap --file path/to/data.csv && npm run db:seed
npm run dev:backend    # :3000
npm run dev:frontend   # :5173 (proxies /api)
npm test               # backend (node:test) + frontend (vitest) + ML (pytest)
```

Environment: `PORT`, `DB_PATH`, `PYTHON_BIN` (default `python3`), `ML_TIMEOUT_MS`, `CORS_ORIGIN`.

Troubleshooting: if `pip install pymatgen` fails while building `bibtexparser`, install
`pip install pymatgen-core --no-deps` plus its runtime deps (`monty ruamel.yaml spglib orjson lxml
tabulate requests tqdm networkx sympy plotly uncertainties pybtex`) — this is what the build
sandbox needed.
