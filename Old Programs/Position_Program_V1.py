import cv2
import csv
import numpy as np
import time

from collections import Counter
from pyaer import libcaer
from pyaer.davis import DAVIS

#initialization
centre_of_masses    = []
centre_of_masses_2  = []
events              = []
speed               = []
x_events            = []

amount              = 0
first_event         = True
initialization      = True
meters_per_pixel    = 0.000544208
n                   = 0
n_events            = 0
period_1_finished   = False
period_2_finished   = False
period_3_finished   = False
period_4_finished   = False
period_5_finished   = False
t2                  = 0.0001
t3                  = 0.0002
t4                  = 0.0003
t5                  = 0.0004
time_memory         = 0
x_total             = 0

device = DAVIS(noise_filter=True)
device.start_data_stream()
# set new bias after data streaming
device.set_bias_from_json("/home/maik/Documents/Python_3/configs/davis240c_config.json")
#  num_packet_before_disable = 1000

with open('Event_data_Real_Time.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

    #Open Event Data Real Time Discarded CSV file
    with open('Event_data_Real_Time_null.csv', 'w', newline='') as csvfile:
        writernull = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        while True:
            try:
                data = device.get_event("events")
                if data is not None:
                    (pol_events, num_pol_event, special_events, num_special_event, frame_ts, frames, imu_events, num_imu_event) = data

                    if pol_events is not None:

                        for event in pol_events:
                            (t, x, y, p, noise) = event

                            #Initialization state
                            if initialization == True:
                                if first_event == True:
                                    initialization_time = t + 3000000
                                    first_event = False

                                if t <= initialization_time:
                                    if t >= time_memory:
                                        writernull.writerow(['-','-','-','-','-'])
                                        time_memory = t + 1000

                                    writernull.writerow([(t/1000000), x, y, p,'Initialization', time.time()])

                                else:
                                     initialization = False

                            #Main Program
                            if initialization == False:
                                if period_1_finished == False and period_2_finished == False and period_3_finished == False and period_4_finished == False and period_5_finished == False:
                                    begin_time = t
                                    t2 = t + 3000
                                    t3 = t + 10000
                                    t4 = t + 13000
                                    t5 = t + 20000

                                    period_1_finished = True

                                if period_1_finished == True and period_2_finished == False and period_3_finished == False and period_4_finished == False and period_5_finished == False:
                                    if t <= t2:
                                        x_events.append(x)
                                        writer.writerow([(t/1000000), x, y, p, 'Period 2', time.time()])
                                    else:
                                        x_events.sort()
                                        unique_x_list = list(dict.fromkeys(x_events))
                                        c = Counter(x_events)
                                        x_previous = unique_x_list[0] - 1

                                        for x_pixel in unique_x_list:
                                            if (x_pixel - x_previous) <= 5:
                                                x_total     = x_total + (c[x_pixel] * x_pixel)
                                                n_events    = n_events + c[x_pixel]

                                                x_previous  = x_pixel

                                            else:
                                                if (n_events <= 10):
                                                    x_total     = (c[x_pixel] * x_pixel)
                                                    n_events    = c[x_pixel]
                                                    x_previous  = x_pixel
                                                else:    
                                                    centre_of_mass = x_total/n_events
                                                    writer.writerow(['-', '-', '-', '-', '-', '-', '-','centre of mass 1', centre_of_mass])
                                                    centre_of_masses.append(centre_of_mass)

                                                    x_total     = (c[x_pixel] * x_pixel)
                                                    n_events    = c[x_pixel]
                                                    x_previous  = x_pixel
                                        
                                        if (n_events > 10):
                                            centre_of_mass = x_total/n_events
                                            writer.writerow(['-', '-', '-', '-', '-', '-', '-','centre of mass 1', centre_of_mass])
                                            centre_of_masses.append(centre_of_mass)

                                        period_2_finished = True
                                        writer.writerow([(t/1000000), x, y, p, 'Period 3', time.time()])
                                        
                                        x_total     = 0
                                        n_events    = 0
                                        x_previous  = 0
                                        
                                        events.clear()
                                        unique_x_list.clear()
                                        x_events.clear()

                                        print("centre of masses 1") 
                                        print(centre_of_masses)

                                if period_1_finished == True and period_2_finished == True and period_3_finished == False and period_4_finished == False and period_5_finished == False:
                                    if (t > t2) and (t <= t3):
                                        writernull.writerow([(t/1000000), x, y, p, 'Period 3', time.time()])
                                    else:
                                        period_3_finished   = True
                                        writer.writerow([(t/1000000), x, y, p, 'Period 4', time.time()])

                                if period_1_finished == True and period_2_finished == True and period_3_finished == True and period_4_finished == False and period_5_finished == False:
                                    if (t > t3) and (t <= t4):
                                        events.append(x)
                                        writer.writerow([(t/1000000), x, y, p, 'Period 4', time.time()])
                                    else:
                                        if not events:
                                            period_1_finished = False
                                            period_2_finished = False
                                            period_3_finished = False
                                            period_4_finished = False

                                            centre_of_masses.clear()
                                        else:
                                            end_time = t
                                            events.sort()
                                            unique_x_list = list(dict.fromkeys(events))
                                            c = Counter(events)
                                            x_previous = unique_x_list[0] - 1

                                            for x_pixel in unique_x_list:
                                                if (x_pixel - x_previous) <= 4:
                                                    x_total     = x_total + (c[x_pixel] * x_pixel)
                                                    n_events    = n_events + c[x_pixel]

                                                    x_previous  = x_pixel

                                                else:
                                                    if (n_events <= 10):
                                                        x_total     = (c[x_pixel] * x_pixel)
                                                        n_events    = c[x_pixel]
                                                        x_previous  = x_pixel
                                                    else:    
                                                        centre_of_mass = x_total/n_events
                                                        writer.writerow(['-', '-', '-', '-', '-', '-', '-','centre of mass 2', centre_of_mass])
                                                        centre_of_masses_2.append(centre_of_mass)

                                                        x_total     = (c[x_pixel] * x_pixel)
                                                        n_events    = c[x_pixel]
                                                        x_previous  = x_pixel

                                            if (n_events > 10):
                                                centre_of_mass = x_total/n_events
                                                writer.writerow(['-', '-', '-', '-', '-', '-', '-','centre of mass 2', centre_of_mass])
                                                centre_of_masses_2.append(centre_of_mass)

                                            period_4_finished = True
                                            writer.writerow([(t/1000000), x, y, p, 'Period 5', time.time()])

                                            x_total     = 0
                                            n_events    = 0
                                            x_previous  = 0

                                            events.clear()
                                            unique_x_list.clear()
                                            x_events.clear()

                                            print("centre of mass 2") 
                                            print(centre_of_masses_2)

                                if period_1_finished == True and period_2_finished == True and period_3_finished == True and period_4_finished == True and period_5_finished == False:
                                    if (t > t4) and (t <= t5):
                                        if not centre_of_masses:
                                            writernull.writerow([(t/1000000), x, y, p, 'Period 5', time.time()])
                                            
                                        else:
                                            while amount < len(centre_of_masses):
                                                difference_centre_of_mass = centre_of_masses_2[amount] - centre_of_masses[amount]
                                                difference_time = (end_time - begin_time)/1000000
                                                difference_meters = difference_centre_of_mass * meters_per_pixel
                                                speed = difference_meters / difference_time
                                                amount += 1
                                                print(speed)
                                                writer.writerow(['-', '-', '-', '-', '-', '-', 'Speed', speed])
                                            
                                            centre_of_masses.clear()
                                            centre_of_masses_2.clear()


                                    else:
                                        period_1_finished = False
                                        period_2_finished = False
                                        period_3_finished = False
                                        period_4_finished = False
                                        amount = 0


            except KeyboardInterrupt:
                device.shutdown()
                break