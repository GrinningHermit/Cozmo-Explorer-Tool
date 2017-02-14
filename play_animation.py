#!/usr/bin/env python3

'''
    Play animation script

    Makes Cozmo execute a sample animation

    If you are looking for the interface to test all animations, run 'animation-explorer.py'
'''

import sys

import cozmo


def run(sdk_conn):
    '''The run method runs once Cozmo is connected.'''
    robot = sdk_conn.wait_for_robot()
    robot.play_anim('anim_freeplay_reacttoface_like_01').wait_for_completed()

    print('Run \'animation-explorer.py\' if you want to try other animations')

if __name__ == '__main__':
    cozmo.setup_basic_logging()

    try:
        cozmo.connect(run)
    except cozmo.ConnectionError as e:
        sys.exit('A connection error occurred: %s' % e)
