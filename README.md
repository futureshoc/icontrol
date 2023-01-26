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
# Written for linux/jack - not sure how virtual ports work in OSX/Windows
#
