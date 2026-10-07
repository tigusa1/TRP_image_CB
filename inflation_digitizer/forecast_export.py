"""Convert digitized chart rows to the six-column downstream CSV schema."""
from pathlib import Path
import pandas as pd
from .core import quarter_number, quarter_label

COLUMNS = ['country', 'report', 'target', 'variable', 'forecast', 'h']
REQUIRED = ['country', 'vintage', 'quarter', 'inflation_pct_yoy']


def convert_frame(frame, variable='CPI'):
    missing = [name for name in REQUIRED if name not in frame.columns]
    if missing:
        raise ValueError('Input is missing columns: ' + ', '.join(missing))
    if not isinstance(variable, str) or not variable.strip():
        raise ValueError('Variable must be a nonempty label, e.g. CPI')
    if frame['country'].isna().any() or frame['country'].astype(str).str.strip().eq('').any():
        raise ValueError('Every row must have a country')
    try:
        reports = frame['vintage'].map(lambda x: quarter_number(str(x)))
        targets = frame['quarter'].map(lambda x: quarter_number(str(x)))
    except ValueError as exc:
        raise ValueError(f'Invalid report or target quarter: {exc}') from exc
    result = pd.DataFrame({
        'country': frame['country'].astype(str).str.strip(),
        'report': reports.map(quarter_label),
        'target': targets.map(quarter_label),
        'variable': variable.strip(),
        'forecast': pd.to_numeric(frame['inflation_pct_yoy'], errors='raise'),
        'h': (targets - reports).astype('int64'),
    }, columns=COLUMNS)
    # Repeated targets in different reports are intentional. Duplicate records
    # within one report are not silently dropped or averaged.
    keys = ['country', 'report', 'target', 'variable']
    duplicates = result.duplicated(keys, keep=False)
    if duplicates.any():
        examples = result.loc[duplicates, keys].head(3).to_dict('records')
        raise ValueError(f'Duplicate country/report/target/variable rows: {examples}')
    return result.sort_values(keys, kind='stable').reset_index(drop=True)


def export_csv_files(source, destination, variable='CPI', per_report_directory=None):
    source, destination = Path(source), Path(destination)
    files = sorted(source.glob('*.csv')) if source.is_dir() else [source]
    if not files:
        raise ValueError(f'No CSV files found in {source}')
    frames = []
    for path in files:
        try:
            frame = pd.read_csv(path)
            converted = convert_frame(frame, variable)
        except (ValueError, OSError) as exc:
            raise ValueError(f'{path.name}: {exc}') from exc
        frames.append((path, frame, converted))
    # Validate the combined table too, before writing any new output.
    combined = convert_frame(pd.concat([frame for _,frame,_ in frames], ignore_index=True), variable)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if any(destination.resolve() == path.resolve() for path in files):
        raise ValueError('Choose an output path different from the source CSVs')
    if per_report_directory is not None:
        per_report_directory = Path(per_report_directory)
        if any((per_report_directory/path.name).resolve() == path.resolve() for path in files):
            raise ValueError('Per-report output directory must differ from the source directory')
        per_report_directory.mkdir(parents=True, exist_ok=True)
        for path, _, converted in frames:
            converted.to_csv(per_report_directory/path.name, index=False)
    temporary = destination.with_suffix(destination.suffix + '.tmp')
    combined.to_csv(temporary, index=False)
    temporary.replace(destination)
    return combined
