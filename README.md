# Gym Log

A personal training app for iPhone that runs Jeff Nippard's Upper/Lower Size & Strength
program (9 weeks; 4 lift days a week by default, or 3, or the program's own 6 and 5) alongside the runs in your
Runna plan. Each session shows sets × reps, % of 1RM worked out into kilos or an RPE target,
rest, the program's notes, its substitutes and weak-point picks, with a set-by-set log, rest
timer, last-set RPE, and a strength chart per lift. Workouts go in order onto your lift days,
so a missed day just moves everything along.

Focus muscles (on by default, Setup > Focus muscles) put chest, lats, biceps and quads first: the
program's weak-point slots are set to them and Upper 1 and Lower 1 get one extra finisher. The app has
light and dark themes; Auto follows the phone.

Live at https://rozbeh99.github.io/gym-log/ (open in Safari, then Share > Add to Home Screen).

## Runna sync

Runs planned in the Runna app can show up on the right days. Runna has no API, but its
Calendar Sync gives a private calendar link. The `Runna sync` GitHub Action
(`.github/workflows/runna-sync.yml`) fetches that link every three hours with
`tools/runna_sync.py` and commits the sessions to `docs/runna.json`, which the app reads.
Runs come from that file; lifting follows the program on your lift days.

To turn it on: in Runna open Profile > Settings > Calendar Sync and copy the link, then add it
in this repo under Settings > Secrets and variables > Actions as a secret named `RUNNA_ICS_URL`.
Run the workflow once from the Actions tab to sync straight away. The link stays secret, but
`docs/runna.json` (session titles, dates, descriptions, and distance and time of finished runs) is public like the rest of the site. Location, laps and PBs are left out.
Runs finished in Runna are added to the log automatically.

## Weigh-in reminder

The `Weigh-in reminder` Action (`.github/workflows/weigh-in.yml`) sends a push notification
through [ntfy](https://ntfy.sh) every Monday at 06:00 UTC. Tapping it opens Gym Log's weigh-in.
To turn it on: install the ntfy app, subscribe to a hard-to-guess topic name, and add that name
as a repo secret named `NTFY_TOPIC`. Run the workflow from the Actions tab to test it.

The site is served by GitHub Pages from `docs/` on `main`. The log is saved on the device;
use Setup > Save backup before switching phones.
