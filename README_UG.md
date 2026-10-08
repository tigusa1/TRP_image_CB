# Student quick start

**Your job:** digitize the assigned charts and check every overlay.
Use the country code given by your supervisor. The examples below use **PER**.
Replace `PER` with your country code in every command and folder name.

## 1. Set up once

You need Git only to download the code and receive updates. You do not need to commit or push anything.

1. Make sure Git is installed (`git --version`). Ask your supervisor for help if needed.
2. In a terminal, go to the folder where you keep projects, then run:

```bash
git clone https://github.com/tigusa1/TRP_image_CB.git
cd TRP_image_CB
```

3. Open this project folder in your preferred IDE. Create and activate a Python **3.13** virtual environment in its terminal.
4. Run all remaining commands from the project folder containing `calibrate.py`.
5. Download the assigned PNGs, including the supervisor's examples, into `data/PER/screenshots/`. Do not rename or resize them.
6. Run:

```bash
python -m pip install -r requirements.txt
python init_country.py PER
```

Your progress is saved in `config/PER.json`. If it already exists, keep it.
**Do not replace it or edit `config/seeds/PER.json`.**

## 2. Digitize

```bash
python calibrate.py --config config/PER.json
```

For each chart:

1. Accept or correct the plot box.
2. Check first/last quarters and Y minimum/maximum. The suggestions can be wrong. Use arrows or type values.
3. Click the last historical point. If the red quarter-snapping vertical guide does not line up with the quarters on the chart, the **First quarter** / **Last quarter** values or the plot box are probably wrong. Check and correct them before continuing.
4. Click inside the darkest forecast band, away from grid lines.
5. Click **Save and next**.

Completed examples are skipped. Closing the window pauses work; the current unsaved chart is not saved. Run the same command to resume.

## 3. Check and submit

```bash
python run_country.py --config config/PER.json --known-only
```

Open `output/PER/review.html`. Check every overlay: black circles should follow the curve/band center; the black square marks the last historical point. Check the green axis labels too.

To redo one chart, use its exact filename:

```bash
python calibrate.py --config config/PER.json --image PER_2020_Q1.png
```

Upload a ZIP to your assigned **OneDrive submission folder**, using your name and country in the ZIP filename. Include:

- `config/PER.json` and the entire `output/PER/` folder.
- Names of skipped or questionable charts.
- Your software version: copy the result of `git rev-parse --short HEAD`.

**Back up your working config and outputs after each session. GitHub does not save them.**

## When the supervisor announces an update

Close the calibration window. In the project folder, run:

```bash
git pull --ff-only
python -m pip install -r requirements.txt
python run_country.py --config config/PER.json --known-only
```

Use the project virtual environment for the Python commands. Keep your working config; do not run initialization again. Your local PNGs, working config, and outputs are not tracked by Git. Rebuilding updates the outputs using your saved calibrations. You do not need to recalibrate unless your supervisor asks.

If Git reports an error, contact your supervisor. Do not delete or reset files. Do not change the extraction code yourself; report new chart formats to your supervisor.

If you used an older version before seed configs existed, back up your country JSON outside the project before your first update and ask your supervisor about restoring it.
