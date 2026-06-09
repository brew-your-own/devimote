# SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>
# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''CRC-16/CCITT-FALSE tests, including the canonical check value.'''

from pydevialet_expert_nonpro import DeviMoteBackEnd
from pydevialet_expert_nonpro.backend import _crc16


def test_canonical_check_value():
    '''The canonical CCITT-FALSE check value for "123456789" is 0x29B1.'''
    assert _crc16(bytearray(b'123456789')) == 0x29B1


def test_empty_input_returns_initial_value():
    '''An empty input yields the unmodified 0xFFFF initial value.'''
    assert _crc16(bytearray()) == 0xFFFF


def test_command_packet_carries_valid_crc(net):
    '''_send_command writes a correct CRC over the first 12 bytes into bytes 12-13.'''
    backend = DeviMoteBackEnd(host='192.0.2.10')
    backend.toggle_power()

    assert net['sent'], 'expected at least one command packet to be sent'
    data, addr = net['sent'][0]
    assert addr == ('192.0.2.10', DeviMoteBackEnd.UDP_PORT_CMD)
    expected = _crc16(bytearray(data[0:12]))
    assert (data[12] << 8) | data[13] == expected
