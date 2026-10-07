import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from matplotlib.widgets import TextBox
from PIL import Image
from inflation_digitizer import axis_review


class AxisReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.path=self.root/'config.json'
        self.name='TST_2025_Q1.png'
        self.spec=dict(image_size=[140,140],plot_box=[20,20,120,120],
                       x_start='2024Q1',x_end='2026Q1',last_historical='2024Q4',
                       y_min=-1,y_max=4,curve_rgb=[35,68,134],color_tolerance=22,
                       review_status='manually_calibrated',notes='Preserve my notes')
        self.config=dict(country='TST',input_directory=str(self.root),
                         output_directory=str(self.root/'out'),images={self.name:self.spec},
                         last_calibrated_image=self.name)
        self.path.write_text(json.dumps(self.config))
        self.backup=self.root/'backups/session.json'
        Image.new('RGB',(140,140),'white').save(self.root/self.name)

    def tearDown(self):
        plt.close('all')
        self.temp.cleanup()

    def test_save_changes_only_limits_and_review_metadata_and_keeps_initial_backup(self):
        original=self.path.read_text()
        axis_review.save_axis_limits(self.path,self.name,-4,10,self.backup)
        updated=json.loads(self.path.read_text())
        actual=updated['images'][self.name]
        self.assertTrue(axis_review.reviewed_limits(actual))
        self.assertEqual(actual['y_min'],-4)
        self.assertEqual(actual['y_max'],10)
        for key,value in self.spec.items():
            if key not in ('y_min','y_max'):
                self.assertEqual(actual[key],value)
        self.assertEqual(updated['last_calibrated_image'],self.name)
        self.assertEqual(self.backup.read_text(),original)
        axis_review.save_axis_limits(self.path,self.name,-5,9,self.backup)
        self.assertEqual(self.backup.read_text(),original)

    def test_invalid_limits_do_not_save(self):
        original=self.path.read_text()
        for low,high in [(4,4),(5,4),(float('nan'),10),(-4,float('inf'))]:
            with self.assertRaises(ValueError):
                axis_review.save_axis_limits(self.path,self.name,low,high,self.backup)
            self.assertEqual(self.path.read_text(),original)
        self.assertFalse(self.backup.exists())

    def test_changed_box_or_limits_invalidates_confirmation(self):
        axis_review.save_axis_limits(self.path,self.name,-4,10,self.backup)
        saved=json.loads(self.path.read_text())['images'][self.name]
        for key,value in [('y_min',-5),('plot_box',[21,20,120,120]),('image_size',[150,140])]:
            changed=copy.deepcopy(saved);changed[key]=value
            self.assertFalse(axis_review.reviewed_limits(changed))

    def test_resume_skips_reviewed_and_stop_does_not_confirm_unfinished_image(self):
        second='TST_2025_Q2.png'
        self.config['images'][second]=copy.deepcopy(self.spec)
        self.path.write_text(json.dumps(self.config))
        axis_review.save_axis_limits(self.path,self.name,-1,4,self.backup)
        with patch.object(axis_review,'launch_axis_review',return_value='stopped') as launch, \
             patch.object(axis_review,'run') as run:
            axis_review.review_axis_queue(self.path)
        self.assertEqual(launch.call_count,1)
        self.assertEqual(launch.call_args.args[1],second)
        self.assertEqual(launch.call_args.kwargs['initial_limits'],{'y_min':-1,'y_max':4})
        self.assertEqual(launch.call_args.kwargs['initial_source'],self.name)
        self.assertFalse(axis_review.reviewed_limits(json.loads(self.path.read_text())['images'][second]))
        run.assert_not_called()

    def test_include_reviewed_can_revisit_confirmed_chart(self):
        axis_review.save_axis_limits(self.path,self.name,-1,4,self.backup)
        with patch.object(axis_review,'launch_axis_review',return_value='stopped') as launch:
            axis_review.review_axis_queue(self.path,include_reviewed=True)
        self.assertEqual(launch.call_args.args[1],self.name)

    def test_ui_saves_without_any_plot_clicks(self):
        fields=[]
        def field(*args,**kwargs):
            widget=TextBox(*args,**kwargs);fields.append(widget);return widget
        def interact(*args,**kwargs):
            self.assertEqual(len(fields),2)
            fig=plt.gcf();fig.canvas.draw()
            fields[0].set_val('-4');fields[1].set_val('10')
            target=next(a for a in fig.axes if any(t.get_text()=='Save and next' for t in a.texts))
            sx,sy=target.transAxes.transform((.5,.5))
            for kind in ('button_press_event','button_release_event'):
                fig.canvas.callbacks.process(kind,MouseEvent(kind,fig.canvas,sx,sy,button=1))
        with patch('matplotlib.widgets.TextBox',side_effect=field), \
             patch.object(plt,'show',side_effect=interact), \
             patch.object(axis_review,'run') as run:
            outcome=axis_review.launch_axis_review(self.path,self.name,position='1 of 2',backup_path=self.backup)
        self.assertEqual(outcome,'saved')
        saved=json.loads(self.path.read_text())['images'][self.name]
        self.assertEqual(saved['y_min'],-4)
        self.assertEqual(saved['y_max'],10)
        self.assertEqual(saved['plot_box'],self.spec['plot_box'])
        run.assert_called_once_with(self.path,images=[self.name])

    def test_saved_limits_carry_forward_and_skips_keep_last_saved_template(self):
        second,third='TST_2025_Q2.png','TST_2025_Q3.png'
        for name in (second,third):
            self.config['images'][name]=copy.deepcopy(self.spec)
        self.path.write_text(json.dumps(self.config))
        def review(config_path,filename,**kwargs):
            if filename==self.name:
                self.assertIsNone(kwargs['initial_limits'])
                axis_review.save_axis_limits(config_path,filename,-4,10,kwargs['backup_path'])
                return 'saved'
            self.assertEqual(kwargs['initial_limits'],{'y_min':-4,'y_max':10})
            self.assertEqual(kwargs['initial_source'],self.name)
            return 'skipped' if filename==second else 'stopped'
        with patch.object(axis_review,'launch_axis_review',side_effect=review) as launch, \
             patch.object(axis_review,'run'):
            axis_review.review_axis_queue(self.path)
        self.assertEqual(launch.call_count,3)

    def test_inherited_defaults_are_displayed_without_saving_on_close(self):
        fields=[]
        def field(*args,**kwargs):
            widget=TextBox(*args,**kwargs);fields.append(widget);return widget
        original=self.path.read_text()
        def interact(*args,**kwargs):
            self.assertEqual([f.text for f in fields],['-4','10'])
            self.assertTrue(any('TST_2024_Q4.png' in t.get_text() for t in plt.gcf().texts))
            plt.close('all')
        with patch('matplotlib.widgets.TextBox',side_effect=field), \
             patch.object(plt,'show',side_effect=interact), patch.object(axis_review,'run') as run:
            result=axis_review.launch_axis_review(self.path,self.name,
                     initial_limits={'y_min':-4,'y_max':10},initial_source='TST_2024_Q4.png')
        self.assertEqual(result,'stopped')
        self.assertEqual(self.path.read_text(),original)
        run.assert_not_called()

if __name__=='__main__':unittest.main()
