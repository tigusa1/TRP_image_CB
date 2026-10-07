import unittest
from PIL import Image, ImageDraw
from inflation_digitizer.plot_box import detect_plot_box

class PlotBoxTests(unittest.TestCase):
    def test_axes_selected_instead_of_decorative_border_or_grid(self):
        im=Image.new('RGB',(300,220),'white');d=ImageDraw.Draw(im)
        d.rectangle((4,4,295,215),outline=(30,150,220),width=2)
        d.rectangle((35,45,265,180),outline=(110,110,110))
        d.line((35,120,265,120),fill=(110,110,110))
        # A coloured curve hides a few pixels of the lower frame.
        d.line((100,178,104,182),fill=(35,68,134),width=2)
        box=detect_plot_box(im)
        self.assertIsNotNone(box)
        for value,expected in zip(box,[35,45,265,180]):
            self.assertAlmostEqual(value,expected,delta=1)

    def test_open_axes_are_detected_only_when_enabled(self):
        im=Image.new('RGB',(300,220),'white');d=ImageDraw.Draw(im)
        d.line((35,45,35,180),fill='black',width=2)
        d.line((35,180,265,180),fill='black',width=2)
        self.assertIsNone(detect_plot_box(im))
        box=detect_plot_box(im,allow_open_axes=True)
        self.assertIsNotNone(box)
        for value,expected in zip(box,[35,45,265,180]):
            self.assertAlmostEqual(value,expected,delta=2)

    def test_no_rectangle_returns_no_suggestion(self):
        im=Image.new('RGB',(300,220),'white');d=ImageDraw.Draw(im)
        d.line((35,45,265,45),fill='black')
        d.line((35,180,265,180),fill='black')
        self.assertIsNone(detect_plot_box(im))

if __name__=='__main__':unittest.main()
