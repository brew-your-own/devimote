# SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>
# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''Status packet decoding tests against synthetic 512-byte frames.'''

from pydevialet_expert_nonpro import DeviMoteBackEnd
from pydevialet_expert_nonpro.backend import _crc16


def _build_status_packet(channels=None, power=True, muted=True, channel=2):
    '''Assemble a valid 512-byte status frame with a correct trailing CRC.'''
    channels = channels or {0: 'Phono', 2: 'Toslink'}
    packet = bytearray(512)

    packet[19:19 + len('TestAmp')] = b'TestAmp'

    # Every channel's enabled flag is read via int(chr(byte)), so all 15 must be ASCII digits.
    for i in range(15):
        packet[52 + i * 17] = ord('0')
    for idx, name in channels.items():
        packet[52 + idx * 17] = ord('1')
        packet[53 + idx * 17:53 + idx * 17 + 16] = name.encode('UTF-8').ljust(16)[:16]

    packet[307] = 0x80 if power else 0x00
    ch_byte = (channel << 2) & 0x3c
    if muted:
        ch_byte |= 0x02
    packet[308] = ch_byte
    packet[310] = 175  # raw 175 -> (175-195)/2 = -10 dB

    crc = _crc16(packet[:-2])
    packet[510] = (crc >> 8) & 0xff
    packet[511] = crc & 0xff
    return bytes(packet)


def test_decodes_all_fields(net):
    '''A well-formed frame decodes every status field correctly.'''
    net['recv'] = (_build_status_packet(), ('192.168.1.50', 45454))
    status = DeviMoteBackEnd().update()

    assert status['connected'] is True
    assert status['ip'] == '192.168.1.50'
    assert status['dev_name'].startswith('TestAmp')
    assert status['power'] is True
    assert status['muted'] is True
    assert status['channel'] == 2
    assert status['volume'] == 175
    assert status['crc_ok'] is True
    assert {i: n.strip() for i, n in status['ch_list'].items()} == {0: 'Phono', 2: 'Toslink'}


def test_ch_list_only_contains_enabled_channels(net):
    '''Only channels whose enabled flag is set appear in ch_list.'''
    net['recv'] = (_build_status_packet(channels={5: 'Optical'}), ('192.168.1.50', 45454))
    status = DeviMoteBackEnd().update()
    assert list(status['ch_list']) == [5]


def test_bad_crc_flagged(net):
    '''A corrupted checksum sets crc_ok to False.'''
    packet = bytearray(_build_status_packet())
    packet[511] ^= 0xFF  # corrupt the checksum
    net['recv'] = (bytes(packet), ('192.168.1.50', 45454))
    status = DeviMoteBackEnd().update()
    assert status['crc_ok'] is False


def test_timeout_marks_disconnected(net):
    '''A receive timeout marks the device disconnected.'''
    net['recv'] = None  # fake socket raises socket.timeout
    status = DeviMoteBackEnd().update()
    assert status['connected'] is False
