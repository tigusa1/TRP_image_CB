"""Run this file in PyCharm to review only Y minimum and Y maximum."""
import argparse
from pathlib import Path
import sys
from inflation_digitizer.batch import DEFAULT_CONFIG
from inflation_digitizer.axis_review import review_axis_queue


def main():
    parser=argparse.ArgumentParser(description='Review saved Y-axis limits without reselecting any points.')
    parser.add_argument('--config',type=Path,default=DEFAULT_CONFIG)
    parser.add_argument('--image',help='Review one saved image, even if already reviewed')
    parser.add_argument('--start-at',help='Start at this saved filename')
    parser.add_argument('--include-reviewed',action='store_true',help='Also revisit previously confirmed limits')
    args=parser.parse_args()
    if args.image and args.start_at:
        parser.error('Use --image or --start-at, not both')
    try:
        from inflation_digitizer.desktop import configure_desktop_backend
        configure_desktop_backend()
        review_axis_queue(args.config.resolve(),image=args.image,start_at=args.start_at,
                          include_reviewed=args.include_reviewed)
        return 0
    except (ValueError,OSError,RuntimeError) as exc:
        print(f'Cannot review axis limits: {exc}',file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Stopped. Earlier confirmed axis limits remain saved.')
        return 130

if __name__=='__main__':
    raise SystemExit(main())
