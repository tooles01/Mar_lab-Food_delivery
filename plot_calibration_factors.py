'''
plot_calibration_factors.py


Plotting calibration datafiles
Each file is the recordings of a single weight (10g, 50g,100g) with different calibration factors


Plot these to see if 
a) the same calibration factor works best for all different weights
b) later: run this again to see if anything has changed over time (hopefully not)


Requirements
    matplotlib
    numpy


ST 2026
'''


import csv, os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

# Turn interactive mode on
plt.ion()

weights = [10, 50, 100, 110]

# Files to import and plot
files = []

'''
# 2026-10-12 test01
files.append('2026-10-12_10g_test01')
files.append('2026-10-12_50g_test01')
files.append('2026-10-12_100g_test01')
files.append('2026-10-12_110g_test01')
'''

'''
# 2026-10-12 test02
files.append('2026-10-12_10g_test02')
files.append('2026-10-12_50g_test02')
files.append('2026-10-12_100g_test02')
files.append('2026-10-12_110g_test02')
'''

'''
# 2026-10-12 test03
files.append('2026-10-12_10g_test03')
files.append('2026-10-12_50g_test03')
files.append('2026-10-12_100g_test03')
files.append('2026-10-12_110g_test03')
'''

'''
# 2026-10-15 test01
files.append('2026-10-15_10g_test01')
files.append('2026-10-15_50g_test01')
files.append('2026-10-15_100g_test01')
files.append('2026-10-15_110g_test01')
'''

# 2026-10-19_test01
files.append('2026-10-19_10g_test01')
files.append('2026-10-19_50g_test01')
files.append('2026-10-19_100g_test01')
files.append('2026-10-19_110g_test01')


def main():
    
    all_files_data = []

    ########################################
    # Import all of the data
    for file_name in files:
        full_filepath = os.path.join(os.getcwd(), 'data_files', f"{file_name}.csv")
        with open(full_filepath,newline='') as f:
            csv_reader = csv.reader(f)

            # Skip the first 2 rows
            line_1 = next(csv_reader)
            line_2 = next(csv_reader)

            # Load in datapoints for the given file
            this_file_weight_readings = []
            this_file_calibration_factors = []
            for row in csv_reader:
                this_file_weight_readings.append(float(row[0]))
                this_file_calibration_factors.append(float(row[1]))

            # Convert to numpy array for analysis
            this_file_weight_readings = np.array(this_file_weight_readings)
            this_file_calibration_factors = np.array(this_file_calibration_factors)
            
            # Sort by ascending to interpolate
            sort_idx = np.argsort(this_file_calibration_factors)
            sorted_weight_readings = this_file_weight_readings[sort_idx]
            sorted_cal_factors = this_file_calibration_factors[sort_idx]

            # Dict of data for this file
            this_file_data = {
                "file_name": file_name,
                "weight_readings": sorted_weight_readings,
                "calibration_factors": sorted_cal_factors
            }
            
            # Interpolate any values between -1900 and -1910 if they do not exist
            cal_factor_targets = np.arange(-1850, -1950, -1)
            cal_factors_to_add = cal_factor_targets[~np.isin(cal_factor_targets, sorted_cal_factors)]

            weights_interpolated = np.interp(cal_factors_to_add, sorted_cal_factors, sorted_weight_readings)
            
            this_file_data["cal_factors_interpolated"] = cal_factors_to_add
            this_file_data["weights_interpolated"] = weights_interpolated

            all_weights = np.concatenate((sorted_weight_readings, weights_interpolated))
            all_cal_factors = np.concatenate((sorted_cal_factors,cal_factors_to_add))

            # Sort it again
            sort_idx = np.argsort(all_cal_factors)
            all_weights = all_weights[sort_idx]
            all_cal_factors = all_cal_factors[sort_idx]

            # Add to the dict
            this_file_data["all_weights"] = all_weights
            this_file_data["all_cal_factors"] = all_cal_factors

            all_files_data.append(this_file_data)

    '''
    ########################################
    # Scatter plot it all
    plt.figure(figsize=(12, 6))
    plt.ylabel('Weight Readings (g)')
    plt.xlabel('Calibration Factor')
    plt.title('Weight Readings at different calibration factors')

    for file_dict in all_files_data:
        this_file_name = file_dict["file_name"]
        this_file_weights = file_dict["weight_readings"]
        this_file_cal_factors = file_dict["calibration_factors"]
        plt.scatter(this_file_cal_factors,this_file_weights,s=40,label=this_file_name)

    # Drop some horizontal lines on there
    weights = [10, 50, 100, 110]
    for weight in weights:
        plt.axhline(weight,color='k')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    '''

    ########################################
    # Plot them all separately
    figsize = 8
    fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(figsize,figsize),sharex=True)
    plt.subplots_adjust(hspace=0.5)
    fig.suptitle('Weight Readings at different calibration factors')
    for file_dict, ax, weight in zip(all_files_data, axs.ravel(),weights):
        this_file_name = file_dict["file_name"]
        this_file_weights = file_dict["weight_readings"]
        this_file_cal_factors = file_dict["calibration_factors"]
        weights_interpolated = file_dict["weights_interpolated"]
        cal_factors_interpolated = file_dict["cal_factors_interpolated"]
        all_weights = file_dict["all_weights"]
        all_cal_factors = file_dict["all_cal_factors"]

        s1 = ax.scatter(this_file_cal_factors,this_file_weights,s=40)#,label=this_file_name)
        s2 = ax.scatter(cal_factors_interpolated,weights_interpolated,alpha=0.4,color=s1.get_facecolors())
        ax.axhline(weight,color='k')
        ax.set_ylabel('Weight Readings (g)')
        ax.set_xlabel('Calibration Factor')
        ax.set_title(this_file_name,fontsize=10)
        ax.grid(True)

        # which was the best calibration factor
        # find the calibration factor where "weight reading" was closest to "weight"
        closest_idx, closest_val = min(
            enumerate(all_weights),
            key=lambda pair: abs(pair[1] - weight))

        # best calibration factor will be found at
        best_cal_factor = all_cal_factors[closest_idx]
        
        # TODO 10/19/2026 maybe we interpolate over the weights, not the calibration factor
                
        # put a vertical line there and a label
        vline_label = f"{best_cal_factor} is best cal factor ({round(closest_val,2)} g)"
        ax.axvline(best_cal_factor,color='k',label=vline_label)
        ax.legend(loc='upper left')


        # ylims
        ymax = weight*1.02
        ymin = weight*.98
        #ymax = weight*1.01
        #ymin = weight*.99
        #ax.set_ylim([ymin, ymax])

    
    plt.tight_layout()
    plt.show(block=True)


main()