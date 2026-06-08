# SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>
# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''Unofficial library for controlling Devialet Expert (non-Pro) amplifiers over UDP.'''

from .backend import DeviMoteBackEnd, DevialetExpertNonPro, _crc16

__all__ = ['DeviMoteBackEnd', 'DevialetExpertNonPro', '_crc16', '__version__']

__version__ = '0.1.0'
