import csv
from math import tan
from typing import Dict, List
from collections import defaultdict
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.game_state_util import (
    GameState,
    CarState,
    Physics,
    Vector3,
    Rotator,
    BallState,
)

from choreography.choreography import Choreography
from choreography.common.preparation import HideBall, LetAllCarsSpawn

from choreography.group_step import (
    DroneListStep,
    StepResult,
    PerDroneStep,
    BlindBehaviorStep,
)

START_ANGLE = 30.0 / 180.0
ANGLE_SPEED = 20.0 / 180.0


def list_to_indexed_map(items):
    indexed = {}
    for i in range(len(items)):
        indexed[i] = items[i]
    return indexed


class BirdFlap(Choreography):
    def __init__(self, game_interface):
        super().__init__()
        self.game_interface = game_interface

        self.data = defaultdict(list)
        with open("wing_flap.csv") as fh:
            reader = csv.DictReader(
                fh,
                quoting=csv.QUOTE_NONNUMERIC,
                fieldnames=["index", "time", "x", "y", "z"],
            )
            for row in reader:
                self.data[row["index"]].append(row)

    @staticmethod
    def get_num_bots():
        return 8

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(LetAllCarsSpawn(self.get_num_bots()))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 2))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 2))
        self.sequence.append(DroneListStep(self.flap))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 2))
        self.sequence.append(DroneListStep(self.score))

    def make_locations(self, angle, length) -> List[Vector3]:
        last = Vector3(0, 0, 500)
        positions = []
        y_spacing = 100
        x_spacing = -30
        last_angle = angle
        for _ in range(length):
            cur_angle = last_angle + angle
            location = Vector3(
                last.x + x_spacing,
                last.y + y_spacing,
                last.z + tan(cur_angle) * y_spacing,
            )
            positions.append(location)
            last = location
            last_angle = cur_angle
        return positions

    def calc_velo(self, now: Vector3, future: Vector3, dt):
        velo = Vector3(
            (future.x - now.x) / dt, (future.y - now.y) / dt, (future.z - now.z) / dt
        )
        return velo

    def calc_angle(self, elapsed):
        angle = START_ANGLE
        if elapsed < 2:
            angle -= elapsed * ANGLE_SPEED
        else:
            angle += -2 * ANGLE_SPEED + (elapsed - 2) * ANGLE_SPEED
        return angle

    def make_car_state(self, elapsed, length):
        car_stats = []
        dt = 1.0 / 60.0
        location_now = self.make_locations(self.calc_angle(elapsed), length)
        location_future = self.make_locations(self.calc_angle(elapsed + dt), length)
        for (now, future) in zip(location_now, location_future):
            velo = self.calc_velo(now, future, dt)
            car_stats.append(CarState(Physics(location=now, velocity=velo)))

        return list_to_indexed_map(car_stats)

    def line_up(self, packet, drones, start_time) -> StepResult:
        car_states = self.make_car_state(0, self.get_num_bots())
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def flap(self, packet, drones, start_time) -> StepResult:
        elapsed = packet.game_info.seconds_elapsed - start_time
        car_states = self.make_car_state(elapsed, self.get_num_bots())
        self.game_interface.set_game_state(GameState(cars=car_states))

        done = elapsed > 4
        return StepResult(finished=done)

    def score(self, packet, drones, start_time) -> StepResult:
        ball = BallState(physics=Physics(location=Vector3(0, 5120 + 800, 200)))
        self.game_interface.set_game_state(GameState(ball=ball))
        return StepResult(finished=True)