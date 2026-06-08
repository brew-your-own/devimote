# SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>
# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''Shared pytest fixtures: a fake UDP socket so tests need no real amplifier.'''

import pytest

from pydevialet_expert_nonpro import backend


class _FakeSocket:
    '''Stand-in for socket.socket that records sends and replays a canned receive.'''

    # pylint: disable=missing-function-docstring
    def __init__(self, state):
        self._state = state

    def setsockopt(self, *args):
        pass

    def bind(self, *args):
        pass

    def settimeout(self, *args):
        pass

    def recvfrom(self, _bufsize):
        recv = self._state['recv']
        if recv is None:
            raise backend.socket.timeout()
        return recv

    def sendto(self, data, addr):
        self._state['sent'].append((bytes(data), addr))


@pytest.fixture
def net(monkeypatch):
    '''Patch socket.socket; expose ``sent`` packets and a settable ``recv`` value.'''
    state = {'recv': None, 'sent': []}
    monkeypatch.setattr(backend.socket, 'socket', lambda *a, **k: _FakeSocket(state))
    return state
