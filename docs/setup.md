# One-time setup

Most of this can be scripted with `gh` and the Vercel CLI once you're logged in to both.

## 1. Contact address

Create a forwarding address on your domain, such as `openroster@yourdomain.com`. On Cloudflare: Email → Email Routing → add a custom address that forwards to your inbox. Most registrars offer free forwarding too.

Then:

```bash
gh variable set OPENROSTER_CONTACT --body "openroster@jayshah.xyz"   # done
```

Also put the address in `TAKEDOWN.md`. The bot's User-Agent picks it up from this variable.

## 2. GitHub repository

```bash
gh repo create OpenRoster --public --source . --push
gh api -X PUT repos/{owner}/OpenRoster/actions/permissions/workflow \
  -f default_workflow_permissions=write -F can_approve_pull_request_reviews=true
```

- **Settings → Actions → General:** "Allow GitHub Actions to create and approve pull requests". The command above sets this.
- **Branch protection:** not needed. The data workflows commit to `main` directly, and Dependabot auto-merge waits for passing checks on its own. If you add protection later, let GitHub Actions bypass it.
- **Labels:** the Maintenance workflow creates them from `.github/labels.yml` on its first run.

## 3. Vercel (Hobby, free)

Done: the Vercel project `openroster` (team `jayshah3616`) is connected to this repository through the Vercel
GitHub app, with Root Directory `web` and "Include files outside the Root Directory" on (the build reads `data/`
and `config/`). From then on:

- every push to `main` deploys to production at https://openroster-seven.vercel.app, including the data
  commits the Update data workflow makes every 6 hours;
- every pull request gets its own preview URL, which Vercel posts on the PR;
- `NEXT_PUBLIC_SITE_URL` and `NEXT_PUBLIC_CONTACT_EMAIL` are set in Vercel for Production and Preview.

No token or deploy workflow is needed. Every page is static; the only function is the per-filter feed, cached for
6 hours on Vercel's CDN. If a token named `openroster-github-actions` exists at https://vercel.com/account/tokens
from the old Actions deploy, it can be deleted, along with the `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` secrets.

To use your own domain, add it in Vercel → Project → Domains (for example `openroster.jayshah.xyz`), then
`gh variable set SITE_URL --body "https://openroster.jayshah.xyz"`.

## 4. AI helpers (optional)

```bash
claude setup-token                       # uses your Claude subscription; no API key
gh secret set CLAUDE_CODE_OAUTH_TOKEN
```

Without this secret the AI jobs are skipped and everything else still works.

## 5. First data run

1. Actions → **Source audit** → Run workflow. It audits every source and opens a **Source review** PR.
2. Read the PR table (robots.txt result, terms link, quoted clauses), remove any `reviewed: true` lines you don't approve, then merge.
3. Actions → **Update data** → Run workflow. Its data commit deploys the site.

## If scheduled workflows were disabled

GitHub turns off scheduled workflows in public repos after 60 days without activity. The **Keep scheduled workflows enabled** workflow re-enables them twice a month. If they were disabled anyway, open Actions → pick each workflow (Update data, Source audit, Daily review, Link check, Maintenance, Keep scheduled workflows enabled) → **Enable workflow**. Or run:

```bash
for wf in scrape audit review links maintenance keepalive; do gh workflow enable $wf.yml; done
```
