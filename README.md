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

### Wiring the PCB
I removed the PCB from the remote and using a multimeter I identified the vias that could be used to simulate a button pressed :

<img src="https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/remote_pcb_back.jpg?raw=true" width="400"/><img src="https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/remote_pcb_front.jpg?raw=true" width="400"/>

- Red : power supply (3V)
- Black : ground
- Blue : the "power" signal which is connected to a button input signal when pressed (all blue vias are linked together)
- Yellow : buttons input :
  - V : validate
  - R : return
  - U : up
  - S : stop
  - D : down

As you might have notice on the back of the PCB (first image) the up button input signal is close to a connector render it difficult to soder, using the other side of the PCB is far easier.

The PCB with the wires :

<img src="https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/remote_pcb_back_wires.jpg?raw=true" width="400"/>

### The relay
To drive the remote I used a 6 channels hl-56S relay :

<img src="https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/relay.png?raw=true" width="600"/>

6 channels is perfect to drive the 5 buttons + the power supply.

### Wiring it all together
As the remote requires 3V power supply I used a 3V3 pin from the Raspberry Pi to power it. The relay is also powered by a 3V3 pin from the Raspberry Pi.

The remote buttons and power supply are connected to the relay 6 channels. The relay itself is connected to a Raspberry Pi GPIOs.

![Chronosoft 8 on a table](https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/cs8p_on_table.jpg?raw=true)
![Chronosoft 8 in a box](https://github.com/mika1337/chronosoft8-puppeteer/blob/master/img/cs8p_in_box.jpg?raw=true)

## Software part
Chronosoft8 puppeteer is a python software to drive the remote. It configures the remote channels (up to 8) and has plugins to manage the remote :
- websocket plugin to manage the remote from a webpage
- scheduling plugin to drive the shutters based on time/sun

## Licensing
This project is licensed under the MIT license.
