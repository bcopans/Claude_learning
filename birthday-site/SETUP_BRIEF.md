# Rio 2027 Birthday Site — Setup Brief for Claude

You are completing the deployment of a finished Next.js birthday website for Ben's 40th.
The code is already built and pushed. Your job is Supabase + Vercel setup, then verify
it works end to end. Do not rewrite any code unless something is genuinely broken.

---

## What exists

`birthday-site/` in this repo is a complete Next.js 16 + TypeScript app:
- Code-gated (friends enter a personal code to get in)
- Supabase for guest codes, RSVPs, shrine offerings, stays, costume photos
- `/admin` for Ben to manage friend accounts and see all data
- All assets already in `public/` (golden-calf.png, altar.png, offerings/, sfx/)
- Schema SQL ready at `birthday-site/supabase-schema.sql`

The only thing missing: real Supabase credentials and a Vercel deployment.

---

## Step 1 — Supabase

Tell Ben: "Go to supabase.com, click 'New project', give it any name (e.g. rio2027),
pick a region close to you, set a database password, and wait for it to provision
(~2 min). Once it's ready, come back here."

When he's done, ask him for:
- **Project URL** — looks like `https://abcdefgh.supabase.co`
- **Anon/public key** — under Project Settings → API → `anon` `public`
- **Service role key** — same page, `service_role` (secret — tell him not to share
  this anywhere else)

Once you have those three values:

1. Create `birthday-site/.env.local` with:
```
NEXT_PUBLIC_SUPABASE_URL=<project URL>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon key>
SUPABASE_SERVICE_ROLE_KEY=<service role key>
ADMIN_PASSWORD=<generate a strong random password and show Ben what it is>
```

2. Run the schema: tell Ben to go to his Supabase project → SQL Editor → New query,
   paste the entire contents of `birthday-site/supabase-schema.sql`, and click Run.
   Confirm with him that it ran without errors.

3. Create the storage bucket: tell Ben to go to Storage → New bucket, name it exactly
   `costume-photos`, toggle Public on, click Save.

---

## Step 2 — Vercel

Tell Ben: "Go to vercel.com, sign up (or log in) with GitHub, click 'Add New Project',
import the `bcopans/Claude_learning` repo. On the configuration screen:
- Set **Root Directory** to `birthday-site`
- Do NOT click Deploy yet — come back here first."

Once he's on the Vercel config screen, tell him to add these 4 environment variables
(under Environment Variables, before deploying):
```
NEXT_PUBLIC_SUPABASE_URL       = <same value from .env.local>
NEXT_PUBLIC_SUPABASE_ANON_KEY  = <same value>
SUPABASE_SERVICE_ROLE_KEY      = <same value>
ADMIN_PASSWORD                 = <same value>
```

Then tell him to click Deploy and wait for it to finish. Ask him to paste the
production URL when it's done (looks like `https://xyz.vercel.app`).

---

## Step 3 — Smoke test

Once you have the production URL, walk Ben through these checks:

1. **Gate**: visit the URL — the gate screen should appear with the golden calf image.
   Enter an invalid code → should show "Hmm — that's not a code the Calf recognizes."
   Enter `BEN-HOST` → should land on the Home/Gospel screen. His name "Ben" should
   appear in the nav and in the RSVP form greeting.

2. **Nav & scroll**: click each nav item — Home, Explore, Shrine. Page should scroll
   to top on each. Members should show 🔒 since he hasn't RSVPd yet.

3. **RSVP**: go to Explore, scroll to RSVP, submit "I'm coming" with a hotel choice.
   After submit, Members should unlock. Verify in Supabase (Table Editor → rsvps) that
   a row appeared.

4. **Shrine**: tap a few offerings — they should fly onto the altar and stack up.
   Reload the page — the offerings should still be there (persisted). Check that
   reactions appear and the counter increments.

5. **Admin**: visit `/admin` on the production URL. Enter the ADMIN_PASSWORD.
   - In the Guests tab: add a friend (e.g., name "Dalton" → code auto-generates as
     BEN-DALTON). Note the code.
   - Open a private/incognito window, visit the site, enter BEN-DALTON → should work
     and show "Dalton" as the name.
   - Back in admin, deactivate Dalton. Try BEN-DALTON again → should be rejected.
   - Check RSVPs tab — Ben's RSVP from step 3 should be visible.

6. **Mobile**: open the site on a phone. Tap any input — the page should NOT zoom.
   The golden calf and altar images should display without cropping.

---

## If something is broken

- **"supabaseUrl is required" error**: the env vars aren't set correctly in Vercel.
  Go to Vercel → Project → Settings → Environment Variables and double-check all four.
  Then redeploy (Deployments → Redeploy).

- **Gate won't accept BEN-HOST**: the schema SQL didn't run, or the guests table is
  empty. Re-run the SQL from `supabase-schema.sql` in the Supabase SQL editor.

- **Offerings don't persist after reload**: check Supabase → Table Editor → offerings.
  If empty after tapping, the API route is likely returning an error — check Vercel
  Functions logs.

- **Costume upload fails**: the `costume-photos` bucket doesn't exist or isn't public.
  Supabase → Storage → check bucket exists and is set to Public.

- **Admin returns 401**: the ADMIN_PASSWORD env var in Vercel doesn't match what Ben
  is typing. Check for extra spaces or quotes when it was set.

---

## Ben's credentials summary (fill in when known)

| Item | Value |
|------|-------|
| Site URL | _pending Vercel deploy_ |
| Your guest code | `BEN-HOST` |
| Admin URL | `<site-url>/admin` |
| Admin password | _set in Step 1_ |
| Supabase dashboard | supabase.com → your project |

---

## Adding more friends later

From `/admin` → Guests & Codes tab → "Add a friend":
- Type their first name → code auto-generates as `BEN-[NAME]`
- Or type a custom code (must be unique, uppercase, no spaces — use hyphens)
- Give them their code directly (text, email, etc.) — the site has no email sending
- To revoke access: click Deactivate next to their name
