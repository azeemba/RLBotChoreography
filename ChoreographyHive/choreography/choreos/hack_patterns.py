import math
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

from RLUtilities.GameInfo import GameInfo
from RLUtilities.Maneuvers import vec3, Aerial
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.messages.flat.GameTickPacket import GameTickPacket
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface
from scipy.spatial.transform import Rotation

from choreography.choreography import Choreography
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone, slow_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, GroupStep, SubGroupChoreography, \
    SubGroupOrchestrator
from util.vec import Vec3

BASE_CAR_Z = 17


class HackSubgroup(SubGroupChoreography):
    def __init__(self, game_interface: GameInterface, game_info: GameInfo, drones: List[Drone],
                 start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.renderer = self.game_interface.renderer
        self.game_info = game_info
        self.aerials: List[Aerial] = []
        self.target_list = []
        self.center_of_rotation = np.array([0, -3000, 800])


    def generate_sequence(self, drones: List[Drone]):
        self.aerials = []

        if len(drones) == 0:
            return


        axis_1 = 4
        axis_2 = 4

        self.target_list = [
            np.array([
                (i % axis_1) * 200 - 300,
                ((i // axis_1) % (axis_1 * axis_2)) * 200 - 100,
                (i // (axis_1 * axis_2)) * 200 + 200
            ])
            for i in range(len(drones))
        ]

        for i in range(60):
            self.sequence.append(DroneListStep(self.arrange_in_grid))

        self.sequence.append(DroneListStep(self.flight_pattern))

    def arrange_in_grid(self, packet, drones, start_time) -> StepResult:
        if len(drones) == 0 or len(self.target_list) < len(drones):
            return StepResult(finished=True)

        car_states = {}

        for index, drone in enumerate(drones):
            loc = self.target_list[index]

            car_states[drone.index] = CarState(
                Physics(location=Vector3(loc[0], loc[1], loc[2]),
                        velocity=Vector3(0, 0, 400),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(math.pi / 2, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def flight_pattern(self, packet, drones: List[Drone], start_time) -> StepResult:

        elapsed = packet.game_info.seconds_elapsed - start_time

        rotation = Rotation.from_rotvec([0, elapsed * 8, 0]).as_matrix()
        car_states = {}

        for index, drone in enumerate(drones):
            drone.ctrl.boost = True
            spawn_loc = self.target_list[index]
            loc = rotation.dot(spawn_loc - self.center_of_rotation) + self.center_of_rotation

            car_states[drone.index] = CarState(
                Physics(location=Vector3(loc[0], loc[1], loc[2]),
                        velocity=Vector3(0, 0, 400),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(math.pi / 2, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))

        return StepResult(finished=elapsed > 7)


class HackPatterns(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

        self.game_info = GameInfo(0, 0)
        self.renderer = self.game_interface.renderer

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        self.game_info.read_packet(packet)

    @staticmethod
    def get_num_bots():
        return 48

    def generate_sequence(self, drones):
        self.sequence.clear()

        if len(drones) == 0:
            return

        self.sequence.append(HideBall(self.game_interface))
        self.sequence.append(LetAllCarsSpawn(self.game_interface, self.get_num_bots()))

        self.sequence.append(SubGroupOrchestrator(group_list=[
            HackSubgroup(self.game_interface, self.game_info, drones, 0)
        ]))
