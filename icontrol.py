#!/bin/python3

# icontrol
#
#
# Little script that bridges the gap between "smart" midi controllers and simple ones that have only 
# momentary switches ie. sends one cc or note when switch is pressed, and another when it is released.
# 
# Implements the following behaviours:
#
# "Sliders" - emulate knobs with switches so you can control parameters like volume or balance in your 
#		DAW or jack_mixer.  Setting output CC to 0 or 1 makes it a "program change" knob, while
#		giving it a non-zero output CC on the fourth row will make it a "reciprocal" slider for
#		controlling balance between two sliders - one goes up and the other goes down.
# "Buttons" - Single switch that can send a quick cc or hold for a "longpress" cc. Again, a value on the
#		fourth row indicates the CC the longpress function should be sent on.
#
#
# At the moment it is configured for my NanoPad 2, and uses note values and velocities as a trigger. It
# could easily be adapted for controllers that send CCs just by renaming "note_on" and "message.note" to
# "control_change" and "message.control_change", and giving it a static velocity.
#
#

import mido
import time

PROGRAMCHANGESLIDERMAX = 15
#PROGRAMCHANGEBUTTONMAX = 8
LONGPRESSTIME = 1.5             # seconds
MAXPRESSURE = 50                # 0-127
SPEED = 70
BUTTONVALUE = 0                 # what data button i.e "single" cc's send

ccin =      ([36,37,38,39,40,41,42,43,44,45,46],                                # input cc number (or note number, currently) of input button
            [26,26,27,27,28,28,0,0,1,1,30],                                     # output cc. 0 or 1 indicates a "program change" slider
            [0,0,0,0,0,0,0,0,1,1,0],                                            # output on channel
            ["up","down","up","down","up","down","up","down","up","down","single"],     # is "up" or "down" or "single" button
            [0,0,0,0,29,29,0,0,0,0,31])                                        # for longpress and "reciprocal sliders" second cc# to send for second function.  if > 0 , is longpress or reciprocal type.


ccout = {}                      # what the output cc value of each slider is.
for i in ccin[1]:
    if not ccout.get(i):
        if i < 2:                           #program change slider
            ccout[i] = 0                    #starts at program 0
        else:
            ccout[i] = 64                   #set sliders i.e. up/down to default "middle"


in_port = mido.open_input('in 1', virtual=True, client_name="icontrol")
out_port = mido.open_output('out 1', virtual=True, client_name="icontrol")

print(in_port.poll())

with in_port as inport:                         # doing this recursively as a callback didn't work because the callback blocked incomming messages, so we are doing it iteratively

    for message in inport:

        if message.type == "note_on" and ccin[0].count(message.note):         # is it one of the notes (or cc's) we are looking for?

            i = ccin[0].index(message.note)
            outcc = ccin[1][i]

            advance = 0
            t = (MAXPRESSURE - message.velocity) / SPEED
            if t < 0:
                t = 1 / SPEED
            if ccin[3][i] == "up":
                t = -t
                advance = -1
            if ccin[3][i] == "down":
                advance = 1

            max = 127

            if outcc < 2:                       # its a program change slider
                max = PROGRAMCHANGESLIDERMAX
                t = 1                           # wait 1 sec each program

            while t != 0:

                if ccin[3][i] == "down" or ccin[3][i] == "up":

                    ccout[outcc] = ccout[outcc] + advance
                    if ccout[outcc] > max:
                        ccout[outcc] = max
                        t = 0
                    if ccout[outcc] <= 0:
                        ccout[outcc] = 0
                        t = 0
                    if outcc < 2:                                                                                   # is program change slider
                        outmessage = mido.Message('program_change', channel=ccin[2][i], program=int(ccout[outcc]))
                    else:                                                                                           # is regular slider
                        outmessage = mido.Message('control_change', channel=ccin[2][i], control=outcc, value=int(ccout[outcc]))

                        if ccin[4][i] > 0:                          # Reciprocal slider -- i.e. vocal goes up when instrument comes down and vica versa, so you can adjust the mix.
                            out_port.send(outmessage)
                            outmessage = mido.Message('control_change', channel=ccin[2][i], control=ccin[4][i], value= max - int(ccout[outcc]))

                    out_port.send(outmessage)

                if ccin[3][i] == "single" and ccin[4][i] == 0:                  # is momentary press only
                    outmessage = mido.Message('control_change', channel=ccin[2][i], control=outcc, value=BUTTONVALUE)
                    out_port.send(outmessage)
                    t = 0

                if ccin[3][i] == "single" and ccin[4][i] > 0:                   # can be momentary or long
                    longpresstime = LONGPRESSTIME
                    t = 0.05
                    
                    while longpresstime > 0:
                        time.sleep(t)
                        message = in_port.poll()
                        if message:                                             # is momentary press
                            outmessage = mido.Message('control_change', channel=ccin[2][i], control=outcc, value=BUTTONVALUE)
                            out_port.send(outmessage)
                            break
                        longpresstime = longpresstime - t

                    if longpresstime <= 0:                                      # is long press
                        outmessage = mido.Message('control_change', channel=ccin[2][i], control=ccin[4][i], value=BUTTONVALUE)
                        out_port.send(outmessage)
                    t = 0

                time.sleep(abs(t))

                if t != 0:
                    message = in_port.poll()
                    if message:
                        t = 0
