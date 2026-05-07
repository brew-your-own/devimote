# SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''An unofficial remote control application for Devialet Expert amplifiers'''

from kivy.app import App
from kivy.properties import ObjectProperty # pylint: disable=no-name-in-module
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout

from backend import DeviMoteBackEnd  # pylint: disable=import-error

class DeviMoteVolume(BoxLayout):
    '''Wrapper class around BoxLayout'''
    vol_slider: ObjectProperty(None)

    def set_byte (self, byte):
        '''Function to adjust the volume slider'''
        self.vol_slider.value = byte

class DeviMoteWidget(GridLayout):
    '''Top-level widget'''
    channels  = ObjectProperty(None)
    volume    = ObjectProperty(None)
    stat_line = ObjectProperty(None)
    sw_power  = ObjectProperty(None)
    sw_mute   = ObjectProperty(None)

    def set_volume(self, byte):
        '''Function to adjust the volume'''
        self.volume.set_byte(byte)

    def update(self, status):
        '''Function to update all GUI elements based on current status'''
        if status and status['connected']:
            self.stat_line.text = 'Status: Connected'
            if status['power']:
                self.sw_power.state = 'down'
                self.sw_power.text  = 'ON'
                self.sw_power.background_color = [1, 1, 1, 1]
            elif status['booting']:
                self.sw_power.state = 'down'
                self.sw_power.text  = 'BOOTING'
                self.sw_power.background_color = [.25, .25, .25, 1]
            else:
                self.sw_power.state = 'normal'
                self.sw_power.text  = 'STANDBY'
                self.sw_power.background_color = [1, 1, 1, 1]
            self.sw_mute.state  = 'down' if status['muted'] else 'normal'
            self.volume.set_byte(status['volume'])
            if not self.channels.values:
                for channel in status['ch_list']:
                    self.channels.values.append(status['ch_list'][channel])
            self.channels.text = status['ch_list'][status['channel']]
        else:
            self.stat_line.text  = 'Status: Not connected'

class DeviMoteApp(App):
    '''Top-level class combining the backend and the top-level widget'''
    def __init__(self):
        '''Constructor'''
        super().__init__()
        self.gui = None
        self.backend = None
        self.status = None

    def _powered(self, _dt):
        '''Internal function to use during booting'''
        self.status['booting'] = False

    def toggle_power_callback(self, _instance):
        '''Callback function for toggling power'''
        if self.status['booting']:
            return
        if not self.status['power']:
            self.status['booting'] = True
            Clock.schedule_once(self._powered, 20)
        self.backend.toggle_power()

    def toggle_mute_callback(self, _instance):
        '''Callback function for toggling mute'''
        self.backend.toggle_mute()

    def set_volume_callback(self, _instance, value):
        '''Callback function for changing the volume'''
        if value != self.status['volume']:
            self.backend.set_volume((value-195.0) / 2)

    def set_output_callback(self, _instance, text):
        '''Callback function for changing the output'''
        for channel in self.status['ch_list']:
            if text == self.status['ch_list'][channel]:
                output = channel
                break
        if output != self.status['channel']:
            self.backend.set_output(output)

    def build(self):
        '''Kivy build function, runs once'''
        self.gui = DeviMoteWidget()
        self.backend = DeviMoteBackEnd()
        self.status = self.backend.update()
        self._powered(0)
        self.gui.update(self.status)
        self.gui.sw_power.bind(on_press=self.toggle_power_callback)
        self.gui.sw_mute.bind(on_press=self.toggle_mute_callback)
        self.gui.volume.vol_slider.bind(value=self.set_volume_callback)
        self.gui.channels.bind(text=self.set_output_callback)
        Clock.schedule_interval(self.update, 0.1)
        return self.gui

    def update(self, _dt):
        '''Function to update both the backend and the GUI. Scheduled to run periodically'''
        self.status = self.backend.update()
        if self.status['power']:
            self._powered(0)
        self.gui.update(self.status)

    def report(self):
        '''Pretty-print current status'''
        if not self.status['crc_ok']:
            print ('[CRC ERROR]')
            return
        if self.status['connected']:
            print (
                f"[{'ON ' if self.status['power'] else 'OFF'}]"
                f" {self.status['dev_name']} ({self.status['ip']}),"
                f" volume: {(self.status['volume'] - 195) / 2.0}dB"
                f" {self.status['ch_list'][self.status['channel']]}"
                f"{'[M]' if self.status['muted'] else ''}"
            )

def main():
    '''Entry point for the GUI'''
    DeviMoteApp().run()

if __name__ == '__main__':
    main()
