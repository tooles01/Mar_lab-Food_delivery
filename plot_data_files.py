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

# make 1 data point for every 30 seconds (average reading + std dev)
# plot these 

# import the file
file_name = '2026-09-28_datafile_00_0g'
file_name = '2026-09-28_datafile_07_0g'
file_name = '2026-09-28_datafile_12_50g'
file_name = '2026-09-28_datafile_13_100g'
#file_name = os.path.join('2026-09-28_over_time',file_name)

file_name = '2026-11-02_datafile_00_100g'


#file_date = '2026-09-28'
#full_filepath = os.path.join(os.getcwd(), 'data_files',file_date, f"{file_name}.csv")
full_filepath = os.path.join(os.getcwd(), 'data_files', f"{file_name}.csv")


def main():

    time = []
    reading = []
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
                time.append(row[0])
                reading.append(row[1])
                calibration_factor.append(row[2])
        
        average_data = []
        start_times = []

        final_time = datetime.strptime(time[-1], "%H:%M:%S.%f")

        # Now parse the data or whatever
        start_time = datetime.strptime(time[0], "%H:%M:%S.%f")
        cutoff_time = start_time + timedelta(seconds=30)

        # Get data for the first 30 seconds
        first_30_seconds = [
            float(reading[i]) for i, t in enumerate(time)
            if datetime.strptime(t, "%H:%M:%S.%f") <= cutoff_time
        ]
        average = sum(first_30_seconds) / len(first_30_seconds)
        average_data.append(average)
        start_times.append(start_time)

        # Keep going for the rest of the data
        prev_cutoff_time = cutoff_time
        start_time = prev_cutoff_time
        while (prev_cutoff_time <= final_time):
            cutoff_time = start_time + timedelta(seconds=30)            
            next_30_seconds = [
                float(reading[i]) for i, t in enumerate(time)
                if datetime.strptime(t, "%H:%M:%S.%f") <= cutoff_time
            ]
            average = sum(next_30_seconds) / len(next_30_seconds)
            average_data.append(average)
            start_times.append(start_time)

            prev_cutoff_time = cutoff_time
            start_time = prev_cutoff_time


        # Convert readings to float if they aren't already
        readings_float = [float(r) for r in reading]

        '''
        # Convert time strings to datetime objects for plotting
        time_objects = [datetime.strptime(t, "%H:%M:%S.%f") for t in time]
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
        
        start_time = datetime.strptime(time[0], "%H:%M:%S.%f")
        time_seconds = [(datetime.strptime(t, "%H:%M:%S.%f") - start_time).total_seconds() for t in time]
        readings_float = [float(r) for r in reading]

        plt.figure(figsize=(12, 6))
        #plt.plot(time_seconds, readings_float, linewidth=1, label='Readings')

        # Plot all of the hlines
        xmin=-30
        for section in average_data:
            xmin = xmin+30
            xmax = xmin+30
            plt.hlines(y=section, xmin=xmin, xmax=xmax, color='r',linestyle='--', linewidth=2,
                       label=f'Avg: {average:.3f} g')
            plt.axvline(x=xmax, color='g', linestyle='--', alpha=0.5)
            
        plt.xlabel('Time (seconds)')
        plt.ylabel('Reading (g)')
        title = 'Sensor Readings Over Time: ' + file_name
        plt.title(title)
        #plt.title('Sensor Readings Over Time')
        plt.legend(fontsize=6)
        plt.grid(True, alpha=0.3)
        #plt.tight_layout()
        plt.show()

        x=1


    except FileNotFoundError as e:
        print(f"ERROR: File does not exist: {e}")


    x=1



# go from the first line 
# get the time and reading
# add 30 seconds to that time, get all of those readings
# get the mean




main()