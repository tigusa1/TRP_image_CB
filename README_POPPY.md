# Poppy: prepare a country and hand it to a student

**Your job:** check a few examples, share them, then review the student's results.
Use **PER** below as an example. Replace it with the real country code.

## 1. Start

Use the setup steps in [Student quick start](README_UG.md).
Run:

```bash
python calibrate.py --config config/PER.json
```

Initialize only once. Keep an existing `config/PER.json`: it contains your progress.
Choose examples from early, middle, and recent reports, including different chart styles.

## 2. Check the examples

Open `output/PER/review.html`.
Check the dates, Y limits, last historical point, and extracted curve.
If a chart format needs a code change, fix and test it before assigning it to a student.

## 3. Share the seed

A **seed** is a shared config containing your completed examples.
Use real PNG filenames in this command:

```bash
python publish_seed.py PER --image PER_2020_Q1.png --image PER_2024_Q3.png
```

This replaces `config/seeds/PER.json` with the selected examples.
**List every example you want to share.** To share all saved calibrations after checking their overlays, use this instead:

```bash
python publish_seed.py PER --all
```

Publishing creates the local seed file; it does not upload anything.

Commit and push the seed to GitHub. Give the student:

- [Student quick start](README_UG.md), the country code, and the assigned PNGs.
- Your checked example overlays and any special instructions.
- The software version to use (`git rev-parse --short HEAD`).

After you push the seed, the student clones or pulls the updated repository, then runs once per assigned country:

```bash
python init_country.py PER --input "THEIR LOCAL SCREENSHOT FOLDER"
```

They replace the placeholder with their own full local path in quotes. A downloaded or synced OneDrive folder works; a sharing URL does not. Your examples are copied and skipped automatically. If their working config already exists, they keep it and skip initialization.
Assign only one person at a time to each country's working config.

## 4. If you change code

1. Pull the latest code before starting.
2. Create a separate branch, for example `poppy/per-format`.
3. Make the change. Run:

```bash
python -m unittest discover -s tests -q
```

4. Check representative overlays. Commit and push your branch.
5. Open a pull request for review before merging into `main`.
6. After merging, tell the student to pull and rebuild the results.

## Keep these files separate

| File | Purpose |
|---|---|
| `config/seeds/PER.json` | Shared examples; commit to GitHub |
| `config/PER.json` | Your local progress; back it up separately |
| `output/PER/` | Results; back up and exchange separately |

New seed changes do **not** update an existing working config. Ask the supervisor to help transfer corrections; do not replace a student's whole file.

If you cloned before this separation, back up your working JSONs outside the project before pulling the migration. Restore them afterward.
