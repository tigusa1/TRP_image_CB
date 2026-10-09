"""Create an empty private working config, once per country and checkout."""
import argparse
from inflation_digitizer.configuration import initialize_country


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('country', help='Three-letter country code, e.g. PER')
    parser.add_argument('--input', help='Local screenshot folder; default: data/COUNTRY/screenshots')
    parser.add_argument('--use-seed', action='store_true', help='Optionally copy existing shared examples instead of starting empty')
    args=parser.parse_args()
    try:
        path=initialize_country(args.country,args.input,use_seed=args.use_seed)
    except (ValueError,OSError) as exc:
        parser.exit(1,str(exc)+'\n')
    detail = 'Shared examples copied.' if args.use_seed else 'No screenshots calibrated yet.'
    print(f'Created {path}. {detail} Future pulls will not overwrite this file.')
    print(f'Run: python calibrate.py --config config/{args.country.upper()}.json')


if __name__=='__main__':
    main()
