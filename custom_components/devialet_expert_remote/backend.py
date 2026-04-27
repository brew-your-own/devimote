# SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>
# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''Backend communication module for Devialet Expert amplifiers'''

import binascii
import socket
import struct
import math as m


def _crc16(data: bytearray) -> int:
    '''CRC-16/CCITT-FALSE checksum'''
    return binascii.crc_hqx(data, 0xFFFF)


class DeviMoteBackEnd():
    '''Backend class handling all control and status monitoring'''
    UDP_PORT_STATUS = 45454
    UDP_PORT_CMD    = 45455
    VOLUME_LIMIT    = -10

    def __init__(self, host=None):
        '''Backend constructor with default initial values'''
        self._configured_host = host
        self.status = {}
        self.status['dev_name'] = 'Unknown'
        self.status['ip'] = None
        self.status['ch_list']  = {}
        self.status['power'] = False
        self.status['muted'] = False
        self.status['channel'] = 0
        self.status['volume'] = 0
        self.status['connected'] = False
        self.status['crc_ok'] = False
        self.packet_cnt = 0

    def _send_command(self, data: bytearray):
        '''Internal function that builds and transmits a UDP packet command to the amplifier'''
        ip = self.status.get('ip') or self._configured_host
        if not ip:
            return
        sock = socket.socket(socket.AF_INET,    # Internet
                             socket.SOCK_DGRAM) # UDP
        data[0] = 0x44
        data[1] = 0x72
        for _ in range(4):
            data[3] = self.packet_cnt
            data[5] = self.packet_cnt >> 1
            self.packet_cnt += 1
            crc = _crc16(data[0:12])
            data[12] = (crc & 0xff00) >> 8
            data[13] = crc & 0x00ff
            sock.sendto(data, (ip, self.UDP_PORT_CMD))

    def toggle_power(self):
        '''Function for toggling the power status'''
        data = bytearray(142)
        data[6] = int(not self.status['power'])
        data[7] = 0x01
        self._send_command(data)

    def toggle_mute(self):
        '''Function for toggling the mute status'''
        data = bytearray(142)
        data[6] = int(not self.status['muted'])
        data[7] = 0x07
        self._send_command(data)

    def set_volume(self, db_value):
        '''Function for changing the volume'''

        db_value = min(db_value, self.VOLUME_LIMIT)
        # Hardware resolution is 0.5 dB; _db_convert crashes on non-multiples.
        db_value = round(db_value * 2) / 2

        def _db_convert(db_value):
            '''Internal function to convert dB to a 16-bit representation used by set_volume'''
            db_abs = m.fabs(db_value)
            if db_abs == 0:
                retval = 0
            elif db_abs == 0.5:
                retval = 0x3f00
            else:
                retval = (256 >> m.ceil(1 + m.log(db_abs, 2))) + _db_convert(db_abs - 0.5)
            return retval

        volume = _db_convert(db_value)

        if db_value < 0:
            volume |= 0x8000

        data = bytearray(142)
        data[6] = 0x00
        data[7] = 0x04
        data[8] = (volume & 0xff00) >> 8
        data[9] = volume & 0x00ff
        self._send_command(data)

    def set_output(self, output):
        '''Function for changing the output'''
        out_val = 0x4000 | (output << 5)
        data = bytearray(142)
        data[6] = 0x00
        data[7] = 0x05
        data[8] = (out_val & 0xff00) >> 8
        if output > 7:
            data[9] = (out_val & 0x00ff) >> 1
        else:
            data[9] = out_val & 0x00ff
        self._send_command(data)

    def update(self):
        '''Try to get UDP status packet and decode it'''
        sock = socket.socket(socket.AF_INET,    # Internet
                             socket.SOCK_DGRAM) # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.UDP_PORT_STATUS))
        sock.settimeout(2)
        try:
            data, addr = sock.recvfrom(512) # buffer size is 512 bytes
        except socket.timeout:
            self.status['connected'] = False
            return self.status
        self.status['connected'] = True
        self.status['ip'] = addr[0]
        self.status['dev_name'] = data[19:50].decode('UTF-8')
        self.status['ch_list'] = {}
        for i in range(0,15):
            enabled = int(chr(data[52+i*17]))
            if enabled:
                self.status['ch_list'][i] = data[53+i*17:52+(i+1)*17].decode('UTF-8')
        self.status['power']   = (data[307] & 0x80) != 0
        self.status['muted']   = (data[308] & 0x2) != 0
        self.status['channel'] = (data[308] & 0x3c) >> 2
        self.status['volume']  =  data[310]
        self.status['crc_ok']  = _crc16(data[:-2]) == struct.unpack('>H',data[-2:])[0]

        return self.status
