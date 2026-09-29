from embrace.core.character import Character_API
from embrace.utils import get_pd_drop_by_reset_params
import time
import re
import math
import numpy as np
import cv2
import json
import unrealcv
import warnings
import sys
import os
import glob


G_pd_name = 'BP_GrabMoveDrop_C_1'
G_pd_pick_thres_dist = 210.0
G_pd_drop_thres_dist = 30.0 # usually about 21~22

G_destroy_time = 1.0  # time to wait after destroying an object
G_pd_drop_reset_thres = 300.0  # if the drop location is too far, reset the pd object
G_character_asset_path = '/Game/SmartLocomotion/Blueprints/BP_Character.BP_Character_C'
G_map_load_timeout = 60.0
G_character_spawn_timeout = 10.0


def _connect_tcp(ip: str, port: int, timeout_s: float = 5.0) -> unrealcv.Client:
    import signal

    class TimeoutError(Exception):
        pass

    def timeout_handler(signum, frame):
        raise TimeoutError("TCP connection timeout")

    c = unrealcv.Client((ip, port))
    # Some versions of unrealcv.Client.connect() don't support timeout parameter, must control externally
    # Set up timeout using signal (only works on Unix-like systems)
    if 'linux' in sys.platform or 'darwin' in sys.platform:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout_s))
        try:
            c.connect()
            signal.alarm(0)  # Cancel the alarm
        except TimeoutError:
            signal.alarm(0)  # Cancel the alarm
            raise
        finally:
            signal.signal(signal.SIGALRM, old_handler)
    else:
        c.connect()
    return c


def _connect_uds(unix_socket_path: str) -> unrealcv.Client:
    # The second parameter here must be 'unix'
    c = unrealcv.Client(unix_socket_path, 'unix')
    c.connect()
    return c

class Character_API(Character_API):
    # Lv_Bazaar's standalone sandstorm emitters create dense white smoke in
    # the playable area. Emitter_1 belongs to the map's general VFX layer and
    # is intentionally excluded; the oven and candle flames use other local
    # components and remain visible after this list is removed.
    LV_BAZAAR_SANDSTORM_EMITTERS = frozenset({
        'emitter_0',
        'emitter_3',
        'emitter_4',
        'emitter_5',
        'emitter_6',
        'emitter_7',
        'emitter_8',
        'emitter_9',
        'emitter_10',
        'emitter_12',
        'emitter_13',
        'emitter_14',
        'emitter_15',
        'emitter_16',
        'emitter_17',
        'emitter_18',
        'emitter_19',
        'emitter_20',
        'emitter_21',
        'emitter_22',
        'emitter_23',
        'emitter_24',
        'emitter_25',
        'emitter_26',
        'emitter_27',
        'emitter_28',
        'emitter_30',
        'emitter_31',
        'emitter_32',
    })

    # Both actors drive large flying rail vehicles through the playable area.
    # Their moving shadows repeatedly sweep over the ego view even when the
    # agent is stationary.
    SCIENCE_FICTION_VALLEY_FLYING_RAILS = frozenset({
        'bp_rails2',
        'bp_rails_5',
    })
    # BP_House_3 contains an upward-sliding door driven by Timeline_0. Its Box
    # overlap trigger opens the door whenever the character approaches.
    SCIENCE_FICTION_VALLEY_FIXED_CLOSED_DOOR = 'bp_house_3'

    # Six independently animated mesh actors form Tokyo's overhead train.
    # The train repeatedly crosses the elevated track and casts a large moving
    # shadow over the playable area even while the agent is stationary.
    TOKYO_OVERHEAD_TRAIN_CARS = frozenset({
        'staticmeshactor_1754',
        'staticmeshactor_1755',
        'staticmeshactor_1899',
        'staticmeshactor_1932',
        'staticmeshactor_1941',
        'staticmeshactor_1944',
    })

    # Old_Factory_01 ships with hundreds of small OF_Junk_01 physics props
    # spread across the playable area. Character contact can kick them and
    # feed rigid-body impulses back into navigation. Remove only this named
    # family during that map's initialization.
    OLD_FACTORY_JUNK_PREFIX = 'of_junk_01_'
    OLD_FACTORY_JUNK_REMOVAL_TIMEOUT = 5.0

    # This standalone particle actor emits dense smoke across the street near
    # the configured JapanTrainStation_Optimised start area. Remove only the
    # visually verified source; other map effects remain untouched.
    JAPAN_STATION_SMOKE_ACTORS = frozenset({
        'p_manholesmoke_2',
    })
    JAPAN_STATION_SMOKE_REMOVAL_TIMEOUT = 3.0

    # This is the single pool ladder beside the SwimmingPool pose
    # (1578.960, -507.888). Other ladders around the pool remain unchanged.
    SWIMMING_POOL_REMOVED_LADDER = 'sm_poolladder_25'
    SWIMMING_POOL_LADDER_REMOVAL_TIMEOUT = 3.0

    # All twelve upward-sliding garage doors in ModularNeighborhood use the
    # same BP_Garage_Single_01_C blueprint, but the map contains two historical
    # actor-name families. Every instance owns a Box overlap trigger that opens
    # the door when the character approaches.
    MODULAR_NEIGHBORHOOD_GARAGE_PREFIXES = (
        'bp_garage_single',
        'garage_door_half_bp',
    )
    MODULAR_NEIGHBORHOOD_GARAGE_COUNT = 12
    # Five loose garden chairs form the seating group near (-4090, 9602).
    # They ship with physics enabled, so character contact can push them out
    # of place and alter navigation. Freeze only this verified local group.
    MODULAR_NEIGHBORHOOD_FIXED_GARDEN_CHAIRS = frozenset({
        'garden_chair_882',
        'garden_chair_883',
        'garden_chair_884',
        'garden_chair_885',
        'garden_chair_886',
    })
    # Three loose wheeled bins beside the garage near (-7050, -514) also move
    # under character contact. Freeze only these verified instances.
    MODULAR_NEIGHBORHOOD_FIXED_TRASH_BINS = frozenset({
        'sm_trash_bin_01_3160',
        'sm_trash_bin_02b_3161',
        'sm_trash_bin_03_3162',
    })

    POSTPROCESS_DISABLED_MAPS = frozenset({
        'asiantemple',
        'colosseum_desert',
        'commandcenter',
        'containeryard_night',
        'demonstration_bunker',
        'demonstration_castle',
        'ef_grounds',
        'forestgasstation',
        'hotel_corridor',
        'industrialarea',
        'japantrainstation_optimised',
        'lv_bazaar',
        'map_chemicalplant_1',
        'medieval_castle',
        'middleeast',
        'modularbuilding',
        'modularneighborhood',
        'museum',
        'old_town',
        'operahouse',
        'postsoviet_village',
        'storagehouse',
        'suburbneighborhood_day',
        'suburbneighborhood_night',
        'tokyo',
        'ultimatefarming',
        'venice',
    })

    def __init__(
        self,
        port=9000,
        ip='127.0.0.1',
        resolution=(160, 120),
        comm_mode='tcp',
        timeout_s=5.0,
        allow_comm_fallback=True,
    ):
        # Store port for unique screenshot directory
        self.server_port = port

        # Try to initialize with the specified comm_mode
        # Auto-fallback logic:
        # - TCP fails on Linux -> try UDS
        # - UDS fails on Linux -> try TCP
        is_linux = ('linux' in sys.platform)
        connection_failed = False
        original_exception = None

        try:
            super(Character_API, self).__init__(port=port, ip=ip, resolution=resolution, comm_mode=comm_mode)
            # Check if connection actually succeeded
            if hasattr(self, 'client') and hasattr(self.client, 'isconnected'):
                if not self.client.isconnected():
                    connection_failed = True
                    original_exception = Exception("Connection verification failed: client not connected")
        except Exception as e:
            connection_failed = True
            original_exception = e

        # Auto-fallback logic for Linux
        if connection_failed and is_linux and allow_comm_fallback:
            if comm_mode == 'tcp':
                # TCP failed -> try UDS
                print(f"[Warning] TCP connection failed: {original_exception}")
                print(f"[Warning] Attempting to reconnect using Unix Domain Socket...")

                unix_socket_path = f"/tmp/unrealcv_{port}.socket"
                if os.path.exists(unix_socket_path):
                    try:
                        # Retry with 'unix' mode
                        super(Character_API, self).__init__(port=port, ip=ip, resolution=resolution, comm_mode='unix')
                        print(f"[>>>] Successfully connected via Unix Domain Socket")
                        connection_failed = False  # Connection succeeded via UDS
                    except Exception as uds_err:
                        print(f"[Warning] UDS connection also failed: {uds_err}")
                        raise original_exception  # Raise the original TCP error
                else:
                    print(f"[Warning] UDS socket file not found at {unix_socket_path}")
                    raise original_exception  # Raise the original TCP error
            elif comm_mode == 'unix':
                # UDS failed -> try TCP
                print(f"[Warning] UDS connection failed: {original_exception}")
                print(f"[Warning] Attempting to reconnect using TCP...")

                try:
                    # Retry with 'tcp' mode
                    super(Character_API, self).__init__(port=port, ip=ip, resolution=resolution, comm_mode='tcp')
                    print(f"[>>>] Successfully connected via TCP")
                    connection_failed = False  # Connection succeeded via TCP
                except Exception as tcp_err:
                    print(f"[Warning] TCP connection also failed: {tcp_err}")
                    raise original_exception  # Raise the original UDS error
            else:
                # Other mode (tcp_then_unix, etc.), re-raise
                raise original_exception
        elif connection_failed:
            # Strict callers use an explicit port to isolate one UE map and
            # must never fall back to a process-global UDS owned by another
            # simulator instance.
            raise original_exception

        self.ue5 = True
        self.player_config = {
            'relative_location': [5, 0, -50],
            'relative_rotation': [0, 0, 0],
            "head_action_continuous": {
                "high": [15, 15, 15],
                "low":  [-15, -15, -15]
            },
            "head_action": [
                [0, 0, 0], [0, 30, 0], [0, -30, 0], [20, 50, -10, -13, -90, 15], [-15, 0, -55, 0, 0, 180]],
            "animation_action": ["stand", "jump", "open_door", "pick", "drop", "crouch", "close_door"],
            "move_action": [
                [0, 100], [0, -100], [15, 50], [-15, 50], [30, 0], [-30, 0], [0, 0]
            ],
            "move_action_continuous": {
                "high": [30, 200],
                "low": [-30, -200]
            }
        }


        self.animation_dict = {
            'stand': self.set_standup,
            'jump': self.set_jump,
            'crouch': self.set_crouch,
            'liedown': self.set_liedown,
            'open_door': self.set_open_door,
            'pick':self.set_pick,
            'drop': self.set_natural_drop,
        }


        forward_speed = 200     # Movement speed (forward/backward)
        turn_speed = 25         # Turning speed (left/right)
        backward_speed = 60     # Movement speed (forward/backward)
        drop_backward_speed = 43  # Small tested margin behind the original XY

        self.ACTION_MAP_Atomic = {
            "MoveForward": ([0, forward_speed], 0, 0),
            "MoveBackward": ([0, -backward_speed], 0, 0),
            "TurnLeft": ([-turn_speed, 0], 0, 0),
            "TurnRight": ([turn_speed, 0], 0, 0),
            "Idle": ([0, 0], 0, 0),
            

            "LookUp": ([0, 0], 1, 0),
            "LookDown": ([0, 0], 2, 0),
            "LookHand": ([0, 0], 3, 0),

            "JumpForward": ([0, forward_speed], 0, 1),
            "MoveForwardDoor": ([0, backward_speed], 0, 0),
            "MoveBackwardDoor": ([0, -backward_speed], 0, 0),
            "MoveBackwardForDrop": ([0, -drop_backward_speed], 0, 0),
            "OpenDoor": ({"animate": 2}),
            "Pick": ({"animate": 3}),
            # Natural UE drop animation. This releases the object without
            # destroying or repositioning it.
            "NaturalDrop": ({"animate": 4}),
        }

        self.ACTION_MAP_Combination = {
            "MoveForward": ["MoveForward", "MoveForward", "Idle", ],
            "MoveBackward": ["MoveBackward", "MoveBackward", "Idle", ],
            "TurnLeft": ["TurnLeft", ],
            "TurnRight": ["TurnRight", ],
            "LookUp": ["LookUp", ],
            "LookDown": ["LookDown", ],
            "LookHand": ["LookHand", ],
            "JumpForward": ["JumpForward", "Idle", "Idle", "Idle", "Idle"],
            "OpenDoor": ["MoveBackwardDoor", "Idle", "MoveForwardDoor", "Idle", "OpenDoor",],
            "Finish": [],
            "MidwayTarget": [],
            "Idle": ["Idle", ],
            "Pick": ["Pick", "Idle", "Idle", "Idle", "LookHand"],
            # Drop variants:
            #   NaturalDrop is an atomic real-time action defined above.
            #   DropByReset: destroy and respawn the PD object in front.
            #   Drop: trajectory action; take two short backward steps, then
            #   DropByReset. One step saturates at about 62.93 uu and cannot
            #   clear the 70-uu placement distance. Two -43 steps move about
            #   72 uu, leaving the object 2 uu behind the original agent XY.
            "DropByReset": ["DropByReset"],
            "Drop": [
                "MoveBackwardForDrop", "MoveBackwardForDrop",
                "Idle", "DropByReset",
            ],
        }

        # Map-specific settings (loaded from configs/maps.json)
        maps_config = self._load_maps_config()
        self.MAP_EXPOSURE_OFFSET = {}
        self.MAP_WARM_UP_FRAMES = {}
        self.MAP_CHARACTER_INIT_POSE = {}
        for m in maps_config.get('maps', []):
            name = m['name'].casefold()
            if 'exposure_offset' in m:
                self.MAP_EXPOSURE_OFFSET[name] = m['exposure_offset']
            if 'warm_up_frames' in m:
                self.MAP_WARM_UP_FRAMES[name] = m['warm_up_frames']
            if 'character_init_pose' in m:
                pose = m['character_init_pose']
                if (not isinstance(pose, list) or len(pose) != 6 or
                        not all(isinstance(value, (int, float))
                                for value in pose)):
                    raise ValueError(
                        f'Invalid character_init_pose for map '
                        f'{m["name"]!r}: {pose!r}'
                    )
                self.MAP_CHARACTER_INIT_POSE[name] = [
                    float(value) for value in pose
                ]


    @staticmethod
    def _load_maps_config():
        """Load maps config from configs/maps.json"""
        configs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'configs')
        maps_path = os.path.join(configs_dir, 'maps.json')
        try:
            with open(maps_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f'[Warning] Failed to load maps config: {e}')
            return {'maps': []}

    @staticmethod
    def _load_door_closed_rotations_config():
        """Load the verified per-map closed rotations for door actors."""
        configs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'configs',
        )
        config_path = os.path.join(configs_dir, 'door_closed_rotations.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as config_file:
                return json.load(config_file)
        except Exception as exc:
            raise RuntimeError(
                f'Failed to load door closed-rotation config {config_path!r}: {exc}'
            ) from exc

    def apply_configured_door_closed_rotations(self):
        """Close every door verified for the current map and check the result."""
        config = self._load_door_closed_rotations_config()
        rotation_order = [
            str(axis).casefold() for axis in config.get('rotation_order', [])
        ]
        if rotation_order != ['pitch', 'yaw', 'roll']:
            raise RuntimeError(
                'door_closed_rotations.json must use rotation_order '
                '["pitch", "yaw", "roll"]'
            )
        configured_maps = config.get('maps', {})
        map_name = self.map_name.casefold()
        door_entries = next(
            (entries for name, entries in configured_maps.items()
             if name.casefold() == map_name),
            [],
        )

        for entry in door_entries:
            actor_id = entry.get('actor_id')
            rotation = entry.get('closed_rotation')
            if not actor_id or not isinstance(rotation, list) or len(rotation) != 3:
                raise RuntimeError(
                    f'Invalid closed-door entry for map {self.map_name!r}: {entry!r}'
                )

            pitch, yaw, roll = (float(value) for value in rotation)
            response = self.set_obj_rotation(
                actor_id, [pitch, yaw, roll], wait=True)
            if self._is_error_response(response):
                raise RuntimeError(
                    f'Failed to close configured door {actor_id!r}: {response!r}'
                )

            actual_rotation = self.get_obj_rotation(actor_id)
            expected_rotation = [pitch, yaw, roll]
            angle_errors = [
                abs((actual - expected + 180.0) % 360.0 - 180.0)
                for actual, expected in zip(actual_rotation, expected_rotation)
            ]
            if len(actual_rotation) != 3 or any(error > 0.01 for error in angle_errors):
                raise RuntimeError(
                    f'Closed-door rotation verification failed for {actor_id!r}: '
                    f'expected {expected_rotation}, got {actual_rotation}'
                )
            print(f'[>>>] Closed configured door {actor_id}: {actual_rotation}')

        print(f'[>>>] Applied {len(door_entries)} configured closed-door '
              f'rotation(s) for {self.map_name}.')

    def _remove_lv_bazaar_sandstorm_emitters(self, object_name_list):
        """Remove the verified Lv_Bazaar sandstorm emitters in one batch."""
        sandstorm_emitters = sorted(
            name for name in object_name_list
            if name.casefold() in self.LV_BAZAAR_SANDSTORM_EMITTERS
        )
        if not sandstorm_emitters:
            return

        commands = [
            f'vset /object/{name}/destroy'
            for name in sandstorm_emitters
        ]
        responses = self.client.request(commands)
        failures = [
            (name, response)
            for name, response in zip(sandstorm_emitters, responses)
            if self._is_error_response(response)
        ]
        if failures:
            raise RuntimeError(
                'Failed to remove Lv_Bazaar sandstorm emitters: '
                f'{failures!r}'
            )
        print(f'[>>>] Removed {len(sandstorm_emitters)} Lv_Bazaar '
              'sandstorm emitters')

    def _remove_science_fiction_valley_flying_rails(self, object_name_list):
        """Remove the verified flying rail vehicles that cast moving shadows."""
        flying_rails = sorted(
            name for name in object_name_list
            if name.casefold() in self.SCIENCE_FICTION_VALLEY_FLYING_RAILS
        )
        if not flying_rails:
            return

        responses = self.client.request([
            f'vset /object/{name}/destroy'
            for name in flying_rails
        ])
        failures = [
            (name, response)
            for name, response in zip(flying_rails, responses)
            if self._is_error_response(response)
        ]
        if failures:
            raise RuntimeError(
                'Failed to remove science-fiction valley flying rails: '
                f'{failures!r}'
            )
        print(f'[>>>] Removed {len(flying_rails)} science-fiction valley '
              'flying rail vehicles')

    def _disable_science_fiction_valley_auto_door(self, object_name_list):
        """Keep BP_House_3's sliding door closed while preserving collision."""
        house_actor = next((
            name for name in object_name_list
            if name.casefold()
            == self.SCIENCE_FICTION_VALLEY_FIXED_CLOSED_DOOR
        ), None)
        if house_actor is None:
            raise RuntimeError(
                'Science_Fiction_Valley_Town fixed-closed door actor '
                f'{self.SCIENCE_FICTION_VALLEY_FIXED_CLOSED_DOOR!r} not found'
            )

        response = self.client.request(
            f'vrun set {house_actor}.Box bGenerateOverlapEvents False'
        )
        if self._is_error_response(response):
            raise RuntimeError(
                'Failed to disable Science_Fiction_Valley_Town automatic '
                f'door trigger: {response!r}'
            )
        print('[>>>] Disabled BP_House_3 automatic door trigger; sliding '
              'door remains closed with collision enabled')

    def _remove_tokyo_overhead_train(self, object_name_list):
        """Remove the verified Tokyo train cars that cast moving shadows."""
        train_cars = sorted(
            name for name in object_name_list
            if name.casefold() in self.TOKYO_OVERHEAD_TRAIN_CARS
        )
        if not train_cars:
            return

        responses = self.client.request([
            f'vset /object/{name}/destroy'
            for name in train_cars
        ])
        failures = [
            (name, response)
            for name, response in zip(train_cars, responses)
            if self._is_error_response(response)
        ]
        if failures:
            raise RuntimeError(
                f'Failed to remove Tokyo overhead train cars: {failures!r}'
            )
        print(f'[>>>] Removed {len(train_cars)} Tokyo overhead train cars')

    def _remove_old_factory_junk_props(self, object_name_list):
        """Remove every OF_Junk_01 actor and wait for deferred destruction."""
        junk_props = sorted(
            name for name in object_name_list
            if name.casefold().startswith(self.OLD_FACTORY_JUNK_PREFIX)
        )
        if not junk_props:
            print('[>>>] No Old_Factory_01 junk actors found to remove')
            return

        started_at = time.monotonic()
        responses = self.client.request([
            f'vset /object/{name}/destroy'
            for name in junk_props
        ])
        if not isinstance(responses, (list, tuple)):
            responses = [responses]
        if len(responses) != len(junk_props):
            raise RuntimeError(
                'Old_Factory_01 junk removal returned an unexpected number '
                f'of responses: expected {len(junk_props)}, got '
                f'{len(responses)}'
            )
        failures = [
            (name, response)
            for name, response in zip(junk_props, responses)
            if self._is_error_response(response)
        ]
        if failures:
            raise RuntimeError(
                f'Failed to remove Old_Factory_01 junk actors: {failures!r}'
            )

        deadline = started_at + self.OLD_FACTORY_JUNK_REMOVAL_TIMEOUT
        while True:
            remaining = sorted(
                name for name in self.get_objects()
                if name.casefold().startswith(self.OLD_FACTORY_JUNK_PREFIX)
            )
            if not remaining:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    'Timed out waiting for Old_Factory_01 junk actors to be '
                    f'destroyed; {len(remaining)} remain: {remaining!r}'
                )
            time.sleep(0.05)

        elapsed = time.monotonic() - started_at
        print(f'[>>>] Removed {len(junk_props)} Old_Factory_01 junk '
              f'actor(s) in {elapsed:.3f}s')

    def _remove_japan_station_smoke(self, object_name_list):
        """Remove the verified Japan station street-smoke particle actor."""
        actors_by_key = {
            name.casefold(): name
            for name in object_name_list
            if name.casefold() in self.JAPAN_STATION_SMOKE_ACTORS
        }
        smoke_actors = [
            actors_by_key[key]
            for key in sorted(actors_by_key)
        ]
        if not smoke_actors:
            print('[Warning] Verified Japan station smoke actor was not found')
            return

        started_at = time.monotonic()
        responses = self.client.request([
            f'vset /object/{name}/destroy'
            for name in smoke_actors
        ])
        if not isinstance(responses, (list, tuple)):
            responses = [responses]
        failures = [
            (name, response)
            for name, response in zip(smoke_actors, responses)
            if self._is_error_response(response)
        ]
        if len(responses) != len(smoke_actors) or failures:
            raise RuntimeError(
                'Failed to remove Japan station smoke actor(s): '
                f'responses={responses!r}, failures={failures!r}'
            )

        deadline = started_at + self.JAPAN_STATION_SMOKE_REMOVAL_TIMEOUT
        while True:
            remaining = sorted(
                name for name in self.get_objects()
                if name.casefold() in self.JAPAN_STATION_SMOKE_ACTORS
            )
            if not remaining:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    'Timed out waiting for Japan station smoke actor(s) to '
                    f'be destroyed: {remaining!r}'
                )
            time.sleep(0.05)

        elapsed = time.monotonic() - started_at
        print(f'[>>>] Removed {len(smoke_actors)} verified Japan station '
              f'smoke actor(s) in {elapsed:.3f}s')

    def _remove_swimming_pool_ladder(self, object_name_list):
        """Remove only the ladder beside the SwimmingPool pose."""
        ladder_actor = next((
            name for name in object_name_list
            if name.casefold() == self.SWIMMING_POOL_REMOVED_LADDER
        ), None)
        if ladder_actor is None:
            raise RuntimeError(
                'SwimmingPool ladder actor '
                f'{self.SWIMMING_POOL_REMOVED_LADDER!r} not found'
            )

        started_at = time.monotonic()
        response = self.client.request(
            f'vset /object/{ladder_actor}/destroy'
        )
        if self._is_error_response(response):
            raise RuntimeError(
                f'Failed to remove SwimmingPool ladder {ladder_actor!r}: '
                f'{response!r}'
            )

        deadline = started_at + self.SWIMMING_POOL_LADDER_REMOVAL_TIMEOUT
        while True:
            remaining = any(
                name.casefold() == self.SWIMMING_POOL_REMOVED_LADDER
                for name in self.get_objects()
            )
            if not remaining:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    'Timed out waiting for SwimmingPool ladder '
                    f'{ladder_actor!r} to be destroyed'
                )
            time.sleep(0.05)

        elapsed = time.monotonic() - started_at
        print(f'[>>>] Removed SwimmingPool ladder {ladder_actor} in '
              f'{elapsed:.3f}s')

    def _disable_modular_neighborhood_garage_triggers(
            self, object_name_list):
        """Keep every automatic rolling garage door closed with collision."""
        garage_actors = sorted({
            name for name in object_name_list
            if name.casefold().startswith(
                self.MODULAR_NEIGHBORHOOD_GARAGE_PREFIXES
            )
        })
        if len(garage_actors) != self.MODULAR_NEIGHBORHOOD_GARAGE_COUNT:
            raise RuntimeError(
                'Expected exactly '
                f'{self.MODULAR_NEIGHBORHOOD_GARAGE_COUNT} automatic garage '
                f'door actors in ModularNeighborhood, found '
                f'{len(garage_actors)}: {garage_actors!r}'
            )
        commands = [
            f'vrun set {name}.Box bGenerateOverlapEvents False'
            for name in garage_actors
        ]
        responses = self.client.request(commands)
        if not isinstance(responses, (list, tuple)):
            responses = [responses]
        failures = [
            (name, response)
            for name, response in zip(garage_actors, responses)
            if self._is_error_response(response)
        ]
        if len(responses) != len(garage_actors) or failures:
            raise RuntimeError(
                'Failed to disable ModularNeighborhood garage trigger(s): '
                f'responses={responses!r}, failures={failures!r}'
            )

        print(f'[>>>] Disabled automatic overlap triggers for '
              f'{len(garage_actors)} ModularNeighborhood garage door(s); '
              'doors remain closed with collision enabled')

    def _freeze_modular_neighborhood_garden_chairs(self, object_name_list):
        """Freeze the verified garden-chair group while preserving collision."""
        actors_by_key = {
            name.casefold(): name
            for name in object_name_list
            if name.casefold()
            in self.MODULAR_NEIGHBORHOOD_FIXED_GARDEN_CHAIRS
        }
        missing = sorted(
            self.MODULAR_NEIGHBORHOOD_FIXED_GARDEN_CHAIRS
            - actors_by_key.keys()
        )
        if missing:
            raise RuntimeError(
                'ModularNeighborhood fixed garden chair actor(s) not found: '
                f'{missing!r}'
            )

        chair_actors = [
            actors_by_key[key]
            for key in sorted(actors_by_key)
        ]
        commands = [
            f'vrun set {name}.StaticMeshComponent0 BodyInstance '
            '(bSimulatePhysics=False)'
            for name in chair_actors
        ]
        responses = self.client.request(commands)
        if not isinstance(responses, (list, tuple)):
            responses = [responses]
        failures = [
            (name, response)
            for name, response in zip(chair_actors, responses)
            if self._is_error_response(response)
        ]
        if len(responses) != len(chair_actors) or failures:
            raise RuntimeError(
                'Failed to freeze ModularNeighborhood garden chair(s): '
                f'responses={responses!r}, failures={failures!r}'
            )

        print(f'[>>>] Disabled physics simulation for '
              f'{len(chair_actors)} ModularNeighborhood garden chair(s); '
              'chairs remain fixed with collision enabled')

    def _freeze_modular_neighborhood_trash_bins(self, object_name_list):
        """Freeze the verified three-bin group while preserving collision."""
        actors_by_key = {
            name.casefold(): name
            for name in object_name_list
            if name.casefold()
            in self.MODULAR_NEIGHBORHOOD_FIXED_TRASH_BINS
        }
        missing = sorted(
            self.MODULAR_NEIGHBORHOOD_FIXED_TRASH_BINS
            - actors_by_key.keys()
        )
        if missing:
            raise RuntimeError(
                'ModularNeighborhood fixed trash-bin actor(s) not found: '
                f'{missing!r}'
            )

        trash_bins = [
            actors_by_key[key]
            for key in sorted(actors_by_key)
        ]
        commands = [
            f'vrun set {name}.StaticMeshComponent0 BodyInstance '
            '(bSimulatePhysics=False)'
            for name in trash_bins
        ]
        responses = self.client.request(commands)
        if not isinstance(responses, (list, tuple)):
            responses = [responses]
        failures = [
            (name, response)
            for name, response in zip(trash_bins, responses)
            if self._is_error_response(response)
        ]
        if len(responses) != len(trash_bins) or failures:
            raise RuntimeError(
                'Failed to freeze ModularNeighborhood trash bin(s): '
                f'responses={responses!r}, failures={failures!r}'
            )

        print(f'[>>>] Disabled physics simulation for '
              f'{len(trash_bins)} ModularNeighborhood trash bin(s); '
              'bins remain fixed with collision enabled')

    def connect(self, ip, port, mode='tcp', wait_uds_s: float = 6.0, timeout_s: float = 5.0):
        """
        mode:
        'tcp'  Use TCP only (auto-fallback to UDS on timeout if on Linux)
        'unix' Prefer UDS, fall back to TCP if not available
        'tcp_then_unix' Connect via TCP first, then disconnect and wait for UDS, then connect via UDS
        """
        is_linux = ('linux' in sys.platform)
        unix_socket_path = f"/tmp/unrealcv_{port}.socket"

        if mode == 'tcp':
            try:
                return _connect_tcp(ip, port, timeout_s=timeout_s)
            except Exception as e:
                # If TCP connection times out and we're on Linux, try UDS
                if is_linux and ('timeout' in str(e).lower() or 'TimeoutError' in str(type(e).__name__)):
                    print(f"[Warning] TCP connection timeout, attempting to use Unix Domain Socket instead...")
                    # Try direct UDS connection if socket file exists
                    if os.path.exists(unix_socket_path):
                        try:
                            return _connect_uds(unix_socket_path)
                        except Exception as uds_err:
                            print(f"[Warning] UDS connection also failed: {uds_err}")
                            raise e  # Raise the original TCP timeout error
                    else:
                        print(f"[Warning] UDS socket file not found at {unix_socket_path}")
                        raise e
                else:
                    raise

        if not is_linux:
            warnings.warn("unix socket mode is not supported in this platform, switch to tcp mode.")
            return _connect_tcp(ip, port, timeout_s=timeout_s)

        if mode == 'unix':
            # After disconnection, UE is usually waiting for UDS, so try direct UDS connection first
            if os.path.exists(unix_socket_path):
                try:
                    return _connect_uds(unix_socket_path)
                except Exception as e:
                    # UDS file exists but not available, fall back to TCP
                    print(f"[Warning] UDS connection failed: {e}")
                    print(f"[Warning] Falling back to TCP...")
            return _connect_tcp(ip, port, timeout_s=timeout_s)

        if mode == 'tcp_then_unix':
            # Connect via TCP first, then disconnect to trigger UE to create UDS, then connect via UDS
            c = _connect_tcp(ip, port, timeout_s=timeout_s)
            try:
                c.disconnect()
            except Exception:
                pass


            t0 = time.time()
            while time.time() - t0 < wait_uds_s:
                if os.path.exists(unix_socket_path):
                    try:
                        return _connect_uds(unix_socket_path)
                    except Exception:
                        # File just appeared but UE is not ready yet, continue waiting
                        pass
                time.sleep(0.2)

            # Fall back to TCP if UDS is not available
            return _connect_tcp(ip, port, timeout_s=timeout_s)

        raise ValueError(f"Unknown mode: {mode}")


    def set_animation(self, player, anim_id, return_cmd=False):
        return self.animation_dict[anim_id](player, return_cmd=return_cmd)

    
    
    def step_by_name(self, actions, char_name):
        actions2move, actions2turn, actions2animate = self.action_mapping(actions)
        if not len(actions2move) == 0:
            move_cmds = [self.set_move_bp(char_name, actions2move[0], return_cmd=True)]
        else:
            move_cmds = []
        
        head_cmds = []
        if not len(actions2turn) == 0:
            if len(actions2turn[0]) == 6:
                head_cmds.append(self.set_cam(char_name, actions2turn[0][:3], actions2turn[0][3:], return_cmd=True))
            else:
                head_cmds.append(self.set_cam(char_name, self.player_config['relative_location'], actions2turn[0], return_cmd=True))

        
        if not len(actions2animate) == 0:
            anim_cmds = [self.set_animation(char_name, actions2animate[0], return_cmd=True)]
        else:
            anim_cmds = []
        
        self.batch_cmd(move_cmds+head_cmds+anim_cmds, None)

    # ------------------- Additional Functions ------------------ #
    def get_agent_pose(self):
        return self.get_obj_pose(self.char_name)
        
    def set_agent_pose(self, pose):
        self.set_obj_pose(self.char_name, pose)

        print("[>>>] Set agent pose to and reset to idle")
        for t in range(10):
            self.step_sync([[0,0],0,0])  # reset to idle
        print("[>>>] Set agent pose done.")
    
    def set_agent_pose_safe(self, pose):
        
        self.set_obj_pose(self.char_name, self.safe_pose)

        print("[>>>] Set agent pose to init pose")
        for t in range(6):
            self.step_sync([[0,0],0,0])  # reset to idle
        print("[>>>] Set agent init pose done.")
        self.set_agent_pose(pose)


    def action_mapping(self, actions):
        """
        Map input actions (which may include move, head, and animate commands)
        into the corresponding Unreal Engine-compatible control lists.

        Supported input formats:
            1. None  -> [None], [None], [None]
            2. [[move_x, move_y], head, animate]  (legacy full action list)
            3. {"move": [x, y], "head": 1, "animate": 2}  (dict format)
            4. "move", "head", or "animate"  (single command placeholder)
        """

        actions2move, actions2head, actions2animate = [], [], []

        # === Case 1: input is None ===
        if actions is None:
            return [None], [None], [None]

        # === Case 2: single string command (e.g., "move") ===
        if isinstance(actions, str):
            if actions == "move":
                actions2move.append(None)
            elif actions == "head":
                actions2head.append(None)
            elif actions == "animate":
                actions2animate.append(None)
            else:
                raise ValueError(f"Unknown single action type: {actions}")
            return actions2move, actions2head, actions2animate

        # === Case 3: dictionary input (e.g., {"move": [0,1], "head": 2}) ===
        if isinstance(actions, dict):
            if "move" in actions:
                move_act = actions["move"]
                if isinstance(move_act, int):
                    move_act = self.player_config["move_action"][move_act]
                actions2move.append(move_act)
            if "head" in actions:
                head_act = actions["head"]
                if isinstance(head_act, int):
                    head_act = self.player_config["head_action"][head_act]
                actions2head.append(head_act)
            if "animate" in actions:
                ani_act = actions["animate"]
                if isinstance(ani_act, int):
                    ani_act = self.player_config["animation_action"][ani_act]
                actions2animate.append(ani_act)
            return actions2move, actions2head, actions2animate

        # === Case 4: legacy list input (e.g., [[0,0], 0, 0]) ===
        if isinstance(actions, (list, tuple)) and len(actions) == 3:
            move_act, head_act, ani_act = actions

            # Move
            if isinstance(move_act, int):
                move_act = self.player_config["move_action"][move_act]
            actions2move.append(move_act)

            # Head
            if isinstance(head_act, int):
                head_act = self.player_config["head_action"][head_act]
            actions2head.append(head_act)

            # Animate
            if isinstance(ani_act, int):
                ani_act = self.player_config["animation_action"][ani_act]
            actions2animate.append(ani_act)

            return actions2move, actions2head, actions2animate

        # === Fallback for invalid input ===
        raise ValueError(f"Invalid action format: {actions}")
 

    def step(self, actions):
        actions2move, actions2turn, actions2animate = self.action_mapping(actions)
        if not len(actions2move) == 0:
            move_cmds = [self.set_move_bp(self.char_name, actions2move[0], return_cmd=True)]
        else:
            move_cmds = []
        
        head_cmds = []
        if not len(actions2turn) == 0:
            if len(actions2turn[0]) == 6:
                head_cmds.append(self.set_cam(self.char_name, actions2turn[0][:3], actions2turn[0][3:], return_cmd=True))
            else:
                head_cmds.append(self.set_cam(self.char_name, self.player_config['relative_location'], actions2turn[0], return_cmd=True))

        
        if not len(actions2animate) == 0:
            anim_cmds = [self.set_animation(self.char_name, actions2animate[0], return_cmd=True)]
        else:
            anim_cmds = []
        
        self.batch_cmd(move_cmds+head_cmds+anim_cmds, None)
    

    def step_sync(self, actions):
        self.set_resume()
        self.step(actions)
        time.sleep(1.0/self.rt)
        self.set_pause()


    def get_screenshot(self, folder=None, save=False):
        """Take a screenshot using vrun Shot command.

        Args:
            folder: Directory to save the screenshot. If None and save=True, saves to ./screenshots
            save: If True, save to disk. If False, save to /dev/shm, load into memory, then delete.

        Returns:
            If save=False: numpy array of the image
            If save=True: None (image is saved to disk)
        """
        if save:
            # Save to disk
            if folder is None:
                screenshot_dir = './screenshots'
            else:
                screenshot_dir = folder

            # Convert to absolute path if relative
            if not os.path.isabs(screenshot_dir):
                screenshot_dir = os.path.abspath(screenshot_dir)

            # Create directory if it doesn't exist
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)

            # The path needs a trailing slash, files will be saved as 00000.png, 00001.png, etc.
            screenshot_path = screenshot_dir + '/'
            cmd = f'vrun Shot filename="{screenshot_path}"'
            self.client.request(cmd)
            return None
        else:
            # Save to /dev/shm (virtual disk), load into memory, then delete
            screenshot_dir = '/dev/shm/ue_screenshot_temp'
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)

            # Use port_timestamp prefix to create unique filename
            timestamp = int(time.time() * 1000000)  # microseconds
            screenshot_path = f'{screenshot_dir}/{self.server_port}_{timestamp}_'
            cmd = f'vrun Shot filename="{screenshot_path}"'
            self.client.request(cmd)

            # Wait for file to appear (loop with timeout)
            png_files = []
            for _ in range(10):  # Max 0.5 seconds (10 * 0.05)
                time.sleep(0.05)
                png_files = glob.glob(f'{screenshot_path}*.png')
                if png_files:
                    break

            if not png_files:
                print(f'[!!!] No screenshot file found for {screenshot_path}')
                return None

            latest_file = png_files[0]

            # Load image into memory
            img = cv2.imread(latest_file)

            # Delete the file
            try:
                os.remove(latest_file)
            except:
                pass

            return img


    def get_image_safe(self, cam_id=0, viewmode='lit'):

        if self.ue5:
            # ue5 has bug of sometimes wrong rendering because it could not update the render buffer
            cmd = f'vget /camera/{cam_id}/location'
            res = None
            while res is None:
                res = self.client.request(cmd)
            res = self.decoder.string2floats(res)

            cmd = f'vset /camera/{cam_id}/location {res[0]+1} {res[1]+1} {res[2]+1}'
            self.client.request(cmd)
            self.get_image(cam_id=cam_id, viewmode=viewmode)
            cmd = f'vset /camera/{cam_id}/location {res[0]} {res[1]} {res[2]}'
            self.client.request(cmd)

        img = self.get_image(cam_id=cam_id, viewmode=viewmode)
        if self.ue5:
            # UE5.6 may return the updated camera view before all scene geometry
            # has reached the capture buffer. Advance the capture once more and
            # return the fully refreshed frame.
            img = self.get_image(cam_id=cam_id, viewmode=viewmode)
        return img

    def step_sync_cmd(self, cmd):
        if cmd == 'Pick':
            self.set_pick_by_reset()
        elif cmd == 'DropByReset':
            self.set_drop_by_reset()
        else:
            actions = self.ACTION_MAP_Atomic[cmd]
            self.step_sync(actions)


    def step_sync_combiation_cmd(self, ccmd):
        cmds = self.ACTION_MAP_Combination[ccmd]
        for cmd in cmds:
            self.step_sync_cmd(cmd)

    def set_init_cam_loc_safe(self):
        print("[>>>] Begin to set initial camera location to a high altitude for safety.")
        cmd = f'vget /camera/0/location'
        res = None
        while res is None:
            res = self.client.request(cmd)
        res = self.decoder.string2floats(res)

        cmd = f'vset /camera/0/location {res[0]} {res[1]} 2000'
        self.client.request(cmd)

        print("[>>>] Set initial camera location done.")

    def get_door_state(self):
        cmd = f'vbp {self.char_name} get_door_state'
        
        try:
            res = None
            while res is None:
                res = self.client.request(cmd)
            # Response format: '{"door_state": "0"}'
            door_state = int(json.loads(res.strip())["door_state"])
        except:
            print('[!!!] Failed to get door state, return 0 as default. Please check!')
            door_state = 0

        return door_state

    def set_pick_drop(self, player, return_cmd=False):
        cmd = f'vbp {player} set_pickup'
        if return_cmd:
            return cmd
        res = None
        while res is None:
            res = self.client.request(cmd, -1)

    def set_pick(self, player, return_cmd=False):
        dist = self.get_char_pd_dist(dims=2)
        if dist < G_pd_pick_thres_dist and dist > G_pd_drop_thres_dist:
            self.set_pd_forward_location()
            cmd = f'vbp {player} set_pickup'
        else:
            cmd = f'vbp n/a' # invalid cmd
        if return_cmd:
            return cmd
        res = None
        while res is None:
            res = self.client.request(cmd, -1)
    
    def set_pick_by_reset(self):
        # remove the old pd object and respawn a new one
        dist = self.get_char_pd_dist(dims=2)
        if dist < G_pd_pick_thres_dist and dist > G_pd_drop_thres_dist:
            cmd = f'vset /object/{G_pd_name}/destroy'
            self.client.request(cmd)
            time.sleep(G_destroy_time)

            self.new_obj('BP_GrabMoveDrop_C', G_pd_name, [0,0,-1000], [0,0,0])
            cmd = f'vbp {G_pd_name} set_app {self.pd_id}'
            self.client.request(cmd)
            self.set_pd_forward_location(dist=60.0)

            self.set_resume()
            self.step(self.ACTION_MAP_Atomic['Pick'])
            time.sleep(1.0/self.rt)
            for _i in range(3):
                self.step(self.ACTION_MAP_Atomic['Idle'])
                time.sleep(1.0/self.rt)

            self.set_obj_scale(G_pd_name, [self.pd_size]*3)
            time.sleep(1.0/self.rt)

    def set_natural_drop(self, player, return_cmd=False):
        """Release the held PD object through the original UE blueprint."""
        dist = self.get_char_pd_dist(dims=2)
        if dist < G_pd_drop_thres_dist:   # object is on the hand
            cmd = f'vbp {player} set_pickup'
        else:
            cmd = f'vbp n/a' # invalid cmd
        if return_cmd:
            return cmd
        res = None
        while res is None:
            res = self.client.request(cmd)
    
    def set_drop_by_reset(self):
        """Destroy the held PD object and respawn it in front of the agent."""
        self.set_resume()
        dist = self.get_char_pd_dist2d_no_resume()
        entered_if = dist < G_pd_drop_thres_dist

        if entered_if:   # object is on the hand
            cmd = f'vset /object/{G_pd_name}/destroy'
            self.client.request(cmd)
            time.sleep(G_destroy_time)

  
            self.new_obj('BP_GrabMoveDrop_C', G_pd_name, [0,0,-1000], [0,0,0])
            cmd = f'vbp {G_pd_name} set_app {self.pd_id}'
            self.client.request(cmd)

            self.set_obj_scale(G_pd_name, [self.pd_size]*3)
            self.set_pd_forward_location_for_drop()

        self.set_pause()


    def get_char_pd_dist(self, dims=2):
        self.set_resume()
        char_pose = self.get_agent_pose()
        try:
            pd_pose = self.get_obj_pose(G_pd_name)
        except:
            print('[!!!] Failed to get pd object pose, return large distance.')
            return 1e6
        pd_pos = np.array(pd_pose[:dims])
        char_pos = np.array(char_pose[:dims])
        dist = np.linalg.norm(pd_pos - char_pos)
        return dist
    
    def get_char_pd_dist2d_no_resume(self):
        char_pose = self.get_agent_pose()
        try:
            pd_pose = self.get_obj_pose(G_pd_name)
        except:
            print('[!!!] Failed to get pd object pose, return large distance.')
            return 1e6
        pd_pos = np.array(pd_pose[:2])
        char_pos = np.array(char_pose[:2])
        dist = np.linalg.norm(pd_pos - char_pos)
        return dist
    
    def get_char_pd_dist2d_pause(self):
        self.set_resume()
        char_pose = self.get_agent_pose()
        try:
            pd_pose = self.get_obj_pose(G_pd_name)
        except:
            print('[!!!] Failed to get pd object pose, return large distance.')
            return 1e6
        pd_pos = np.array(pd_pose[:2])
        char_pos = np.array(char_pose[:2])
        dist = np.linalg.norm(pd_pos - char_pos)
        self.set_pause()
        return dist
    
    def set_pd_forward_location(self, dist=60.0):
        char_pose = self.get_agent_pose()
        x, y, z, pitch, yaw, roll = char_pose
        rad = np.deg2rad(yaw)
        new_x = x + dist * np.cos(rad)
        new_y = y + dist * np.sin(rad)
        new_loc = [float(new_x), float(new_y), float(z)]
        self.set_obj_location(G_pd_name, new_loc)
    
    def set_pd_forward_location_withz(self, dist=60.0):
        char_pose = self.get_agent_pose()
        x, y, z, pitch, yaw, roll = char_pose
        rad = np.deg2rad(yaw)
        new_x = x + dist * np.cos(rad)
        new_y = y + dist * np.sin(rad)
        new_loc = [float(new_x), float(new_y), float(z-90)]
        self.set_obj_location(G_pd_name, new_loc)

    def set_pd_forward_location_withz_height(self, dist=60.0, height=90):
        char_pose = self.get_agent_pose()
        x, y, z, pitch, yaw, roll = char_pose
        rad = np.deg2rad(yaw)
        new_x = x + dist * np.cos(rad)
        new_y = y + dist * np.sin(rad)
        new_loc = [float(new_x), float(new_y), float(z-height)]
        self.set_obj_location(G_pd_name, new_loc)
    
    def set_pd_forward_location_for_drop(self, dist=None, height=None):
        # Object-specific values live in pd_config.json. Unknown IDs and
        # configured objects without an override use the config defaults.
        default_dist, default_height, relative_rotation = (
            get_pd_drop_by_reset_params(self.pd_id)
        )
        rel_pitch, rel_yaw, rel_roll = relative_rotation

        # Use provided values or defaults
        dist = dist if dist is not None else default_dist
        height = height if height is not None else default_height

        # Get character pose and calculate new position
        char_pose = self.get_agent_pose()
        x, y, z, char_pitch, char_yaw, char_roll = char_pose
        rad = np.deg2rad(char_yaw)
        new_x = x + dist * np.cos(rad)
        new_y = y + dist * np.sin(rad)
        new_loc = [float(new_x), float(new_y), float(z-height)]

        # Set location
        self.set_obj_location(G_pd_name, new_loc)

        # Calculate absolute rotation from relative rotation
        # PD rotation = agent rotation + relative rotation
        abs_pitch = char_pitch + rel_pitch
        abs_yaw = char_yaw + rel_yaw
        abs_roll = char_roll + rel_roll

        # Always apply the relative rotation. A zero relative rotation means
        # "align with the character", not "keep the actor's world rotation".
        # Skipping [0, 0, 0] made asymmetric default objects such as the
        # jerry can appear sideways whenever the character yaw was non-zero.
        new_rotation = [float(abs_pitch), float(abs_yaw), float(abs_roll)]
        self.set_obj_rotation(G_pd_name, new_rotation)

    def nav_to_goal_bypath(self, obj, loc): # navigate the agent to a goal location
        # Assign the agent a navigation goal, and use Navmesh to automatically control its movement to reach the goal via the shortest path.
        # The goal should be reachable in the environment.
        x, y, z = loc
        cmd = f'vbp {obj} nav_to_goal_bypath {x} {y} {z}'
        res = self.client.request(cmd)
        return res
    
    def nav_to_goal_bypath_char(self, loc):
        return self.nav_to_goal_bypath(self.char_name, loc)


    
    def remove_pd(self):
        cmd = f'vset /object/{G_pd_name}/destroy'
        self.client.request(cmd)
        time.sleep(G_destroy_time)
        self.pd_size = None
        self.pd_id = None


    def new_obj_v2(self, obj_class_name, obj_name, loc, rot=[0, 0, 0]):
        # spawn, set obj pose, enable physics
        [x, y, z] = loc
        [pitch, yaw, roll] = rot
        if obj_class_name =="bp_character_C" or obj_class_name =="target_C":
            cmd = [f'vset /objects/spawn {obj_class_name} {obj_name}',
                   f'vset /object/{obj_name}/location {x} {y} {z}',
                   f'vset /object/{obj_name}/rotation {pitch} {yaw} {roll}',
                   f'vbp {obj_name} set_phy 1'
                   ]
        else:
            cmd = [f'vset /objects/spawn {obj_class_name} {obj_name}',
                   f'vset /object/{obj_name}/location {x} {y} {z}',
                   f'vset /object/{obj_name}/rotation {pitch} {yaw} {roll}',
                   f'vbp {obj_name} set_phy 1'
                   ]
        self.client.request(cmd, -1)
        return obj_name
    

    def pre_loading_setup_by_droppose(self, pd_id=None, pd_size=None, drop_pose=None):
        if self.pd_id is not None: # there is a pd object in the scene
            self.remove_pd()

        if pd_id is not None:
            self.new_obj('BP_GrabMoveDrop_C', G_pd_name, [0,0,-1000], [0,0,0])
            self.pd_size = pd_size
            self.pd_id = pd_id
            cmd = f'vbp {G_pd_name} set_app {pd_id}'
            self.client.request(cmd)
            self.set_char_pose_by_spawn(drop_pose)
            self.set_pd_forward_location(dist=60.0)
            self.step_sync_combiation_cmd('Pick')
            self.set_resume()
            time.sleep(1.0/self.rt)
            self.set_obj_scale(G_pd_name, [pd_size]*3)
            self.pd_size = pd_size
            self.step(self.ACTION_MAP_Atomic['NaturalDrop'])
            for _i in range(10):
                self.step(self.ACTION_MAP_Atomic['Idle'])
                time.sleep(1.0 / self.rt)
            self.set_pause()

    def pre_loading_setup(self, pd_id=None, pd_size=None, pd_pose=None):
        if self.pd_id is not None: # there is a pd object in the scene
            self.remove_pd()
        
        if pd_id is not None:
            self.set_resume()
            self.new_obj('BP_GrabMoveDrop_C', G_pd_name, [0,0,-1000], [0,0,0])
            self.pd_size = pd_size
            self.pd_id = pd_id
            cmd = f'vbp {G_pd_name} set_app {pd_id}'
            self.client.request(cmd)

            self.set_obj_scale(G_pd_name, [pd_size]*3)
            self.pd_size = pd_size
            self.set_obj_location(G_pd_name, pd_pose[:3])
            if len(pd_pose) > 3:
                self.set_obj_rotation(
                    G_pd_name, pd_pose[3:6], wait=True)
            self.set_pause()
    
    def init_pd_for_edit(self, pd_id=None, pd_size=None):
        if self.pd_id is not None: # there is a pd object in the scene
            self.remove_pd()

        if pd_id is not None:
            self.new_obj('BP_GrabMoveDrop_C', G_pd_name, [0,0,-1000], [0,0,0])
            self.pd_size = pd_size
            self.pd_id = pd_id
            cmd = f'vbp {G_pd_name} set_app {pd_id}'
            self.client.request(cmd)
            self.set_pd_forward_location(dist=60.0)

            self.step(self.ACTION_MAP_Atomic['Pick'])
            self.set_resume()
            time.sleep(1.0/self.rt)
            self.get_obj_scale(G_pd_name)  # query first to sync object state
            self.set_obj_scale(G_pd_name, [self.pd_size]*3)
            time.sleep(1.0/self.rt)
            self.pd_size = pd_size


    def set_camera_params(self, cam_id=0):
        # UE5.6 defaults the UnrealCV lit sensor to SceneColorHDR, which is
        # captured before tone mapping. Exposure bias has no visible effect in
        # that mode, so use the final tone-mapped LDR output for ego images.
        commands = (
            f'vset /camera/{cam_id}/lit_source ldr',
            f'vset /camera/{cam_id}/reflection none',
            f'vset /camera/{cam_id}/illumination none',
        )
        for cmd in commands:
            response = self.client.request(cmd)
            if self._is_error_response(response):
                raise RuntimeError(f'Failed to configure camera: {cmd!r} -> {response!r}')


    @staticmethod
    def _is_error_response(response):
        """Return whether an UnrealCV response represents a failed command."""
        return response is None or str(response).lower().startswith('error')

    def _wait_for_map_ready(self, timeout=G_map_load_timeout):
        """Wait until camera queries work again after an UE5.6 level switch."""
        deadline = time.time() + timeout
        last_response = None

        while time.time() < deadline:
            last_response = self.client.request('vget /camera/0/location')
            if not self._is_error_response(last_response):
                try:
                    location = self.decoder.string2floats(last_response)
                    if len(location) == 3:
                        return
                except (TypeError, ValueError, AttributeError):
                    pass
            time.sleep(0.5)

        raise TimeoutError(
            f'UE5.6 map load did not become responsive within {timeout:.0f}s; '
            f'last camera response: {last_response!r}'
        )

    def _spawn_character_from_path(self, char_name, pose=None):
        """Spawn the UE5.6 character blueprint and wait until it is queryable.

        UnrealZoo UE5.6 v3 maps do not contain a pre-placed bp_character and
        may not register that class for the legacy ``/objects/spawn`` command.
        ``spawn_from_path`` loads the blueprint through its asset path, so it
        works even when the current map has no reference to the class.

        If ``pose`` is None, keep the transform chosen by UE instead of
        overwriting it with a Python-side position.
        """
        response = self.client.request(
            f'vset /objects/spawn_from_path {G_character_asset_path} {char_name}'
        )
        if self._is_error_response(response):
            raise RuntimeError(
                f'Failed to spawn UE5.6 character {char_name!r} from '
                f'{G_character_asset_path}: {response!r}'
            )

        deadline = time.time() + G_character_spawn_timeout
        last_response = None
        while time.time() < deadline:
            last_response = self.client.request(f'vget /object/{char_name}/location')
            if not self._is_error_response(last_response):
                try:
                    location = self.decoder.string2floats(last_response)
                    if len(location) == 3:
                        break
                except (TypeError, ValueError, AttributeError):
                    pass
            time.sleep(0.25)
        else:
            raise TimeoutError(
                f'UE5.6 character {char_name!r} was spawned but did not become '
                f'queryable within {G_character_spawn_timeout:.0f}s; '
                f'last response: {last_response!r}'
            )

        if pose is not None:
            location = pose[:3]
            rotation = pose[3:]
            pose_commands = (
                f'vset /object/{char_name}/location {" ".join(map(str, location))}',
                f'vset /object/{char_name}/rotation {" ".join(map(str, rotation))}',
            )
            for command in pose_commands:
                response = self.client.request(command)
                if self._is_error_response(response):
                    raise RuntimeError(
                        f'UE5.6 character setup failed: '
                        f'{command!r} -> {response!r}'
                    )

        return char_name


    def set_char_pose_by_spawn(self, pose):
        print("[>>>] Set agent pose by spawn.")
        cmd = f'vset /object/{self.char_name}/destroy'
        self.client.request(cmd)
        time.sleep(G_destroy_time)
        self._spawn_character_from_path(self.char_name, pose)
        self.cam = self.get_camera_config()
        self.set_interval(self.char_name, 1000)
        cmd = f'vbp {self.char_name} set_app 4'
        self.client.request(cmd)
        cmd = f'vrun ViewActor {self.char_name}'
        self.client.request(cmd)

        self.set_camera_params(self.cam_id)
        # Respawning the UE5.6 character also recreates its camera sensor.
        # Reapply the map exposure to the new sensor after configuring it.
        self.apply_map_exposure_settings()

        warm_up_frames = self.MAP_WARM_UP_FRAMES.get(self.map_name.lower(), 1)
        self.warm_up_cam_view(warm_up_frames)

        print("[>>>] Set agent pose done.")

 


    def set_exposure_offset(self, offset):
        """Apply one exposure offset to both the viewport and ego camera.

        Args:
            offset: Exposure offset value to set
        """
        cam_id = self.cam_id
        commands = (
            # The UE main viewport (third-person/follow view).
            f'vrun r.ExposureOffset {offset}',
            # UnrealCV's independent, tone-mapped ego SceneCapture sensor.
            f'vset /camera/{cam_id}/exposure_bias {offset}',
        )
        for cmd in commands:
            response = self.client.request(cmd)
            if self._is_error_response(response):
                raise RuntimeError(f'Failed to set exposure: {cmd!r} -> {response!r}')
        print(f"[>>>] Set exposure offset to {offset} "
              f"for main viewport and ego camera {cam_id}")

    def apply_map_exposure_settings(self):
        """Restore the current map's exposure offset (default: 0)."""
        map_name_lower = self.map_name.casefold()
        offset = self.MAP_EXPOSURE_OFFSET.get(map_name_lower, 0)
        self.set_exposure_offset(offset)
        return offset

    def reload_map_exposure_settings(self):
        """Reload and apply the current map exposure directly from maps.json.

        ``Character_API`` normally caches map settings when it is created. A
        task load uses this method so edits to ``maps.json`` take effect on the
        next task without restarting the web process.
        """
        map_name_lower = self.map_name.casefold()
        maps_config = self._load_maps_config()
        map_entry = next(
            (entry for entry in maps_config.get('maps', [])
             if str(entry.get('name', '')).casefold() == map_name_lower),
            None,
        )
        if map_entry is None:
            raise ValueError(f'Map not found in maps.json: {self.map_name}')

        value = map_entry.get('exposure_offset', 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f'Invalid exposure_offset for map {self.map_name!r}: '
                f'{value!r}')
        offset = float(value)
        if not math.isfinite(offset):
            raise ValueError(
                f'Invalid exposure_offset for map {self.map_name!r}: '
                f'{value!r}')
        if offset < -10 or offset > 10:
            raise ValueError('Map exposure_offset must be between -10 and 10')

        # Keep the cache synchronized for camera respawns and other callers,
        # but apply the freshly read value immediately for this task load.
        self.MAP_EXPOSURE_OFFSET[map_name_lower] = offset
        self.set_exposure_offset(offset)
        return offset

    @staticmethod
    def get_task_exposure(task_data):
        """Return a validated optional ``Exposure`` override from task JSON.

        ``Exposure`` has the same absolute exposure-offset semantics as the
        map-level ``exposure_offset`` setting. It is not added to the map
        value. A missing or null value means that the map setting is used.
        """
        if not isinstance(task_data, dict):
            raise ValueError('Task data must be a JSON object')

        value = task_data.get('Exposure')
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Task Exposure must be a number or null')

        value = float(value)
        if not math.isfinite(value):
            raise ValueError('Task Exposure must be finite')
        if value < -10 or value > 10:
            raise ValueError('Task Exposure must be between -10 and 10')
        return value

    def apply_task_exposure_settings(self, task_data):
        """Apply fresh map exposure first, followed by a task override.

        Run this after ``set_char_pose_by_spawn`` because respawning the UE5.6
        character recreates the ego camera. The map value is re-read from disk
        for every task load, so changing ``maps.json`` does not require a web
        restart. Applying the map first prevents a previous task override from
        leaking; when this task has an override, that absolute value is applied
        second.
        """
        task_offset = self.get_task_exposure(task_data)
        map_offset = self.reload_map_exposure_settings()
        if task_offset is None:
            print(f'[>>>] Applied exposure {map_offset} '
                  f'(fresh map default)')
            return map_offset

        self.set_exposure_offset(task_offset)
        print(f'[>>>] Applied map exposure {map_offset}, then task override '
              f'{task_offset}')
        return task_offset

    def warm_up_cam_view(self, num_iterations=20):
        """Warm up the camera view by getting images multiple times.

        This helps stabilize rendering and should be called separately when needed,
        not during map loading.

        Args:
            num_iterations: Number of times to get the image for warm up (default: 20)
        """
        self.set_resume()
        print(f"[>>>] Begin warm up the cam view.")
        start = time.time()
        for ii in range(num_iterations):
            self.get_image(self.cam_id, viewmode='lit')
        print(f"[>>>] Warm up the cam view done.")
        end = time.time()
        print(f"Warm up time: {end - start:.3f} sec")

    def load_map(self, map_name):
        # UnrealZoo UE5.6 v3 maps no longer guarantee that bp_character is
        # pre-placed, so never reuse a character name from the previous world.
        self.char_name = None

        response = self.client.request(f'vset /action/game/level {map_name}')
        if self._is_error_response(response):
            raise RuntimeError(f'Failed to load UE5.6 map {map_name!r}: {response!r}')

        self.map_name = map_name
        self._wait_for_map_ready()
        # Refresh camera/object caches only after the new world is responsive.
        self.init_map()


        self.slomo = 6
        self.rt = 4

        cmd = f'vrun slomo {self.slomo}'
        debug = self.client.request(cmd)

        # Disable motion blur
        cmd = 'vrun r.MotionBlurQuality 0'
        self.client.request(cmd)

        # Use single-frame FXAA for LDR captures to avoid temporal ghosting.
        cmd = 'vrun r.AntiAliasingMethod 1'
        self.client.request(cmd)

        object_name_list = self.get_objects()

        char_pattern = re.compile(r'^bp_character', re.IGNORECASE)
        other_pattern = re.compile(r'^(bp_animal|bp_basecar|bp_basebike|bp_grabmovedrop|bp_hatchback_child_base|sport|motorbike|bp_drone|drone)', re.IGNORECASE)

        # delete other objects
        for name in object_name_list:

            if other_pattern.match(name):
                self.destroy_obj(name)


            if char_pattern.match(name):
                self.char_name = name

        # Delete DirectionalLight for SuburbNeighborhood_Day map
        if map_name.lower() == 'suburbneighborhood_day':
            cmd = f'vset /object/DirectionalLight/destroy'
            self.client.request(cmd)
            print('[>>>] Deleted DirectionalLight for SuburbNeighborhood_Day map')

        # Some IndustrialArea doors are shipped partially open. Restore every
        # manually verified closed pose before spawning/positioning the agent.
        if map_name.casefold() == 'industrialarea':
            self.apply_configured_door_closed_rotations()

        if map_name.casefold() == 'old_factory_01':
            self._remove_old_factory_junk_props(object_name_list)

        if map_name.casefold() == 'japantrainstation_optimised':
            self._remove_japan_station_smoke(object_name_list)

        if map_name.casefold() == 'swimmingpool':
            self._remove_swimming_pool_ladder(object_name_list)

        if map_name.casefold() == 'modularneighborhood':
            self._disable_modular_neighborhood_garage_triggers(
                object_name_list
            )
            self._freeze_modular_neighborhood_garden_chairs(
                object_name_list
            )
            self._freeze_modular_neighborhood_trash_bins(
                object_name_list
            )

        # Match only the verified standalone emitter allowlist so Emitter_1
        # and the local oven/candle flame components are preserved.
        if map_name.casefold() == 'lv_bazaar':
            self._remove_lv_bazaar_sandstorm_emitters(object_name_list)

        if map_name.casefold() == 'science_fiction_valley_town':
            self._remove_science_fiction_valley_flying_rails(object_name_list)
            self._disable_science_fiction_valley_auto_door(object_name_list)

        if map_name.casefold() == 'tokyo':
            self._remove_tokyo_overhead_train(object_name_list)

        # These maps ship with post-process settings that make UE5.6 LDR
        # captures visibly washed out or blurry. Disable their map-local
        # volumes during level preprocessing; the UE assets remain unchanged
        # and are restored by the next reload.
        if map_name.casefold() in self.POSTPROCESS_DISABLED_MAPS:
            cmd = 'vrun set PostProcessVolume BlendWeight 0'
            response = self.client.request(cmd)
            if self._is_error_response(response):
                raise RuntimeError(
                    f'Failed to disable {map_name} post-process volume: '
                    f'{response!r}'
                )
            print(f'[>>>] Disabled {map_name} PostProcessVolume '
                  '(BlendWeight=0)')

        # Disable height/atmospheric fog for every map. Maps without fog are
        # visually unaffected, while maps that use fog retain clear distant
        # scene details. Send this on every load because r.Fog is process-wide
        # and may have been changed by an earlier runtime command.
        response = self.client.request('vrun r.Fog 0')
        if self._is_error_response(response):
            raise RuntimeError(
                f'Failed to disable fog for {map_name}: {response!r}'
            )
        print(f'[>>>] Disabled {map_name} height/atmospheric fog '
              '(r.Fog=0)')

        # No map-specific volumetric-fog override is active. Restore this
        # process-wide CVar in case an earlier runtime test disabled it.
        response = self.client.request('vrun r.VolumetricFog 1')
        if self._is_error_response(response):
            raise RuntimeError(
                f'Failed to restore volumetric fog for {map_name}: '
                f'{response!r}'
            )

        # A small number of maps need different sharpening strengths under
        # FXAA at the 640x480 UnrealCV capture resolution. Tonemapper
        # sharpening is process-wide, so restore it to zero for every other
        # map.
        map_sharpen_amounts = {
            'victoriantrainstation': 1.5,
            'russianwintertowndemo01': 0.5,
            'swimmingpool': 0.5,
        }
        sharpen_amount = map_sharpen_amounts.get(map_name.casefold(), 0)
        response = self.client.request(
            f'vrun r.Tonemapper.Sharpen {sharpen_amount}'
        )
        if self._is_error_response(response):
            raise RuntimeError(
                f'Failed to configure sharpening for {map_name}: '
                f'{response!r}'
            )
        if sharpen_amount:
            print(f'[>>>] Enabled {map_name} tonemapper sharpening '
                  f'(r.Tonemapper.Sharpen={sharpen_amount})')

        # UE5.5 maps supplied a pre-placed character at the map's intended
        # starting transform. UE5.6 removed that actor, so map loading itself
        # must always recreate it at the recorded transform. Task Start_Pose is
        # applied later only when a task is explicitly loaded.
        configured_init_pose = self.MAP_CHARACTER_INIT_POSE.get(
            map_name.casefold()
        )
        if configured_init_pose is None:
            raise RuntimeError(
                f'No character_init_pose configured for map {map_name!r}'
            )
        initial_char_pose = list(configured_init_pose)
        print('[>>>] Using configured UE5.5 character initial pose: '
              f'{initial_char_pose}')

        # Keep camera 0 away from the scene while the character is created and
        # positioned. This avoids transient physics/rendering interference.
        self.set_init_cam_loc_safe()

        if self.char_name is None:
            spawned_name = 'spawned_char_0'

            # A same-name actor can survive a repeated setup in the same UE
            # session. Remove it before spawning to avoid a name collision.
            existing_location = self.client.request(
                f'vget /object/{spawned_name}/location'
            )
            if not self._is_error_response(existing_location):
                self.client.request(f'vset /object/{spawned_name}/destroy')
                time.sleep(G_destroy_time)

            self.char_name = self._spawn_character_from_path(
                spawned_name, initial_char_pose
            )
            # The spawned blueprint contributes its own camera, so refresh the
            # client-side camera cache before matching the active camera below.
            self.cam = self.get_camera_config()
            print(f'[>>>] No bp_character found in UE5.6 map; spawned '
                  f'{self.char_name} from asset path '
                  f'(camera_num={self.get_camera_num()}).')

        cmd = f'vrun ViewActor {self.char_name}'
        debug = self.client.request(cmd)
        # get camera locations

        cmd = f'vbp {self.char_name} set_app 4'
        debug = self.client.request(cmd)

        time.sleep(1+2/self.rt)
        cam_num = self.get_camera_num()
        cam_locs = [self.get_cam_location(i) for i in range(cam_num)]

        def match_cam_id(cam_locs, obj_name):
            obj_loc = self.get_obj_location(obj_name)
            dis_list = [self.get_distance(loc, obj_loc, 3) for loc in cam_locs]
            return dis_list.index(min(dis_list))  # Closest camera ID

        # get cam id for character
        self.cam_id = match_cam_id(cam_locs, self.char_name)

        # Configure the camera created for the initial map-load character as
        # soon as its ID is known. Without this, maps with no existing tasks
        # stay on UE5.6's default HDR sensor until the first task respawn,
        # while task previews and reloads use the tone-mapped LDR sensor.
        self.set_camera_params(self.cam_id)

        # set interval for character
        self.set_interval(self.char_name, 1000)

        # set safe pose: it will be used to set pose to init pose before setting to a new pose. (for better physics)
        self.safe_pose = self.get_agent_pose()

        self.pd_id = None
        self.pd_name = G_pd_name

        # Apply map-specific exposure settings if needed
        self.apply_map_exposure_settings()


        self.set_pause()
    
    pass
