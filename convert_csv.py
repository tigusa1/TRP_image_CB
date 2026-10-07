"""Run directly in PyCharm to export all saved chart CSVs in downstream format."""
import argparse
import json
from pathlib import Path
import sys
from inflation_digitizer.batch import DEFAULT_CONFIG, resolve_output
from inflation_digitizer.forecast_export import export_csv_files


def main():
    parser = argparse.ArgumentParser(description='Convert extracted CSVs to country,report,target,variable,forecast,h.')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--input', type=Path, help='One detailed CSV or a directory of per-chart CSVs; defaults to configured output/tables')
    parser.add_argument('--output', type=Path, help='Combined output CSV; defaults to configured output/forecasts.csv')
    parser.add_argument('--variable', default='CPI', help='Variable label; default CPI')
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text())
        out = resolve_output(config)
        source = args.input or out/'tables'
        destination = args.output or out/'forecasts.csv'
        per_report = out/'formatted_tables' if args.input is None else None
        result = export_csv_files(source, destination, args.variable, per_report)
        print(f'Saved {len(result)} rows across {result[["country", "report"]].drop_duplicates().shape[0]} reports: {destination}')
        if len(result):
            print(f'Horizons: {result.h.min()} to {result.h.max()} quarters; zero and negative horizons retained.')
        if per_report is not None:
            print(f'Per-chart formatted CSVs: {per_report}')
        return 0
    except (ValueError, OSError) as exc:
        print(f'Cannot convert: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
