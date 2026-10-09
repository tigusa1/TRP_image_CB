# Poppy: prepare a country and hand it to a student

**Your job:** test a few screenshots, assign the country, then review the student's results.
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

## 3. Hand off the country

No seed or calibration file needs to be published. Students repeat your test
screenshots as part of their assignment.

Give the student:

- [Student quick start](README_UG.md), the country code, and private OneDrive access.
- The names of your tested screenshots and any special instructions.
- Optionally, your checked overlays for comparison.

Students pull the latest code, then initialize once using their own synced folder:

```bash
python init_country.py PER --input "THEIR LOCAL SCREENSHOT FOLDER"
python calibrate.py --config config/PER.json
```

Each student keeps their own working config. An existing config is preserved;
do not delete it to restart setup. Assign distinct screenshot ranges if several
students work on one country.

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
| `config/PER.json` | Your local progress; back it up separately |
| `output/PER/` | Results; back up and exchange separately |

Students receive algorithm updates through GitHub. Keep personal calibration JSONs and outputs separate; do not commit or replace a student's working file.

If you cloned before this separation, back up your working JSONs outside the project before pulling the migration. Restore them afterward.
