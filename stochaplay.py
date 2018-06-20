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


C1 = 36
C2 = 48
C3 = 60

PLAYERS = [Basic, Chaotic, Soloist, Pad, Monotone]


# Diatonic scales
scales = {
    'ionian/Major': [2, 2, 1, 2, 2, 2, 1],
    'dorian':       [2, 1, 2, 2, 2, 1, 2],
    'phrygian':     [1, 2, 2, 2, 1, 2, 2],
    'lydian':       [2, 2, 2, 1, 2, 2, 1],
    'myxolidian':   [2, 2, 1, 2, 2, 1, 2],
    'aeolian/minor':[2, 1, 2, 2, 1, 2, 2],
    'locrian':      [1, 2, 2, 1, 2, 2, 2],

# Pentatonic scales
    'hirajoshi':    [4, 2, 1, 4, 1],
    'insen':        [1, 4, 2, 3, 2],
    'iwato':        [1, 4, 1, 4, 2],

# Other scales
    'enigmatic':    [1, 3, 2, 2, 2, 1, 1],
    'flamenco':     [1, 3, 1, 2, 1, 3, 1],
    'gypsy':        [2, 1, 3, 1, 1, 2, 2],
    'prometheus':   [2, 2, 2, 3, 1, 2],
    'phrygiandom':  [1, 3, 1, 2, 1, 2, 2],
}


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

"""
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
"""


class PlayerUI(tk.Frame):
    def __init__(self, master, player):
        super(PlayerUI, self).__init__(master)
        self.master = master
        self.player = player
        self.active = tk.IntVar()
        self.active.set(self.player.active)
        self.dialog_midi = None
        self.dialog_key = None
        self.dialog_weights = None
        
        # Name label
        lbl_name = tk.Label(self,
                            text=self.player.name.upper().ljust(10, '_')[:10])
        lbl_name.pack(side="left")
        
        # Midi button
        btn_midi = tk.Button(self, text="MIDI",
            command=self.open_midi_dialog)
        btn_midi.pack(side="left")
        
        # Key button
        btn_key = tk.Button(self, text="Key",
            command=self.open_key_dialog)
        btn_key.pack(side="left")
        
        # Weights button
        btn_weights = tk.Button(self, text="Probability weights",
            command=self.open_weights_dialog)
        btn_weights.pack(side="left")
    
        # Activate checkbox
        btn_activate = tk.Checkbutton(self, variable=self.active,
            command=self.activate)
        btn_activate.pack(side="left")
    
    def activate(self):
        self.player.active = self.active.get()
    
    def open_midi_dialog(self):
        if self.dialog_midi == None:
            self.dialog_midi = MidiDialog(self, self.player)
        else:
            self.dialog_midi.close_window()
    
    def open_key_dialog(self):
        if self.dialog_key == None:
            self.dialog_key = KeyDialog(self, self.player)
        else:
            self.dialog_key.close_window()
    
    def open_weights_dialog(self):
        if self.dialog_weights == None:
            pass
        else:
            self.dialog_weights.close_window()
    
    def tick(self, *args):
        self.player.tick(*args)


class MidiDialog(tk.Toplevel):
    def __init__(self, master, player):
        super(MidiDialog, self).__init__(master)
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.master = master
        self.player = player
        
        # Name label
        lbl_name = tk.Label(self, text=self.player.name.upper())
        lbl_name.pack()
        
        # Midi channel
        self.channel = tk.IntVar()
        self.channel.set(self.player.channel)
        spinb_channel = tk.Spinbox(self, from_=1, to=16)
        spinb_channel["textvariable"] = self.channel
        tk.Label(self, text="Midi channel:").pack()
        spinb_channel.pack()
        
        # Midi program
        self.program = tk.IntVar()
        self.program.set(self.player.program)
        spinb_program = tk.Spinbox(self, from_=0, to=127)
        spinb_program["textvariable"] = self.program
        tk.Label(self, text="Midi program:").pack()
        spinb_program.pack()
        
        # Midi volume
        self.volume = tk.IntVar()
        self.volume.set(self.player.volume*100)
        scale_volume = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL)
        scale_volume["variable"] = self.volume
        tk.Label(self, text="Volume:").pack()
        scale_volume.pack()
        
        # OK Button
        btn_ok = tk.Button(self, text="OK", command=self.on_ok)
        btn_ok.pack()
        
    def on_ok(self):
        self.player.channel = self.channel.get()
        self.player.program_change(self.program.get())
        self.player.set_volume(self.volume.get()/100)
    
    def close_window(self):
        self.master.dialog_midi = None
        self.destroy()


class KeyDialog(tk.Toplevel):
    def __init__(self, master, player):
        super(KeyDialog, self).__init__(master)
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.master = master
        self.player = player
        
        # Name label
        lbl_name = tk.Label(self, text=self.player.name.upper())
        lbl_name.pack()
        
        tk.Label(self, text="Scale:").pack()
        self.scale_frame = tk.Frame(self)
        self.scale_frame.pack()
        scrollbar = tk.Scrollbar(self.scale_frame, orient=tk.VERTICAL)
        scrollbar.config(command=self.yview)
        scrollbar.pack(side="right", fill=tk.Y)
        self.listb_scales = tk.Listbox(self.scale_frame,
            yscrollcommand=scrollbar.set)
        self.listb_scales.pack()
        self.listb_scales.bind('<Double-Button-1>', self.on_ok)
        for s in sorted(scales.keys()):
            self.listb_scales.insert(tk.END, s)
        
        self.rootnote = tk.IntVar()
        self.rootnote.set(self.player.scale[0])
        self.spinb_rootnote = tk.Spinbox(self, from_=0, to=127)
        self.spinb_rootnote["textvariable"] = self.rootnote
        tk.Label(self, text="Root note:").pack()
        self.spinb_rootnote.pack()
        
        self.octavespan = tk.IntVar()
        self.octavespan.set(1)
        self.spinb_octavespan = tk.Spinbox(self, from_=1, to=5)
        self.spinb_octavespan["textvariable"] = self.octavespan
        tk.Label(self, text="Span (octaves):").pack()
        self.spinb_octavespan.pack()
        
        # OK Button
        btn_ok = tk.Button(self, text="OK", command=self.on_ok)
        btn_ok.pack()
    
    def yview(self, *args):
        self.listb_scales.yview(*args)
    
    def on_ok(self, *args):
        index = self.listb_scales.curselection()
        scale_name = self.listb_scales.get(tk.ACTIVE)
        print("Changed {} scale to {}".format(self.player.name, scale_name))
        self.player.set_scale(create_scale(self.rootnote.get(),
            scales[scale_name], self.octavespan.get()))
    
    def close_window(self):
        self.master.dialog_key = None
        self.destroy()


class AddDialog(tk.Toplevel):
    default_scale = create_scale(C2, scales['ionian/Major'], 1)
    
    def __init__(self, master):
        super(AddDialog, self).__init__(master)
        self.master = master
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.grab_set()
        
        upper_frame = tk.Frame(self)
        upper_frame.pack()
        players_frame = tk.Frame(upper_frame)
        players_frame.pack(side="left")
        tk.Label(players_frame, text="Player:").pack()
        scrollbar = tk.Scrollbar(players_frame, orient=tk.VERTICAL)
        scrollbar.config(command=self.yview)
        scrollbar.pack(side="right", fill=tk.Y)
        self.listb_players = tk.Listbox(players_frame,
            yscrollcommand=scrollbar.set)
        self.listb_players.pack()
        #listb_scales.bind('<<ListboxSelect>>', self.on_scale)
        for p in PLAYERS:
            self.listb_players.insert(tk.END, p.name)
        
        buttons_frame = tk.Frame(self)
        buttons_frame.pack()
        btn_ok = tk.Button(buttons_frame, text="Ok", command=self.ok)
        btn_ok.pack(side="left")
        btn_cancel = tk.Button(buttons_frame, text="Cancel", command=self.cancel)
        btn_cancel.pack(side="left")
    
    def yview(self, *args):
        self.listb_scales.yview(*args)
    
    def ok(self):
        index = self.listb_players.curselection()
        P = PLAYERS[index[0]](self.master.midiout)
        P.set_scale(self.default_scale)
        self.master.add_player(P)
        self.destroy()
    
    def cancel(self):
        self.destroy()


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super(MainWindow, self).__init__(master)
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.client_exit)
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
        s = Soloist(self.midiout, channel=2)
        s.set_volume(0.5)
        s.set_scale(create_scale(C2, scales['gypsy'], 3))
        s2 = Pad(self.midiout, channel=1)
        s2.set_volume(0.5)
        s2.set_scale(create_scale(C1, scales['aeolian/minor'], 2))
        self.add_player(s)
        self.add_player(s2)
    
    def add_player(self, player):
        p = PlayerUI(self.frame_players, player)
        p.pack()
        self.players.append(p)
        print("Player added...")
    
    def init_window(self):
        print("init window")
        # Menu
        menu = tk.Menu(self)
        self.master.config(menu=menu)
        file = tk.Menu(menu)
        file.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file)
        about = tk.Menu(menu)
        menu.add_cascade(label="About", menu=about)
        
        self.toolbar = tk.Frame(self)
        self.toolbar.pack()
        self.spinb_tempo = tk.Spinbox(self.toolbar, from_=1, to=240)
        self.spinb_tempo["textvariable"] = self.tempo
        self.spinb_tempo.pack(side="left")
        btn_add = tk.Button(self.toolbar, text="+",
            command=self.add_player_dialog)
        btn_add.pack(side="left")
        
        self.frame_players = tk.Frame(self)
        self.frame_players.pack()
    
    def update_time_step(self, *args):
        dt = 60000 / self.tempo.get()
        # Time step is divided by 4 for better resolution (4 ticks per beat)
        dt /= TICKS_PER_BEAT
        self.time_step = int(dt)
    
    def add_player_dialog(self):
        self.wait_window(AddDialog(self))
    
    def client_exit(self):
        print("Goodbye !")
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
    
    #random.seed(0)
    
    # Tkinter GUI below
    root = tk.Tk()
    app = MainWindow(master=root)
    app.mainloop()
