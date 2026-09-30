# Deploying this site

Publish directory is this folder (`kessler/`). There is no build step — it is
static HTML.

## Option A — drag and drop (fastest)

1. Zip this folder, or use the zip from the chat.
2. Go to https://app.netlify.com/drop and drop it in.
3. To update the existing site instead of creating a new one, open that site →
   **Deploys** → drag the folder onto the "Need to update your site?" area.

`_redirects` and `_headers` in this folder are picked up automatically.

## Option B — connect the Git repo

1. Netlify → **Add new site** → **Import an existing project** → pick this repo.
2. Branch to deploy: whichever branch you want live.
3. Build command: leave empty. Publish directory: `kessler`.

`netlify.toml` at the repo root already sets the publish directory, headers and
the root redirect, so steps 2–3 mostly fill themselves in.

## After it is live

1. Open `https://<your-domain>/robots.txt` and `/sitemap.xml` and confirm both load.
2. Google Search Console → add the property → submit `sitemap.xml`.
3. Bing Webmaster Tools → add the site → submit the same sitemap. Bing is the
   index behind ChatGPT search and Copilot, so this is the one that affects
   whether AI assistants cite the firm.
4. Rich Results Test on one practice page and one blog post to confirm the
   FAQPage and LegalService markup is read correctly.
5. If the real domain is not `sweet-platypus-bc9aa4.netlify.app`, the canonical
   URLs, Open Graph URLs, `sitemap.xml`, `robots.txt` and `llms.txt` all need
   the real hostname. Tell Claude the domain and it will reissue them.
