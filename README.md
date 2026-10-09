# Inflation chart digitizer

**Short guides:** [Students](README_UG.md) · [Poppy / country supervisors](README_POPPY.md)

Extract quarterly historical curves and darkest-forecast-band midpoints from PNG charts. Produces deterministic annotated PNGs, CSVs, Excel tables, and a local HTML review report. Source images are never modified. No API key, internet service, or GPU is needed to run it.

## Country setup and personal progress

Each person has their own checkout, virtual environment, locally synced PNGs,
working config (`config/COUNTRY.json`), and output folder. Git ignores working
configs and outputs. New configs start empty by default; students calibrate all
assigned screenshots, including the supervisor's test examples. No seed handoff
is required. Existing configs and saved progress are preserved.

### Supervisor: start a country, then hand it off

For a new country such as PER, download or sync its PNGs locally, then create a working config once:

```bash
python init_country.py PER --input "YOUR LOCAL SCREENSHOT FOLDER"
```

Replace the quoted placeholder with the full folder path on your computer. For OneDrive, use the downloaded or synced local folder, not a sharing URL. Keep the quotes around paths containing spaces. Folder names do not need to change; for example:

```bash
python init_country.py COL --input "/your/local/path/COL/COL Screenshots"
```

If you omit `--input`, the default is `data/PER/screenshots/` inside the project.

The command starts with no calibrated screenshots, even if a shared seed exists.
It refuses to overwrite an existing working config. To change a
local path later, edit `input_directory` in your ignored working JSON.
Relative input and output directories resolve from the project root.

Calibrate representative images and inspect their overlays:

```bash
python calibrate.py --config config/PER.json
```

Once the format works, give students the country code, private OneDrive access,
and any special instructions. They repeat your test screenshots. Commit and push
any necessary code changes so students can pull them before starting.

### Student: initialize once, then continue

Clone the repository, install the requirements, and download or sync the assigned PNGs. If you already cloned, run `git pull --ff-only` to get the latest code before initializing. Then:

```bash
python init_country.py PER --input "YOUR LOCAL SCREENSHOT FOLDER"
python calibrate.py --config config/PER.json
```

Use your own local folder path in quotes. Initialization is once per assigned country; if `config/PER.json` exists, skip initialization and retain your progress. Run the calibration command whenever you want to start or resume.

Screenshots you have already calibrated are skipped automatically. After pulling
code updates, keep using the same working config. Rebuild saved charts with:

```bash
python run_country.py --config config/PER.json --known-only
```

Return your working config and outputs through project storage; Git ignores both
and is not their backup. PNGs can stay in the synced OneDrive folder. Use a clean
output folder for each assignment because CSV exports include all saved source tables.

### Optional shared examples (advanced)

The seed tools remain available, but are not needed for student assignments.
To deliberately copy an existing seed during first-time initialization, add
`--use-seed` to the initialization command. This never overwrites an existing config.
Supervisors can publish all checked examples with `python publish_seed.py PER --all`
and commit/push `config/seeds/PER.json`. Later seed updates do not merge into
existing working configs automatically.

### First pull for an existing collaborator

This migration stops tracking the old `config/COUNTRY.json` paths. Before pulling
this migration into an older clone, copy any working country JSONs outside the
repository; Git may remove the formerly tracked files. After pulling, restore your
working copies to `config/`. Subsequent pulls leave these ignored files alone.
Fresh clones use `init_country.py` instead. The maintainer's current local working
files were retained when making this change.

## PyCharm setup

1. Open `/Users/ti/Sites/GitHub/TRP_image_CB` as a project.
2. Select the project interpreter `.venv/bin/python` under **Settings → Python → Interpreter** (the exact labels vary by PyCharm version).
3. If the virtual environment is missing, create a new local virtualenv using Python 3.13, at `.venv` in this project.
4. Install dependencies with the selected interpreter: `python -m pip install -r requirements.txt`.
5. On a fresh clone, run `python init_country.py THA --input "YOUR LOCAL SCREENSHOT FOLDER"` and provide matching PNGs before right-clicking `run_thailand.py` to run it. All paths default to this project's configuration, independent of PyCharm's working directory.

The current setup includes two visually checked seed calibrations: `THA_2000_Q4.png` and `THA_2025_Q3.png`. These are image-based estimates, not externally verified source data.

The setup includes `requirements-lock.txt` with the exact installed package versions. To recreate this environment, install that file instead of `requirements.txt`.

The initial folder inventory found **102 Thailand PNGs**, with two seed charts extracted and 100 awaiting calibration. Representative charts from 2000, 2005, 2010, 2015, 2020, and 2026 show multiple layout and colour changes.

## First run

In the PyCharm terminal:

```bash
python run_thailand.py --known-only
```

This processes only saved calibrations and avoids listing the OneDrive directory. Open `output/THA/review.html` in a browser and review the images. Output files:

- `overlays/*.png`: original chart with historical trace (orange), estimated central forecast (magenta), quarterly markers, and calibrated axis box (green).
- `tables/*.csv`: each chart's data.
- `quarterly_estimates.csv` / `.xlsx`: this run's combined estimates; Excel includes a review-status sheet.
- `manifest.csv`: success, review flags, errors, and charts requiring calibration.
- `calibrations/*.json`: calibration, source SHA-256, timestamp, and warnings for reproducibility.

Running for a subset replaces the combined tables/report with that subset. Per-image outputs from older runs remain; they are not automatically merged. Run the full batch to regenerate combined outputs for all available images.

## Full Thailand batch

```bash
python run_thailand.py
```

The source directory is configured in `config/THA.json`. Only images with saved calibrations are extracted. Unknown PNGs appear in the manifest as `needs_calibration` instead of receiving guessed axis values. Exit code 2 means some images still need calibration or failed; 1 is a batch setup error.

If listing OneDrive files times out, use Finder to make this folder available offline (OneDrive's **Always Keep on This Device** option), allow synchronization to finish, and retry. Alternatively, point `input_directory` at a local copy. `--known-only` and `--image NAME.png` bypass directory enumeration but still require the named files to be locally readable.

## Calibrate the whole folder in one session

Run `calibrate.py` directly in PyCharm with no parameters, or run:

```bash
python calibrate.py
```

The program opens uncalibrated PNGs in filename order. Each new image inherits the axis values and colour tolerance from the previous completed chart. The first image uses your most recent completed calibration, or a nearby saved template. An orange rectangle suggests the plot bounds. Accept it with one click, then select the historical endpoint and darkest band. If the rectangle is off, correct either corner or select both manually.

- For a new chart later than its template in filename order, **Last quarter automatically advances by one quarter**. First quarter and the vertical-axis values carry forward. Revisiting an already calibrated chart preserves its saved values. Check the date range, especially after skips, gaps, or layout changes; the increment is a convenience, not a reading of the axis labels.
- Use the **left/right arrows** beside **First quarter** and **Last quarter** to move backward/forward one quarter, including across year boundaries. You can also type in the boxes.
- **Save and next** saves the calibration and extracts the chart, then opens the next image.
- **Skip** leaves this image unsaved and moves on; it will return next session.
- **Stop** or closing the window ends the session without saving the current unfinished image. Earlier completed images remain saved.
- Restart the same command to resume: saved calibrations are skipped automatically.
- Each chart's PNG and CSV are written as it is completed. When the session stops or finishes, combined reports are regenerated for all saved charts. If the process is forcibly terminated, run `python run_thailand.py --known-only` to rebuild the combined outputs.

Optional controls:

```bash
python calibrate.py --template THA_2000_Q4.png
python calibrate.py --start-at THA_2005_Q1.png
python calibrate.py --include-calibrated
```

`--include-calibrated` revisits saved images; those images start with their own saved values. Uncalibrated images inherit the last completed chart's values with the last-quarter increment described above. The program does not read axis dates: check both endpoints and the vertical-axis limits on each chart.

## Calibrate a new image

```bash
python calibrate.py --image THA_2024_Q3.png
```

Use `--image` for a single chart; running without it starts the folder queue.

In the calibration window:

1. Enter the first and last plotted quarter and the vertical-axis minimum and maximum. Quarters refer to the plotting-box edges, not the first and last printed year labels. Confirm that time is evenly spaced and the vertical scale is linear.
2. Inspect the orange suggested rectangle and click **Accept box** if it follows the plot axes. To fix one corner, choose **Adjust top left** or **Adjust bottom right**, click its correct position, then accept. Alternatively, click top left and bottom right directly to replace both corners. If no box is detected, select both corners manually. Existing calibrations show their saved box; new images use neutral horizontal and vertical axis lines to estimate it.
3. Move the cursor to the final historical observation, where the fan begins. A dashed vertical guide snaps to the nearest quarter and extends through the horizontal-axis labels; the sidebar displays that quarter. Click to select it. The guide remains visible after selection. This sets the historical/forecast boundary independently of the filename's forecast vintage. If the red quarter-snapping vertical guide does not line up with the quarters on the chart, the **First quarter** / **Last quarter** values or the plot box are probably wrong. Check and correct them before continuing.
4. Click inside the darkest forecast band, away from text and grid lines.
5. Click **Save and extract**. Review the resulting overlay before using the values.

Use the toolbar to zoom for precise clicking; turn zoom/pan off before making selections. **Reset clicks** clears your selections and restores the box suggestion. If PyCharm captures the plot in a noninteractive tool window, disable its **Show plots in tool window** setting or run `python calibrate.py ...` from the project terminal.

You can prefill axis values using a saved chart:

```bash
python calibrate.py --image THA_2024_Q3.png --template THA_2025_Q3.png
```

The box must be accepted or manually selected, followed by the historical endpoint and band colour. A template does not prove that a new chart has the same axes. Calibrations are saved in `config/THA.json`; replacing an existing calibration also saves a `.json.bak`. After checking an overlay, set that image's `review_status` to `reviewed` in the JSON and rerun it. `manually_calibrated` is deliberately flagged until reviewed.

## Method and limitations

The selected curve colour is matched within a configurable RGB distance. At each quarterly x-position, the extractor checks three adjacent pixel columns and estimates the midpoint between the darkest band's visible upper and lower edges. Small grid-line gaps are tolerated. Missing or substantially disconnected colour matches are flagged, with missing values left blank. The forecast colour remains the primary match. If a historical point has no matches, a separate recovery step finds a darker, less saturated stroke in the same broad colour family while rejecting neutral grid lines. Small forecast-band gaps filled by overprinted ink can be joined; blank separations remain ambiguous. For a narrow fan wholly covered by an explicit dark centreline, the visible line can supply the central estimate, with shaded-band bounds left blank. A thick plot frame can trigger sampling a few pixels farther inside the plot. Every recovery is recorded in the `extraction_method` column, actual sampling columns in `sampled_x_min`/`sampled_x_max`, and warnings in the review report. These recovered points should be checked against their overlays.

The midpoint of a shaded interval is not necessarily the statistical median or mode. Exports therefore call the forecast series `forecast_band_midpoint`. Confirm a central bank's methodology before relabelling it as a median. The exported central-band bounds describe the visible band, not uncertainty in the digitization or a known-probability confidence interval.

Saved figures and four-decimal exports preserve the pixel calculation for reproducibility; they do not imply four-decimal accuracy. For analysis, rounding to approximately 0.1 percentage point is more appropriate until independently validated. Curves clipped by an axis boundary, overlapping labels, antialiasing, different colours, asymmetric bands, and incorrect quarterly interpretation need review.

This version uses per-image calibration with suggested plot bounds. It does not automatically read axis labels. The detector looks for long neutral-coloured lines forming a rectangle and can confuse unusual frames or grid layouts; suggestions always require acceptance. Once the full Thailand collection is available and reviewed, repeated layouts can be grouped into profiles to reduce manual work. Every chart should retain an overlay for auditing.

## Add another country

Copy `config/THA.json` to a new country JSON, change `country`, `input_directory`, and `output_directory`, and replace `images` with an empty object. Use `--config config/NEW.json` with both scripts. The processing engine is shared; calibrations are separate by country and image. No source files need to be moved.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests exercise known synthetic curves, band bounds, grid-line interference, missing data, dates, and calibration rejection. GUI interaction needs a desktop session and should also be checked manually.


## CSVs for downstream analysis

Run `convert_csv.py` directly in PyCharm, or:

```bash
python convert_csv.py
```

This reads **all individual chart CSVs** from the configured `output_directory/tables`, including reports not present in the most recent subset run's combined table. It writes:

- `forecasts.csv`: all saved reports, sorted by country, report, target, and variable.
- `formatted_tables/*.csv`: one converted CSV per input chart.

Both use exactly these columns, with no index column:

```text
country,report,target,variable,forecast,h
```

`report` is the filename-derived report vintage; `target` is the plotted quarter; `variable` defaults to `CPI`; `forecast` contains the extracted inflation percentage (no unit conversion or extra rounding). The horizon is the integer difference in quarters: `4 * (target year - report year) + target quarter - report quarter`. All source rows are retained, including historical observations, zero/negative horizons, and blank estimates if present. The column name `forecast` is required by the downstream format; it does not reclassify historical data as forecasts. Detailed source tables retain that distinction and review flags.

The new exports refresh automatically after extraction runs. They include **all existing per-chart files**, while the original `quarterly_estimates.csv`/Excel files retain their existing current-run scope. If you remove a report from the project, also remove its obsolete individual CSV from `tables` to exclude it from future downstream exports.

To convert one detailed file or use another label:

```bash
python convert_csv.py --input output/THA/tables/THA_2001_Q2.csv --output output/THA/THA_2001_Q2_formatted.csv
python convert_csv.py --variable CPI
```

For another country, pass its `--config` file. Invalid quarter labels or duplicate country/report/target/variable rows raise an error instead of silently changing data.


## Review only Y minimum and Y maximum

Run **`review_axes.py`** directly in PyCharm with no parameters, or:

```bash
python review_axes.py
```

This opens each chart that has a saved calibration and has not yet completed this axis-limit review. It displays the original PNG, saved plot box, and two numeric fields. In the queue, these fields start with the previous completed chart’s Y limits. On resuming, they start with the most recently confirmed chart’s limits; the sidebar identifies the source chart. If none has been confirmed yet, the first chart uses its own saved limits. Explicit `--image` reviews use that chart’s own values. Skipping a chart does not carry forward unsaved edits. There are **no cursor selections**. Enter the correct Y minimum and Y maximum (or adjust using − / + in units of one), then click **Save and next**. If the numbers are already correct, still click Save and next to confirm them.

- **Save and next** updates only the two numeric limits and their review metadata; plot corners, dates, the historical boundary, colour, and other settings are preserved. The per-chart outputs and downstream CSVs regenerate automatically.
- **Skip** moves on without confirming the current chart; it appears again next session.
- **Stop** or closing the window leaves the current unfinished chart unsaved. Previous confirmations remain saved. Restarting resumes unreviewed charts automatically.
- A copy of the calibration JSON from before the session's first save is kept under `config/backups/`.
- Full combined CSV/Excel results refresh when the session stops or finishes. If the process is forcibly terminated, `python run_thailand.py --known-only` rebuilds them from saved calibrations.

Review progress is separate from the broader calibration review status. Confirming axis values does not mark every extracted point as reviewed. Changing the saved box, image size, or limits invalidates the axis-review confirmation; rerunning full calibration also clears it.

Optional controls:

```bash
python review_axes.py --image THA_2001_Q2.png
python review_axes.py --start-at THA_2010_Q1.png
python review_axes.py --include-reviewed
python review_axes.py --config config/COL.json
```

To revisit a previously confirmed sequence, combine `--start-at` with `--include-reviewed`.


## Chile (CHL)

CHL is configured in `config/CHL.json`, reading the original OneDrive
`CHL/Inflation_screenshots` folder and writing separate `output/CHL` results.
Its defaults support black historical lines, red forecast bands, and an open
left/bottom axis frame. The first chart, `CHL_2012_Q2.png`, has a seed calibration
and overlay; the remaining charts need calibration.

In PyCharm, run `calibrate.py` with Parameters `--config config/CHL.json` and
working directory set to this project. Or run:

```bash
python calibrate.py --config config/CHL.json
```

Accept or correct the suggested plot corners, check the axis dates and numeric
limits, click the last historical point, and click inside the darkest **red**
forecast band. Black history is detected separately. Save and next carries the
previous values forward and advances the end quarter by one; check this against
each image because layouts and displayed date ranges change. The right edge of
an open frame is inferred from the bottom axis, so check its date carefully.

To inspect or redo the seed chart:

```bash
python calibrate.py --config config/CHL.json --image CHL_2012_Q2.png
```

To review only numeric Y limits, or rebuild all saved calibrations:

```bash
python review_axes.py --config config/CHL.json
python run_country.py --config config/CHL.json --known-only
```

Each save updates `output/CHL/forecasts.csv` automatically. Conversion alone uses
`python convert_csv.py --config config/CHL.json`. Always include the CHL config:
the scripts' default remains Thailand. Existing THA results are separate.

Some later CHL charts have a first forecast band too thin to identify its darkest
colour. Such points remain blank and flagged in the review report; inspect the
overlay rather than treating blanks as zeros or assuming every point was read.


## Brazil (BRA)

Use `calibrate.py --config config/BRA.json` in PyCharm with this project as the
working directory. Month filenames are supported without renaming:
Mar = Q1, Jun = Q2, Sep = Q3, Dec = Q4. The queue sorts report dates chronologically.
The first chart (September 2012) has a checked seed calibration and overlay.

The BRA queue includes quarterly PNGs in the configured `finished digitizing`
folder, with no report-date cutoff. Keep monthly charts outside that folder.
Monthly-axis sampling has been removed. Previously generated
monthly example files are archived outside the active tables folder and excluded
from `forecasts.csv`. Month names in report filenames remain supported.

Both Y minimum and Y maximum in `calibrate.py` have − / + buttons that adjust
by exactly one per click. You can also type a value. `review_axes.py` retains its
existing one-unit buttons.

For the gold fans, align the left/right calibration bounds with the FIRST/LAST
QUARTERLY DATA positions, not the padded outer axis ends. The vertical bounds
still correspond to the numeric Y limits. Pale axes may require manual corners.
Check both quarter fields and Y limits for every image; gaps between reports mean
the automatic +1 end-quarter suggestion is not always correct. Click inside the
darkest GOLD band, avoiding the blue target lines. Save and next saves each chart.

Outputs go to `output/BRA`, including automatically updated `forecasts.csv`.
Axis review and conversion use the same `--config config/BRA.json` parameter.

## Import central estimates from Excel report tables

For a country workbook with one sheet per report, run:

```bash
python import_excel.py --config config/BRA.json --excel "/path/to/BRA CPI.xlsx"
```

Use sheet names such as `2015 Mar`, `2015 Jun`, `2015 Sep`, `2015 Dec`, or `2015Q1`.
The first row must include `Period` and `central`. Use either a separate `Year`
column or a combined Period such as `2015 2`. Quarters may be 1–4, Q1–Q4, or
I–IV. Central values must be numbers in percentage points (8.1 means 8.1%).
Non-report sheets such as `wraprows` are skipped and listed. Missing/invalid
values and duplicate report/target rows stop the import before source CSVs change.

The importer stores the workbook values and source sheet/cell references in
`output/BRA/tables/BRA_CPI_excel.csv` and rebuilds `output/BRA/forecasts.csv`.
The output retains zero and negative horizons. Normal calibration and
`convert_csv.py` refreshes include these saved table values automatically.
After editing the Excel workbook, rerun the import command to replace its saved
values. Include the imported source CSV when handing off work to another person.
Table estimates do not create chart overlays or enter `quarterly_estimates.xlsx`.
