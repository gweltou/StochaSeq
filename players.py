#! /usr/bin/env python
# -*- coding: utf-8 -*-

import random
import mido

TICKS_PER_BEAT = 4


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
        self.active = False
        self.wait_nticks = 0
        self.played_notes = []
        self.scale = scale
        if self.scale:
            self.set_scale(self.scale)
        self.weights_desc = ["functions",
                             "silence durations",
                             "note/chord durations"]
        self.update_weights([[5, 2, 2, 1],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def set_scale(self, scale):
        self.scale = sorted(scale)
    
    def update_weights(self, weights):
        assert(len(weights) > 0)
        self.weights = weights
        self._fweights = []
        for table in self.weights:
            s = sum(table)
            cumul = 0
            formatted_table = []
            for w in table:
                formatted_table.append((w+cumul)/s)
                cumul += w
            self._fweights.append(formatted_table)
    
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
    
    def stop_all_notes(self):
        for note in self.played_notes:
            self.midi.send(mido.Message('note_off',
                                        channel=self.channel, note=note))
        self.wait_nticks = 0
    
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
            i = self.get_weighted_index(random.random(), self._fweights[2])
            dur = self.durations[i]
        self.wait_nticks = dur - 1  # skip a tick
        self.played_notes = notes
    
    def tick(self, *rand):
        if self.wait_nticks > 0:
            self.wait_nticks -= 1
            return
        for note in self.played_notes:
            self.midi.send(mido.Message('note_off',
                                        channel=self.channel, note=note))
        
        if self.active:
            i = self.get_weighted_index(rand[0], self._fweights[0])
            eval("self.f{}(*rand[1:])".format(i))
    
    def f0(self, *rand):
        """Silence"""
        i = self.get_weighted_index(rand[0], self._fweights[1])
        self.wait_nticks = self.durations[i] - 1
        if __debug__:
            print('-', end=' ')


class Chaotic(StochaPlayer):
    name = "Chaotic"
    color = "#aa5555"
    
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Chaotic, self).__init__(midiout, channel, timesig)
        self.update_weights([[5, 2, 2, 1],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def f1(self, *rand):
        """Play a random note"""
        pitch = random.choice(self.scale)
        self.play_notes([pitch])
    
    def f2(self, *rand):
        """Play two different random notes"""
        notes = random.sample(self.scale, 2)
        self.play_notes(notes)
    
    def f3(self, *rand):
        """Play three different random notes"""
        notes = random.sample(self.scale, 3)
        self.play_notes(notes)


class Basic(StochaPlayer):
    name = "Basic"
    color = "#00ff00"
    
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Basic, self).__init__(midiout, channel, timesig)
        self.update_weights([[5, 2, 2, 1],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def f1(self, *rand):
        """Play a random note"""
        note = self.scale[int(rand[0]*len(self.scale))]
        i = self.get_weighted_index(rand[1], self._fweights[2])
        dur =  self.durations[i]
        self.play_notes([note], dur)
    
    def f2(self, *rand):
        """Play two random notes """
        index = int(rand[0]*len(self.scale))
        note = self.scale[index]
        index2 = int(rand[1]*len(self.scale)) % len(self.scale)
        note2 = self.scale[index2]
        i = self.get_weighted_index(rand[1], self._fweights[2])
        dur =  self.durations[i]
        self.play_notes([note, note2], dur)
    
    def f3(self, *rand):
        """Play a triad"""
        i0 = int(rand[0]*len(self.scale))
        i1 = (i0+2) % len(self.scale)
        i2 = (i0+4) % len(self.scale)
        i = self.get_weighted_index(rand[1], self._fweights[2])
        dur =  self.durations[i]
        self.play_notes([self.scale[i0], self.scale[i1], self.scale[i2]], dur)


class Soloist(StochaPlayer):
    name = "Soloist"
    color = "#ff0000"
    
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Soloist, self).__init__(midiout, channel, timesig)
        self.direction = 1
        self.index = 0
        self.update_weights([[2, 1, 4, 4, 2],
            [8, 12, 1, 4, 0, 1, 0, 0, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0]])
    
    def f1(self, *rand):
        """Play a new random note"""
        self.index = int(rand[0]*len(self.scale))
        i = self.get_weighted_index(rand[1], self._fweights[2])
        dur =  self.durations[i]
        self.play_notes([self.scale[self.index]], dur)
    
    def f2(self, *rand):
        """Play next note on scale (1 step)"""
        self.index = (self.index + self.direction) % len(self.scale)
        i = self.get_weighted_index(rand[1], self._fweights[2])
        dur =  self.durations[i]
        self.play_notes([self.scale[self.index]], dur)
    
    def f3(self, *rand):
        """Play next note on scale (2 steps)"""
        self.index = (self.index + 2*self.direction) % len(self.scale)
        i = self.get_weighted_index(rand[1], self._fweights[2])
        dur =  self.durations[i]
        self.play_notes([self.scale[self.index]], dur)
    
    def f4(self, *rand):
        """Change direction (up/down)"""
        self.direction = -self.direction
        self.f2(*rand)


class Pad(Basic):
    name = "Pad"
    color = "#0000ff"
    
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Pad, self).__init__(midiout, channel, timesig)
        self.durations = list(map(lambda x: x*4, self.durations))
        self.update_weights([[6, 2, 2, 4],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 6, 0, 6, 0, 4]])


class Monotone(StochaPlayer):
    name = "Monotone"
    color = "#ff00ff"
    
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(Monotone, self).__init__(midiout, channel, timesig)
        self.pitch = None
        self.durations = list(map(lambda x: x*4, self.durations))
        self.update_weights([[1, 10, 2, 1],
            [],
            [1, 2, 0, 10, 0, 4, 0, 1, 0, 1]])
        self.halfbeat = False
    
    def set_scale(self, scale):
        self.scale = sorted(scale)
        self.pitch = random.choice(self.scale)
    
    def tick(self, *rand):
        if self.wait_nticks > 0:
            self.wait_nticks -= 1
            return
        if self.played_notes:
            for note in self.played_notes:
                self.midi.send(mido.Message('note_off',
                     channel=self.channel, note=note))
        
        if not self.active:
            return
        if self.halfbeat:
            self.f2(*rand[1:])
        else:
            i = self.get_weighted_index(r1, self._fweights[0])
            eval("self.f{}(*rand[1:])".format(i))
    
    def f1(self, *rand):
        """Play on beat"""
        if self.pitch:
            self.play_notes([self.pitch], TICKS_PER_BEAT)
    
    def f2(self, *rand):
        """Play on half beat"""
        if self.pitch:
            self.play_notes([self.pitch], TICKS_PER_BEAT//2)
            self.halfbeat = not self.halfbeat
   
    def f3(self, *rand):
        """Change pitch"""
        self.pitch = self.scale[int(rand[0]*len(self.scale))]
        self.f1(*rand)


class BasicLooper(Basic):
    name = "Basic Looper"
    color = "#aaaa00"
    # States
    SILENCE = 0
    REPEAT1 = 1
    REPEAT2 = 2
    RECORDING = 3
    
    def __init__(self, midiout, channel=0, timesig=(4,4)):
        super(BasicLooper, self).__init__(midiout, channel, timesig)
        self.ticks_counter = 0
        self.ticks_in_measure = TICKS_PER_BEAT * timesig[0]
        self.patterns = []
        self.measure_pattern = []
        self.i_measure = 0
        self.state = self.RECORDING
        self.weights_desc = ["basic functions",
                             "silence durations",
                             "note/chord durations",
                             "looping function"]
        self.update_weights([[1, 3, 2, 1],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [1, 2, 0, 10, 0, 3, 0, 1, 0, 0],
            [0, 1, 2, 2]])
    
    def change_state(self, r):
        i = self.get_weighted_index(r, self._fweights[3])
        self.state = i
        self.ticks_counter = 0
        self.i_measure = 0
        self.stop_all_notes()
    
    def tick(self, *rand):
        #self.ticks_counter += 1
        if self.ticks_counter >= self.ticks_in_measure:
            if self.state == self.REPEAT2 and self.i_measure == 0:
                self.ticks_counter = 0
                self.i_measure += 1
                self.stop_all_notes()
            elif self.state == self.RECORDING:
                # add pattern to memory
                if len(self.patterns) < 2:
                    self.patterns.append(self.measure_pattern)
                else:
                    self.patterns[0] = self.patterns[1]
                    self.patterns[1] = self.measure_pattern[:]
                self.measure_pattern = []
                self.change_state(rand[2])
            else:
                self.change_state(rand[2])
        
        if self.state == self.SILENCE:
            pass
        
        elif self.state == self.REPEAT1:
            if len(self.patterns) >= 1:
                super(BasicLooper, self).tick(*(self.patterns[-1][self.ticks_counter]))
            else:
                pass
                self.state = self.RECORDING
        
        elif self.state == self.REPEAT2:
            if len(self.patterns) >= 2:
                assert(self.ticks_counter<self.ticks_in_measure)
                assert(self.i_measure<len(self.patterns))
                try:
                    super(BasicLooper, self).tick(*(self.patterns[self.i_measure][self.ticks_counter]))
                except IndexError:
                    print(self.ticks_counter)
                    print(self.ticks_in_measure)
                    print(self.i_measure)
                    for p in self.patterns:
                        print(len(p), p)
            else:
                pass
                self.state = self.RECORDING
        
        elif self.state == self.RECORDING:
            self.measure_pattern.append(rand)
            super(BasicLooper, self).tick(*rand)
        
        self.ticks_counter += 1
        
            
