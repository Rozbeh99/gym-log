# Gym Log

A personal training app for iPhone: four lifting days (Push, Pull, Legs, Upper) and
two runs a week, with sets × reps targets, swap-in exercises for whatever the gym has,
a set-by-set log with a rest timer, and a strength chart per lift.

Live at https://rozbeh99.github.io/gym-log/ (open in Safari, then Share > Add to Home Screen).

## Runna sync

Runs planned in the Runna app can show up on the right days. Runna has no API, but its
Calendar Sync gives a private calendar link. The `Runna sync` GitHub Action
(`.github/workflows/runna-sync.yml`) fetches that link every three hours with
`tools/runna_sync.py` and commits the sessions to `docs/runna.json`, which the app reads.
Once that file has runs, run days come from Runna and the schedule only places the lift days.

To turn it on: in Runna open Profile > Settings > Calendar Sync and copy the link, then add it
in this repo under Settings > Secrets and variables > Actions as a secret named `RUNNA_ICS_URL`.
Run the workflow once from the Actions tab to sync straight away. The link stays secret, but
`docs/runna.json` (session titles, dates and descriptions) is public like the rest of the site.

The site is served by GitHub Pages from `docs/` on `main`. The log is saved on the device;
use Setup > Save backup before switching phones.

Exercise photos come from the public-domain [Free Exercise DB](https://github.com/yuhonas/free-exercise-db)
(Unlicense), resized to WebP in `docs/img/`. `tools/images.json` maps each exercise name in the plan to its
photo; a few swaps use the closest standard version.
