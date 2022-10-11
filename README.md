# Python Open Network Simulator (PyONS)

The package provides the kernel for discrete-event simulations in Python 3 language.

It is designed to be suitable for various tasks in mind, while the first objective is 
to simulate networks and queueing systems.

## Working in development mode

It is my project for master thesis in MIPT. Now it is my present work for PhD thesis.

To install this project, simply use the following:

Open your terminal and then do

> git clone https://github.com/VilmenAbramian/RFID_sim
> python -m venv .venv
> .venv/scripts/activate   
>pip install -r requirements.txt    

After that, to call the help of the simulation model, you can call:

> sim start --help

For a test run, you can call:

> sim start -n 50 --encoding 8 --tari 25 --tid-word-size 256 --tag-offset 5 --reader-offset 5 --altitude 5 -p 29  -s 5 -s 10 -s 15
