"""

Event Monitor for Cozmo
============================

Based on Event Monitor for cozmo-tools:
https://github.com/touretzkyds/cozmo-tools

Created by: David S. Touretzky, Carnegie Mellon University

Edited by: GrinningHermit
=====

"""

import re
import threading
import time
import cozmo

robot = None
q = None # dependency on queue variable for messaging instead of printing to event-content directly
thread_running = False # starting thread for custom events

# custom eventlistener for picked-up and falling state, more states could be added
class CheckState (threading.Thread):
    def __init__(self, thread_id, name, _q):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.q = _q

    def run(self):
        delay = 10
        is_picked_up = False
        is_falling = False
        is_on_charger = False
        while thread_running:
            if robot.is_picked_up:
                delay = 0
                if not is_picked_up:
                    is_picked_up = True
                    msg = 'cozmo.robot.Robot.is_pickup_up: True'
                    self.q.put(msg)
            elif is_picked_up and delay > 9:
                is_picked_up = False
                msg = 'cozmo.robot.Robot.is_pickup_up: False'
                self.q.put(msg)
            elif delay <= 9:
                delay += 1

            if robot.is_falling:
                if not is_falling:
                    is_falling = True
                    msg = 'cozmo.robot.Robot.is_falling: True'
                    self.q.put(msg)
            elif not robot.is_falling:
                if is_falling:
                    is_falling = False
                    msg = 'cozmo.robot.Robot.is_falling: False'
                    self.q.put(msg)

            if robot.is_on_charger:
                if not is_on_charger:
                    is_on_charger = True
                    msg = 'cozmo.robot.Robot.is_on_charger: True'
                    self.q.put(msg)
            elif not robot.is_on_charger:
                if is_on_charger:
                    is_on_charger = False
                    msg = 'cozmo.robot.Robot.is_on_charger: False'
                    self.q.put(msg)

            time.sleep(0.1)


def print_prefix(evt):
    msg = evt.event_name + ' '
    return msg

def print_object(obj):
    if isinstance(obj,cozmo.objects.LightCube):
        cube_id = next(k for k,v in robot.world.light_cubes.items() if v==obj)
        msg = 'LightCube-' + str(cube_id)
    else:
        r = re.search('<(\w*)', obj.__repr__())
        msg = r.group(1)
    return msg

def monitor_generic(evt, **kwargs):
    msg = print_prefix(evt)
    if 'behavior_type_name' in kwargs:
        msg += kwargs['behavior_type_name'] + ' '
    if 'obj' in kwargs:
        msg += print_object(kwargs['obj']) + ' '
    if 'action' in kwargs:
        action = kwargs['action']
        if isinstance(action, cozmo.anim.Animation):
            msg += action.anim_name + ' '
        elif isinstance(action, cozmo.anim.AnimationTrigger):
            msg += action.trigger.name + ' '
    msg += str(set(kwargs.keys()))
    q.put(msg)

def monitor_EvtActionCompleted(evt, action, state, failure_code, failure_reason, **kwargs):
    msg = print_prefix(evt)
    msg += print_object(action) + ' '
    if isinstance(action, cozmo.anim.Animation):
        msg += action.anim_name
    elif isinstance(action, cozmo.anim.AnimationTrigger):
        msg += action.trigger.name
    if failure_code is not None:
        msg += str(failure_code) + failure_reason
    q.put(msg)

def monitor_EvtObjectTapped(evt, *, obj, tap_count, tap_duration, tap_intensity, **kwargs):
    msg = print_prefix(evt)
    msg += print_object(obj)
    msg += ' count=' + str(tap_count) + ' duration=' + str(tap_duration) + ' intensity=' + str(tap_intensity)
    q.put(msg)

def monitor_face(evt, face, **kwargs):
    msg = print_prefix(evt)
    name = face.name if face.name is not '' else '[unknown face]'
    msg += name + ' face_id=' + str(face.face_id)
    q.put(msg)


dispatch_table = {
  cozmo.action.EvtActionStarted        : monitor_generic,
  cozmo.action.EvtActionCompleted      : monitor_EvtActionCompleted,
  cozmo.behavior.EvtBehaviorStarted    : monitor_generic,
  cozmo.behavior.EvtBehaviorStopped    : monitor_generic,
  cozmo.anim.EvtAnimationsLoaded       : monitor_generic,
  cozmo.anim.EvtAnimationCompleted     : monitor_EvtActionCompleted,
  # cozmo.objects.EvtObjectAvailable     : monitor_generic, # deprecated
  cozmo.objects.EvtObjectAppeared      : monitor_generic,
  cozmo.objects.EvtObjectDisappeared   : monitor_generic,
  cozmo.objects.EvtObjectObserved      : monitor_generic,
  cozmo.objects.EvtObjectTapped        : monitor_EvtObjectTapped,
  cozmo.faces.EvtFaceAppeared          : monitor_face,
  cozmo.faces.EvtFaceObserved          : monitor_face,
  cozmo.faces.EvtFaceDisappeared       : monitor_face,
}

excluded_events = {    # Occur too frequently to monitor by default
    cozmo.objects.EvtObjectObserved,
    cozmo.faces.EvtFaceObserved,
}

def monitor(_robot, _q, evt_class=None):
    if not isinstance(_robot, cozmo.robot.Robot):
        raise TypeError('First argument must be a Robot instance')
    if evt_class is not None and not issubclass(evt_class, cozmo.event.Event):
        raise TypeError('Second argument must be an Event subclass')
    global robot
    global q
    global thread_running
    robot = _robot
    q = _q
    thread_running = True
    if evt_class in dispatch_table:
        robot.world.add_event_handler(evt_class,dispatch_table[evt_class])
    elif evt_class is not None:
        robot.world.add_event_handler(evt_class,monitor_generic)
    else:
        for k,v in dispatch_table.items():
            if k not in excluded_events:
                robot.world.add_event_handler(k,v)
    thread_is_state_changed = CheckState(1, 'ThreadCheckState', q)
    thread_is_state_changed.start()


def unmonitor(_robot, evt_class=None):
    if not isinstance(_robot, cozmo.robot.Robot):
        raise TypeError('First argument must be a Robot instance')
    if evt_class is not None and not issubclass(evt_class, cozmo.event.Event):
        raise TypeError('Second argument must be an Event subclass')
    global robot
    global thread_running
    robot = _robot
    thread_running = False

    try:
        if evt_class in dispatch_table:
            robot.world.remove_event_handler(evt_class,dispatch_table[evt_class])
        elif evt_class is not None:
            robot.world.remove_event_handler(evt_class,monitor_generic)
        else:
            for k,v in dispatch_table.items():
                robot.world.remove_event_handler(k,v)
    except Exception:
        pass

