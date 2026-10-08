"""Import report-table central estimates into the normal forecast CSV export."""
import argparse
from pathlib import Path

from inflation_digitizer.batch import resolve_output
from inflation_digitizer.configuration import load_working_config
from inflation_digitizer.excel_import import import_excel_tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--excel', type=Path, required=True)
    args = parser.parse_args()
    try:
        config = load_working_config(args.config)
        output = resolve_output(config)
        imported, combined, skipped = import_excel_tables(
            args.excel, config['country'], output, config.get('variable', 'CPI'))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Cannot import: {exc}\n')
    print(f'Imported {len(imported)} estimates from {imported.vintage.nunique()} reports.')
    if skipped:
        print('Skipped non-report sheets: ' + ', '.join(skipped))
    print(f'Saved {len(combined)} total rows: {output / "forecasts.csv"}')
    print('Future CSV refreshes include these imported rows. Rerun this command after editing the workbook.')


if __name__ == '__main__':
    main()
