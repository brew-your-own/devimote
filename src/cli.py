# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''CLI remote control for Devialet Expert amplifiers'''

import os
import socket

import click
from dotenv import load_dotenv

from backend import DeviMoteBackEnd

load_dotenv()


def _volume_db(raw: int) -> float:
    return (raw - 195) / 2.0


def _connect() -> DeviMoteBackEnd:
    backend = DeviMoteBackEnd()
    expected_ip = os.getenv('DEVIALET_IP')
    s = backend.update()
    if not s['connected']:
        raise click.ClickException(
            'Amplifier not found (timeout waiting for UDP broadcast on port 45454)'
        )
    if expected_ip:
        resolved = socket.gethostbyname(expected_ip)
        if s['ip'] != resolved:
            click.echo(
                f"Warning: expected {expected_ip} ({resolved}), connected to {s['ip']}",
                err=True,
            )
    return backend


@click.group()
def main():
    '''CLI remote control for Devialet Expert amplifiers'''


@main.command()
def status():
    '''Show current amplifier status'''
    backend = _connect()
    s = backend.status
    ch_name = s['ch_list'].get(s['channel'], f"#{s['channel']}").strip()
    sources = ', '.join(f"{n.strip()} ({i})" for i, n in sorted(s['ch_list'].items()))
    click.echo(f"Device:  {s['dev_name'].strip()}")
    click.echo(f"IP:      {s['ip']}")
    click.echo(f"Power:   {'ON' if s['power'] else 'STANDBY'}")
    click.echo(f"Volume:  {_volume_db(s['volume']):+.1f} dB")
    click.echo(f"Muted:   {'Yes' if s['muted'] else 'No'}")
    click.echo(f"Source:  {ch_name} ({s['channel']})")
    click.echo(f"Sources: {sources}")


@main.command()
@click.argument('db', type=float)
def volume(db):
    '''Set volume in dB. Use -- before negative values: volume -- -15'''
    if db > DeviMoteBackEnd.VOLUME_LIMIT:
        raise click.ClickException(
            f"Volume {db:+.1f} dB exceeds limit {DeviMoteBackEnd.VOLUME_LIMIT:+.1f} dB"
        )
    backend = _connect()
    backend.set_volume(db)
    click.echo(f"Volume set to {db:+.1f} dB")


@main.command()
def mute():
    '''Toggle mute on/off'''
    backend = _connect()
    backend.toggle_mute()
    click.echo('Mute toggled')


@main.command()
def power():
    '''Toggle power (on/standby)'''
    backend = _connect()
    backend.toggle_power()
    click.echo('Power toggled')


@main.command()
@click.argument('name')
def source(name):
    '''Select input source by name (case-insensitive partial match)'''
    backend = _connect()
    ch_list = backend.status['ch_list']
    matches = {idx: n for idx, n in ch_list.items() if name.lower() in n.lower()}
    if not matches:
        available = ', '.join(n.strip() for n in ch_list.values())
        raise click.ClickException(f"No source matching '{name}'. Available: {available}")
    if len(matches) > 1:
        found = ', '.join(f"{n.strip()} ({i})" for i, n in sorted(matches.items()))
        raise click.ClickException(f"Ambiguous source '{name}', matches: {found}")
    idx, n = next(iter(matches.items()))
    backend.set_output(idx)
    click.echo(f"Source set to {n.strip()}")
