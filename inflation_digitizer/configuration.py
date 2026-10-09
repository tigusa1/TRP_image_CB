"""Shared seed configurations and private, per-checkout working configurations."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def country_code(value):
    value = value.upper()
    if not re.fullmatch(r'[A-Z]{3}', value):
        raise ValueError('Country must be a three-letter code, such as PER.')
    return value


def load_working_config(path):
    path = Path(path)
    if not path.exists():
        raise ValueError(f'Working config not found: {path}. Run python init_country.py COUNTRY first.')
    config = json.loads(path.read_text())
    if config.get('config_role') == 'seed' or path.resolve().parent == (ROOT/'config/seeds').resolve():
        raise ValueError('This is a shared seed. Run python init_country.py COUNTRY and use --config config/COUNTRY.json.')
    return config


def input_directory(config, root=ROOT):
    path = Path(config['input_directory']).expanduser()
    return path if path.is_absolute() else Path(root)/path


def seed_config(config, names):
    country = country_code(config['country'])
    seed = {key: config[key] for key in ('country', 'variable', 'directory_timeout_seconds',
            'calibration_defaults') if key in config}
    missing = sorted(set(names)-set(config.get('images', {})))
    if missing:
        raise ValueError('No saved calibration for: '+', '.join(missing))
    seed.update(config_role='seed', input_directory=f'data/{country}/screenshots',
                output_directory=f'output/{country}',
                images={name:config['images'][name] for name in sorted(set(names))})
    # Image-specific defaults may be required to reproduce the selected seeds.
    if config.get('image_defaults'):
        seed['image_defaults'] = {n:config['image_defaults'][n] for n in names if n in config['image_defaults']}
    return seed


def initialize_country(country, source=None, root=ROOT, *, use_seed=False):
    root = Path(root)
    country = country_code(country)
    destination = root/'config'/f'{country}.json'
    if destination.exists():
        raise ValueError(f'{destination} already exists; its progress was preserved. Continue using that file.')
    seed = root/'config/seeds'/f'{country}.json'
    if use_seed:
        if not seed.exists():
            raise ValueError(f'No shared seed found: {seed}')
        config = json.loads(seed.read_text())
    else:
        config = dict(country=country, variable='CPI', images={},
                      input_directory=f'data/{country}/screenshots', output_directory=f'output/{country}')
    config['config_role'] = 'working'
    if source is not None:
        config['input_directory'] = str(Path(source).expanduser().resolve())
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents two initializations from overwriting each other.
    with destination.open('x') as stream:
        json.dump(config, stream, indent=2)
        stream.write('\n')
    return destination


def publish_seed(country, names=None, all_images=False, root=ROOT):
    root = Path(root)
    country = country_code(country)
    config = load_working_config(root/'config'/f'{country}.json')
    if config['country'] != country:
        raise ValueError('Working config country does not match its filename.')
    if bool(names) == bool(all_images):
        raise ValueError('Specify selected --image filenames OR --all, not both.')
    selected = list(config['images']) if all_images else names
    if not selected:
        raise ValueError('No saved examples to publish.')
    seed = seed_config(config, selected)
    destination = root/'config/seeds'/f'{country}.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(seed, indent=2)+'\n')
    temporary.replace(destination)
    return destination
