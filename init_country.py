"""Create a private working config from a shared country seed, once per checkout."""
import argparse
from inflation_digitizer.configuration import initialize_country


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('country', help='Three-letter country code, e.g. PER')
    parser.add_argument('--input', help='Local screenshot folder; default: data/COUNTRY/screenshots')
    args=parser.parse_args()
    try:
        path=initialize_country(args.country,args.input)
    except (ValueError,OSError) as exc:
        parser.exit(1,str(exc)+'\n')
    print(f'Created {path}. Shared seed examples were copied; future pulls will not overwrite this file.')
    print(f'Run: python calibrate.py --config config/{args.country.upper()}.json')


if __name__=='__main__':
    main()
