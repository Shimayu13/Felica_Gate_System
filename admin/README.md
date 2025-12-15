Admin UI (static prototype)

This is a minimal admin panel using plain HTML + JS that talks to the FastAPI server.

To run locally, open `index.html` in a browser or serve via a simple static server:

```bash
python3 -m http.server 3000 --directory admin
```

Then open `http://localhost:3000`.

The prototype expects the API to be at `http://127.0.0.1:8000`.
