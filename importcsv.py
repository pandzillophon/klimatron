import csv
from sys import argv
from sklearn import preprocessing
from warnings import catch_warnings
from midiutil import MidiFile
import numpy
from datetime import datetime



def readfile(filename):
    measurement_data = {}
    with open(filename) as csvdata:
        csv_reader = csv.reader(csvdata, delimiter=";")
        for row in csv_reader:
            if len(row) > 1:
                try:
                    measurement_data[datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%S")] = (float(row[1]))
                except:
                    print("couldn't parse data:" + str(row))
    return(measurement_data)


def main():
    outdict = {}
    measured_parsed = readfile(argv[1])
    temps = measured_parsed.values()
    print("number of temperature data sets: " + str(len(temps)))
    lookup_dict = create_dict(temps)
    temp_cc = assign_scaled_values(lookup_dict, temps)
    for timestamp in measured_parsed.keys(): 
        outdict[timestamp] = (temp_cc[measured_parsed[timestamp]], measured_parsed[timestamp])
    output_for_file = sorted(outdict.items())
    create_midifile(output_for_file)

    

def create_dict(values):
    sorted_originals = sorted(values, reverse=True)
    print("sorted originals length", len(sorted_originals))
    scaler = preprocessing.MinMaxScaler((1,127))
    arr = numpy.array(sorted_originals)
    scaled = scaler.fit_transform(arr.reshape(-1,1))
    lookup_dict = {}
    for x in range(0, len(scaled)): 
        lookup_dict[sorted_originals[x]] = round(scaled[x][0])
    return(lookup_dict)
    

def assign_scaled_values(lookup_dict, values):
    temp_cc = {}
    for value in values:
        temp_cc[value] = lookup_dict[value]
    return(temp_cc)


def create_midifile(output):
    # initialize the MIDI file 
    track = 0 
    channel = 0 
    tempo = 120 # in bpm
    volume = 100
    controller_number = 1 
    
    cursor = 0 # init the cursor within the file at whose location the event gets inserted

    last_timestamp = None # timestamp of previous value
    
    midi_file = MidiFile.MIDIFile(1)
    midi_file.addTempo(track, cursor, tempo)

    for value in output:
        if (last_timestamp == None):
            last_timestamp = value[0]
        delta_t = value[0] - last_timestamp # calculate time between previous and current timestamp
        realtime_hours = delta_t.total_seconds() / 3600 # 3600 seconds in an hour, total hours of delta between timestamps
        beats = realtime_hours * 5  # one hour in real time is 2.5 sec at 120bpm in our output. At 120bpm one second has two beats, 
                                    # so one hour is the equivalent of 5 beats at this speed 
        parameter = value[1][0]     # this is the scaled value
        midi_file.addControllerEvent(track, channel, cursor, controller_number, parameter)
        cursor = cursor + beats 
        last_timestamp = value[0]
    with open("testfile.mid", "wb") as output_file:
        midi_file.writeFile(output_file)



        
main()