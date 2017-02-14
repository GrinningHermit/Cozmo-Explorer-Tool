"""

Remote control for Cozmo
============================

Based on remote_control_cozmo.py for cozmo SDK:
https://developer.anki.com

Created by: Anki

Edited by: GrinningHermit

Code from example file is separated in 2 functionalities:
- viewer / robot camera
- keyboard command handling <-- this is where you are

=====

"""
import json

from flask import Blueprint, request
import cozmo

remote_control = Blueprint('remote_control', __name__)

robot = None
remote_control_cozmo = None

_is_mouse_look_enabled_by_default = False

def remap_to_range(x, x_min, x_max, out_min, out_max):
    """convert x (in x_min..x_max range) to out_min..out_max range"""
    if x < x_min:
        return out_min
    elif x > x_max:
        return out_max
    else:
        ratio = (x - x_min) / (x_max - x_min)
        return out_min + ratio * (out_max - out_min)

class RemoteControlCozmo:
    def __init__(self, coz):
        self.cozmo = coz

        self.drive_forwards = 0
        self.drive_back = 0
        self.turn_left = 0
        self.turn_right = 0
        self.lift_up = 0
        self.lift_down = 0
        self.head_up = 0
        self.head_down = 0

        self.go_fast = 0
        self.go_slow = 0

        self.is_mouse_look_enabled = _is_mouse_look_enabled_by_default
        self.mouse_dir = 0

        all_anim_names = list(self.cozmo.anim_names)
        all_anim_names.sort()
        self.anim_names = []

        # Hide a few specific test animations that don't behave well
        """
        bad_anim_names = [
            "ANIMATION_TEST",
            "soundTestAnim"]

        for anim_name in all_anim_names:
            if anim_name not in bad_anim_names:
                self.anim_names.append(anim_name)

        default_anims_for_keys = ["anim_bored_01",  # 0
                                  "id_poked_giggle",  # 1
                                  "anim_pounce_success_02",  # 2
                                  "anim_bored_event_02",  # 3
                                  "anim_bored_event_03",  # 4
                                  "anim_petdetection_cat_01",  # 5
                                  "anim_petdetection_dog_03",  # 6
                                  "anim_reacttoface_unidentified_02",  # 7
                                  "anim_upgrade_reaction_lift_01",  # 8
                                  "anim_speedtap_wingame_intensity02_01"  # 9
                                  ]

        self.anim_index_for_key = [0] * 10
        kI = 0
        for default_key in default_anims_for_keys:
            try:
                anim_idx = self.anim_names.index(default_key)
            except ValueError:
                print("Error: default_anim %s is not in the list of animations" % default_key)
                anim_idx = kI
            self.anim_index_for_key[kI] = anim_idx
            kI += 1
        """

        self.action_queue = []
        self.text_to_say = "Hi I'm Cozmo"

    """
    def set_anim(self, key_index, anim_index):
        self.anim_index_for_key[key_index] = anim_index


    def handle_mouse(self, mouse_x, mouse_y, delta_x, delta_y, is_button_down):
        '''Called whenever mouse moves
            mouse_x, mouse_y are in in 0..1 range (0,0 = top left, 1,1 = bottom right of window)
            delta_x, delta_y are the change in mouse_x/y since the last update
        '''
        if self.is_mouse_look_enabled:
            mouse_sensitivity = 1.5  # higher = more twitchy
            self.mouse_dir = remap_to_range(mouse_x, 0.0, 1.0, -mouse_sensitivity, mouse_sensitivity)
            self.update_driving()

            desired_head_angle = remap_to_range(mouse_y, 0.0, 1.0, 45, -25)
            head_angle_delta = desired_head_angle - self.cozmo.head_angle.degrees
            head_vel = head_angle_delta * 0.03
            self.cozmo.move_head(head_vel)


    def set_mouse_look_enabled(self, is_mouse_look_enabled):
        was_mouse_look_enabled = self.is_mouse_look_enabled
        self.is_mouse_look_enabled = is_mouse_look_enabled
        if not is_mouse_look_enabled:
            # cancel any current mouse-look turning
            self.mouse_dir = 0
            if was_mouse_look_enabled:
                self.update_driving()
                self.update_head()
    """

    def handle_key(self, key_code, is_shift_down, is_ctrl_down, is_alt_down, is_key_down):
        """Called on any key press or release
           Holding a key down may result in repeated handle_key calls with is_key_down==True
        """
        # Update desired speed / fidelity of actions based on shift/alt being held
        was_go_fast = self.go_fast
        was_go_slow = self.go_slow

        self.go_fast = is_shift_down
        self.go_slow = is_alt_down

        speed_changed = (was_go_fast != self.go_fast) or (was_go_slow != self.go_slow)

        # Update state of driving intent from keyboard, and if anything changed then call update_driving
        update_driving = True
        if key_code == ord('W'):
            self.drive_forwards = is_key_down
        elif key_code == ord('S'):
            self.drive_back = is_key_down
        elif key_code == ord('A'):
            self.turn_left = is_key_down
        elif key_code == ord('D'):
            self.turn_right = is_key_down
        else:
            if not speed_changed:
                update_driving = False

        # Update state of lift move intent from keyboard, and if anything changed then call update_lift
        update_lift = True
        if key_code == ord('R'):
            self.lift_up = is_key_down
        elif key_code == ord('F'):
            self.lift_down = is_key_down
        else:
            if not speed_changed:
                update_lift = False

        # Update state of head move intent from keyboard, and if anything changed then call update_head
        update_head = True
        if key_code == ord('Q'):
            self.head_up = is_key_down
        elif key_code == ord('E'):
            self.head_down = is_key_down
        else:
            if not speed_changed:
                update_head = False

        # Update driving, head and lift as appropriate
        if update_driving:
            self.update_driving()
        if update_head:
            self.update_head()
        if update_lift:
            self.update_lift()

        # Handle any keys being released (e.g. the end of a key-click)
        if not is_key_down:
            if (key_code >= ord('0')) and (key_code <= ord('9')):
                anim_name = self.key_code_to_anim_name(key_code)
                self.play_animation(anim_name)
            elif key_code == ord(' '):
                self.say_text(self.text_to_say)

    """
    def key_code_to_anim_name(self, key_code):
        key_num = key_code - ord('0')
        anim_num = self.anim_index_for_key[key_num]
        anim_name = self.anim_names[anim_num]
        return anim_name
    """

    def func_to_name(self, func):
        if func == self.try_say_text:
            return "say_text"
        elif func == self.try_play_anim:
            return "play_anim"
        else:
            return "UNKNOWN"


    def action_to_text(self, action):
        func, args = action
        return self.func_to_name(func) + "( " + str(args) + " )"


    def action_queue_to_text(self, action_queue):
        out_text = ""
        i = 0
        for action in action_queue:
            out_text += "[" + str(i) + "] " + self.action_to_text(action)
            i += 1
        return out_text


    def queue_action(self, new_action):
        if len(self.action_queue) > 10:
            self.action_queue.pop(0)
        self.action_queue.append(new_action)


    def try_say_text(self, text_to_say):
        try:
            self.cozmo.say_text(text_to_say)
            return True
        except cozmo.exceptions.RobotBusy:
            return False

    """
    def try_play_anim(self, anim_name):
        try:
            self.cozmo.play_anim(name=anim_name)
            return True
        except cozmo.exceptions.RobotBusy:
            return False
    """


    def say_text(self, text_to_say):
        self.queue_action((self.try_say_text, text_to_say))
        self.update()


    def play_animation(self, anim_name):
        self.queue_action((self.try_play_anim, anim_name))
        self.update()


    def update(self):
        """Try and execute the next queued action"""
        if len(self.action_queue) > 0:
            queued_action, action_args = self.action_queue[0]
            if queued_action(action_args):
                self.action_queue.pop(0)


    def pick_speed(self, fast_speed, mid_speed, slow_speed):
        if self.go_fast:
            if not self.go_slow:
                return fast_speed
        elif self.go_slow:
            return slow_speed
        return mid_speed


    def update_lift(self):
        lift_speed = self.pick_speed(8, 4, 2)
        lift_vel = (self.lift_up - self.lift_down) * lift_speed
        self.cozmo.move_lift(lift_vel)


    def update_head(self):
        if not self.is_mouse_look_enabled:
            head_speed = self.pick_speed(2, 1, 0.5)
            head_vel = (self.head_up - self.head_down) * head_speed
            self.cozmo.move_head(head_vel)


    def update_driving(self):
        drive_dir = (self.drive_forwards - self.drive_back)

        if (drive_dir > 0.1) and self.cozmo.is_on_charger:
            # cozmo is stuck on the charger, and user is trying to drive off - issue an explicit drive off action
            try:
                # don't wait for action to complete - we don't want to block the other updates (camera etc.)
                self.cozmo.drive_off_charger_contacts()
            except cozmo.exceptions.RobotBusy:
                # Robot is busy doing another action - try again next time we get a drive impulse
                pass

        turn_dir = (self.turn_right - self.turn_left) + self.mouse_dir

        if drive_dir < 0:
            # It feels more natural to turn the opposite way when reversing
            turn_dir = -turn_dir

        forward_speed = self.pick_speed(150, 75, 50)
        turn_speed = self.pick_speed(100, 50, 30)

        l_wheel_speed = (drive_dir * forward_speed) + (turn_speed * turn_dir)
        r_wheel_speed = (drive_dir * forward_speed) - (turn_speed * turn_dir)

        self.cozmo.drive_wheels(l_wheel_speed, r_wheel_speed, l_wheel_speed * 4, r_wheel_speed * 4)

@remote_control.route('/updateCozmo', methods=['POST'])
def handle_updateCozmo():
    """Called very frequently from Javascript to provide an update loop"""
    if remote_control_cozmo:
        remote_control_cozmo.update()
    return ""

def handle_key_event(key_request, is_key_down):
    message = json.loads(key_request.data.decode("utf-8"))
    if remote_control_cozmo:
        remote_control_cozmo.handle_key(key_code=(message['keyCode']), is_shift_down=message['hasShift'], is_ctrl_down=message['hasCtrl'], is_alt_down=message['hasAlt'],is_key_down=is_key_down)
    return ""

@remote_control.route('/keydown', methods=['POST'])
def handle_keydown():
    """Called from Javascript whenever a key is down (note: can generate repeat calls if held down)"""
    return handle_key_event(request, is_key_down=True)


@remote_control.route('/keyup', methods=['POST'])
def handle_keyup():
    """Called from Javascript whenever a key is released"""
    return handle_key_event(request, is_key_down=False)


@remote_control.route('/setHeadlightEnabled', methods=['POST'])
def handle_setHeadlightEnabled():
    '''Called from Javascript whenever headlight is toggled on/off'''
    message = json.loads(request.data.decode("utf-8"))
    if remote_control_cozmo:
        remote_control_cozmo.cozmo.set_head_light(enable=message['isHeadlightEnabled'])
    return ""


@remote_control.route('/setFreeplayEnabled', methods=['POST'])
def handle_setFreeplayEnabled():
    '''Called from Javascript whenever freeplay mode is toggled on/off'''
    message = json.loads(request.data.decode("utf-8"))
    if remote_control_cozmo:
        isFreeplayEnabled = message['isFreeplayEnabled']
        if isFreeplayEnabled:
            remote_control_cozmo.cozmo.start_freeplay_behaviors()
        else:
            remote_control_cozmo.cozmo.stop_freeplay_behaviors()
    return ""


@remote_control.route('/getDebugInfo', methods=['POST'])
def handle_getDebugInfo():
    if remote_control_cozmo:
        action_queue_text = ""
        i = 1
        for action in remote_control_cozmo.action_queue:
            action_queue_text += str(i) + ": " + remote_control_cozmo.action_to_text(action) + "<br>"
            i += 1

        return '''Action Queue:<br>''' + action_queue_text + '''
        '''
    return ""


def activate_controls(_robot):
    global robot
    robot = _robot
    global remote_control_cozmo
    remote_control_cozmo = RemoteControlCozmo(robot)