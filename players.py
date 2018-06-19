#! /usr/bin/env python
# -*- coding: utf-8 -*-

import random
import mido


class StochaPlayer(object):
    durations = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    chords = [('Maj', (0, 4, 7)),
              ('min', (0, 3, 7)),
              ('Aug', (0, 4, 8)),
              ('dim', (0, 3, 6)),
              ]
    
    def __init__(self, midiout, channel=0, timesig=(4,4), scale=None):
        assert(midiout)
        self.midi = midiout
        self.channel = channel
        self.program = 0
        self.volume = 1
        self.timesig = timesig
        self.active = True
        self.wait_nticks = 0
        self.played_notes = []
        self.scale = scale
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
        self.program = num
    
    def set_volume(self, vol):
        self.volume = vol
    
    def play_notes(self, notes, dur=None):
        """ Play notes with a given (or random if dur=None) duration
            
            Args:
                dur: duration of the note (in ticks). If none (or value 0),
                     a random duration will be chosen.
            
                Note duration (in ticks) = note value × self.timesig[1] × TICKS_PER_BEAT
                    sixteenth note (semiquaver)		1
                    eighth note (quaver)	    	2
                    quarter note (crotchet)	    	4
                    half note (minim)		    	8
                    whole note (semibreve)	    	16
                    double note (breve)			    32
        """
        vol = int(self.volume * random.gauss(64, 16))
        for note in notes:
            if __debug__:
                print(note, end=', ')
            self.midi.send(mido.Message('note_on', channel=self.channel,
                note=note, velocity=vol))
        if not dur:
            i = self.get_weighted_index(random.random(), self.weights[1])
            dur = self.durations[i]
        self.wait_nticks = dur - 1  # skip a tick
        self.played_notes = notes
    
    def tick(self, r1, r2):
        if self.wait_nticks > 0:
            self.wait_nticks -= 1
            return
        if self.played_notes:
            for note in self.played_notes:
                self.midi.send(mido.Message('note_off', channel=self.channel,
                    note=note))
        
        if self.active:
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
        self.play_notes([pitch])
    
    def f2(self, r):
        """Play two different random notes"""
        notes = random.sample(self.scale, 2)
        self.play_notes(notes)
    
    def f3(self, r):
        """Play three different random notes"""
        notes = random.sample(self.scale, 3)
        self.play_notes(notes)


class Basic(StochaPlayer):
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Basic, self).__init__(midiout, channel, timesig)
        self.update_weights([[5, 2, 2, 1],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def f1(self, r):
        """Play a random note"""
        note = self.scale[int(r*len(self.scale))]
        self.play_notes([note])
    
    def f2(self, r):
        """Play two harmonious notes """
        note = self.scale[int(r*len(self.scale))]
        interval = random.choice([4, 5, 7, 12]) ### TODO: this is bad
        self.play_notes([note, note+interval])
    
    def f3(self, r):
        """Play a triad"""
        ### TODO: la note de l'accord peut dépasser la valeur 127 !
        root = self.scale[int(r*len(self.scale))]
        chord_name, chord = self.chords[int(r*len(self.chords))]
        notes = [root+interval for interval in chord] 
        self.play_notes(notes)
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
        self.play_notes([self.scale[self.index]])
    
    def f2(self, r):
        """Play next note on scale (1 step)"""
        self.index = (self.index + self.direction) % len(self.scale)
        self.play_notes([self.scale[self.index]])
    
    def f3(self, r):
        """Play next note on scale (2 steps)"""
        self.index = (self.index + 2*self.direction) % len(self.scale)
        self.play_notes([self.scale[self.index]])
    
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
        self.halfbeat = False
    
    def tick(self, r1, r2):
        if self.wait_nticks > 0:
            self.wait_nticks -= 1
            return
        if self.played_notes:
            for note in self.played_notes:
                self.midi.send(mido.Message('note_off', channel=self.channel, note=note))
        
        if self.halfbeat:
            self.f2(r2)
        else:
            i = self.get_weighted_index(r1, self.weights[0])
            eval("self.f{}(r2)".format(i))
    
    def f1(self, r):
        """Play on beat"""
        self.play_notes([self.pitch], TICKS_PER_BEAT)
    
    def f2(self, r):
        """Play on half beat"""
        self.play_notes([self.pitch], TICKS_PER_BEAT//2)
        self.halfbeat = not self.halfbeat
   
    def f3(self, r):
        """Change pitch"""
        self.pitch = self.scale[int(r*len(self.scale))]
        self.f1(r)

