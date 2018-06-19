#! /usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import division, print_function
import sys
import random
import time
import heapq
import mido
from players import *

# Backward compatibility with python 2.7
if sys.version_info[0] < 3:
    import Tkinter as tk
else:
    import tkinter as tk


TICKS_PER_BEAT = 4

C1 = 36
C2 = 48
C3 = 60

# diatonic scales
scales = {
    'ionian':      [2, 2, 1, 2, 2, 2, 1],
    'dorian':      [2, 1, 2, 2, 2, 1, 2],
    'phrygian':    [1, 2, 2, 2, 1, 2, 2],
    'lydian':      [2, 2, 2, 1, 2, 2, 1],
    'myxolidian':  [2, 2, 1, 2, 2, 1, 2],
    'aeolian':     [2, 1, 2, 2, 1, 2, 2],
    'locrian':     [1, 2, 2, 1, 2, 2, 2],

    'hirajoshi':   [4, 2, 1, 4, 1],
    'insen':       [1, 4, 2, 3, 2],
    'iwato':       [1, 4, 1, 4, 2],

    'enigmatic':   [1, 3, 2, 2, 2, 1, 1],
    'flamenco':    [1, 3, 1, 2, 1, 3, 1],
    'gypsy':       [2, 1, 3, 1, 1, 2, 2],
    'prometheus':  [2, 2, 2, 3, 1, 2],
    'phrygiandom': [1, 3, 1, 2, 1, 2, 2],
}
scales['major'] = scales['ionian']
scales['minor'] = scales['aeolian']


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


class DevicePickerGui:
    def __init__(self, top):
        self.top = top
        self.top.title("Midi output ports")
        frame = tk.Frame(top)
        frame.pack()
        
        self.buttons = []
        
        for d in mido.get_output_names():
            self.buttons.append(tk.Button(frame, text=d,
                command=lambda dev=d: self.openPort(dev)))
            self.buttons[-1].pack()
        
    def openPort(self, device):
        global midiout
        midiout = mido.open_output(device, autoreset=True)
        top.destroy()


class PlayerUI(tk.Frame):
    def __init__(self, master, player):
        super(PlayerUI, self).__init__(master)
        self.player = player
        self.active = tk.IntVar()
        self.active.set(True)
        btn_activate = tk.Checkbutton(self, variable=self.active,
            command=self.activate)
        btn_activate.pack()
        lbl = tk.Label(self)
        lbl["text"] = "yooooo"
        lbl.pack()
    
    def activate(self):
        self.player.active = self.active.get()
    
    def tick(self, *args):
        self.player.tick(*args)


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super(MainWindow, self).__init__(master)
        self.master = master
        self.master.title("StochaPlay")
        #self.master.geometry("400x400")
        
        self.midiout = mido.open_output('amsynth:MIDI IN 128:0', autoreset=True)
        assert(self.midiout)
        self.tempo = tk.IntVar()
        self.tempo.trace("w", self.update_time_step)
        self.tempo.set(120)
        self.players = []
        
        self.pack()
        self.init_window()
        self.init_players()
        
        self.tick()
    
    def init_players(self):
        s = Soloist(self.midiout, channel=0)
        s.set_volume(0.5)
        s.set_scale(create_scale(C2, scales['minor']))
        s2 = Pad(self.midiout, channel=1)
        s2.set_volume(0.5)
        s2.set_scale(create_scale(C1, scales['minor'], 2))
        self.add_player(s)
        self.add_player(s2)
    
    def init_window(self):
        # Menu
        menu = tk.Menu(self)
        self.master.config(menu=menu)
        file = tk.Menu(menu)
        file.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file)
        about = tk.Menu(menu)
        menu.add_cascade(label="About", menu=about)
        
        self.box_tempo = tk.Spinbox(self, from_=1, to=240)
        self.box_tempo["textvariable"] = self.tempo
        #self.box_tempo.bind("<Button-1>", self.test)
        self.box_tempo.pack(side="left")
        
        self.btn_mutate = tk.Button(self)
        self.btn_mutate["text"] = "Mutate"
        self.btn_mutate.pack(side="left")
        
        self.frame_players = tk.Frame(self)
        self.frame_players.pack()
    
    def add_player(self, player):
        p = PlayerUI(self.frame_players, player)
        p.pack()
        self.players.append(p)
        print(self.players) ###
    
    def update_time_step(self, *args):
        dt = 60000 / self.tempo.get()
        # Time step is divided by 4 for better resolution (4 ticks per beat)
        dt /= TICKS_PER_BEAT
        self.time_step = int(dt)
    
    def client_exit(self):
        self.midiout.close()
        self.master.destroy()
        sys.exit()
    
    def tick(self):
        r1 = random.random()
        r2 = random.random()
        for p in self.players:
            p.tick(r1, r2)
        if __debug__:
            print('.')
        self.master.after(self.time_step, self.tick)


################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    #mido.set_backend('mido.backends.portmidi')
    if __debug__:
        print(mido.get_output_names())
        
    midiout = None
    """
    top = tk.Tk()
    devicePickerGui(top)
    top.mainloop()
    """
    
    random.seed(0)
    
    # Tkinter GUI below
    root = tk.Tk()
    app = MainWindow(master=root)
    app.mainloop()
