import cv2
import csv
import numpy as np
import time

from collections import Counter
from pyaer import libcaer
from pyaer.davis import DAVIS

Positive_events             = []
Positive_centres_of_masses  = []
Negative_events             = []
Negative_centres_of_masses  = []

amount_of_events = 0
Collection_Period_1 = False
Positive_n_events = 0
Negative_n_events = 0
x_total = 0
y_total = 0


device = DAVIS(noise_filter=True)
device.start_data_stream()
# set new bias after data streaming
device.set_bias_from_json("/home/maik/Documents/Python_3/configs/davis240c_config.json")
#  num_packet_before_disable = 1000

with open('Position_and_Speed_31_01_2020.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

    #Open Event Data Real Time Discarded CSV file
    with open('Events_31_01_2020.csv', 'w', newline='') as csvfile:
        writerevents = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        #Open Event Data Real Time Discarded CSV file
        with open('Noise_Events_31_01_2020.csv', 'w', newline='') as csvfile:
            writernoise = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    
            while True:
                try:
                    data = device.get_event("events")
                    if data is not None:
                        (pol_events, num_pol_event, special_events, num_special_event, frame_ts, frames, imu_events, num_imu_event) = data

                        if pol_events is not None:
                        
                            for event in pol_events:
                                (t, x, y, p, noise) = event
                                if(noise == 1):
                                    
                                    if (Collection_Period_1 == False) and (Positive_n_events == 0) and (Negative_n_events == 0):
                                        t1 = t
                                        t2 = t + 1000
                                        t3 = t + 11000
                                        t4 = t + 12000

                                    if (Collection_Period_1 == False) and (t <= t2):
                                        if p == 0:
                                            writerevents.writerow([(t/1000000), x, y, p, noise, 'Collection period 1 - Negative', time.time()])
                                            Negative_events.append([x, y])
                                            
                                            Negative_n_events += 1

                                        if p == 1:
                                            writerevents.writerow(['','','','','','','','',(t/1000000), x, y, p, noise, 'Collection period 1 - Positive', time.time()])
                                            Positive_events.append([x, y])
                                            
                                            Positive_n_events += 1 

                                    else:
                                        if Positive_events != 0:
                                            Positive_events.sort() 
                                            x_previous = Positive_events[0][0] - 1
                                        
                                        if Negative_events != 0:
                                            Negative_events.sort()

                                        

                                        for pixel in Positive_events:
                                            if (pixel[0] - x_previous) <= 1:
                                                x_total = x_total + pixel[0]
                                                y_total = y_total + pixel[1]

                                                
                                                amount_of_events += 1
                                            else:
                                                if(x_total != 0):

                                                    positive_centre_of_mass_x = x_total/amount_of_events
                                                    positive_centre_of_mass_y = y_total/amount_of_events

                                                    Positive_centres_of_masses.append([positive_centre_of_mass_x,positive_centre_of_mass_y])

                                                    writerevents.writerow(['','','','','Positive centre of mass', positive_centre_of_mass_x, positive_centre_of_mass_y])

                                                    x_total = 0
                                                    y_total = 0
                                                    amount_of_events = 0
                                                
                                            x_previous = pixel[0]
                                        
                                        if x_total != 0:
                                                positive_centre_of_mass_x = x_total/amount_of_events
                                                positive_centre_of_mass_y = y_total/amount_of_events

                                                Positive_centres_of_masses.append([positive_centre_of_mass_x,positive_centre_of_mass_y])
                                                
                                                writerevents.writerow(['','','','','Positive centre of mass', positive_centre_of_mass_x, positive_centre_of_mass_y])
                                                
                                                x_total = 0
                                                y_total = 0
                                                amount_of_events = 0

                                        #print(*Positive_centres_of_masses, sep = ", ")

                                        Positive_n_events = 0
                                        Negative_n_events = 0
                                        writerevents.writerow(['-','-','-','-','-','-','-','-'])

                                else:
                                    writernoise.writerow([(t/1000000), x, y, p, noise, 'Noise', time.time()])

                except KeyboardInterrupt:
                    device.shutdown()
                    break
