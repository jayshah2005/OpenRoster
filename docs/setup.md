# One-time setup

Most of this can be scripted with `gh` and the Vercel CLI once you're logged in to both.

## 1. Contact address

Create a forwarding address on your domain, such as `openroster@yourdomain.com`. On Cloudflare: Email → Email Routing → add a custom address that forwards to your inbox. Most registrars offer free forwarding too.

Then:

```bash
gh variable set OPENROSTER_CONTACT --body "openroster@yourdomain.com"
```

Also put the address in `TAKEDOWN.md`. The bot's User-Agent picks it up from this variable.

## 2. GitHub repository

```bash
gh repo create OpenRoster --public --source . --push
gh api -X PUT repos/{owner}/OpenRoster/actions/permissions/workflow \
  -f default_workflow_permissions=write -F can_approve_pull_request_reviews=true
```

- **Settings → Actions → General:** "Allow GitHub Actions to create and approve pull requests". The command above sets this.
- **Branch protection on `main`:** require the `CI` checks before merging. Dependabot auto-merge depends on this.
- **Labels:** the Maintenance workflow creates them from `.github/labels.yml` on its first run.

## 3. Vercel (Hobby, free)

```bash
cd web && npx vercel link        # create or link the project; root directory: web
gh secret set VERCEL_TOKEN       # from vercel.com/account/tokens
gh secret set VERCEL_ORG_ID     --body "$(jq -r .orgId .vercel/project.json)"
gh secret set VERCEL_PROJECT_ID --body "$(jq -r .projectId .vercel/project.json)"
gh variable set SITE_URL --body "https://openroster.vercel.app"   # or your custom domain
```

The site is built in GitHub Actions and uploaded with `vercel deploy --prebuilt`, so Vercel build minutes stay at zero. Every page is static. The only function is the per-filter feed, cached for 6 hours on Vercel's CDN.

To use your own domain, add it in Vercel → Project → Domains (for example `openroster.yourdomain.com`), then update `SITE_URL`.

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
