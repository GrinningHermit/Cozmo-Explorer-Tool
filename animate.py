import json
import time
import cozmo

from flask import Blueprint, request

animate = Blueprint('animate', __name__)

robot = None
return_to_pose = False
animations = ''
triggers = ''
behaviors = ''
action = []
pose = None

@animate.route('/toggle_pose', methods=['POST'])
def toggle_pose():
    global return_to_pose
    # Toggle for returning to pose after finishing animation
    return_to_pose = not return_to_pose
    print('return_to_pose is set to: ' + str(return_to_pose))
    return str(return_to_pose)


@animate.route('/play_animation', methods=['POST'])
def play_animation():
    # Handling of received animation
    global pose
    animation = json.loads(request.data.decode('utf-8'))
    pose = robot.pose
    robot.play_anim(animation).wait_for_completed()
    print('Animation \'' + animation + '\' started')
    check_pose_return()

    return 'true'


@animate.route('/play_trigger', methods=['POST'])
def play_trigger():
    # Handling of received trigger
    global pose
    trigger = json.loads(request.data.decode('utf-8'))
    pose = robot.pose
    robot.play_anim_trigger(getattr(cozmo.anim.Triggers, trigger)).wait_for_completed()
    print('Trigger \'' + trigger + '\' started')
    check_pose_return()

    return 'true'


@animate.route('/play_behavior', methods=['POST'])
def play_behavior():
    # Handling of received behavior
    global pose
    global action
    behavior = json.loads(request.data.decode('utf-8'))
    pose = robot.pose
    action = [robot.start_behavior(getattr(cozmo.behavior.BehaviorTypes, behavior)), behavior]
    print('Behavior \'' + behavior + '\' started')
    return 'true'


@animate.route('/stop', methods=['POST'])
def stop():
    global action
    if action is not []:
        robot.stop_freeplay_behaviors()
        print('behavior \'' + action[1] + '\' stopped')
        action = []
        check_pose_return()
    else:
        robot.abort_all_actions()

    return 'false'


def check_pose_return():
    if return_to_pose:
        robot.go_to_pose(pose)
        print('Cozmo returning to pose he had before animation started')

def init_animate(_robot):
    global robot
    robot = _robot

    global animations
    global triggers
    global behaviors
    for a in robot.conn.anim_names:
        animations += a + ','
    animations = animations[:-1]
    for t in dir(cozmo.anim.Triggers):
        if '__' not in t:
            triggers += t + ','
    triggers = triggers[:-1]
    for b in dir(cozmo.behavior.BehaviorTypes):
        if '__' not in b:
            behaviors += b + ','
    behaviors = behaviors[:-1]

    return [animations, triggers, behaviors]

