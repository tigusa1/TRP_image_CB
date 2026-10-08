"""Interactive per-image calibration. Run in a desktop PyCharm session."""
from __future__ import annotations
import argparse
import json
from inflation_digitizer.configuration import load_working_config, input_directory
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from inflation_digitizer.batch import DEFAULT_CONFIG, discover, run
from inflation_digitizer.core import quarter_number, quarter_label, validate_calibration, report_sort_key
from inflation_digitizer.plot_box import detect_plot_box


def launch(config_path, filename, template=None, *, queue_position=None, advance_end=False):
    import matplotlib.pyplot as plt
    from matplotlib.widgets import TextBox, Button
    config = load_working_config(config_path)
    if Path(filename).name != filename:
        raise ValueError('Use a filename, not a full path, for --image')
    path = input_directory(config)/filename
    im = Image.open(path).convert('RGB')
    pixels = np.asarray(im)
    w, h = im.size
    saved = config.get('images', {}).get(filename)
    seed = dict(config.get('calibration_defaults', {}))
    seed.update(config.get('images', {}).get(template, {}))
    seed.update(config.get('image_defaults', {}).get(filename, {}))
    seed.update(saved or {})
    if template and template not in config.get('images', {}):
        raise ValueError(f'Template {template!r} is not in this config')
    advanced = bool(advance_end and not saved and seed.get('x_end'))
    if advanced:
        seed['x_end'] = quarter_label(quarter_number(seed['x_end']) + 1)
    suggested = (list(saved['plot_box']) if saved and saved.get('image_size') == [w,h]
                 and saved.get('plot_box') else detect_plot_box(im, allow_open_axes=seed.get('plot_box_style') == 'open_axes'))
    fig = plt.figure(figsize=(14, 9))
    fig.canvas.manager.set_window_title(f'Calibrate {filename}')
    ax = fig.add_axes([0.035, 0.15, 0.71, 0.79])
    ax.imshow(im)
    ax.set_title(filename if queue_position is None else f'{filename} — {queue_position}')
    ax.set_axis_off()
    fig.text(0.76, 0.94, 'Enter axis values, then click:', fontsize=11, weight='bold')
    instruction = fig.text(0.76, 0.89, '1. Plot TOP LEFT corner', fontsize=11, color='#00816f')
    fig.text(0.76, 0.84, 'Accept the orange box, or\ncorrect its corners below.', fontsize=10, va='top')
    fields = {}
    quarter_buttons = []  # Keep widget objects alive for their callbacks.
    for i, (key, label, default) in enumerate([
        ('x_start', 'First quarter', '2022Q1'),
        ('x_end', 'Last quarter', '2027Q3'),
        ('y_min', 'Y minimum', '-4'), ('y_max', 'Y maximum', '10'),
        ('color_tolerance', 'Colour tolerance', '22'),
    ]):
        y = 0.68-i*0.09
        fig.text(0.77, y+0.042, label + (' (+1 quarter)' if key == 'x_end' and advanced else ''), fontsize=10)
        is_quarter = key in ('x_start', 'x_end')
        is_axis_limit = key in ('y_min', 'y_max')
        bounds = [0.81, y, 0.12, 0.038] if is_quarter or is_axis_limit else [0.77, y, 0.20, 0.038]
        fields[key] = TextBox(fig.add_axes(bounds), '', initial=str(seed.get(key, default)))
        if is_quarter or is_axis_limit:
            for left, delta, label in [(0.77, -1, '◀'), (0.94, 1, '▶')]:
                button = Button(fig.add_axes([left, y, 0.03, 0.038]), label if is_quarter else ('−' if delta < 0 else '+'))
                def increment(event, field=key, amount=delta):
                    try:
                        if field in ('y_min', 'y_max'):
                            value = float(fields[field].text) + amount
                            if not np.isfinite(value):
                                raise ValueError('Enter a finite Y-axis value.')
                            fields[field].set_val(f'{value:g}')
                            fig.canvas.draw_idle()
                            return
                        value = quarter_number(fields[field].text) + amount
                        if not 4000 <= value <= 39999:
                            raise ValueError('Quarter must use a four-digit year.')
                        fields[field].set_val(quarter_label(value))
                    except ValueError as exc:
                        note.set_text(str(exc))
                        note.set_color('#a00000')
                    fig.canvas.draw_idle()
                button.on_clicked(increment)
                quarter_buttons.append(button)
    note = fig.text(0.04, 0.05, 'Accept the box or select two corners; then select the historical endpoint and darkest band.', fontsize=10)
    picks, markers = [], []
    adjustment = [None]
    proposal, = ax.plot([], [], '--o', color='#e69500', lw=1.5, ms=5, visible=False)
    def show_proposal():
        if suggested is not None:
            l,t,r,b = suggested
            proposal.set_data([l,r,r,l,l], [t,t,b,b,t])
            proposal.set_visible(True)
        accept_button.set_active(suggested is not None)
        accept_button.ax.set_alpha(1 if suggested is not None else .4)

    def show_selected_box():
        (l,t),(r,b) = picks[:2]
        markers.extend(ax.plot([l,r,r,l,l], [t,t,b,b,t], '--', color='#00816f', lw=1))
        quarter_readout.set_text('Hover over the endpoint.')
        note.set_text('The vertical guide snaps to quarters. Click the final historical point to select its quarter.')
        instruction.set_text('3. LAST HISTORICAL point')

    # Span the whole displayed image, including the printed quarter labels.
    quarter_guide = ax.axvline(0, color='#d60078', linestyle='--', lw=1,
                              visible=False, zorder=5)
    quarter_readout = fig.text(0.77, 0.225, '', fontsize=11, color='#d60078')

    # A white outline keeps the moving crosshairs visible over dark fan bands.
    import matplotlib.patheffects as path_effects
    crosshair_style = dict(color='black', lw=.8, visible=False, zorder=10,
                           path_effects=[path_effects.withStroke(linewidth=2, foreground='white')])
    cursor_x = ax.axvline(0, gid='cursor-crosshair-x', **crosshair_style)
    cursor_y = ax.axhline(0, gid='cursor-crosshair-y', **crosshair_style)

    def hide_crosshairs():
        cursor_x.set_visible(False)
        cursor_y.set_visible(False)

    def nearest_quarter(x):
        (l, t), (r, b) = picks[:2]
        start = quarter_number(fields['x_start'].text)
        end = quarter_number(fields['x_end'].text)
        if r <= l or b <= t or end <= start:
            raise ValueError('Check plot corners and first/last quarters.')
        q = max(start, min(end, round(start + (x-l)*(end-start)/(r-l))))
        return l + (r-l)*(q-start)/(end-start), quarter_label(q)

    def guide_at(x, selected=False):
        try:
            snapped_x, label = nearest_quarter(x)
        except ValueError:
            quarter_guide.set_visible(False)
            quarter_readout.set_text('Check the axis values.')
            return None
        quarter_guide.set_xdata([snapped_x, snapped_x])
        quarter_guide.set_visible(True)
        quarter_readout.set_text(('Selected: ' if selected else 'Quarter: ') + label)
        return snapped_x

    def move(event):
        x, y = getattr(event, 'xdata', None), getattr(event, 'ydata', None)
        on_image = (getattr(event, 'inaxes', None) == ax and
                    x is not None and y is not None and
                    not getattr(fig.canvas.manager.toolbar, 'mode', ''))
        if on_image and len(picks) < 4:
            cursor_x.set_xdata([x, x])
            cursor_y.set_ydata([y, y])
            cursor_x.set_visible(True)
            cursor_y.set_visible(True)
        else:
            hide_crosshairs()
        if len(picks) == 2:
            if on_image and picks[0][0] <= x <= picks[1][0]:
                guide_at(x)
            else:
                quarter_guide.set_visible(False)
                quarter_readout.set_text('Hover over the endpoint.')
        fig.canvas.draw_idle()

    def leave(event):
        hide_crosshairs()
        if len(picks) == 2:
            quarter_guide.set_visible(False)
            quarter_readout.set_text('Hover over the endpoint.')
        fig.canvas.draw_idle()

    def refresh_guide(text):
        if len(picks) >= 3:
            guide_at(picks[2][0], selected=True)
        elif len(picks) == 2:
            quarter_guide.set_visible(False)
            quarter_readout.set_text('Hover over the endpoint.')
        fig.canvas.draw_idle()

    for key in ('x_start', 'x_end'):
        fields[key].on_text_change(refresh_guide)
    hints = ['1. Plot TOP LEFT corner', '2. Plot BOTTOM RIGHT corner',
             '3. LAST HISTORICAL point', '4. INSIDE darkest forecast band', 'Ready: save calibration']
    def click(event):
        if event.inaxes != ax or event.button != 1 or len(picks) >= 4:
            return
        if getattr(fig.canvas.manager.toolbar, 'mode', ''):
            return
        x, y = event.xdata, event.ydata
        if adjustment[0] is not None:
            offset = adjustment[0] * 2
            suggested[offset:offset+2] = [x,y]
            adjustment[0] = None
            show_proposal()
            instruction.set_text('Review corrected box')
            note.set_text('Click Accept box if the orange rectangle follows the plot axes.')
            fig.canvas.draw_idle()
            return
        if len(picks) == 0:
            proposal.set_visible(False)
            accept_button.set_active(False)
            accept_button.ax.set_alpha(.4)
        if len(picks) == 2:
            (l, t), (r, b) = picks
            if not l <= x <= r or not t <= y <= b:
                note.set_text('Click the historical endpoint inside the plot.')
                fig.canvas.draw_idle()
                return
            x = guide_at(x, selected=True)
            if x is None:
                fig.canvas.draw_idle()
                return
        picks.append((x, y))
        markers.extend(ax.plot(x, y, 'o', ms=7, mfc='none', mec='#d60078', mew=2))
        instruction.set_text(hints[len(picks)])
        if len(picks) == 4:
            hide_crosshairs()
        if len(picks) == 2:
            show_selected_box()
        fig.canvas.draw_idle()
    def reset(event):
        hide_crosshairs()
        picks.clear()
        adjustment[0] = None
        quarter_guide.set_visible(False)
        quarter_readout.set_text('')
        note.set_text('Accept the box or select two corners; then select the historical endpoint and darkest band.')
        note.set_color('black')
        for marker in markers:
            marker.remove()
        markers.clear()
        show_proposal()
        instruction.set_text('Review suggested box' if suggested is not None else hints[0])
        fig.canvas.draw_idle()

    def accept_box(event):
        if suggested is None:
            return
        l,t,r,b = suggested
        if not (0 <= l < r < w and 0 <= t < b < h):
            note.set_text('Correct the corners: top left must be above and left of bottom right.')
            fig.canvas.draw_idle()
            return
        reset(None)
        picks.extend([(l,t),(r,b)])
        proposal.set_visible(False)
        accept_button.set_active(False)
        accept_button.ax.set_alpha(.4)
        show_selected_box()
        fig.canvas.draw_idle()

    def adjust_corner(index):
        if suggested is None:
            return
        reset(None)
        adjustment[0] = index
        instruction.set_text('Click TOP LEFT correction' if index == 0 else 'Click BOTTOM RIGHT correction')
        note.set_text('Click the corrected corner; then accept the updated orange rectangle.')
        fig.canvas.draw_idle()

    outcome = ['stopped']
    def save(event):
        try:
            if len(picks) != 4:
                raise ValueError('Accept or select the box, then click the historical endpoint and darkest band.')
            (l,t),(r,b),(hx,hy),(cx,cy) = picks
            start, end = (quarter_number(fields['x_start'].text),quarter_number(fields['x_end'].text))
            if r <= l or b <= t:
                raise ValueError('Select top left, then bottom right in that order.')
            if not l <= hx <= r or not t <= hy <= b:
                raise ValueError('The historical endpoint must be inside the plot.')
            if not l <= cx <= r or not t <= cy <= b:
                raise ValueError('The colour sample must be inside the plot.')
            hist = round(start+(hx-l)*(end-start)/(r-l))
            # Use the actual selected pixel so a very narrow band is not
            # replaced by the majority colour of a surrounding square.
            color = pixels[min(h-1, max(0, round(cy))), min(w-1, max(0, round(cx)))].tolist()
            if max(color)-min(color) < 20:
                raise ValueError('Selected colour is nearly grey. Click inside the coloured darkest band, away from grid lines.')
            c = dict(image_size=[w,h], plot_box=[round(v,2) for v in (l,t,r,b)],
                     y_min=float(fields['y_min'].text), y_max=float(fields['y_max'].text),
                     x_start=quarter_label(start), x_end=quarter_label(end), last_historical=quarter_label(hist),
                     curve_rgb=color, color_tolerance=float(fields['color_tolerance'].text),
                     review_status='manually_calibrated', notes='Review generated overlay before changing review_status to reviewed.')
            for key in ('historical_rgb', 'historical_color_tolerance', 'plot_box_style', 'ignore_regions'):
                if key in seed:
                    c[key] = seed[key]
            validate_calibration(c, (w,h))
            latest_config = load_working_config(config_path)
            if filename in latest_config.get('images', {}):
                backup = config_path.with_suffix('.json.bak')
                backup.write_text(config_path.read_text())
            latest_config.setdefault('images', {})[filename] = c
            latest_config['last_calibrated_image'] = filename
            temporary = config_path.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(latest_config, indent=2)+'\n')
            temporary.replace(config_path)
            outcome[0] = 'saved'
            plt.close(fig)
        except (ValueError, OSError) as exc:
            note.set_text(str(exc))
            note.set_color('#a00000')
            fig.canvas.draw_idle()
    accept_button = Button(fig.add_axes([0.77,0.755,0.20,0.04]), 'Accept box')
    accept_button.on_clicked(accept_box)
    corner_buttons = []
    for index, label in enumerate(('Adjust top left', 'Adjust bottom right')):
        button = Button(fig.add_axes([0.04+index*.19,0.095,0.18,0.04]), label)
        button.on_clicked(lambda event, i=index: adjust_corner(i))
        button.set_active(suggested is not None)
        button.ax.set_alpha(1 if suggested is not None else .4)
        corner_buttons.append(button)
    show_proposal()
    if suggested is not None:
        instruction.set_text('Review suggested box')
    else:
        note.set_text('No clear plot box detected. Click the top-left and bottom-right corners.')
    reset_button = Button(fig.add_axes([0.77,0.14,0.20,0.05]), 'Reset clicks')
    save_button = Button(fig.add_axes([0.77,0.075,0.20,0.05]),
                         'Save and next' if queue_position is not None else 'Save and extract')
    navigation_buttons = []
    if queue_position is not None:
        def skip(event):
            outcome[0] = 'skipped'
            plt.close(fig)
        def stop(event):
            plt.close(fig)
        skip_button = Button(fig.add_axes([0.77,0.015,0.095,0.04]), 'Skip')
        stop_button = Button(fig.add_axes([0.875,0.015,0.095,0.04]), 'Stop')
        skip_button.on_clicked(skip)
        stop_button.on_clicked(stop)
        navigation_buttons.extend([skip_button, stop_button])
    reset_button.on_clicked(reset)
    save_button.on_clicked(save)
    fig.canvas.mpl_connect('button_press_event', click)
    fig.canvas.mpl_connect('motion_notify_event', move)
    fig.canvas.mpl_connect('figure_leave_event', leave)
    fig.canvas.mpl_connect('axes_leave_event', leave)
    plt.show(block=True)
    if outcome[0] == 'saved':
        run(config_path, images=[filename])
    elif outcome[0] == 'skipped':
        print(f'Skipped for this session: {filename}')
    else:
        print('Closed without saving the current image. Earlier calibrations are retained.')
    return outcome[0]


def launch_queue(config_path, template=None, start_at=None, include_calibrated=False):
    """Process remaining images in filename order; save each result immediately."""
    config = load_working_config(config_path)
    names = discover(input_directory(config),
                     config.get('directory_timeout_seconds', 20))
    if not names:
        raise ValueError('No PNG files found in the configured input folder.')
    if config.get('calibration_end_before'):
        cutoff = config['calibration_end_before']
        names = [name for name in names if report_sort_key(name) < report_sort_key(cutoff)]
        print(f'Queue limited to reports before {cutoff}: see configuration notes.', flush=True)
    if start_at:
        if start_at not in names:
            raise ValueError(f'Start image not found in folder: {start_at}')
        names = names[names.index(start_at):]
    known = config.get('images', {})
    if template and template not in known:
        raise ValueError(f'Template {template!r} is not in this config')
    pending = [name for name in names if include_calibrated or name not in known]
    if not pending:
        print('All images in this range already have saved calibrations. Use --include-calibrated to revisit them.')
        return
    # Resume with the most recently completed image when possible. For the
    # first session, choose the closest preceding calibrated filename.
    previous = template or config.get('last_calibrated_image')
    if previous not in known:
        before = [name for name in sorted(known, key=report_sort_key) if report_sort_key(name) < report_sort_key(pending[0])]
        previous = before[-1] if before else next(iter(sorted(known, key=report_sort_key)), None)
    print(f'Calibration queue: {len(pending)} images. Save and next advances; closing the window stops.', flush=True)
    completed = 0
    try:
        for index, name in enumerate(pending, 1):
            print(f'[{index}/{len(pending)}] {name}; template: {previous or "defaults"}', flush=True)
            result = launch(config_path, name, previous,
                            queue_position=f'{index} of {len(pending)} remaining',
                            advance_end=bool(previous and report_sort_key(name) > report_sort_key(previous)))
            if result == 'saved':
                previous = name
                completed += 1
            elif result == 'stopped':
                break
    finally:
        # Individual artifacts are saved after every completion; refresh the
        # combined report for all saved charts when stopping or finishing.
        current = load_working_config(config_path)
        if current.get('images'):
            print('Refreshing combined results for all saved calibrations...', flush=True)
            run(config_path, known_only=True)
    print(f'Session finished: {completed} calibrations saved. Run again to resume unsaved images.', flush=True)


def main():
    parser = argparse.ArgumentParser(description='Calibrate a folder continuously, or one selected image.')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--image', help='Calibrate just this PNG filename instead of the folder queue')
    parser.add_argument('--template', help='Existing calibration to prefill the first chart')
    parser.add_argument('--start-at', help='Start the queue at this filename')
    parser.add_argument('--include-calibrated', action='store_true', help='Also revisit already saved calibrations')
    args = parser.parse_args()
    if args.image and (args.start_at or args.include_calibrated):
        parser.error('--start-at and --include-calibrated apply to folder mode, not --image')
    try:
        from inflation_digitizer.desktop import configure_desktop_backend
        configure_desktop_backend()
        if args.image:
            launch(args.config.resolve(), args.image, args.template)
        else:
            launch_queue(args.config.resolve(), args.template, args.start_at, args.include_calibrated)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'Cannot calibrate: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Stopped. Completed calibrations have been saved.')
        return 130
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
