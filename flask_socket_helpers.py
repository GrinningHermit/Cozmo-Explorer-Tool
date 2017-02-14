"""
Wrappers and helpers for using Flask with Cozmo.

Flask is a Python web framework. remote_control_cozmo.py and other js may use
these utility functions to interact with a web browser.

Created by: Anki
http://www.anki.com

Edited by: GrinningHermit

"""

import logging
import sys
from threading import Thread
import webbrowser
from time import sleep
import socket

def _delayed_open_web_browser(url, delay, new=0, autoraise=True, specific_browser=None):
    """
    Spawn a thread and call sleep_and_open_web_browser from within it so that main thread can keep executing at the
    same time. Insert a small sleep before opening a web-browser
    this gives Flask a chance to start running before the browser starts requesting data from Flask.
    """

    def _sleep_and_open_web_browser(url, delay, new, autoraise, specific_browser):
        sleep(delay)
        browser = webbrowser

        # E.g. On OSX the following would use the Chrome browser app from that location
        # specific_browser = 'open -a /Applications/Google\ Chrome.app %s'
        if specific_browser:
            browser = webbrowser.get(specific_browser)

        browser.open(url, new=new, autoraise=autoraise)

    thread = Thread(target=_sleep_and_open_web_browser,
                    kwargs=dict(url=url, new=new, autoraise=autoraise, delay=delay, specific_browser=specific_browser))
    thread.daemon = True # Force to quit on main quitting
    thread.start()


def run_flask(socketio, app, host_ip='0.0.0.0', host_port=5000, enable_flask_logging=False,
              open_page=True, open_page_delay=1.0):
    '''
    Run the Flask webserver on specified host and port
    optionally also open that same host:port page in your browser to connect
    '''

    global count

    if not enable_flask_logging:
        # disable logging in Flask (it's enabled by default)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    if open_page:
        # we add a delay (dispatched in another thread) to open the page so that the flask webserver is open
        # before the webpage requests any data
        _delayed_open_web_browser("http://" + host_ip + ":" + str(host_port), delay=open_page_delay)
    print('Host IP: ' + str(socket.gethostbyname(socket.gethostname())) + ':' + str(host_port))
    if socketio:
        socketio.run(app, host=host_ip, port=host_port)
    else:
        app.run(host=host_ip, port=host_port)

