import csv
from collections import defaultdict
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

from choreography.group_step import DroneListStep, StepResult, PerDroneStep


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
        self.sequence.append(DroneListStep(self.line_up))

    def line_up(self, packet, drones, start_time) -> StepResult:
        offset_z = 500
        car_states = {}
        for drone in drones:
            row = self.data[drone.index][0]
            location = Vector3(row["x"]*2, row["y"]*2, row["z"]*2 + offset_z)
            car_states[drone.index] = CarState(Physics(location=location))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)