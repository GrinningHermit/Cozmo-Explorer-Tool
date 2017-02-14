"""

Remote control for Cozmo
============================

Based on remote_control_cozmo.py for cozmo SDK:
https://developer.anki.com

Created by: Anki

Edited by: GrinningHermit

Code from example file is separated in 2 functionalities:
- viewer / robot camera <-- this is where you are
- keyboard command handling

=====

"""
import json
from io import BytesIO
import logging
from flask import request,make_response, send_file, Blueprint
import cozmo
pil_installed = False
try:
    from PIL import Image, ImageDraw, ImageFont
    pil_installed = True
except ImportError:
    logging.warning("Cannot import from PIL: Do `pip3 install --user Pillow` to install")


viewer = Blueprint('viewer', __name__)

DEBUG_ANNOTATIONS_DISABLED = 0
DEBUG_ANNOTATIONS_ENABLED_VISION = 1
DEBUG_ANNOTATIONS_ENABLED_ALL = 2

robot = None
cozmoEnabled = True

# Annotator for displaying RobotState (position, etc.) on top of the camera feed
class RobotStateDisplay(cozmo.annotate.Annotator):
    def apply(self, image, scale):
        d = ImageDraw.Draw(image)

        bounds = [10, 5, image.width, image.height]
        bounds_shadow = [10, 6, image.width, image.height]
        font = ImageFont.truetype('static/fonts/LiberationSans-Bold.ttf', 15)
        def print_line(text_line):
            shadow = cozmo.annotate.ImageText(text_line, position=cozmo.annotate.TOP_LEFT, color='#000000', font=font)
            shadow.render(d, bounds_shadow)
            text = cozmo.annotate.ImageText(text_line, position=cozmo.annotate.TOP_LEFT, color='#ffffff', font=font)
            text.render(d, bounds)
            TEXT_HEIGHT = 15
            bounds[1] += TEXT_HEIGHT
            bounds_shadow[1] += TEXT_HEIGHT

        # Display the Pose info for the robot

        pose = robot.pose
        print_line('Pose: Pos = <%.1f, %.1f, %.1f>' % pose.position.x_y_z)
        print_line('Pose: Rot quat = <%.1f, %.1f, %.1f, %.1f>' % pose.rotation.q0_q1_q2_q3)
        print_line('Pose: angle_z = %.1f' % pose.rotation.angle_z.degrees)
        print_line('Pose: origin_id: %s' % pose.origin_id)

        # Display the Accelerometer and Gyro data for the robot

        print_line('Accelmtr: <%.1f, %.1f, %.1f>' % robot.accelerometer.x_y_z)
        print_line('Gyro: <%.1f, %.1f, %.1f>' % robot.gyro.x_y_z)


def create_default_image(image_width, image_height, do_gradient=False):
    """Create a place-holder PIL image to use until we have a live feed from Cozmo"""
    image_bytes = bytearray([0x70, 0x70, 0x70]) * image_width * image_height

    if do_gradient:
        i = 0
        for y in range(image_height):
            for x in range(image_width):
                image_bytes[i] = int(255.0 * (x / image_width))   # R
                image_bytes[i+1] = int(255.0 * (y / image_height))  # G
                image_bytes[i+2] = 0                                # B
                i += 3

    image = Image.frombytes('RGB', (image_width, image_height), bytes(image_bytes))
    return image

if pil_installed:
    _default_camera_image = create_default_image(320, 240)
    _display_debug_annotations = DEBUG_ANNOTATIONS_ENABLED_ALL

@viewer.route("/cozmoImage")
def handle_cozmoImage():
    """Called very frequently from Javascript to request the latest camera image"""
    if cozmoEnabled and pil_installed:
        image = robot.world.latest_image
        if image:
            if _display_debug_annotations != DEBUG_ANNOTATIONS_DISABLED:
                image = image.annotate_image(scale=2)
            else:
                image = image.raw_image

            return serve_pil_image(image)
        return serve_pil_image(_default_camera_image)
    return ''

@viewer.route('/setAreDebugAnnotationsEnabled', methods=['POST'])
def handle_setAreDebugAnnotationsEnabled():
    """Called from Javascript whenever debug-annotations mode is toggled"""
    message = json.loads(request.data.decode("utf-8"))
    global _display_debug_annotations
    _display_debug_annotations = message['areDebugAnnotationsEnabled']
    if _display_debug_annotations == DEBUG_ANNOTATIONS_ENABLED_ALL:
        robot.world.image_annotator.annotation_enabled = True
        # robot.world.image_annotator.enable_annotator('robotState')
    else:
        robot.world.image_annotator.annotation_enabled = False
        # robot.world.image_annotator.disable_annotator('robotState')
    return ""

def make_uncached_response(in_file):
    response = make_response(in_file)
    response.headers['Pragma-Directive'] = 'no-cache'
    response.headers['Cache-Directive'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


def serve_pil_image(pil_img, serve_as_jpeg=False, jpeg_quality=70):
    """Convert PIL image to relevant image file and send it"""
    img_io = BytesIO()

    if serve_as_jpeg:
        pil_img.save(img_io, 'JPEG', quality=jpeg_quality)
        img_io.seek(0)
        return make_uncached_response(send_file(img_io, mimetype='image/jpeg'))
    else:
        pil_img.save(img_io, 'PNG')
        img_io.seek(0)
        return make_uncached_response(send_file(img_io, mimetype='image/png'))


def activate_viewer_if_enabled(_robot):
    global robot
    robot = _robot
    if pil_installed:
        robot.world.image_annotator.add_annotator('robotState', RobotStateDisplay)
        # Turn on image receiving by the camera
        robot.camera.image_stream_enabled = True
        return True
    else:
        return False