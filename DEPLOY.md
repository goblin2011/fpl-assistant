# Deploying FPL Assistant so friends can use it

Everything below can be done on free tiers. Total cost: $0/month for a
friend-group's worth of traffic.

## 1. Push the code to GitHub

```bash
cd ~/code/fpl-assistant
git remote add origin https://github.com/<your-username>/fpl-assistant.git
git branch -M main
git push -u origin main
```

(If you've already created the repo and added the remote, just run
`git push -u origin main`.)

## 2. Deploy the backend on Render (free)

1. Sign up at https://render.com (free, can use your GitHub login).
2. Click **New +** → **Blueprint**, connect your GitHub account, and select
   the `fpl-assistant` repo. Render will read `render.yaml` automatically and
   set everything up (build command, start command, free plan).
3. Click **Apply** / **Create**. First deploy takes a few minutes.
4. Once live, copy the URL Render gives you, e.g.
   `https://fpl-assistant-backend.onrender.com`.

Free-tier note: Render's free web services sleep after ~15 min of no
traffic, so the first request after idling takes ~30-50s to wake up. Fine
for a friend group checking in a few times a week.

## 3. Point the frontend at your live backend

Open `index.html`, find this line near the top of the `<script>`:

```js
: "REPLACE_WITH_YOUR_DEPLOYED_BACKEND_URL";
```

Replace it with your actual Render URL from step 2, e.g.:

```js
: "https://fpl-assistant-backend.onrender.com";
```

Commit and push that change:

```bash
git add index.html
git commit -m "Point frontend at deployed backend"
git push
```

## 4. Turn on GitHub Pages for the frontend (free)

Everything lives in one flat folder, including `index.html` at the repo
root, so Pages can serve straight from the root — no `/docs` subfolder
needed.

1. On GitHub, go to your repo → **Settings** → **Pages** (left sidebar).
2. Under **Build and deployment** → **Source**, choose **Deploy from a
   branch**.
3. Under **Branch**, choose `main` and folder **`/ (root)`**, then **Save**.
4. GitHub builds the page (takes a minute or two). Refresh the Pages
   settings screen and it'll show your live URL, something like
   `https://<your-username>.github.io/fpl-assistant/`.

That URL is what you share with friends. (The Python files sitting
alongside `index.html` in the repo just get served as inert static text if
anyone requests them directly — there's nothing sensitive in them, no API
keys, since the FPL API needs none.)

## 5. Lock down CORS (optional but recommended)

Right now the backend allows requests from any origin (`allow_origins=["*"]`
in `main.py`) so local testing was easy. Once you have your real
GitHub Pages URL, tighten it:

```python
allow_origins=["https://<your-username>.github.io"],
```

Commit, push — Render will auto-redeploy.

## Updating later

Any `git push` to `main` auto-redeploys Render, and GitHub Pages
auto-rebuilds from the repo root — no manual redeploy steps needed after the
initial setup.
