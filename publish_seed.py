"""Supervisor: replace a shared seed with selected saved calibration examples."""
import argparse
from inflation_digitizer.configuration import publish_seed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('country')
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--image',action='append',help='Exact PNG filename; repeat for more examples')
    group.add_argument('--all',action='store_true',help='Include every saved calibration')
    args=parser.parse_args()
    try:
        path=publish_seed(args.country,args.image,args.all)
    except (ValueError,OSError) as exc:
        parser.exit(1,str(exc)+'\n')
    print(f'Updated {path}. Review its diff, then commit and push it. Existing working configs were not changed.')


if __name__=='__main__':
    main()
