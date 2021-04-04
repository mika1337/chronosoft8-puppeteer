# chronosoft8-puppeteer
Drive your Chronosoft 8 remote from a Raspberry Pi.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Requirements
- [PyYAML](https://pyyaml.org)
- [Python astral](https://github.com/sffjunkie/astral)
- [Python websockets](https://websockets.readthedocs.io/en/stable/)
- [RPi.GPIO](http://sourceforge.net/projects/raspberry-gpio-python/)

## Objectives
If you want to know how to use your Chronosoft 8 remote you're in the wrong place :)

I made this project because my roller shutters use a proprietary protocol (M4G) which I did not manage to handle using open tools. To drive them from my computer/phone/tablet/\<add any connected device here\> I decided to solder a few wires to the remote PCB and drive them with relays from a Raspberry Pi.

## Hardware part
### The remote
The Chronosoft 8 is a remote sold by Franciaflex, it managed up to 8 roller shutters :

![Chronosoft 8](https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/remote.png?raw=true)

It is also able to shedule roller shutters opening and closing.

The remote has 5 buttons :
- Retour (Return)
- Valider (Validate)
- Up
- Stop
- Down

### The mod
I removed the PCB from the remote and using a multimeter I identified the vias that could be used to simulate a button pressed :

<img src="https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/remote_back.jpg?raw=true" width="400"/><img src="https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/remote_front.jpg?raw=true" width="400"/>

- Red : power supply (3V)
- Black : ground
- Blue : the "power" signal which is connected to a button input signal when pressed (all blue vias are linked together)
- Yellow : buttons input :
  - V : validate
  - R : return
  - U : up
  - S : stop
  - D : down

As you might have notice on the back of the PCB (first image) the uo button input signal is close to a connector render it difficult to soder, using the other side of the PCB is far easier.

## Licensing
This project is licensed under the MIT license.