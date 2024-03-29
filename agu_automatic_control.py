#!/usr/bin/env python

# Copyright (c) 2018 Intel Labs.
# authors: German Ros (german.ros@intel.com)
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""Agu automatic vehicle control from client side."""

from __future__ import print_function

import argparse
import collections
import datetime
import glob
import logging
import math
import os
import numpy.random as random
import re
import sys
import weakref

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_q
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError(
        'cannot import numpy, make sure numpy package is installed')

# ==============================================================================
# -- Find CARLA module ---------------------------------------------------------
# ==============================================================================
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# ==============================================================================
# -- Add PythonAPI for release mode --------------------------------------------
# ==============================================================================
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/carla')
except IndexError:
    pass

import carla
from carla import ColorConverter as cc

from agents.navigation.behavior_agent import BehaviorAgent  # pylint: disable=import-error
from agents.navigation.basic_agent import BasicAgent  # pylint: disable=import-error

import agu_generator_KITTI as gen
import time

# ==============================================================================
# -- Global parameters ---------------------------------------------------------
# ==============================================================================
global_map_id = 1
flag_spawn_walkers = False

v_start_point = []
v_waypoint = []

w_start_point = []
w_waypoint = []

if global_map_id==1:
    agent_start_point = carla.Transform(carla.Location(x=170.0,y=55.6,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))
    agent_waypoint = np.array([
     (carla.Location(x=130.0, y=55.5,  z=0.3)), #첫번째 교차로 전 
     (carla.Location(x=88.4,  y=88.3,  z=0.3)), #좌회전 후 
     (carla.Location(x=230.0, y=133.5, z=0.3)), #좌회전 후 
     (carla.Location(x=338.8, y=88.3,  z=0.3)), #긴 직진 후 좌회전
     (carla.Location(x=300.0, y=55.5,  z=0.3)), #마지막 좌회전 후
     (carla.Location(x=120.0, y=55.5,  z=0.3))  #최종 목적지
     ])
    # agent_start_point = carla.Transform(carla.Location(x=120.0, y=55.5,  z=0.3), carla.Rotation(pitch = 0, yaw=180, roll=0))
    # agent_waypoint = np.array([
    #  (carla.Location(x=88.4,  y=88.3,  z=0.3)), #좌회전 후 
    #  (carla.Location(x=230.0, y=133.5, z=0.3)), #좌회전 후 
    #  (carla.Location(x=338.8, y=88.3,  z=0.3)), #긴 직진 후 좌회전
    #  (carla.Location(x=300.0, y=55.5,  z=0.3)), #마지막 좌회전 후
    #  (carla.Location(x=120.0, y=55.5,  z=0.3))  #최종 목적지
    #  ])
    #firetruck 1
    v1_start_point = carla.Transform(carla.Location(x=211.5,y=129.5,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))
    v1_waypoint = np.array([
     (carla.Location(x=111.0, y=129.5, z=0.3)),
     (carla.Location(x=92.3, y=120.8, z=2))
     ])
    #ambulance 1
    v2_start_point = carla.Transform(carla.Location(x=334.8,y=40.5,z=2), carla.Rotation(pitch = 0, yaw=90, roll=0))
    v2_waypoint = np.array([
    (carla.Location(x=311.5, y=129.5,  z=0.3)),
    # (carla.Location(x=111.0, y=129.5,  z=0.3))
     ])
    #cybertruck 1
    v3_start_point = carla.Transform(carla.Location(x=92.3,y=120.8,z=2), carla.Rotation(pitch = 0, yaw=-90, roll=0))
    v3_waypoint = np.array([
    (carla.Location(x=190.0, y=59.5,  z=0.3))
     ])
    #sprinter 1
    v4_start_point = carla.Transform(carla.Location(x=150.0,y=59.5,z=2), carla.Rotation(pitch = 0, yaw=0, roll=0))
    v4_waypoint = np.array([
    (carla.Location(x=158.0, y=28.0,  z=0.3))
     ])
    #firetruck 2
    v5_start_point = carla.Transform(carla.Location(x=334.8,y=80.5,z=2), carla.Rotation(pitch = 0, yaw=90, roll=0))
    v5_waypoint = np.array([
    # carla.Location(x=300.0,y=129.5,z=2),
    (carla.Location(x=311.5, y=129.5,  z=0.3)),
     ])
    #firetruck 3
    v6_start_point = carla.Transform(carla.Location(x=334.8,y=60.5,z=2), carla.Rotation(pitch = 0, yaw=0, roll=0))
    v6_waypoint = np.array([
    # carla.Location(x=300.0,y=129.5,z=2),
    (carla.Location(x=311.5, y=129.5,  z=0.3)),
     ])
    #firetruck 4
    v7_start_point = carla.Transform(carla.Location(x=154,y=40,z=2), carla.Rotation(pitch = 0, yaw=90, roll=0))
    v7_waypoint = np.array([
    (carla.Location(x=130.0, y=55.5,  z=0.3)),
    (carla.Location(x=92.3, y=35.5,  z=0.3))
     ])
    #firetruck 5
    v8_start_point = carla.Transform(carla.Location(x=160.0,y=129.5,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))
    v8_waypoint = np.array([
    (carla.Location(x=150.0, y=59.5,  z=0.3)),
     ])
    #ambulance 3rd
    v9_start_point = carla.Transform(carla.Location(x=230.5,y=129.5,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))
    v9_waypoint = np.array([
    (carla.Location(x=111.0, y=129.5,  z=0.3)),
    (carla.Location(x=92.3, y=120.8, z=2))
     ])
    #carlacola
    v10_start_point = carla.Transform(carla.Location(x=92.3,y=110.0,z=2), carla.Rotation(pitch = 0, yaw=-90, roll=0))
    v10_waypoint = np.array([
    (carla.Location(x=150.0, y=59.5,  z=0.3))
     ])
    v_start_point.append(v1_start_point)
    v_waypoint.append(v1_waypoint)
    v_start_point.append(v2_start_point)
    v_waypoint.append(v2_waypoint)
    v_start_point.append(v3_start_point)
    v_waypoint.append(v3_waypoint)
    v_start_point.append(v4_start_point)
    v_waypoint.append(v4_waypoint)
    v_start_point.append(v5_start_point)
    v_waypoint.append(v5_waypoint)
    v_start_point.append(v6_start_point)
    v_waypoint.append(v6_waypoint)
    v_start_point.append(v7_start_point)
    v_waypoint.append(v7_waypoint)
    v_start_point.append(v8_start_point)
    v_waypoint.append(v8_waypoint)
    v_start_point.append(v9_start_point)
    v_waypoint.append(v9_waypoint)
    v_start_point.append(v10_start_point)
    v_waypoint.append(v10_waypoint)

    
    w1_start_point = carla.Transform(carla.Location(x=110.0,y=61.0,z=2), carla.Rotation(pitch = 0, yaw=-180, roll=0))
    w1_waypoint = np.array([
    w1_start_point.location
    # (carla.Location(x=130.0, y=61.0,  z=0.3))
     ])
    w2_start_point = carla.Transform(carla.Location(x=130.0,y=51.0,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))
    w2_waypoint = np.array([
    w2_start_point.location
    # (carla.Location(x=120.0, y=51.0,  z=0.3))
     ])
    w_start_point.append(w1_start_point)
    w_start_point.append(w2_start_point)
    w_waypoint.append(w1_waypoint)
    w_waypoint.append(w2_waypoint)
    
    
# elif global_map_id == 2:
#     agent_start_point = carla.Transform(carla.Location(x=168.7,y=55.6,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))
# elif global_map_id == 3:
#     agent_start_point = carla.Transform(carla.Location(x=168.7,y=55.6,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))
# elif global_map_id == 4:
#     agent_start_point = carla.Transform(carla.Location(x=168.7,y=55.6,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))
# elif global_map_id == 5:
#     agent_start_point = carla.Transform(carla.Location(x=168.7,y=55.6,z=2), carla.Rotation(pitch = 0, yaw=180, roll=0))

# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================


def find_weather_presets():
    """Method to find weather presets"""
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    def name(x): return ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    """Method to get actor display name"""
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


# ==============================================================================
# -- World ---------------------------------------------------------------
# ==============================================================================

class World(object):
    """ Class representing the surrounding environment """

    def __init__(self, client, hud, args):
        """Constructor method"""
        self._client = client
        self._args = args
        self.world = client.get_world()
        try:
            self.map = self.world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)
        self.hud = hud
        self.player = None
        self.npc_v1 = None
        self.npc_v2 = None
        self.npc_v3 = None
        self.npc_v4 = None
        self.npc_v5 = None
        self.npc_v6 = None
        self.npc_v7 = None
        self.npc_v8 = None
        self.npc_v9 = None
        self.npc_v10 = None
        self.npc_v = []
        
        self.npc_w1 = None
        self.npc_w2 = None
        self.npc_w = []
        
        self.v_agent = []
        self.v_control = []
        
        self.w_speed = []
        
        self.actor_list = []
        
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self._actor_filter = args.filter
        self.restart(args)
        self.world.on_tick(hud.on_world_tick)
        self.recording_enabled = False
        self.recording_start = 0
        
        
    def spawn_vehicle(self, vehicle_model, self_vehicle, start_point):
        blueprint = self.world.get_blueprint_library().filter(vehicle_model)[0]
        if self_vehicle is not None:
            spawn_point = self_vehicle.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self_vehicle = self.world.try_spawn_actor(blueprint, spawn_point)
            self.modify_vehicle_physics(self_vehicle)
        while self_vehicle is None:
            if not self.map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)
            spawn_point = start_point;
            self_vehicle = self.world.try_spawn_actor(blueprint, spawn_point)
            self.modify_vehicle_physics(self_vehicle)
            return self_vehicle
        self.actor_list.append(self_vehicle)
        
    def spawn_walker(self, p_type, self_walker, start_point):
        walkers_list = []
        while self_walker is None:
            blueprint_walker = self.world.get_blueprint_library().filter('walker.pedestrian.*')
            walker_bp = random.choice(blueprint_walker)
            
            # set as not invincible
            if walker_bp.has_attribute('is_invincible'):
                walker_bp.set_attribute('is_invincible', 'false')

            # set the max speed
            if walker_bp.has_attribute('speed'):
                if (p_type == 'run'):
                    # running
                    self.w_speed.append(walker_bp.get_attribute('speed').recommended_values[2])
                else:
                    # walking
                    self.w_speed.append(walker_bp.get_attribute('speed').recommended_values[1])
            else:
                    print("Walker has no speed")
                    self.w_speed.append(0.0)
            spawn_point = start_point;
            self_walker = self.world.try_spawn_actor(walker_bp, spawn_point)
            # print(self_walker.id)
        
            # 3. we spawn the walker controller
            # walker_controller_bp = self.world.get_blueprint_library().find('controller.ai.walker')
            # self_pedestrian_control = self.world.try_spawn_actor(walker_controller_bp, carla.Transform(), self_walker.id)
        self.actor_list.append(self_walker)
        return self_walker
        
    def control_walkers(self):
        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor
        
        all_walkers_id = []
        walkers_list = []
        walker_speed2 = []
        percentagePedestriansCrossing = 0.0
        for i in range(len(self.npc_w)):
            walkers_list.append({"id": self.npc_w[i].id})
            walker_speed2.append(self.w_speed[i])
        walker_speed = walker_speed2
        
        # 3. we spawn the walker controller
        batch = []
        walker_controller_bp = self.world.get_blueprint_library().find('controller.ai.walker')
        for i in range(len(walkers_list)):
                batch.append(SpawnActor(walker_controller_bp, carla.Transform(), walkers_list[i]["id"]))
        results = self._client.apply_batch_sync(batch, True)
        for i in range(len(results)):
            if results[i].error:
                logging.error(results[i].error)
            else:
                walkers_list[i]["con"] = results[i].actor_id
        # 4. we put altogether the walkers and controllers id to get the objects from their id
        for i in range(len(walkers_list)):
                all_walkers_id.append(walkers_list[i]["con"])
                all_walkers_id.append(walkers_list[i]["id"])
        all_actors = self.world.get_actors(all_walkers_id)
        
        # wait for a tick to ensure client receives the last transform of the walkers we have just created
        self.world.tick()

        # 5. initialize each controller and set target to walk to (list is [controler, actor, controller, actor ...])
        # set how many pedestrians can cross the road
        self.world.set_pedestrians_cross_factor(percentagePedestriansCrossing)
        
        for i in range(0, len(all_walkers_id), 2):
                # start walker
                all_actors[i].start()
                # set walk to random point
                # all_actors[i].go_to_location(w_waypoint[int(i/2)-1][0])
                all_actors[i].go_to_location(self.world.get_random_location_from_navigation())
                # max speed
                all_actors[i].set_max_speed(float(walker_speed[int(i/2)]))

        print('Spawned %d vehicles and %d walkers' % (len(vehicles_list), len(walkers_list)))

    

    def restart(self, args):
        """Restart the world"""
        # @todo cannot import these directly.
        # SpawnActor = carla.command.SpawnActor
        
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_id = self.camera_manager.transform_index if self.camera_manager is not None else 0

        # Get a random blueprint.
        # blueprint = random.choice(self.world.get_blueprint_library().filter(self._actor_filter))
        blueprint = self.world.get_blueprint_library().filter('vehicle.audi.tt')[0]
        # https://carla.readthedocs.io/en/latest/bp_library/
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)

        # Spawn the player.
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
            self.modify_vehicle_physics(self.player)
        while self.player is None:
            if not self.map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)
            # spawn_points = self.map.get_spawn_points()
            # spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            spawn_point = agent_start_point;
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
            self.modify_vehicle_physics(self.player)
        self.actor_list.append(self.player)
            
        # Spawn the vehicles
        self.npc_v1 = self.spawn_vehicle('firetruck',  self.npc_v1, v1_start_point)
        self.npc_v.append(self.npc_v1)
        self.npc_v2 = self.spawn_vehicle('ambulance',  self.npc_v2, v2_start_point)
        self.npc_v.append(self.npc_v2)
        self.npc_v3 = self.spawn_vehicle('cybertruck', self.npc_v3, v3_start_point)
        self.npc_v.append(self.npc_v3)
        self.npc_v4 = self.spawn_vehicle('sprinter',   self.npc_v4, v4_start_point)
        self.npc_v.append(self.npc_v4)
        self.npc_v5 = self.spawn_vehicle('firetruck',   self.npc_v5, v5_start_point)
        self.npc_v.append(self.npc_v5)
        self.npc_v6 = self.spawn_vehicle('firetruck',   self.npc_v6, v6_start_point)
        self.npc_v.append(self.npc_v6)
        self.npc_v7 = self.spawn_vehicle('firetruck',   self.npc_v7, v7_start_point)
        self.npc_v.append(self.npc_v7)

        self.npc_v8 = self.spawn_vehicle('firetruck',   self.npc_v8, v8_start_point)
        self.npc_v.append(self.npc_v8)
        self.npc_v9 = self.spawn_vehicle('ambulance',   self.npc_v9, v9_start_point)
        self.npc_v.append(self.npc_v9)
        self.npc_v10 = self.spawn_vehicle('carlacola',   self.npc_v10, v10_start_point)
        self.npc_v.append(self.npc_v10)

        # print(len(self.npc_v))
        
        # Spawn the walkers
        if flag_spawn_walkers == True:
            self.npc_w1 = self.spawn_walker('run', self.npc_w1, w1_start_point)
            self.npc_w2 = self.spawn_walker('run', self.npc_w2, w2_start_point)
            self.npc_w.append(self.npc_w1)
            self.npc_w.append(self.npc_w2)
            self.control_walkers();
        
        # example of how to use parameters
        # self._client.get_trafficmanager().global_percentage_speed_difference(30.0)
       
        
        if self._args.sync:
            self.world.tick()
        else:
            self.world.wait_for_tick()

        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud)
        self.camera_manager.transform_index = cam_pos_id
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

    def next_weather(self, reverse=False):
        """Get next weather setting"""
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def modify_vehicle_physics(self, actor):
        #If actor is not a vehicle, we cannot use the physics control
        try:
            physics_control = actor.get_physics_control()
            physics_control.use_sweep_wheel_collision = True
            actor.apply_physics_control(physics_control)
        except Exception:
            pass

    def tick(self, clock):
        """Method for every tick"""
        self.hud.tick(self, clock)

    def render(self, display):
        """Render world"""
        self.camera_manager.render(display)
        self.hud.render(display)

    def destroy_sensors(self):
        """Destroy sensors"""
        self.camera_manager.sensor.destroy()
        self.camera_manager.sensor = None
        self.camera_manager.index = None

    def destroy(self):
        """Destroys all actors"""
        actors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor,
            self.player,
            self.npc_v1,
            self.npc_v2,
            self.npc_v3,
            self.npc_v4,
            self.npc_v5,
            self.npc_v6,
            self.npc_v7,
            self.npc_v8,
            self.npc_v9,
            self.npc_v10,
            # self.npc_v,
            # self.v_agent,
            # self.v_control
            ]
        for actor in actors:
            if actor is not None:
                actor.destroy()


# ==============================================================================
# -- KeyboardControl -----------------------------------------------------------
# ==============================================================================


class KeyboardControl(object):
    def __init__(self, world):
        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def parse_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True

    @staticmethod
    def _is_quit_shortcut(key):
        """Shortcut for quitting"""
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

# ==============================================================================
# -- HUD -----------------------------------------------------------------------
# ==============================================================================


class HUD(object):
    """Class for HUD text"""

    def __init__(self, width, height):
        """Constructor method"""
        self.dim = (width, height)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.help = HelpText(pygame.font.Font(mono, 24), width, height)
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()

    def on_world_tick(self, timestamp):
        """Gets informations from the world at every tick"""
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        self.frame = timestamp.frame_count
        self.simulation_time = timestamp.elapsed_seconds

    def tick(self, world, clock):
        """HUD method for every tick"""
        self._notifications.tick(world, clock)
        if not self._show_info:
            return
        transform = world.player.get_transform()
        vel = world.player.get_velocity()
        control = world.player.get_control()
        heading = 'N' if abs(transform.rotation.yaw) < 89.5 else ''
        heading += 'S' if abs(transform.rotation.yaw) > 90.5 else ''
        heading += 'E' if 179.5 > transform.rotation.yaw > 0.5 else ''
        heading += 'W' if -0.5 > transform.rotation.yaw > -179.5 else ''
        colhist = world.collision_sensor.get_collision_history()
        collision = [colhist[x + self.frame - 200] for x in range(0, 200)]
        max_col = max(1.0, max(collision))
        collision = [x / max_col for x in collision]
        vehicles = world.world.get_actors().filter('vehicle.*')

        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % clock.get_fps(),
            '',
            'Vehicle: % 20s' % get_actor_display_name(world.player, truncate=20),
            'Map:     % 20s' % world.map.name.split('/')[-1],
            'Simulation time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            '',
            'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(vel.x**2 + vel.y**2 + vel.z**2)),
            u'Heading:% 16.0f\N{DEGREE SIGN} % 2s' % (transform.rotation.yaw, heading),
            'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (transform.location.x, transform.location.y)),
            'GNSS:% 24s' % ('(% 2.6f, % 3.6f)' % (world.gnss_sensor.lat, world.gnss_sensor.lon)),
            'Height:  % 18.0f m' % transform.location.z,
            '']
        if isinstance(control, carla.VehicleControl):
            self._info_text += [
                ('Throttle:', control.throttle, 0.0, 1.0),
                ('Steer:', control.steer, -1.0, 1.0),
                ('Brake:', control.brake, 0.0, 1.0),
                ('Reverse:', control.reverse),
                ('Hand brake:', control.hand_brake),
                ('Manual:', control.manual_gear_shift),
                'Gear:        %s' % {-1: 'R', 0: 'N'}.get(control.gear, control.gear)]
        elif isinstance(control, carla.WalkerControl):
            self._info_text += [
                ('Speed:', control.speed, 0.0, 5.556),
                ('Jump:', control.jump)]
        self._info_text += [
            '',
            'Collision:',
            collision,
            '',
            'Number of vehicles: % 8d' % len(vehicles)]

        if len(vehicles) > 1:
            self._info_text += ['Nearby vehicles:']

        def dist(l):
            return math.sqrt((l.x - transform.location.x)**2 + (l.y - transform.location.y)
                             ** 2 + (l.z - transform.location.z)**2)
        vehicles = [(dist(x.get_location()), x) for x in vehicles if x.id != world.player.id]

        for dist, vehicle in sorted(vehicles):
            if dist > 200.0:
                break
            vehicle_type = get_actor_display_name(vehicle, truncate=22)
            self._info_text.append('% 4dm %s' % (dist, vehicle_type))

    def toggle_info(self):
        """Toggle info on or off"""
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        """Notification text"""
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        """Error text"""
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def render(self, display):
        """Render for HUD class"""
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        fig = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect(
                                (bar_h_offset + fig * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (fig * bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (8, v_offset))
                v_offset += 18
        self._notifications.render(display)
        self.help.render(display)

# ==============================================================================
# -- FadingText ----------------------------------------------------------------
# ==============================================================================


class FadingText(object):
    """ Class for fading text """

    def __init__(self, font, dim, pos):
        """Constructor method"""
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        """Set fading text"""
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        """Fading text method for every tick"""
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        """Render fading text method"""
        display.blit(self.surface, self.pos)

# ==============================================================================
# -- HelpText ------------------------------------------------------------------
# ==============================================================================


class HelpText(object):
    """ Helper class for text render"""

    def __init__(self, font, width, height):
        """Constructor method"""
        lines = __doc__.split('\n')
        self.font = font
        self.dim = (680, len(lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))
        for i, line in enumerate(lines):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, i * 22))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        """Toggle on or off the render help"""
        self._render = not self._render

    def render(self, display):
        """Render help text method"""
        if self._render:
            display.blit(self.surface, self.pos)

# ==============================================================================
# -- CollisionSensor -----------------------------------------------------------
# ==============================================================================


class CollisionSensor(object):
    """ Class for collision sensors"""

    def __init__(self, parent_actor, hud):
        """Constructor method"""
        self.sensor = None
        self.history = []
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to
        # self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: CollisionSensor._on_collision(weak_self, event))

    def get_collision_history(self):
        """Gets the history of collisions"""
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        """On collision method"""
        self = weak_self()
        if not self:
            return
        actor_type = get_actor_display_name(event.other_actor)
        self.hud.notification('Collision with %r' % actor_type)
        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x ** 2 + impulse.y ** 2 + impulse.z ** 2)
        self.history.append((event.frame, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)

# ==============================================================================
# -- LaneInvasionSensor --------------------------------------------------------
# ==============================================================================


class LaneInvasionSensor(object):
    """Class for lane invasion sensors"""

    def __init__(self, parent_actor, hud):
        """Constructor method"""
        self.sensor = None
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: LaneInvasionSensor._on_invasion(weak_self, event))

    @staticmethod
    def _on_invasion(weak_self, event):
        """On invasion method"""
        self = weak_self()
        if not self:
            return
        lane_types = set(x.type for x in event.crossed_lane_markings)
        text = ['%r' % str(x).split()[-1] for x in lane_types]
        self.hud.notification('Crossed line %s' % ' and '.join(text))

# ==============================================================================
# -- GnssSensor --------------------------------------------------------
# ==============================================================================


class GnssSensor(object):
    """ Class for GNSS sensors"""

    def __init__(self, parent_actor):
        """Constructor method"""
        self.sensor = None
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(blueprint, carla.Transform(carla.Location(x=1.0, z=2.8)),
                                        attach_to=self._parent)
        # We need to pass the lambda a weak reference to
        # self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: GnssSensor._on_gnss_event(weak_self, event))

    @staticmethod
    def _on_gnss_event(weak_self, event):
        """GNSS method"""
        self = weak_self()
        if not self:
            return
        self.lat = event.latitude
        self.lon = event.longitude

# ==============================================================================
# -- CameraManager -------------------------------------------------------------
# ==============================================================================


class CameraManager(object):
    """ Class for camera management"""

    def __init__(self, parent_actor, hud):
        """Constructor method"""
        self.sensor = None
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        bound_y = 0.5 + self._parent.bounding_box.extent.y
        attachment = carla.AttachmentType
        self._camera_transforms = [
            (carla.Transform(
                carla.Location(x=-5.5, z=2.5), carla.Rotation(pitch=8.0)), attachment.SpringArm),
            (carla.Transform(
                carla.Location(x=1.6, z=1.7)), attachment.Rigid),
            (carla.Transform(
                carla.Location(x=5.5, y=1.5, z=1.5)), attachment.SpringArm),
            (carla.Transform(
                carla.Location(x=-8.0, z=6.0), carla.Rotation(pitch=6.0)), attachment.SpringArm),
            (carla.Transform(
                carla.Location(x=-1, y=-bound_y, z=0.5)), attachment.Rigid)]
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB'],
            ['sensor.camera.depth', cc.Raw, 'Camera Depth (Raw)'],
            ['sensor.camera.depth', cc.Depth, 'Camera Depth (Gray Scale)'],
            ['sensor.camera.depth', cc.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)'],
            ['sensor.camera.semantic_segmentation', cc.Raw, 'Camera Semantic Segmentation (Raw)'],
            ['sensor.camera.semantic_segmentation', cc.CityScapesPalette,
             'Camera Semantic Segmentation (CityScapes Palette)'],
            ['sensor.lidar.ray_cast', None, 'Lidar (Ray-Cast)']]
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            blp = bp_library.find(item[0])
            if item[0].startswith('sensor.camera'):
                blp.set_attribute('image_size_x', str(hud.dim[0]))
                blp.set_attribute('image_size_y', str(hud.dim[1]))
            elif item[0].startswith('sensor.lidar'):
                blp.set_attribute('range', '50')
            item.append(blp)
        self.index = None

    def toggle_camera(self):
        """Activate a camera"""
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.set_sensor(self.index, notify=False, force_respawn=True)

    def set_sensor(self, index, notify=True, force_respawn=False):
        """Set a sensor"""
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None else (
            force_respawn or (self.sensors[index][0] != self.sensors[self.index][0]))
        if needs_respawn:
            if self.sensor is not None:
                self.sensor.destroy()
                self.surface = None
            self.sensor = self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[self.transform_index][0],
                attach_to=self._parent,
                attachment_type=self._camera_transforms[self.transform_index][1])

            # We need to pass the lambda a weak reference to
            # self to avoid circular reference.
            weak_self = weakref.ref(self)
            self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        """Get the next sensor"""
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        """Toggle recording on or off"""
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        """Render method"""
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        if self.sensors[self.index][0].startswith('sensor.lidar'):
            points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
            points = np.reshape(points, (int(points.shape[0] / 4), 4))
            lidar_data = np.array(points[:, :2])
            lidar_data *= min(self.hud.dim) / 100.0
            lidar_data += (0.5 * self.hud.dim[0], 0.5 * self.hud.dim[1])
            lidar_data = np.fabs(lidar_data)  # pylint: disable=assignment-from-no-return
            lidar_data = lidar_data.astype(np.int32)
            lidar_data = np.reshape(lidar_data, (-1, 2))
            lidar_img_size = (self.hud.dim[0], self.hud.dim[1], 3)
            lidar_img = np.zeros(lidar_img_size)
            lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
            self.surface = pygame.surfarray.make_surface(lidar_img)
        else:
            image.convert(self.sensors[self.index][1])
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            image.save_to_disk('_out/%08d' % image.frame)

# ==============================================================================
# -- Game Loop ---------------------------------------------------------
# ==============================================================================


vehicles_list = []

def game_loop(args):
    """
    Main loop of the simulation. It handles updating all the HUD information,
    ticking the agent and, if needed, the world.
    """

    pygame.init()
    pygame.font.init()
    world = None
    
    #parameter
    fps_simu = 100.0
    time_stop = 2.0
    nbr_frame = 500 #180 #MAX=10000
    
    try:
        if args.seed:
            random.seed(args.seed)

        
        client = carla.Client(args.host, args.port)
        client.set_timeout(4.0)
        
        traffic_manager = client.get_trafficmanager()
        # sim_world = client.get_world()
        # sim_world = client.load_world("Town01")
        sim_world = client.load_world('Town01_Opt', carla.MapLayer.Buildings | carla.MapLayer.ParkedVehicles | carla.MapLayer.StreetLights)
        sim_world.unload_map_layer(carla.MapLayer.StreetLights)
        
        if args.sync:
            settings = sim_world.get_settings()
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = 1.0/fps_simu #0.05
            sim_world.apply_settings(settings)

            traffic_manager.set_synchronous_mode(True)
        
        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        hud = HUD(args.width, args.height)
        world = World(client, hud, args)
        
        # Weather
        sim_world.set_weather(carla.WeatherParameters.CloudyNoon)
        # ClearNoon, CloudyNoon, WetNoon, WetCloudyNoon, SoftRainNoon, MidRainyNoon, HardRainNoon, 
        # ClearSunset, CloudySunset, WetSunset, WetCloudySunset, SoftRainSunset, MidRainSunset, HardRainSunset.
        
        folder_output = "../../results_kitti_carla/KITTI_Dataset_CARLA_v%s/%s/generated" %(client.get_client_version(), sim_world.get_map().name)
        os.makedirs(folder_output) if not os.path.exists(folder_output) else [os.remove(f) for f in glob.glob(folder_output+"/*") if os.path.isfile(f)]
        client.start_recorder(os.path.dirname(os.path.realpath(__file__))+"/"+folder_output+"/recording.log")
        
        # Wait for KITTI to stop
        start = sim_world.get_snapshot().timestamp.elapsed_seconds
        print("Waiting for KITTI to stop ...")
        while sim_world.get_snapshot().timestamp.elapsed_seconds-start < time_stop: sim_world.tick()
        print("KITTI stopped")
        
        # Set sensors transformation from KITTI
        lidar_transform = carla.Transform(carla.Location(x=0, y=0, z=1.73), carla.Rotation(pitch=0, yaw=180, roll=0))
        cam0_transform  = carla.Transform(carla.Location(x=0.27, y=0, z=1.65), carla.Rotation(pitch=0, yaw=0, roll=0))
        cam1_transform  = carla.Transform(carla.Location(x=0.27, y=0.54, z=1.65), carla.Rotation(pitch=0, yaw=0, roll=0))
        
        # Take a screenshot
        gen.screenshot(world.player, sim_world, world.actor_list, folder_output, carla.Transform(carla.Location(x=0.0, y=0, z=2.0), carla.Rotation(pitch=0, yaw=0, roll=0)))

        # Create our sensors
        gen.RGB.sensor_id_glob = 0
        gen.SS.sensor_id_glob = 10
        gen.Depth.sensor_id_glob = 20
        gen.HDL64E.sensor_id_glob = 100
        VelodyneHDL64 = gen.HDL64E(world.player, sim_world, world.actor_list, folder_output, lidar_transform)
        cam0 = gen.RGB(world.player, sim_world, world.actor_list, folder_output, cam0_transform)
        cam1 = gen.RGB(world.player, sim_world, world.actor_list, folder_output, cam1_transform)
        cam0_ss = gen.SS(world.player, sim_world, world.actor_list, folder_output, cam0_transform)
        cam1_ss = gen.SS(world.player, sim_world, world.actor_list, folder_output, cam1_transform)
        cam0_depth = gen.Depth(world.player, sim_world, world.actor_list, folder_output, cam0_transform)
        cam1_depth = gen.Depth(world.player, sim_world, world.actor_list, folder_output, cam1_transform)
        print("create sensors")

        # Export cam0 to LiDAR transformation: T_CL
        tf_cam0_lidar = gen.transform_camera_to_lidar(lidar_transform, cam0_transform)
        with open(folder_output+"/cam0_to_lidar.txt", 'w') as posfile:
            posfile.write("#R(0,0) R(0,1) R(0,2) t(0) R(1,0) R(1,1) R(1,2) t(1) R(2,0) R(2,1) R(2,2) t(2)\n")
            posfile.write(str(tf_cam0_lidar[0][0])+" "+str(tf_cam0_lidar[0][1])+" "+str(tf_cam0_lidar[0][2])+" "+str(tf_cam0_lidar[0][3])+" ")
            posfile.write(str(tf_cam0_lidar[1][0])+" "+str(tf_cam0_lidar[1][1])+" "+str(tf_cam0_lidar[1][2])+" "+str(tf_cam0_lidar[1][3])+" ")
            posfile.write(str(tf_cam0_lidar[2][0])+" "+str(tf_cam0_lidar[2][1])+" "+str(tf_cam0_lidar[2][2])+" "+str(tf_cam0_lidar[2][3]))
        
        # Export cam1 to LiDAR transformation: T_CL
        tf_cam1_lidar = gen.transform_camera_to_lidar(lidar_transform, cam1_transform)
        with open(folder_output+"/cam1_to_lidar.txt", 'w') as posfile:
            posfile.write("#R(0,0) R(0,1) R(0,2) t(0) R(1,0) R(1,1) R(1,2) t(1) R(2,0) R(2,1) R(2,2) t(2)\n")
            posfile.write(str(tf_cam1_lidar[0][0])+" "+str(tf_cam1_lidar[0][1])+" "+str(tf_cam1_lidar[0][2])+" "+str(tf_cam1_lidar[0][3])+" ")
            posfile.write(str(tf_cam1_lidar[1][0])+" "+str(tf_cam1_lidar[1][1])+" "+str(tf_cam1_lidar[1][2])+" "+str(tf_cam1_lidar[1][3])+" ")
            posfile.write(str(tf_cam1_lidar[2][0])+" "+str(tf_cam1_lidar[2][1])+" "+str(tf_cam1_lidar[2][2])+" "+str(tf_cam1_lidar[2][3]))
        
        controller = KeyboardControl(world)
        if args.agent == "Basic":
            agent = BasicAgent(world.player)
        else:
            agent = BehaviorAgent(world.player, behavior=args.behavior)

        # Set the agent destination
        agent.set_destination(agent_waypoint[0])
        print('new destination: Location(x=%.1f, y=%.1f, z=%.1f)'
              %(agent_waypoint[0].x, agent_waypoint[0].y, agent_waypoint[0].z) )
        
        # generate_npc  
        v1_agent = BehaviorAgent(world.npc_v1, behavior=args.behavior)
        v1_agent.set_destination(v1_waypoint[0])
        
        v2_agent = BehaviorAgent(world.npc_v2, behavior=args.behavior)
        v2_agent.set_destination(v2_waypoint[0])
        
        v3_agent = BehaviorAgent(world.npc_v3, behavior=args.behavior)
        v3_agent.set_destination(v3_waypoint[0])
        
        v4_agent = BehaviorAgent(world.npc_v4, behavior=args.behavior)
        v4_agent.set_destination(v4_waypoint[0])

        v5_agent = BehaviorAgent(world.npc_v5, behavior=args.behavior)
        v5_agent.set_destination(v5_waypoint[0])

        v6_agent = BehaviorAgent(world.npc_v6, behavior=args.behavior)
        v6_agent.set_destination(v6_waypoint[0])

        v7_agent = BehaviorAgent(world.npc_v7, "aggressive")
        v7_agent.set_destination(v7_waypoint[0])

        v8_agent = BehaviorAgent(world.npc_v8, "aggressive")
        v8_agent.set_destination(v8_waypoint[0])
        
        v9_agent = BehaviorAgent(world.npc_v9, "aggressive")
        v9_agent.set_destination(v9_waypoint[0])

        v10_agent = BehaviorAgent(world.npc_v10, behavior=args.behavior)
        v10_agent.set_destination(v10_waypoint[0])
        
        for i in range(0,len(world.npc_v)):
            v_agent_temp = BehaviorAgent(world.npc_v[i], behavior=args.behavior)
            v_agent_temp.set_destination(v_waypoint[i][0])
            world.v_agent.append(v_agent_temp)
            
        # Set pedestrian
        # results = client.apply_batch_sync(world.npc_w, True)
        # walkers_list = []
        # walker_speed2 = []
        # for i in range(len(results)):
        #         if results[i].error:
        #                 logging.error(results[i].error)
        #         else:
        #                 walkers_list.append({"id": results[i].actor_id})
        #                 walker_speed2.append(walker_speed[i])
        # walker_speed = walker_speed2

        clock = pygame.time.Clock()

        cnt_waypoint = 0;
        
        cnt_v_waypoint = []
        for i in range(0, len(v_waypoint)):
            cnt_v_waypoint.append(0)
            
        v_spawn_points = world.map.get_spawn_points()

        # Pass to the next simulator frame to spawn sensors and to retrieve first data
        sim_world.tick()
        
        VelodyneHDL64.init()
        gen.follow(world.player.get_transform(), sim_world)
        # All sensors produce first data at the same time (this ts)
        gen.Sensor.initial_ts = sim_world.get_snapshot().timestamp.elapsed_seconds
            
        start_record = time.time()
        print("Start record : ")
        frame_current = 0

        for i in range(0, len(world.v_agent)):
            print('<V%d_agent> 1th destination: Location(x=%.1f, y=%.1f, z=%.1f)'
                %(i+1, v_waypoint[i][cnt_v_waypoint[i]].x, v_waypoint[i][cnt_v_waypoint[i]].y, v_waypoint[i][cnt_v_waypoint[i]].z) )
        
        while (frame_current < nbr_frame):
            clock.tick()
            if args.sync:
                world.world.tick()
            else:
                world.world.wait_for_tick()
            # if controller.parse_events():
            #     return

            sim_world.tick()
            world.tick(clock)
            world.render(display)
            pygame.display.flip()
            
            frame_current = VelodyneHDL64.save()
            # cam0.save()
            # cam1.save()
            # cam0_ss.save()
            # cam1_ss.save()
            # cam0_depth.save()
            # cam1_depth.save()
            gen.follow(world.player.get_transform(), sim_world)
            # world.tick()    # Pass to the next simulator frame
            for i in range(0, len(world.v_agent)):
                if world.v_agent[i].done():
                    cnt_v_waypoint[i] += 1
                    if cnt_v_waypoint[i] > len(v_waypoint[i])-1:
                        world.v_agent[i].set_destination(random.choice(v_spawn_points).location)
                    else:
                        world.v_agent[i].set_destination(v_waypoint[i][cnt_v_waypoint[i]])
                        print('<V%d_agent> %dth destination: Location(x=%.1f, y=%.1f, z=%.1f)'
                                %(i+1, cnt_waypoint+1, v_waypoint[i][cnt_v_waypoint[i]].x, v_waypoint[i][cnt_v_waypoint[i]].y, v_waypoint[i][cnt_v_waypoint[i]].z) )

            # if v1_agent.done():
            #     cnt_waypoint_v1 += 1
            #     if cnt_waypoint_v1 > len(v1_waypoint)-1:
            #         v1_agent.set_destination(random.choice(v_spawn_points).location)
            #     else:
            #         agent.set_destination(v1_waypoint[cnt_waypoint_v1])
            #         print('v1_agent new destination: Location(x=%.1f, y=%.1f, z=%.1f)'
            #                 %(v1_waypoint[cnt_waypoint_v1].x, v1_waypoint[cnt_waypoint_v1].y, v1_waypoint[cnt_waypoint_v1].z) )
            
            # if v2_agent.done():
            #     cnt_waypoint_v2 += 1
            #     if cnt_waypoint_v2 > len(v2_waypoint)-1:
            #         v2_agent.set_destination(random.choice(v_spawn_points).location)
            #     else:
            #         agent.set_destination(v2_waypoint[cnt_waypoint_v2])
            #         print('v2_agent new destination: Location(x=%.1f, y=%.1f, z=%.1f)'
            #                 %(v2_waypoint[cnt_waypoint_v2].x, v2_waypoint[cnt_waypoint_v2].y, v2_waypoint[cnt_waypoint_v2].z) )
                    
            # if v3_agent.done():
            #     cnt_waypoint_v3 += 1
            #     if cnt_waypoint_v3 > len(v3_waypoint)-1:
            #         v3_agent.set_destination(random.choice(v_spawn_points).location)
            #     else:
            #         agent.set_destination(v3_waypoint[cnt_waypoint_v3])
            #         print('v3_agent new destination: Location(x=%.1f, y=%.1f, z=%.1f)'
            #                 %(v3_waypoint[cnt_waypoint_v3].x, v3_waypoint[cnt_waypoint_v3].y, v3_waypoint[cnt_waypoint_v3].z) )
                    
            # if v4_agent.done():
            #     cnt_waypoint_v4 += 1
            #     if cnt_waypoint_v4 > len(v4_waypoint)-1:
            #         v4_agent.set_destination(random.choice(v_spawn_points).location)
            #     else:
            #         agent.set_destination(v4_waypoint[cnt_waypoint_v4])
            #         print('v4_agent new destination: Location(x=%.1f, y=%.1f, z=%.1f)'
            #                 %(v4_waypoint[cnt_waypoint_v4].x, v4_waypoint[cnt_waypoint_v4].y, v4_waypoint[cnt_waypoint_v4].z) )

            # if v7_agent.done():
            #     cnt_waypoint_v7 += 1
            #     if cnt_waypoint_v7 > len(v7_waypoint)-1:
            #         v7_agent.set_destination(random.choice(v_spawn_points).location)
            #     else:
            #         agent.set_destination(v7_waypoint[cnt_waypoint_v7])
            #         print('v7_agent new destination: Location(x=%.1f, y=%.1f, z=%.1f)'
            #                 %(v7_waypoint[cnt_waypoint_v7].x, v7_waypoint[cnt_waypoint_v7].y, v7_waypoint[cnt_waypoint_v7].z) ) 

            # if v9_agent.done():
            #     cnt_waypoint_v9 += 1
            #     if cnt_waypoint_v9 > len(v9_waypoint)-1:
            #         v9_agent.set_destination(random.choice(v_spawn_points).location)
            #     else:
            #         agent.set_destination(v9_waypoint[cnt_waypoint_v9])
            #         print('v9_agent new destination: Location(x=%.1f, y=%.1f, z=%.1f)'
            #                 %(v9_waypoint[cnt_waypoint_v9].x, v9_waypoint[cnt_waypoint_v9].y, v9_waypoint[cnt_waypoint_v9].z) ) 

            if agent.done():
                cnt_waypoint += 1
                if cnt_waypoint > len(agent_waypoint)-1:
                    break
                agent.set_destination(agent_waypoint[cnt_waypoint])
                print('<Player>   %dth destination: Location(x=%.1f, y=%.1f, z=%.1f)'
                    %(cnt_waypoint+1, agent_waypoint[cnt_waypoint].x, agent_waypoint[cnt_waypoint].y, agent_waypoint[cnt_waypoint].z) )
                
               
            
            if agent.done():
                if args.loop:
                    world.hud.notification("The target has been reached, searching for another target", seconds=4.0)
                    print("The target has been reached, searching forW another target")
                else:
                    print("The target has been reached, stopping the simulation")
                    break
                    
            control = agent.run_step()
            control.manual_gear_shift = False
            world.player.apply_control(control)
            
            for i in range(0,len(world.v_agent)):
                world.v_control.insert(i, world.v_agent[i].run_step())
                world.v_control[i].manual_gear_shift = False
                world.npc_v[i].apply_control(world.v_control[i])
            
            # v1_control = v1_agent.run_step()
            # v1_control.manual_gear_shift = False
            # world.npc_v1.apply_control(v1_control)
            
            # v2_control = v2_agent.run_step()
            # v2_control.manual_gear_shift = False
            # world.npc_v2.apply_control(v2_control)
            
            # v3_control = v3_agent.run_step()
            # v3_control.manual_gear_shift = False
            # world.npc_v3.apply_control(v3_control)
            
            # v4_control = v4_agent.run_step()
            # v4_control.manual_gear_shift = False
            # world.npc_v4.apply_control(v4_control)
        
        VelodyneHDL64.save_poses()
        client.stop_recorder()
        print("Stop record")
        
        vehicles_list.clear()
        
        # print('Destroying KITTI')
        # client.apply_batch([carla.command.DestroyActor(x) for x in world.actor_list])
        # world.actor_list.clear()
            
        # print("Elapsed time : ", time.time()-start_record)
        # print()
            
        # time.sleep(2.0)

    finally:

        if world is not None:
            settings = world.world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            world.world.apply_settings(settings)
            traffic_manager.set_synchronous_mode(True)

            world.destroy()
            print("-->Destroying world")

        pygame.quit()


# ==============================================================================
# -- main() --------------------------------------------------------------
# ==============================================================================


def main():
    """Main method"""

    argparser = argparse.ArgumentParser(
        description='CARLA Automatic Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='Print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='Window resolution (default: 1280x720)')
    argparser.add_argument(
        '--sync',
        action='store_true',
        help='Synchronous mode execution')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='Actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '-l', '--loop',
        action='store_true',
        dest='loop',
        help='Sets a new random destination upon reaching the previous one (default: False)')
    argparser.add_argument(
        "-a", "--agent", type=str,
        choices=["Behavior", "Basic"],
        help="select which agent to run",
        default="Behavior")
    argparser.add_argument(
        '-b', '--behavior', type=str,
        choices=["cautious", "normal", "aggressive"],
        help='Choose one of the possible agent behaviors (default: normal) ',
        default='aggressive')
    argparser.add_argument(
        '-s', '--seed',
        help='Set seed for repeating executions (default: None)',
        default=None,
        type=int)

    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    try:
        game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':
    main()
