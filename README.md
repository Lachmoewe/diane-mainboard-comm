# diane-mainboard-comm
Software to monitor and control the status of the DIANE experiment.

## Requirements
- Python 2.7 with following packages: `serial, io, time, struct`
- USB to serial converter
- DIANE Mainboard

## Usage
Fire up your editor of choice and edit file `com.py` . In line 261, change
`mb = Mainboard()` to `mb = Mainboard("COM0")` or whatever your RS232 port might be.
Save and run with `python com.py`.

A Window looking like this should appear:

![DIANE Mainboard Comm GUI](https://raw.githubusercontent.com/Lachmoewe/diane-mainboard-comm/master/software_layout.png)

To close, first press the X of the window, then in the terminal `<ctrl>-c` to kill the remaining process.

## Logfiles
This software will create two logfiles, one datalog and a text log. The datalog is for professionals only, the test log is called unixtime.log. You will find timestamps and the received package in there. This file will only exist after exiting the software.
