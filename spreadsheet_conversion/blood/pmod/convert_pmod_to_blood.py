import pandas as pd
from pathlib import Path


class PmodToBlood:
    def __init__(
            self,
            whole_blood_activity: Path,
            parent_fraction: Path,
            plasma_activity: Path = None,
            blood_sampling_type: str = 'manual',
            output_name: str = '',
            output_json: bool = False,
            **kwargs):

        self.blood_series = {'whole_blood_activity': self.load_pmod_file(whole_blood_activity),
                             'parent_fraction': self.load_pmod_file(parent_fraction)}
        if parent_fraction:
            self.blood_series['plasma_activity'] = self.load_pmod_file(plasma_activity)

        # scale time to seconds
        self.scale_time()

        if output_name:
            self.output_name = Path(output_name)
        else:
            self.output_name = Path(whole_blood_activity).parent

    @staticmethod
    def load_pmod_file(pmod_blood_file: Path):
        if pmod_blood_file.is_file() and pmod_blood_file.exists():
            loaded_file = pd.read_excel(str(pmod_blood_file))
            return loaded_file
        else:
            raise FileNotFoundError(str(pmod_blood_file))

    def check_time_info(self):
        """
        Checks for time units, and time information between .bld files, number of rows and the values
        in the time index must be the same across each input .bld file. Additionally, renames time column
        to 'time' instead of what it's defined as in the pmod file.
        """
        # if there is only a single input do nothing, else go through each file. This shouldn't get reached
        # as whole_blood_activity and plasma_activity are required
        if len(self.blood_series) >= 2:
            row_lengths = {}
            for key, bld_data in self.blood_series.items():
                row_lengths[key] = len(bld_data)

            if len(set(row_lengths.values())) > 1:
                err_message = "PMOD blood files (.bld) must be of the same dimensions row-wise!\n"
                for key, value in row_lengths.items():
                    err_message += f"{key} file has {value} columns\n"

                err_message += "Check input files are valid."

                raise Exception(err_message)

        # lastly make sure the same time points exist across each input file/dataframe
        whole_blood_activity = self.blood_series.pop('whole_blood_activity')
        for key, dataframe in self.blood_series.items():
            try:
                assert whole_blood_activity['time'].equals(dataframe['time'])
            except AssertionError:
                raise AssertionError(f"Time(s) must have same values between input files, check time columns.")
        # if it all checks out put the whole blood activity back into our blood series object
        self.blood_series['whole_blood_activity'] = whole_blood_activity

    def scale_time(self):
        # scale time info to seconds if it's minutes
        time_scalar = 1.0
        for name, dataframe in self.blood_series.items():
            time_column_header_name = [header for header in dataframe.columns if 'sec' in str.lower(header)]
            if not time_column_header_name:
                time_column_header_name = [header for header in dataframe.columns if 'min' in str.lower(header)]
                time_scalar = 60.0

            if time_column_header_name and len(time_column_header_name) == 1:
                dataframe.rename(columns={time_column_header_name[0]: 'time'})
            else:
                raise Exception("Unable to locate time column in blood file, make sure input files are formatted "
                                "to include a single time column in minutes or seconds.")

            # scale the time column to seconds
            dataframe['time'] = dataframe['time']*time_scalar
            self.blood_series[name] = dataframe

