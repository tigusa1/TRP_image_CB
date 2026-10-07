import tempfile
import unittest
from pathlib import Path
import pandas as pd
from inflation_digitizer.forecast_export import COLUMNS, convert_frame, export_csv_files


class ForecastExportTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({
            'country':['COL']*4,
            'vintage':['2021Q4']*4,
            'quarter':['2022Q2','2021Q4','2020Q3','2022Q1'],
            'inflation_pct_yoy':[5.6,4.0,2.1,6.23],
            'series':['forecast_band_midpoint','historical','historical','forecast_band_midpoint'],
        })

    def test_exact_schema_signed_horizons_and_value_preservation(self):
        result=convert_frame(self.frame())
        self.assertEqual(list(result.columns),COLUMNS)
        self.assertEqual(result.target.tolist(),['2020Q3','2021Q4','2022Q1','2022Q2'])
        self.assertEqual(result.h.tolist(),[-5,0,1,2])
        self.assertEqual(result.forecast.tolist(),[2.1,4.0,6.23,5.6])
        self.assertEqual(result.variable.tolist(),['CPI']*4)
        self.assertEqual(result.h.dtype.kind,'i')

    def test_missing_estimates_remain_blank_not_zero(self):
        frame=self.frame();frame.loc[0,'inflation_pct_yoy']=None
        result=convert_frame(frame)
        self.assertEqual(len(result),4)
        self.assertTrue(pd.isna(result.loc[result.target=='2022Q2','forecast'].iloc[0]))

    def test_invalid_dates_and_duplicate_keys_are_rejected(self):
        frame=self.frame();frame.loc[0,'quarter']='2022Q5'
        with self.assertRaisesRegex(ValueError,'Invalid report or target'):
            convert_frame(frame)
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            convert_frame(pd.concat([self.frame(),self.frame()],ignore_index=True))

    def test_all_per_report_files_are_combined_without_dropping_repeated_targets(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'tables';source.mkdir()
            self.frame().to_csv(source/'a.csv',index=False)
            second=self.frame();second['vintage']='2022Q1';second.to_csv(source/'b.csv',index=False)
            result=export_csv_files(source,root/'forecasts.csv',per_report_directory=root/'formatted')
            self.assertEqual(len(result),8)
            self.assertEqual(len(list((root/'formatted').glob('*.csv'))),2)
            saved=pd.read_csv(root/'forecasts.csv')
            self.assertEqual(list(saved.columns),COLUMNS)
            self.assertEqual(sorted(saved.report.unique()),['2021Q4','2022Q1'])
            self.assertEqual(len(pd.read_csv(source/'a.csv')),4)
            self.assertEqual((root/'forecasts.csv').read_text().splitlines()[0],','.join(COLUMNS))

    def test_empty_input_with_headers_has_exact_output_headers(self):
        result=convert_frame(self.frame().iloc[:0])
        self.assertEqual(list(result.columns),COLUMNS)
        self.assertEqual(len(result),0)

if __name__=='__main__':unittest.main()
