# Duc Nguyen Tien: portfolio site

A one-page static site: Vite + Three.js, no backend. All text, numbers and links live in **`content/site.json`**.

## 1. Run it on your computer

You need Node.js (already installed: v22).

```bash
cd C:\Users\ZinCruise\Documents\portfolio
npm install
npm run dev
```

Open http://localhost:5173. The page reloads by itself when you save `content/site.json`.

Useful extras:
- `http://localhost:5173/?no3d` shows the 2D fallback (what phones without WebGL see).
- `npm test` checks the maths behind the portfolio demo.
- `npm run build` creates the final site in `dist/`; `npm run preview` serves that build.

## 2. Edit the content (no code needed)

Open `content/site.json` in any editor (VS Code or Notepad) and change the text between the quotes.

| What you want to change | Where in `site.json` |
|---|---|
| Name, positioning line, email, LinkedIn, GitHub | `person` |
| Page title and LinkedIn preview text | `meta` |
| About text (3 sentences) | `about` |
| Jobs | `experience` |
| Featured case studies | `featured` (each has `problem`, `data`, `method`, `result`, `tools`, `links`) |
| Other projects | `more` |
| Demo assets and assumptions | `demo` (returns and volatilities as decimals: 0.08 = 8%) |
| Skills, certificates, languages | `skills`, `certificates`, `languages` |
| Education, awards | `education`, `beyond` |

Rules of thumb:
- Keep the quotes and commas. If the page goes blank after an edit, a comma or quote is missing; paste the file into https://jsonlint.com to find it.
- Anything written as `[TODO: ...]` shows up highlighted in yellow on the page. Replace every one before you share the link.
- To hide GitHub, leave `"github": ""`.
- A project that is not finished can keep `"status": "In progress"`. Set it to `""` when it is done.

### Files
- **CV:** the Download CV buttons serve `public/Tien_Duc_Nguyen_CV.pdf`. To update the CV, replace that file but keep the same name (or change `person.cv` to match).
- **Images** (for example dashboard screenshots): put them in `public/`.
- **LinkedIn preview image:** `public/og-image.png` (1200×630). It is a screenshot of the hero. Replace it with any 1200×630 image if you like.

## 3. Put it online (free, about 10 minutes)

### Option A: Vercel (recommended)
1. Create a free account at https://github.com and a new **public** repository called `portfolio`.
2. On the repository page click **uploading an existing file** and drag in everything from this folder **except** `node_modules` and `dist`. Click **Commit changes**.
   (Or, if you use Git: `git init`, `git add .`, `git commit -m "Portfolio"`, then follow GitHub's "push an existing repository" commands.)
3. Go to https://vercel.com, sign in with GitHub, click **Add New → Project**, pick `portfolio`, and click **Deploy**. Vercel detects Vite by itself; you don't need to change any settings.
4. After about a minute you get an address like `https://portfolio-xyz.vercel.app`. In Vercel → Project → Settings → Domains you can change it to something like `ducnguyen.vercel.app` if that name is free.
5. Put that final address in `content/site.json` → `meta.url`, then upload the changed file to GitHub. Vercel redeploys automatically. This matters because LinkedIn needs the correct address to show the preview image.
6. Check the preview at https://www.linkedin.com/post-inspector/ by pasting your URL.

From then on, every change you upload to GitHub goes live within a minute.

### Option B: GitHub Pages
`.github/workflows/deploy.yml` builds and publishes the site every time you push to `main`, so there is no `dist` folder to upload by hand.
1. Create a **public** repository named exactly `<your-username>.github.io`. Leave README, .gitignore and licence unticked.
2. In that repository go to **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions**.
3. Push this folder to the repository (see the commands below).
4. Open the **Actions** tab. When the run shows a green tick (about 2 minutes), the site is live at `https://<your-username>.github.io`.
5. Put that address in `content/site.json` → `meta.url`, then commit and push again.

```bash
git add -A
git commit -m "Portfolio site and projects"
git remote add origin https://github.com/<your-username>/<your-username>.github.io.git
git push -u origin main
```

## How it works (for the curious)
- `vite.config.js` turns `content/site.json` into plain HTML when the site is built, so the page is readable before any JavaScript runs.
- `src/hero3d.js`: the 3D bar terrain, loaded only after the page is ready and only on devices with WebGL 2. Phones in data-saver mode and very weak devices get the SVG drawing instead. With "reduce motion" switched on, the 3D scene stays still.
- `src/demo.js` + `src/portfolio.js`: the portfolio widget (mean–variance maths, efficient frontier on a 5% weight grid).
- `src/style.css`: colours and layout. The palette is at the top of the file.
