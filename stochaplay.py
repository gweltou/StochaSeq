#! /usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import division, print_function
import sys
import random
import time
import heapq
import mido

# Backward compatibility with python 2.7
if sys.version_info[0] < 3:
    import tKinter as tk
else:
    import tkinter as tk


TICKS_PER_BEAT = 4

C1 = 36
C2 = 48
C3 = 60

# diatonic scales
ionian = [2, 2, 1, 2, 2, 2, 1]
major = ionian
dorian = [2, 1, 2, 2, 2, 1, 2]
phrygian = [1, 2, 2, 2, 1, 2, 2]
lydian = [2, 2, 2, 1, 2, 2, 1]
myxolidian = [2, 2, 1, 2, 2, 1, 2]
aeolian = [2, 1, 2, 2, 1, 2, 2]
minor = aeolian
locrian = [1, 2, 2, 1, 2, 2, 2]

hirajoshi = [4, 2, 1, 4, 1]
insen = [1, 4, 2, 3, 2]
iwato = [1, 4, 1, 4, 2]

enigmatic = [1, 3, 2, 2, 2, 1, 1]
flamenco = [1, 3, 1, 2, 1, 3, 1]
gypsy = [2, 1, 3, 1, 1, 2, 2]
prometheus = [2, 2, 2, 3, 1, 2]
phrygiandom = [1, 3, 1, 2, 1, 2, 2]


def create_scale(tonic, pattern, octave=1):
    """
        Create an octave-repeating scale from a tonic note
        and a pattern of intervals
        
        Args:
            tonic: root note (midi note number)
            pattern: pattern of intervals (list of numbers representing
            intervals in semitones)
            octave: span of scale (in octaves)
        
        Returns:
            list of midi notes in the scale
    """
    assert(sum(pattern)==12)
    scale = [tonic]
    note = tonic
    for o in range(octave):
        for i in pattern:
            note += i
            if note <= 127:
                scale.append(note)
    return scale


################################################################################
################################################################################
################################################################################


class StochaPlayer(object):
    durations = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    chords = [('Maj', (0, 4, 7)),
              ('min', (0, 3, 7)),
              ('Aug', (0, 4, 8)),
              ('dim', (0, 3, 6)),
              ]
    
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        self.midi = midiout
        self.channel = channel
        self.volume = 1
        self.timesig = timesig
        self.wait_nticks = 0
        self.played_notes = []
        self.scale = create_scale(C2, major)  # Set au default music scale
        self.weigths_desc = ["function", "note/chord duration", "silence duration"]
        self.update_weights([[5, 2, 2, 1],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def set_scale(self, scale):
        self.scale = sorted(scale)
    
    def update_weights(self, weights):
        formatted = []
        for table in weights:
            s = sum(table)
            cumul = 0
            formatted_table = []
            for w in table:
                formatted_table.append((w+cumul)/s)
                cumul += w
            formatted.append(formatted_table)
        self.weights = formatted
    
    def get_weighted_index(self, r, weights):
        """Returns an index number depending on r and weights
           
           Args:
               r: a float between 0 and 1
               weights: list of weights
           
           Returns: an index number (between 0 and len(weights)-1)
        """
        for i, p in enumerate(weights):
            if r < p:
                return i
    
    def program_change(self, num=0):
        m = mido.Message('program_change', channel=self.channel, program=num)
        if __debug__:
            print(m)
        self.midi.send(m)
    
    def set_volume(self, vol):
        self.volume = vol
    
    def play_notes_random_dur(self, notes):
        """ Play notes with a random duration
            
            Note duration (dur):
                duration (in ticks) = note value × self.timesig[1] × TICKS_PER_BEAT
                sixteenth note (semiquaver)	1
                eighth note (quaver)		2
                quarter note (crotchet)		4
                half note (minim)		8
                whole note (semibreve)		16
                double note (breve)		32
        """
        vol = int(self.volume * random.gauss(64, 16))
        for note in notes:
            if __debug__:
                print(note, end=' ')
            self.midi.send(mido.Message('note_on', channel=self.channel, note=note, velocity=vol))
        i = self.get_weighted_index(random.random(), self.weights[1])
        self.wait_nticks = self.durations[i] - 1  # skip a tick
        self.played_notes = notes
    
    def play_notes(self, notes, dur=4):
        """ Play notes with a given duration
            
            Note duration (dur):
                duration (in ticks) = note value × self.timesig[1] × TICKS_PER_BEAT
                sixteenth note (semiquaver)	1
                eighth note (quaver)		2
                quarter note (crotchet)		4
                half note (minim)		8
                whole note (semibreve)		16
                double note (breve)		32
        """
        vol = int(self.volume * random.gauss(64, 16))
        for note in notes:
            if __debug__:
                print(note, end=' ')
            self.midi.send(mido.Message('note_on', channel=self.channel, note=note, velocity=vol))
        self.wait_nticks = dur - 1  # skip a tick
        self.played_notes = notes
    
    def tick(self, r1, r2):
        if self.wait_nticks > 0:
            self.wait_nticks -= 1
            return
        if self.played_notes:
            for note in self.played_notes:
                self.midi.send(mido.Message('note_off', channel=self.channel, note=note))
        
        i = self.get_weighted_index(r1, self.weights[0])
        eval("self.f{}(r2)".format(i))
    
    def f0(self, r):
        """Silence"""
        i = self.get_weighted_index(random.random(), self.weights[2])
        self.wait_nticks = self.durations[i] - 1
        if __debug__:
            print('-', end=' ')


class Chaotic(StochaPlayer):
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Chaotic, self).__init__(midiout, channel, timesig)
        self.update_weights([[5, 2, 2, 1],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def f1(self, r):
        """Play a random note"""
        pitch = random.choice(self.scale)
        self.play_notes_random_dur([pitch])
    
    def f2(self, r):
        """Play two different random notes"""
        notes = random.sample(self.scale, 2)
        self.play_notes_random_dur(notes)
    
    def f3(self, r):
        """Play three different random notes"""
        notes = random.sample(self.scale, 3)
        self.play_notes_random_dur(notes)


class Basic(StochaPlayer):
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Basic, self).__init__(midiout, channel, timesig)
        self.update_weights([[5, 2, 2, 1],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def f1(self, r):
        """Play a random note"""
        pitch = random.choice(self.scale)
        self.play_notes_random_dur([pitch])
    
    def f2(self, r):
        """Play two different random notes"""
        note = random.choice(self.scale)
        interval = random.choice([4, 5, 6, 12]) ### TODO: this is bad
        self.play_notes_random_dur([note, note+interval])
    
    def f3(self, r):
        """Play a triad"""
        ### TODO: la note de l'accord peut dépasser la valeur 127 !
        root = random.choice(self.scale)
        chord_name, chord = self.chords[int(r*len(self.chords))]
        notes = [root+interval for interval in chord] 
        self.play_notes_random_dur(notes)
        print(chord_name, end=' ')


class Soloist(StochaPlayer):
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Soloist, self).__init__(midiout, channel, timesig)
        self.direction = 1
        self.index = 0
        self.update_weights([[2, 1, 4, 4, 2],
            [8, 12, 1, 4, 0, 1, 0, 0, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def f1(self, r):
        """Play a new random note"""
        self.index = int(r*len(self.scale))
        self.play_notes_random_dur([self.scale[self.index]])
    
    def f2(self, r):
        """Play next note on scale (1 step)"""
        self.index = (self.index + self.direction) % len(self.scale)
        self.play_notes_random_dur([self.scale[self.index]])
    
    def f3(self, r):
        """Play next note on scale (2 steps)"""
        self.index = (self.index + 2*self.direction) % len(self.scale)
        self.play_notes_random_dur([self.scale[self.index]])
    
    def f4(self, r):
        """Change direction (up/down)"""
        self.direction = -self.direction
        self.f2(r)


class Pad(Basic):
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Pad, self).__init__(midiout, channel, timesig)
        self.durations = list(map(lambda x: x*4, self.durations))
        self.update_weights([[6, 2, 2, 4],
            [1, 2, 0, 10, 0, 6, 0, 6, 0, 4],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])


class Monotone(StochaPlayer):
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Monotone, self).__init__(midiout, channel, timesig)
        self.pitch = random.choice(self.scale)
        self.durations = list(map(lambda x: x*4, self.durations))
        self.update_weights([[1, 10, 2, 1],
            [],
            [1, 2, 0, 10, 0, 4, 0, 1, 0, 1]])
    
    def f1(self, r):
        """Play on beat"""
        self.play_notes([self.pitch], TICKS_PER_BEAT)
    
    def f2(self, r):
        """Play on half beat"""
        self.play_notes([self.pitch], TICKS_PER_BEAT // 2)
   
    def f3(self, r):
        """Change pitch"""
        i = self.get_weighted_index(r, self.scale)
        self.pitch = self.scale[i]
        self.f1(r)


################################################################################
################################################################################
################################################################################


class devicePickerGui:
    def __init__(self, top):
        self.top = top
        self.top.title("Midi output ports")
        frame = tk.Frame(top)
        frame.pack()
        
        self.buttons = []
        
        for d in mido.get_output_names():
            self.buttons.append(tk.Button(frame, text=d, command=lambda dev=d: self.openPort(dev)))
            self.buttons[-1].pack()
        
    def openPort(self, device):
        global midiout
        midiout = mido.open_output(device, autoreset=True)
        top.destroy()


################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    #mido.set_backend('mido.backends.portmidi')
    if __debug__:
        print(mido.get_output_names())
        
    midiout = None
    top = tk.Tk()
    devicePickerGui(top)
    top.mainloop()
    s = Monotone(midiout, channel=0)
    s.program_change(92)
    s2 = Soloist(midiout, channel=1)
    s2.program_change(84)
    s2.set_volume(0.5)
    s.set_scale(create_scale(C1, gypsy, 2))
    s2.set_scale(create_scale(C3, major, 2))
    
    tempo = 120
    time_step = 60/tempo
    # Time step is divided by 4 for better resolution (4 ticks per beat)
    time_step /= TICKS_PER_BEAT
    
    random.seed(0)
    while True:
        r1 = random.random()
        r2 = random.random()
        s.tick(r1, r2)
        #s2.tick(r1, r2)
        if __debug__:
            print('.')
        time.sleep(time_step)
