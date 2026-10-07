"""Review only numeric vertical-axis limits while preserving pixel calibration."""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import shutil
from PIL import Image
from .batch import run
from .core import validate_calibration, report_sort_key


def reviewed_limits(calibration):
    review = calibration.get('axis_limits_review', {})
    return bool(review.get('reviewed_at')) and all(
        review.get(key) == calibration.get(key)
        for key in ('y_min', 'y_max', 'plot_box', 'image_size'))


def backup_name(config_path):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    return config_path.parent/'backups'/f'{config_path.stem}.before_axis_review.{stamp}.json'


def save_axis_limits(config_path, filename, y_min, y_max, backup_path):
    low, high = float(y_min), float(y_max)
    if not math.isfinite(low) or not math.isfinite(high) or low >= high:
        raise ValueError('Enter finite numbers with Y minimum smaller than Y maximum.')
    # Reload at save time, so unrelated edits and chart records are preserved.
    config = json.loads(config_path.read_text())
    if filename not in config.get('images', {}):
        raise ValueError('This image has no saved calibration. Use calibrate.py first.')
    updated = dict(config['images'][filename])
    updated.update(y_min=low, y_max=high)
    validate_calibration(updated, tuple(updated['image_size']))
    updated['axis_limits_review'] = {
        'reviewed_at': datetime.now(timezone.utc).isoformat(),
        **{key: updated[key] for key in ('y_min','y_max','plot_box','image_size')},
    }
    if not backup_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_path, backup_path)
    config['images'][filename] = updated
    temporary = config_path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(config, indent=2)+'\n')
    temporary.replace(config_path)


def launch_axis_review(config_path, filename, *, position=None, backup_path=None, initial_limits=None, initial_source=None):
    import matplotlib.pyplot as plt
    from matplotlib.widgets import TextBox, Button
    config = json.loads(config_path.read_text())
    if Path(filename).name != filename or filename not in config.get('images', {}):
        raise ValueError('Select a filename with a saved calibration.')
    saved = config['images'][filename]
    initial = initial_limits if initial_limits is not None else saved
    source = Path(config['input_directory']).expanduser()/filename
    with Image.open(source) as image:
        image = image.convert('RGB')
    if list(image.size) != saved['image_size']:
        raise ValueError(f'{filename}: image dimensions changed; use full calibration.')
    backup_path = backup_path or backup_name(config_path)
    fig = plt.figure(figsize=(14,9))
    fig.canvas.manager.set_window_title(f'Review axis limits: {filename}')
    ax = fig.add_axes([.03,.13,.72,.81])
    ax.imshow(image)
    ax.set_axis_off()
    ax.set_title(filename + (f' — {position}' if position else ''))
    l,t,r,b = saved['plot_box']
    ax.plot([l,r,r,l,l],[t,t,b,b,t],'--',color='#00816f',lw=1)
    fig.text(.77,.93,'Review Y-axis limits',fontsize=14,weight='bold')
    fig.text(.77,.865,'Read the axis labels on the chart.\nEdit the two numbers below.\nNo cursor selections are needed.',fontsize=10,va='top')
    label = f'From previous saved chart:\n{initial_source}' if initial_source else "This chart's saved limits."
    fig.text(.77,.765,label,fontsize=10,va='top',color='#00816f')
    fields, buttons = {}, []
    status = fig.text(.035,.05,'Save confirms these limits, even when the numbers are already correct.',fontsize=10)
    for key,label,y in [('y_min','Y minimum',.66),('y_max','Y maximum',.53)]:
        fig.text(.77,y+.05,label,fontsize=12)
        fields[key] = TextBox(fig.add_axes([.81,y,.12,.045]),'',initial=f'{initial[key]:g}')
        for left,amount,text in [(.77,-1,'−'),(.94,1,'+')]:
            button = Button(fig.add_axes([left,y,.03,.045]),text)
            def change(event,k=key,delta=amount):
                try:
                    value=float(fields[k].text)+delta
                    if not math.isfinite(value):
                        raise ValueError('Enter a finite number.')
                    fields[k].set_val(f'{value:g}')
                except ValueError:
                    status.set_text('Enter a numeric axis limit, then use − / + to adjust by one.')
                    status.set_color('#a00000')
                fig.canvas.draw_idle()
            button.on_clicked(change)
            buttons.append(button)
    fig.text(.77,.44,f"Saved time range:\n{saved['x_start']} to {saved['x_end']}",fontsize=11,va='top')
    fig.text(.77,.34,'The box, dates and curve colour\nkeep their saved settings.',fontsize=10,va='top')
    outcome=['stopped']
    def save(event):
        try:
            save_axis_limits(config_path,filename,fields['y_min'].text,fields['y_max'].text,backup_path)
            outcome[0]='saved'
            plt.close(fig)
        except (ValueError,OSError) as exc:
            status.set_text(str(exc))
            status.set_color('#a00000')
            fig.canvas.draw_idle()
    def skip(event):
        outcome[0]='skipped'
        plt.close(fig)
    def stop(event):
        plt.close(fig)
    save_button=Button(fig.add_axes([.77,.21,.20,.055]),'Save and next' if position else 'Save and extract')
    skip_button=Button(fig.add_axes([.77,.125,.095,.05]),'Skip')
    stop_button=Button(fig.add_axes([.875,.125,.095,.05]),'Stop')
    save_button.on_clicked(save)
    skip_button.on_clicked(skip)
    stop_button.on_clicked(stop)
    buttons.extend([save_button,skip_button,stop_button])
    plt.show(block=True)
    if outcome[0]=='saved':
        run(config_path,images=[filename])
    return outcome[0]


def review_axis_queue(config_path, *, image=None, start_at=None, include_reviewed=False):
    config = json.loads(config_path.read_text())
    saved = config.get('images', {})
    names = sorted(saved, key=report_sort_key)
    if image:
        if image not in saved:
            raise ValueError(f'No saved calibration for {image}')
        pending=[image]
    else:
        if start_at:
            if start_at not in names:
                raise ValueError(f'No saved calibration for {start_at}')
            names=names[names.index(start_at):]
        pending=[name for name in names if include_reviewed or not reviewed_limits(saved[name])]
    if not pending:
        print('No saved charts need axis-limit review. Use --include-reviewed to revisit them.')
        return
    # Review timestamps let older sessions participate without requiring new
    # progress keys. Explicit single-chart reviews retain that chart's limits.
    reviewed = [name for name, spec in saved.items() if reviewed_limits(spec)]
    previous = max(reviewed, key=lambda name: saved[name]['axis_limits_review']['reviewed_at']) if reviewed and not image else None
    initial_limits = {key: saved[previous][key] for key in ('y_min','y_max')} if previous else None
    backup = backup_name(config_path)
    completed=0
    try:
        for index,name in enumerate(pending,1):
            print(f'Axis limits [{index}/{len(pending)}]: {name}',flush=True)
            outcome=launch_axis_review(config_path,name,
                                      position=f'{index} of {len(pending)} to review',backup_path=backup,
                                      initial_limits=initial_limits,initial_source=previous)
            if outcome=='saved':
                completed+=1
                # Only confirmed values carry forward; Skip/Stop cannot make
                # unsaved edits the next chart's defaults.
                latest = json.loads(config_path.read_text())['images'][name]
                initial_limits = {key: latest[key] for key in ('y_min','y_max')}
                previous = name
            elif outcome=='stopped':
                break
    finally:
        # Saving each chart already persists its values and individual outputs.
        # Refresh the full combined tables when this session has made changes.
        if completed or backup.exists():
            print('Rebuilding combined results for all saved charts...',flush=True)
            run(config_path,known_only=True)
    print(f'Axis review finished: {completed} charts saved. Restart to resume unreviewed charts.',flush=True)
