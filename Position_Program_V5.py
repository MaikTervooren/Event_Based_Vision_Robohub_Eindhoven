import cv2
import csv
import time

from collections import Counter
from pyaer.davis import DAVIS

Positive_events                 = []
Positive_events_x               = []
Positive_centres_of_masses      = []
Positive_centres_of_masses_2    = []
Negative_events                 = []
Negative_events_x               = []
Negative_centres_of_masses      = []
Negative_centres_of_masses_2    = []

amount_of_events = 0
Between_Period = False
Collection_Period_1 = False
Collection_Period_2 = False
Initialization_Period = False
Positive_n_events = 0
Negative_n_events = 0
x_total = 0
y_total = 0


device = DAVIS(noise_filter=True)
device.start_data_stream()
# set new bias after data streaming
device.set_bias_from_json("/home/maik/Documents/Python_3/configs/davis240c_config.json")
#  num_packet_before_disable = 1000


def calculating_centre_of_mass(events_list, x_previous):
    centres_of_masses = []
    unique_x_list = []

    x_list, y_list = map(list, zip(*events_list))

    Event_amount = 0
    x_total = 0
    y_total = 0

    unique_x_list = list(dict.fromkeys(x_list))
    c = Counter(x_list)
    
    for x in unique_x_list:
        if ((c[x] >= 4) and (Event_amount == 0)) or ((c[x] >= 2) and (Event_amount != 0)): 
            
            if ((x - x_previous) <= 2) or (x_total == 0 ):
                for event in events_list:
                    (event_x, event_y) = event

                    if x == event_x:
                        x_total = x_total + event_x 
                        y_total = y_total + event_y

                        Event_amount += 1
                        x_previous = event_x

            else:
                if(x_total != 0):
                    x_total = x_total/Event_amount
                    y_total = y_total/Event_amount

                    centres_of_masses.append([x_total, y_total])
                    x_total = 0
                    y_total = 0

                    x_previous = event_x
                    Event_amount = 0

        else:
            x_previous = x

            x_total = 0
            y_total = 0

            Event_amount = 0

    if(Event_amount != 0):
        x_total = x_total/Event_amount
        y_total = y_total/Event_amount
        
        centres_of_masses.append([x_total, y_total])
        x_total = 0
        y_total = 0

        Event_amount = 0

    return centres_of_masses



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
                                    
                                    if (Initialization_Period == False) and (Collection_Period_1 == False) and (Between_Period == False) and (Collection_Period_2 == False):
                                        if (Positive_n_events == 0) and (Negative_n_events == 0):
                                            t1 = t
                                            t2 = t + 1000
                                            t3 = t + 11000
                                            t4 = t + 12000

                                            Initialization_Period = True

                                    if (Initialization_Period == True) and (Collection_Period_1 == False) and (Between_Period == False) and (Collection_Period_2 == False):  
                                        if (t <= t2):
                                            if p == 0:
                                                writerevents.writerow([(t/1000000), x, y, p, noise, 'Collection period 1 - Negative', time.time()])
                                                Negative_events.append([x, y])

                                                Negative_n_events += 1

                                            if p == 1:
                                                writerevents.writerow(['','','','','','','','',(t/1000000), x, y, p, noise, 'Collection period 1 - Positive', time.time()])
                                                Positive_events.append([x, y])

                                                Positive_n_events += 1

                                        else:
                                            if len(Positive_events) != 0:
                                                Positive_events.sort() 
                                            
                                                x_previous = Positive_events[0][0] - 1

                                                Positive_centres_of_masses = calculating_centre_of_mass(Positive_events, x_previous)

                                                for centre_of_mass in Positive_centres_of_masses:
                                                    writerevents.writerow(['Centre of mass Positive: ', centre_of_mass[0], centre_of_mass[1]])

                                                Positive_n_events = 0

                                            
                                            if len(Negative_events) != 0:
                                                Negative_events.sort()
                                                x_previous = Negative_events[0][0] - 1

                                                Negative_centres_of_masses = calculating_centre_of_mass(Negative_events, x_previous)

                                                for centre_of_mass in Negative_centres_of_masses:
                                                    writerevents.writerow(['Centre of mass Negative: ', centre_of_mass[0], centre_of_mass[1]])

                                                Negative_n_events = 0

                                            Collection_Period_1 = True

                                            Positive_events.clear()
                                            Negative_events.clear()

                                            Positive_centres_of_masses.clear()
                                            Negative_centres_of_masses.clear()

                                    if (Initialization_Period == True) and (Collection_Period_1 == True) and (Between_Period == False)and (Collection_Period_2 == False): 
                                        if(t <= t3):
                                        
                                            writernoise.writerow([(t/1000000), x, y, p, noise, 'In Between Collection Periods', time.time()])

                                        else:
                                            Between_Period = True

                                    if (Initialization_Period == True) and (Collection_Period_1 == True) and (Between_Period == True) and (Collection_Period_2 == False):
                                            
                                        if(t <= t4):

                                            if p == 0:
                                                writerevents.writerow([(t/1000000), x, y, p, noise, 'Collection period 2 - Negative', time.time()])
                                                Negative_events.append([x, y])

                                                Negative_n_events += 1

                                            if p == 1:
                                                writerevents.writerow(['','','','','','','','',(t/1000000), x, y, p, noise, 'Collection period 2 - Positive', time.time()])
                                                Positive_events.append([x, y])

                                                Positive_n_events += 1

                                        else:
                                            if len(Positive_events) != 0:
                                                Positive_events.sort() 
                                                x_previous = Positive_events[0][0] - 1

                                                Positive_centres_of_masses_2 = calculating_centre_of_mass(Positive_events, x_previous)

                                                for centre_of_mass in Positive_centres_of_masses_2:
                                                    writerevents.writerow(['Centre of mass Positive - Second collection: ', centre_of_mass[0], centre_of_mass[1]])

                                                Positive_n_events = 0

                                            
                                            if len(Negative_events) != 0:
                                                Negative_events.sort()
                                                x_previous = Negative_events[0][0] - 1

                                                Negative_centres_of_masses_2 = calculating_centre_of_mass(Negative_events, x_previous)

                                                for centre_of_mass in Negative_centres_of_masses_2:
                                                    writerevents.writerow(['Centre of mass Negative - Second collection: ', centre_of_mass[0], centre_of_mass[1]])

                                                Negative_n_events = 0

                                            Collection_Period_2 = True

                                            Positive_events.clear()
                                            Negative_events.clear()

                                            Positive_centres_of_masses_2.clear()
                                            Negative_centres_of_masses_2.clear()

                                    if (t > t4):
                                        
                                        Initialization_Period = False
                                        Between_Period = False
                                        Collection_Period_1 = False
                                        Collection_Period_2 = False
                                        Positive_n_events = 0
                                        Negative_n_events = 0

                                        Positive_events.clear()
                                        Negative_events.clear()
                                        Positive_centres_of_masses.clear()
                                        Negative_centres_of_masses.clear()



                                else:
                                    writernoise.writerow([(t/1000000), x, y, p, noise, 'Noise', time.time()])

                except KeyboardInterrupt:
                    device.shutdown()
                    break
