#!/usr/bin/env python3

"""
    List all Cozmo animations on a web page with buttons to try the animations.
    In order to run this script, you also need all the other files inside the project.
    If that is the case, running this script will load the interface.

    Created by: GrinningHermit
"""
import datetime
import os
import queue
import random
import logging
from flask import Flask, render_template

import flask_socket_helpers
import cozmo
import event_monitor
from viewer import viewer, activate_viewer_if_enabled
from remote_control import remote_control, activate_controls
from animate import animate, init_animate

# logging.basicConfig(format='%(asctime)s animation explorer %(levelname)s %(message)s', level=print)

flask_socketio_installed = False
try:
    from flask_socketio import SocketIO, emit, disconnect
    flask_socketio_installed = True
except ImportError:
    logging.warning('Cannot import from flask_socketio: Do `pip3 install --user flask-socketio` to install\nProgram runs without flask_socketio, but without event monitoring')

eventlet_installed = False
try:
    import eventlet
    eventlet_installed = True
except ImportError:
    logging.warning('Cannot import from eventlet: Do `pip3 install --user eventlet` to install\nEvent monitoring works, but performance is decreased')


thread = None
robot = None
cozmoEnabled = True
active_viewer = False
lists = []
async_mode = 'threading'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.register_blueprint(viewer)
app.register_blueprint(remote_control)
app.register_blueprint(animate)
rndID = random.randrange(1000000000, 9999999999)
q = queue.Queue()

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

if flask_socketio_installed:
    socketio = SocketIO(app, async_mode=async_mode)

    # Functions for event monitoring
    def print_queue(qval):
        while qval.qsize() > 0:
            timestamp = '{:%H:%M:%S.%f}'.format(datetime.datetime.now())
            message = qval.get()
            print(timestamp + ' -> ' + message)
            socketio.emit('my_response',
                {'data': message, 'type': 'event', 'time': timestamp})


    def background_thread(qval):
        while True:
            if not qval.empty():
                print_queue(qval)
            socketio.sleep(.1)


    @socketio.on('connect')
    def test_connect():
        global thread
        if thread is None:
            thread = socketio.start_background_task(background_thread, q)
        emit('my_response', {'data': 'SERVER: websocket connection established. Displaying events, like  Cozmo seeing a cube or tapping a cube.'})


@app.route('/')
def index():
    return render_template('index.html', randomID=rndID, animations=lists[0], triggers=lists[1], behaviors=lists[2], hasSocketIO=flask_socketio_installed, hasPillow=active_viewer)


def start_server():
    if flask_socketio_installed:
        flask_socket_helpers.run_flask(socketio, app)
    else:
        flask_socket_helpers.run_flask(None, app)


def cozmo_program(_robot: cozmo.robot.Robot):
    global robot
    global lists
    global active_viewer
    robot = _robot

    try:
        lists = init_animate(robot)
        event_monitor.monitor(robot, q)
        active_viewer = activate_viewer_if_enabled(robot)
        activate_controls(robot)
        start_server()

    except KeyboardInterrupt:
        print("\nExit requested by user")


try:
    cozmo.robot.Robot.drive_off_charger_on_connect = False
    cozmo.run_program(cozmo_program)

except SystemExit as e:
    cozmoEnabled = False
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nExit requested by user")

