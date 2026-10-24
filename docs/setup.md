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

Already done: the Vercel project `openroster` exists (team `jayshah3616`), `web/` is linked to it, and the
`VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` secrets are set. One step is left, and only the account owner can do it:

1. Create a token at https://vercel.com/account/tokens (name it `openroster-github-actions`, scope it to the
   `openroster` project if offered).
2. Save it as a repository secret: `gh secret set VERCEL_TOKEN -R jayshah2005/OpenRoster` and paste it.
3. Run Actions → **Deploy** → Run workflow.

Until the token exists, the Deploy workflow skips with a notice instead of failing.

The site is built in GitHub Actions and uploaded with `vercel deploy --prebuilt`, so Vercel build minutes stay at
zero. Every page is static; the only function is the per-filter feed, cached for 6 hours on Vercel's CDN.

Alternative: install the Vercel GitHub app on the repository and run `npx vercel git connect` in `web/`. Vercel then
deploys every push itself and the token is not needed.

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
3. Actions → **Update data** → Run workflow (tick "Deploy even if no data changed" the first time).

## If scheduled workflows were disabled

GitHub turns off scheduled workflows in public repos after 60 days without activity. The **Keep scheduled workflows enabled** workflow re-enables them twice a month. If they were disabled anyway, open Actions → pick each workflow (Update data, Source audit, Daily review, Link check, Maintenance, Keep scheduled workflows enabled) → **Enable workflow**. Or run:

```bash
for wf in scrape audit review links maintenance keepalive; do gh workflow enable $wf.yml; done
```
