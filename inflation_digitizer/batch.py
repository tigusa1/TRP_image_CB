from __future__ import annotations
import argparse
import hashlib
import html
import json
from .configuration import load_working_config, input_directory
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import pandas as pd
from .core import extract, report_sort_key
from .overlay import save_overlay
from .forecast_export import export_csv_files

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / 'config/THA.json'


def discover(source: Path, timeout: int) -> list[str]:
    # Some cloud placeholder directories block during enumeration. Keep that
    # operation in a child process, which can be stopped on timeout.
    code = "import os,json,sys; print(json.dumps(sorted(e.name for e in os.scandir(sys.argv[1]) if e.name.lower().endswith('.png') and e.is_file())))"
    try:
        proc = subprocess.run([sys.executable, '-c', code, str(source)], capture_output=True,
                              text=True, timeout=timeout, check=True)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f'Directory listing timed out after {timeout}s: {source}. Open it in Finder and make the PNGs available offline, or use --known-only / --image FILENAME.') from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip()) from exc
    return sorted(json.loads(proc.stdout), key=report_sort_key)


def resolve_output(config):
    output = Path(config['output_directory']).expanduser()
    return output if output.is_absolute() else ROOT / output


def write_review(out, entries):
    cards = []
    for entry in entries:
        title = html.escape(entry['source_file'])
        status = html.escape(entry['status'])
        msg = html.escape(entry.get('message', ''))
        image = f'<a href="{html.escape(entry["overlay"])}"><img loading="lazy" src="{html.escape(entry["overlay"])}" alt="{title}"></a>' if entry.get('overlay') else ''
        cards.append(f'<article><h2>{title}</h2><p><b>{status}</b> {msg}</p>{image}</article>')
    content = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Inflation digitization review</title>
<style>body{font:16px system-ui,sans-serif;max-width:1250px;margin:30px auto;padding:0 20px;color:#172c43}article{border-top:1px solid #ccd4dc;padding:18px 0}img{max-width:100%;height:auto}h2{font-size:20px}p{line-height:1.5}</style>
<h1>Inflation digitization review</h1><p>Check axis dates, vertical limits, the historical/forecast boundary, and the pink curve against the darkest band. Unknown images have no extracted values until calibrated. Midpoints are not verified statistical medians.</p>'''
    (out/'review.html').write_text(content+'\n'.join(cards)+'</html>', encoding='utf-8')


def run(config_path: Path, known_only=False, images=None):
    config = load_working_config(config_path)
    source = input_directory(config)
    calibrations = config.get('images', {})
    if images:
        names = images
    elif known_only:
        names = sorted(calibrations, key=report_sort_key)
    else:
        names = discover(source, config.get('directory_timeout_seconds', 20))
    if not names:
        raise RuntimeError('No PNG files found.')
    out = resolve_output(config)
    out.mkdir(parents=True, exist_ok=True)
    all_rows, entries = [], []
    for name in names:
        # Config keys and command-line --image arguments are filenames only.
        if Path(name).name != name:
            raise ValueError('--image must be a filename in the configured input directory')
        path = source/name
        c = calibrations.get(name)
        if not c:
            entries.append(dict(source_file=name, status='needs_calibration', message=f'Run calibrate.py --image "{name}"'))
            print(f'NEEDS CALIBRATION: {name}', flush=True)
            continue
        try:
            result = extract(path, c, config['country'])
            rel_overlay = f'overlays/{path.stem}_overlay.png'
            save_overlay(path, result, out/rel_overlay)
            (out/'tables').mkdir(exist_ok=True)
            frame = pd.DataFrame(result.rows)
            frame.to_csv(out/'tables'/f'{path.stem}.csv', index=False)
            (out/'calibrations').mkdir(exist_ok=True)
            audit = dict(calibration=c, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         generated_utc=datetime.now(timezone.utc).isoformat(), warnings=result.warnings)
            (out/'calibrations'/f'{path.stem}.json').write_text(json.dumps(audit, indent=2))
            all_rows.extend(result.rows)
            entries.append(dict(source_file=name, status='review_flags' if result.warnings else 'extracted',
                                message='; '.join(result.warnings), overlay=rel_overlay))
            print(f'EXTRACTED: {name} ({len(result.rows)} quarters, {len(result.warnings)} flags)', flush=True)
        except Exception as exc:
            entries.append(dict(source_file=name, status='error', message=str(exc)))
            print(f'ERROR: {name}: {exc}', flush=True)
    manifest = pd.DataFrame(entries)
    manifest.to_csv(out/'manifest.csv', index=False)
    # Every run replaces the combined table with this run's scope. Per-image
    # artifacts from earlier runs remain available but are not silently merged.
    frame = pd.DataFrame(all_rows)
    frame.to_csv(out/'quarterly_estimates.csv', index=False)
    with pd.ExcelWriter(out/'quarterly_estimates.xlsx', engine='openpyxl') as writer:
        frame.to_excel(writer, sheet_name='Estimates', index=False)
        manifest.to_excel(writer, sheet_name='Review', index=False)
    # The downstream-format export includes every available per-chart CSV,
    # even when this extraction run only regenerated a single chart.
    if (out/'tables').is_dir() and any((out/'tables').glob('*.csv')):
        export_csv_files(out/'tables', out/'forecasts.csv',
                         variable=config.get('variable', 'CPI'),
                         per_report_directory=out/'formatted_tables')
    write_review(out, entries)
    print(f'\nReview: {out / "review.html"}\nData: {out / "quarterly_estimates.xlsx"}', flush=True)
    return entries


def main():
    parser = argparse.ArgumentParser(description='Extract calibrated inflation charts and create review overlays.')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--known-only', action='store_true', help='Only process saved calibrations; do not list the input folder.')
    parser.add_argument('--image', action='append', help='Process one filename; can be repeated.')
    args = parser.parse_args()
    try:
        entries = run(args.config.resolve(), args.known_only, args.image)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'Cannot run: {exc}', file=sys.stderr)
        return 1
    return 2 if any(e['status'] in ('needs_calibration', 'error') for e in entries) else 0
