'''
plot_data_files.py


Plotting calibration datafiles over time to check for load cell drift


Requirements
    matplotlib


ST 2026
'''


import csv, os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# make 1 data point for every 30 seconds (average readings_raw + std dev)
# plot these 

# import the file
file_name = '2026-09-28_datafile_00_0g'
file_name = '2026-09-28_datafile_07_0g'
file_name = '2026-09-28_datafile_12_50g'
file_name = '2026-09-28_datafile_13_100g'
#file_name = os.path.join('2026-09-28_over_time',file_name)

file_name = '2026-11-02_datafile_00_100g'
file_name = '2026-11-02_datafile_01_100g'
file_name = '2026-11-02_datafile_02_100g'
file_name = '2026-11-02_datafile_04'    # 400g
average_the_data = 'yes'
#file_name = '2026-11-02_datafile_02'    # Place 200mg, then 250mg
#file_name = '2026-11-02_datafile_03'    # Place 200mg, then 100mg
#average_the_data = 'no'
file_name = '2026-11-02_datafile_04_400g'
file_name = '2026-11-09_datafile_00_400g'

#file_date = '2026-09-28'
#full_filepath = os.path.join(os.getcwd(), 'data_files',file_date, f"{file_name}.csv")
plot_in = 'seconds'
plot_in = 'minutes'
file_name = '2026-11-02_datafile_02_100g'
file_name = '2026-11-09_datafile_00_400g - Copy'
full_filepath = os.path.join(os.getcwd(), 'data_files', f"{file_name}.csv")

def main():

    time_raw = []
    readings_raw = []
    calibration_factor = []
    try:
        with open(full_filepath,newline='') as f:
            # Cut off the first 6 lines (header)
            csv_reader = csv.reader(f)
            line_1 = next(csv_reader)
            line_2 = next(csv_reader)
            line_3 = next(csv_reader)
            line_4 = next(csv_reader)
            line_5 = next(csv_reader)
            line_6 = next(csv_reader)

            # Load all of the data in
            for row in csv_reader:
                time_raw.append(row[0])
                readings_raw.append(row[1])
                calibration_factor.append(row[2])
        
        all_data_averaged = []
        all_start_times = []

        final_time = datetime.strptime(time_raw[-1], "%H:%M:%S.%f")

        # Now parse the data or whatever
        start_time = datetime.strptime(time_raw[0], "%H:%M:%S.%f")
        cutoff_time = start_time + timedelta(seconds=30)

        # Get data for the first 30 seconds
        first_30_seconds = [
            float(readings_raw[i]) for i, t in enumerate(time_raw)
            if datetime.strptime(t, "%H:%M:%S.%f") <= cutoff_time
        ]
        average = sum(first_30_seconds) / len(first_30_seconds)
        all_data_averaged.append(average)
        all_start_times.append(start_time)

        # Keep going for the rest of the data
        prev_cutoff_time = cutoff_time
        start_time = prev_cutoff_time
        while (prev_cutoff_time <= final_time):
            cutoff_time = start_time + timedelta(seconds=30)            
            next_30_seconds = [
                float(readings_raw[i]) for i, t in enumerate(time_raw)
                if datetime.strptime(t, "%H:%M:%S.%f") <= cutoff_time
            ]
            average = sum(next_30_seconds) / len(next_30_seconds)
            all_data_averaged.append(average)
            all_start_times.append(start_time)

            prev_cutoff_time = cutoff_time
            start_time = prev_cutoff_time


        # Convert readings to float if they aren't already
        readings_float = [float(r) for r in readings_raw]

        '''
        # Convert time_raw strings to datetime objects for plotting
        time_objects = [datetime.strptime(t, "%H:%M:%S.%f") for t in time_raw]
        # Create the plot
        plt.figure(figsize=(12, 6))
        plt.plot(time_objects, readings_float, linewidth=1)
        plt.xlabel('Time')
        plt.ylabel('Reading (g)')
        plt.title('Sensor Readings Over Time')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        '''
        
        start_time = datetime.strptime(time_raw[0], "%H:%M:%S.%f")
        time_seconds = [(datetime.strptime(t, "%H:%M:%S.%f") - start_time).total_seconds() for t in time_raw]
        readings_float = [float(r) for r in readings_raw]

        plt.figure(figsize=(12, 6))
        
        if average_the_data == 'no':
            plt.plot(time_seconds, readings_float, linewidth=1, label='Readings')
        if average_the_data == 'yes':
            if plot_in == 'seconds':
                # Plot all of the hlines
                line_start=-30
                for section_average in all_data_averaged:
                    line_start = line_start+30
                    line_end = line_start+30
                    plt.hlines(y=section_average, xmin=line_start, xmax=line_end, color='r',linestyle='--', linewidth=2)#,
                            #label=f'Avg: {average:.3f} g')
                    plt.axvline(x=line_end, color='g', linestyle='--', alpha=0.5)
            if plot_in == 'minutes':
                # Plot all of the hlines
                time_minutes = [x / 60 for x in time_seconds]
                line_start = -.5
                for section_average in all_data_averaged:
                    line_start = line_start + .5
                    line_end = line_start + .5
                    plt.hlines(y=section_average, xmin=line_start, xmax=line_end, color='r',linestyle='--', linewidth=2)#,
                    plt.axvline(x=line_end, color='g', linestyle='--', alpha=0.5)

        '''
        # 2026-11-02_datafile_02
        plt.hlines(y=100,xmin=0,xmax=time_seconds[len(time_seconds)-1],color='k',label='100g')
        plt.hlines(y=100.2,xmin=0,xmax=time_seconds[len(time_seconds)-1],color='g',label='100.2g')
        plt.hlines(y=100.25,xmin=0,xmax=time_seconds[len(time_seconds)-1],color='m',label='100.25g')
        # 2026-11-02_datafile_03
        plt.hlines(y=100,xmin=0,xmax=time_seconds[len(time_seconds)-1],color='k',label='100g')
        plt.hlines(y=100.1,xmin=0,xmax=time_seconds[len(time_seconds)-1],color='g',label='100.1g')
        plt.ylim(99.8, 100.5)
        '''

        #plt.xlim(0, time_seconds[len(time_seconds)-1])
        if plot_in == 'seconds':
            plt.xlabel('Time (seconds)')
        if plot_in == 'minutes':
            plt.xlabel('Time (minutes)')
        plt.ylabel('Reading (g)')
        title = 'Sensor Readings Over Time: ' + file_name
        plt.title(title)
        #plt.title('Sensor Readings Over Time')
        plt.legend(fontsize=6)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.ticklabel_format(axis='y',style='plain',useOffset=False)
        plt.show(block=True)    # keep the plot open/the script running

    except FileNotFoundError as e:
        print(f"ERROR: File does not exist: {e}")


main()