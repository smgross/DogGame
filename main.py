from __future__ import annotations

import json
import math
import os
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

try:
    import pygame
except ImportError:
    print("Pygame is not installed. Install it with: python -m pip install -r requirements.txt")
    raise


WIDTH, HEIGHT = 960, 540
FPS = 60
GROUND_Y = 385
WORLD_LENGTH = 3600
ASSET_DIR = Path(__file__).parent / "assets"
IMAGE_DIR = ASSET_DIR / "images"
SOUND_DIR = ASSET_DIR / "sounds"
SCORE_FILE = Path(__file__).parent / "scores.json"
SCORE_VALUES = {
    "ring": 15,
    "fire": 50,
    "pond": 25,
}


@dataclass(frozen=True)
class DogSpec:
    name: str
    body: tuple[int, int, int]
    mask: tuple[int, int, int]
    light: tuple[int, int, int]
    eye: tuple[int, int, int]
    collar: tuple[int, int, int]


@dataclass(frozen=True)
class LevelSpec:
    name: str
    world_length: int
    intro: str
    finish: str
    sky: tuple[int, int, int]
    ground: tuple[int, int, int]
    path: tuple[int, int, int]
    obstacles: tuple[tuple[str, float, float], ...]


DOGS = (
    DogSpec("Nova", (112, 137, 158), (64, 83, 104), (245, 249, 250), (92, 159, 210), (239, 76, 92)),
    DogSpec("Hurley", (235, 239, 235), (47, 49, 49), (250, 251, 247), (127, 88, 45), (45, 126, 127)),
)

LEVELS = (
    LevelSpec(
        "Happy Course",
        3600,
        "Guide {dog} through the happy course!",
        "{dog} finished the course!",
        (135, 204, 235),
        (106, 181, 94),
        (225, 207, 150),
        (
            ("ring", 430, 310),
            ("food", 650, GROUND_Y),
            ("fire", 840, GROUND_Y),
            ("ring", 1110, 285),
            ("water", 1325, GROUND_Y),
            ("pond", 1545, GROUND_Y),
            ("ring", 1840, 330),
            ("fire", 2120, GROUND_Y),
            ("food", 2360, GROUND_Y),
            ("pond", 2610, GROUND_Y),
            ("water", 2880, GROUND_Y),
            ("ring", 3160, 300),
        ),
    ),
    LevelSpec(
        "Pine Trail",
        4300,
        "Guide {dog} through the pine trail!",
        "{dog} conquered the pine trail!",
        (150, 199, 221),
        (83, 152, 106),
        (196, 176, 128),
        (
            ("ring", 410, 300),
            ("water", 610, GROUND_Y),
            ("pond", 805, GROUND_Y),
            ("ring", 1050, 336),
            ("fire", 1280, GROUND_Y),
            ("food", 1515, GROUND_Y),
            ("ring", 1785, 286),
            ("pond", 2055, GROUND_Y),
            ("water", 2305, GROUND_Y),
            ("fire", 2540, GROUND_Y),
            ("ring", 2820, 318),
            ("food", 3100, GROUND_Y),
            ("pond", 3375, GROUND_Y),
            ("ring", 3690, 292),
            ("fire", 3940, GROUND_Y),
        ),
    ),
)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def make_tone(path: Path, notes: list[tuple[float, float, float]], volume: float = 0.45) -> None:
    """Create small friendly wav effects without requiring bundled audio files."""
    sample_rate = 22050
    samples: list[int] = []
    for freq, duration, wobble in notes:
        count = int(sample_rate * duration)
        for i in range(count):
            t = i / sample_rate
            env = min(1.0, i / max(1, count * 0.12)) * min(1.0, (count - i) / max(1, count * 0.18))
            bend = freq + math.sin(t * 22.0) * wobble
            sample = math.sin(2 * math.pi * bend * t) * env * volume
            samples.append(int(sample * 32767))

    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(int(s).to_bytes(2, "little", signed=True) for s in samples))


def make_soundtrack(path: Path) -> None:
    sample_rate = 22050
    duration = 20.0
    total_samples = int(sample_rate * duration)
    melody = [
        523.25,
        587.33,
        659.25,
        783.99,
        659.25,
        587.33,
        523.25,
        392.00,
        440.00,
        493.88,
        523.25,
        659.25,
        587.33,
        523.25,
        440.00,
        392.00,
    ]
    bass = [130.81, 146.83, 164.81, 196.00]
    harmony = [261.63, 329.63, 392.00, 349.23]
    melody_step = 0.625
    bass_step = 1.25
    samples: list[int] = []

    for i in range(total_samples):
        t = i / sample_rate
        loop_env = min(1.0, t / 0.6, (duration - t) / 0.6)

        melody_index = int(t / melody_step) % len(melody)
        melody_t = t % melody_step
        melody_env = min(1.0, melody_t / 0.05, (melody_step - melody_t) / 0.16)
        melody_wave = math.sin(2 * math.pi * melody[melody_index] * t)
        bell_wave = math.sin(2 * math.pi * melody[melody_index] * 2.0 * t) * 0.35

        bass_index = int(t / bass_step) % len(bass)
        bass_wave = math.sin(2 * math.pi * bass[bass_index] * t)

        harmony_index = int(t / (bass_step * 2)) % len(harmony)
        harmony_wave = math.sin(2 * math.pi * harmony[harmony_index] * t)
        harmony_wave += math.sin(2 * math.pi * harmony[harmony_index] * 1.5 * t) * 0.45

        pulse = 0.55 + 0.45 * math.sin(2 * math.pi * 2.4 * t) ** 2
        sample = (
            melody_wave * melody_env * 0.20
            + bell_wave * melody_env * 0.12
            + bass_wave * pulse * 0.12
            + harmony_wave * 0.08
        )
        samples.append(int(clamp(sample * loop_env, -0.85, 0.85) * 32767))

    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(int(s).to_bytes(2, "little", signed=True) for s in samples))


def ensure_assets() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    SOUND_DIR.mkdir(parents=True, exist_ok=True)

    sounds = {
        "bark.wav": [(520, 0.08, 70), (300, 0.11, 35), (610, 0.07, 60)],
        "pant.wav": [(180, 0.10, 90), (0.01, 0.05, 0), (210, 0.10, 80), (0.01, 0.05, 0)],
        "eat.wav": [(260, 0.07, 30), (230, 0.07, 25), (310, 0.08, 40)],
        "drink.wav": [(430, 0.05, 80), (500, 0.05, 90), (380, 0.05, 80), (540, 0.06, 90)],
        "success.wav": [(392, 0.10, 15), (523, 0.10, 15), (659, 0.18, 20)],
    }
    for filename, notes in sounds.items():
        path = SOUND_DIR / filename
        if not path.exists():
            make_tone(path, notes)

    soundtrack_path = SOUND_DIR / "soundtrack.wav"
    if not soundtrack_path.exists():
        make_soundtrack(soundtrack_path)


def rounded_rect(surface: pygame.Surface, color: tuple[int, int, int], rect: pygame.Rect, radius: int) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def format_time(milliseconds: int | None) -> str:
    if milliseconds is None:
        return "--:--"
    total_seconds = max(0, milliseconds // 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def load_records() -> dict[str, dict[str, int | None]]:
    if not SCORE_FILE.exists():
        return {}
    try:
        with SCORE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    records: dict[str, dict[str, int | None]] = {}
    for name, record in data.items():
        if isinstance(name, str) and isinstance(record, dict):
            records[name] = {
                "best_score": int(record.get("best_score", 0)),
                "best_time_ms": record.get("best_time_ms"),
                "games": int(record.get("games", 0)),
            }
    return records


def save_records(records: dict[str, dict[str, int | None]]) -> None:
    try:
        with SCORE_FILE.open("w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)
    except OSError:
        pass


def make_hurley_surface(frame: int = 0) -> pygame.Surface:
    scale = 3
    canvas_size = (132 * scale, 92 * scale)
    surf = pygame.Surface(canvas_size, pygame.SRCALPHA)

    def rect(values: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        return tuple(value * scale for value in values)

    def point(values: tuple[int, int]) -> tuple[int, int]:
        return values[0] * scale, values[1] * scale

    def points(values: list[tuple[int, int]]) -> list[tuple[int, int]]:
        return [point(value) for value in values]

    def width(value: int) -> int:
        return value * scale

    white = (247, 249, 244)
    cream = (230, 232, 223)
    charcoal = (43, 45, 45)
    graphite = (86, 91, 91)
    harness = (39, 125, 126)
    harness_dark = (26, 65, 76)
    eye = (126, 79, 34)
    pink = (230, 126, 140)

    leg_shift = 3 if frame % 2 else -3
    rear_shift = -2 if frame % 2 else 2

    pygame.draw.ellipse(surf, (42, 58, 76, 58), rect((22, 74, 84, 11)))

    pygame.draw.line(surf, charcoal, point((34, 47)), point((25, 37)), width(10))
    pygame.draw.line(surf, charcoal, point((25, 37)), point((17, 34)), width(9))
    pygame.draw.circle(surf, charcoal, point((34, 47)), width(6))
    pygame.draw.ellipse(surf, white, rect((6, 24, 20, 14)))
    pygame.draw.circle(surf, white, point((21, 34)), width(5))

    for x, shift, color in [(43, rear_shift, cream), (62, leg_shift, white), (81, -rear_shift, cream), (95, -leg_shift, white)]:
        pygame.draw.line(surf, color, point((x, 58)), point((x + shift, 82)), width(7))
        pygame.draw.ellipse(surf, white, rect((x + shift - 6, 78, 15, 8)))

    pygame.draw.ellipse(surf, white, rect((29, 34, 72, 36)))
    pygame.draw.ellipse(surf, cream, rect((39, 51, 52, 21)))
    pygame.draw.polygon(
        surf,
        charcoal,
        points([(38, 36), (51, 30), (80, 31), (98, 42), (96, 55), (75, 53), (56, 49), (42, 50)]),
    )
    pygame.draw.ellipse(surf, graphite, rect((55, 47, 35, 18)))
    pygame.draw.circle(surf, white, point((50, 43)), width(10))
    pygame.draw.ellipse(surf, white, rect((70, 48, 20, 12)))

    pygame.draw.line(surf, harness_dark, point((54, 42)), point((84, 43)), width(6))
    pygame.draw.line(surf, harness_dark, point((82, 41)), point((95, 35)), width(4))
    pygame.draw.line(surf, harness, point((58, 45)), point((70, 66)), width(7))
    pygame.draw.polygon(surf, harness, points([(62, 48), (79, 48), (86, 64), (70, 68), (58, 60)]))
    pygame.draw.line(surf, (96, 171, 169), point((65, 50)), point((79, 50)), width(2))

    pygame.draw.ellipse(surf, cream, rect((78, 33, 20, 27)))
    pygame.draw.ellipse(surf, white, rect((83, 23, 37, 30)))
    pygame.draw.ellipse(surf, white, rect((94, 36, 31, 19)))
    pygame.draw.ellipse(surf, cream, rect((88, 39, 25, 16)))
    pygame.draw.polygon(surf, graphite, points([(90, 25), (80, 22), (86, 17), (98, 23), (96, 29)]))
    pygame.draw.line(surf, cream, point((86, 22)), point((94, 24)), width(2))
    pygame.draw.polygon(surf, graphite, points([(106, 23), (117, 20), (121, 26), (112, 29)]))
    pygame.draw.line(surf, cream, point((111, 23)), point((117, 25)), width(2))
    pygame.draw.arc(surf, graphite, rect((83, 24, 25, 33)), math.pi * 0.78, math.pi * 1.42, width(4))

    pygame.draw.circle(surf, eye, point((105, 36)), width(4))
    pygame.draw.circle(surf, (32, 22, 15), point((106, 36)), width(2))
    pygame.draw.circle(surf, (255, 248, 225), point((104, 34)), width(1))
    pygame.draw.ellipse(surf, (19, 24, 29), rect((116, 43, 10, 8)))
    pygame.draw.arc(surf, (22, 27, 32), rect((103, 45, 19, 14)), 0.05, math.pi * 0.75, width(2))
    pygame.draw.ellipse(surf, pink, rect((111, 52, 8, 5)))

    pygame.draw.line(surf, white, point((19, 29)), point((13, 21)), width(3))
    pygame.draw.circle(surf, (232, 235, 230), point((42, 60)), width(3))
    pygame.draw.circle(surf, (232, 235, 230), point((86, 62)), width(3))

    return pygame.transform.smoothscale(surf, (132, 92))


def make_husky_surface(frame: int = 0, dog: DogSpec = DOGS[0]) -> pygame.Surface:
    if dog.name == "Hurley":
        return make_hurley_surface(frame)

    surf = pygame.Surface((132, 92), pygame.SRCALPHA)
    leg_shift = 3 if frame % 2 else -2
    shadow = (42, 58, 76, 70)
    dark = dog.mask
    mid = dog.body
    light = dog.light
    blue = dog.eye
    pink = (238, 132, 145)

    pygame.draw.ellipse(surf, shadow, (24, 72, 78, 12))
    pygame.draw.ellipse(surf, mid, (28, 33, 70, 38))
    pygame.draw.ellipse(surf, light, (40, 43, 48, 28))
    pygame.draw.circle(surf, dark, (94, 38), 27)
    pygame.draw.circle(surf, light, (97, 44), 20)
    pygame.draw.polygon(surf, dark, [(76, 22), (83, 3), (92, 25)])
    pygame.draw.polygon(surf, dark, [(103, 19), (114, 2), (116, 28)])
    pygame.draw.polygon(surf, light, [(81, 21), (84, 10), (88, 23)])
    pygame.draw.polygon(surf, light, [(107, 20), (113, 10), (113, 25)])
    pygame.draw.circle(surf, blue, (91, 40), 3)
    pygame.draw.circle(surf, blue, (106, 39), 3)
    pygame.draw.circle(surf, (20, 26, 32), (99, 49), 4)
    pygame.draw.arc(surf, (20, 26, 32), (91, 46, 18, 16), 0.15, math.pi - 0.15, 2)
    pygame.draw.circle(surf, pink, (106, 54), 3)
    pygame.draw.arc(surf, dark, (10, 23, 32, 36), math.pi * 1.05, math.pi * 2.15, 8)
    pygame.draw.line(surf, light, (21, 36), (15, 23), 5)

    for x, y in [(42, 62), (62, 62), (78, 61), (93, 58)]:
        pygame.draw.line(surf, dark, (x, y), (x + leg_shift, y + 22), 7)
        pygame.draw.ellipse(surf, light, (x + leg_shift - 6, y + 18, 15, 8))
    pygame.draw.circle(surf, dog.collar, (68, 42), 4)
    return surf


def draw_legend_icon(surface: pygame.Surface, kind: str, center: tuple[int, int]) -> None:
    cx, cy = center
    if kind == "ring":
        pygame.draw.ellipse(surface, (244, 197, 66), (cx - 24, cy - 33, 48, 66), 7)
        pygame.draw.ellipse(surface, (255, 238, 145), (cx - 17, cy - 24, 34, 48), 3)
    elif kind == "fire":
        pygame.draw.rect(surface, (117, 77, 41), (cx - 26, cy + 18, 52, 8), border_radius=4)
        for i in range(4):
            fx = cx - 23 + i * 14
            pygame.draw.polygon(surface, (236, 74, 49), [(fx, cy + 18), (fx + 8, cy - 24), (fx + 17, cy + 18)])
            pygame.draw.polygon(surface, (255, 194, 62), [(fx + 4, cy + 18), (fx + 9, cy - 8), (fx + 14, cy + 18)])
    elif kind == "pond":
        pygame.draw.ellipse(surface, (75, 164, 214), (cx - 43, cy - 14, 86, 31))
        pygame.draw.arc(surface, (210, 242, 255), (cx - 32, cy - 10, 48, 16), 0.2, 2.7, 3)
    elif kind == "food":
        pygame.draw.ellipse(surface, (232, 103, 82), (cx - 30, cy + 3, 60, 25))
        pygame.draw.ellipse(surface, (255, 242, 219), (cx - 20, cy - 2, 40, 17))
        for bx in [-13, 0, 13]:
            pygame.draw.circle(surface, (112, 70, 48), (cx + bx, cy - 1), 5)
    elif kind == "water":
        pygame.draw.rect(surface, (78, 145, 207), (cx - 20, cy - 33, 40, 56), border_radius=7)
        pygame.draw.rect(surface, (191, 229, 250), (cx - 13, cy - 17, 26, 26), border_radius=4)
        pygame.draw.circle(surface, (255, 255, 255), (cx + 8, cy - 7), 3)


def make_legend_icon_surface(kind: str) -> pygame.Surface:
    surf = pygame.Surface((96, 80), pygame.SRCALPHA)
    draw_legend_icon(surf, kind, (48, 40))
    return surf


def save_reference_images() -> None:
    samples = {
        "nova_run_1.png": make_husky_surface(0, DOGS[0]),
        "nova_run_2.png": make_husky_surface(1, DOGS[0]),
        "hurley_run_1.png": make_husky_surface(0, DOGS[1]),
        "hurley_run_2.png": make_husky_surface(1, DOGS[1]),
        "husky_run_1.png": make_husky_surface(0, DOGS[0]),
        "husky_run_2.png": make_husky_surface(1, DOGS[0]),
        "legend_ring.png": make_legend_icon_surface("ring"),
        "legend_fire.png": make_legend_icon_surface("fire"),
        "legend_pond.png": make_legend_icon_surface("pond"),
        "legend_food.png": make_legend_icon_surface("food"),
        "legend_water.png": make_legend_icon_surface("water"),
    }
    for filename, surface in samples.items():
        path = IMAGE_DIR / filename
        pygame.image.save(surface, str(path))


class SoundBox:
    def __init__(self) -> None:
        self.enabled = False
        self.music_loaded = False
        self.music_started = False
        self.last_pant = 0
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            pygame.mixer.init()
            for name in ["bark", "pant", "eat", "drink", "success"]:
                self.sounds[name] = pygame.mixer.Sound(str(SOUND_DIR / f"{name}.wav"))
            try:
                pygame.mixer.music.load(str(SOUND_DIR / "soundtrack.wav"))
                pygame.mixer.music.set_volume(0.32)
                self.music_loaded = True
            except pygame.error:
                self.music_loaded = False
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def start_music(self) -> None:
        if self.enabled and self.music_loaded and not self.music_started:
            pygame.mixer.music.play(-1)
            self.music_started = True

    def pause_music(self) -> None:
        if self.enabled and self.music_started:
            pygame.mixer.music.pause()

    def resume_music(self) -> None:
        if self.enabled and self.music_started:
            pygame.mixer.music.unpause()

    def stop_music(self) -> None:
        if self.enabled and self.music_started:
            pygame.mixer.music.fadeout(500)
            self.music_started = False

    def pant_if_ready(self, now: int) -> None:
        if now - self.last_pant > 1650:
            self.last_pant = now
            self.play("pant")


@dataclass
class Obstacle:
    kind: str
    x: float
    y: float
    passed: bool = False

    @property
    def rect(self) -> pygame.Rect:
        if self.kind == "ring":
            return pygame.Rect(int(self.x - 38), int(self.y - 62), 76, 118)
        if self.kind == "fire":
            return pygame.Rect(int(self.x - 35), int(GROUND_Y - 44), 70, 50)
        if self.kind == "pond":
            return pygame.Rect(int(self.x - 58), int(GROUND_Y - 26), 116, 40)
        if self.kind == "food":
            return pygame.Rect(int(self.x - 28), int(GROUND_Y - 28), 56, 38)
        return pygame.Rect(int(self.x - 26), int(GROUND_Y - 54), 52, 62)


class Dog:
    def __init__(self) -> None:
        self.x = 105.0
        self.y = GROUND_Y
        self.speed = 2.1
        self.z = 0.0
        self.vz = 0.0
        self.energy = 88.0
        self.water = 82.0
        self.happy = 80.0
        self.frame_time = 0.0
        self.direction = 1

    @property
    def jumping(self) -> bool:
        return self.z > 4 or self.vz > 0

    def jump(self) -> None:
        if not self.jumping and self.energy > 8 and self.water > 8:
            self.vz = 12.5
            self.energy = max(0, self.energy - 4.0)
            self.water = max(0, self.water - 2.0)

    def update(self, keys: pygame.key.ScancodeWrapper, dt: float, world_length: int) -> None:
        if keys[pygame.K_RIGHT]:
            self.speed += 3.0 * dt
        if keys[pygame.K_LEFT]:
            self.speed -= 3.2 * dt
        self.speed = clamp(self.speed, 0.0, 6.8)
        if self.speed < 0.04:
            self.speed = 0.0

        if keys[pygame.K_UP]:
            self.y -= 235 * dt
        if keys[pygame.K_DOWN]:
            self.y += 235 * dt
        self.y = clamp(self.y, 245, GROUND_Y)

        tired_factor = 0.48 if self.energy < 13 or self.water < 13 else 1.0
        self.x += self.speed * 72 * dt * tired_factor
        self.x = clamp(self.x, 80, world_length)
        if self.speed > 0 or self.jumping:
            self.frame_time += dt * (6 + self.speed)

        if self.vz or self.z:
            self.z += self.vz
            self.vz -= 28 * dt
            if self.z <= 0:
                self.z = 0
                self.vz = 0

        drain = self.speed * 0.35 * dt
        self.energy = clamp(self.energy - drain, 0, 100)
        self.water = clamp(self.water - drain * 0.52, 0, 100)
        if self.energy < 12 or self.water < 12:
            self.speed = min(self.speed, 2.2)

    def screen_rect(self, camera_x: float) -> pygame.Rect:
        return pygame.Rect(int(self.x - camera_x - 47), int(self.y - self.z - 58), 94, 55)


class Game:
    def __init__(self) -> None:
        pygame.init()
        ensure_assets()
        save_reference_images()
        pygame.display.set_caption("Husky Happy Run")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 22)
        self.small_font = pygame.font.SysFont("segoeui", 16)
        self.big_font = pygame.font.SysFont("segoeui", 34, bold=True)
        self.dog = Dog()
        self.selected_dog = 0
        self.selected_level = 0
        self.level = LEVELS[self.selected_level]
        self.sound = SoundBox()
        self.camera_x = 0.0
        self.score = 0
        self.started = False
        self.paused = False
        self.pause_started_at = 0
        self.pause_button_rect = pygame.Rect(WIDTH - 124, 14, 108, 38)
        self.restart_button_rect = pygame.Rect(WIDTH // 2 - 82, 188, 164, 42)
        self.finished = False
        self.finish_walkback = False
        self.finish_resting = False
        self.finish_rest_target_x = 0.0
        self.message = self.level.intro.format(dog=self.current_dog.name)
        self.message_until = 4200
        self.obstacles = self.make_obstacles()

    @property
    def current_dog(self) -> DogSpec:
        return DOGS[self.selected_dog]

    @property
    def ring_total(self) -> int:
        return sum(1 for obstacle in self.obstacles if obstacle.kind == "ring")

    def make_obstacles(self) -> list[Obstacle]:
        return [Obstacle(kind, x, y) for kind, x, y in self.level.obstacles]

    def choose_dog(self, direction: int) -> None:
        if self.started:
            return
        self.selected_dog = (self.selected_dog + direction) % len(DOGS)
        self.message = self.level.intro.format(dog=self.current_dog.name)

    def choose_level(self, direction: int) -> None:
        if self.started:
            return
        self.selected_level = (self.selected_level + direction) % len(LEVELS)
        self.level = LEVELS[self.selected_level]
        self.obstacles = self.make_obstacles()
        self.message = self.level.intro.format(dog=self.current_dog.name)

    def set_message(self, text: str, duration: int = 2300) -> None:
        self.message = text
        self.message_until = pygame.time.get_ticks() + duration

    def start_game(self) -> None:
        if self.started:
            return
        self.started = True
        self.paused = False
        self.set_message(self.level.intro.format(dog=self.current_dog.name), 4200)
        self.sound.start_music()
        self.sound.play("bark")

    def toggle_pause(self) -> None:
        if not self.started or self.finished:
            return
        now = pygame.time.get_ticks()
        if self.paused:
            self.message_until += now - self.pause_started_at
            self.pause_started_at = 0
            self.paused = False
            self.sound.resume_music()
        else:
            self.paused = True
            self.pause_started_at = now
            self.sound.pause_music()

    def restart_game(self) -> None:
        self.sound.stop_music()
        self.__init__()

    def begin_finish_rest(self) -> None:
        self.finished = True
        self.finish_walkback = True
        self.finish_resting = False
        self.finish_rest_target_x = clamp(self.camera_x + WIDTH * 0.50, 80, self.level.world_length)
        self.dog.speed = 0.0
        self.set_message(f"Course complete! {self.current_dog.name} is heading back to rest.", 8000)
        self.sound.play("success")

    def update_finish_rest(self, dt: float) -> None:
        if not self.finish_walkback:
            return

        self.dog.direction = -1
        walk_step = 145 * dt
        if self.dog.x > self.finish_rest_target_x:
            self.dog.x = max(self.finish_rest_target_x, self.dog.x - walk_step)
            self.dog.frame_time += dt * 5.0
        else:
            self.finish_walkback = False
            self.finish_resting = True
            self.dog.speed = 0.0
            self.dog.z = 0.0
            self.dog.vz = 0.0
            self.set_message(f"{self.current_dog.name} is resting after a great run.", 8000)

    def draw_background(self) -> None:
        self.screen.fill(self.level.sky)
        pygame.draw.rect(self.screen, (230, 250, 255), (0, 0, WIDTH, 78))
        for i in range(8):
            cx = int((i * 390 - self.camera_x * 0.22) % (WIDTH + 240)) - 120
            pygame.draw.ellipse(self.screen, (248, 252, 253), (cx, 64 + (i % 2) * 28, 105, 34))
            pygame.draw.ellipse(self.screen, (248, 252, 253), (cx + 48, 50 + (i % 2) * 28, 92, 40))

        pygame.draw.rect(self.screen, self.level.ground, (0, GROUND_Y + 14, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.rect(self.screen, self.level.path, (0, GROUND_Y + 4, WIDTH, 44))
        pygame.draw.line(self.screen, (190, 169, 119), (0, GROUND_Y + 47), (WIDTH, GROUND_Y + 47), 3)
        for x in range(-80, WIDTH + 120, 110):
            sx = int((x - self.camera_x * 0.75) % (WIDTH + 180)) - 80
            pygame.draw.line(self.screen, (86, 154, 78), (sx, GROUND_Y + 55), (sx + 10, GROUND_Y + 41), 2)

    def draw_bar(self, label: str, value: float, x: int, y: int, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(self.screen, (35, 46, 58), (x, y, 185, 22), border_radius=5)
        pygame.draw.rect(self.screen, color, (x + 3, y + 3, int(179 * value / 100), 16), border_radius=4)
        text = self.font.render(f"{label} {int(value)}", True, (255, 255, 255))
        self.screen.blit(text, (x + 8, y - 1))

    def draw_hud(self) -> None:
        rounded_rect(self.screen, (37, 53, 67), pygame.Rect(16, 14, 360, 88), 8)
        self.draw_bar("Energy", self.dog.energy, 30, 28, (249, 189, 69))
        self.draw_bar("Water", self.dog.water, 30, 62, (85, 180, 231))
        score = self.font.render(f"Rings: {self.score}/{self.ring_total}   Speed: {self.dog.speed:.1f}", True, (255, 255, 255))
        self.screen.blit(score, (226, 44))

        now = self.pause_started_at if self.paused else pygame.time.get_ticks()
        if now < self.message_until:
            text = self.font.render(self.message, True, (34, 43, 54))
            panel = pygame.Rect(WIDTH // 2 - text.get_width() // 2 - 18, 26, text.get_width() + 36, 38)
            rounded_rect(self.screen, (255, 250, 218), panel, 8)
            self.screen.blit(text, (panel.x + 18, panel.y + 7))

        if self.started and not self.finished:
            label = "Resume" if self.paused else "Pause"
            rounded_rect(self.screen, (37, 53, 67), self.pause_button_rect, 8)
            pygame.draw.rect(self.screen, (255, 250, 218), self.pause_button_rect, 2, border_radius=8)
            text = self.font.render(label, True, (255, 255, 255))
            self.screen.blit(
                text,
                (
                    self.pause_button_rect.centerx - text.get_width() // 2,
                    self.pause_button_rect.centery - text.get_height() // 2,
                ),
            )

        controls = self.font.render("Arrows move/speed  |  Space jump  |  F/f feed  |  W/w water  |  P pause", True, (36, 52, 58))
        self.screen.blit(controls, (WIDTH - controls.get_width() - 18, HEIGHT - 35))

    def draw_obstacle(self, obstacle: Obstacle) -> None:
        sx = int(obstacle.x - self.camera_x)
        if sx < -160 or sx > WIDTH + 160:
            return
        if obstacle.kind == "ring":
            color = (244, 197, 66) if not obstacle.passed else (139, 214, 123)
            pygame.draw.ellipse(self.screen, color, (sx - 38, int(obstacle.y - 62), 76, 118), 9)
            pygame.draw.ellipse(self.screen, (255, 238, 145), (sx - 29, int(obstacle.y - 50), 58, 94), 3)
        elif obstacle.kind == "fire":
            pygame.draw.rect(self.screen, (117, 77, 41), (sx - 39, GROUND_Y - 2, 78, 12), border_radius=4)
            for i in range(5):
                fx = sx - 28 + i * 14
                pygame.draw.polygon(self.screen, (236, 74, 49), [(fx, GROUND_Y - 2), (fx + 9, GROUND_Y - 47), (fx + 19, GROUND_Y - 2)])
                pygame.draw.polygon(self.screen, (255, 194, 62), [(fx + 4, GROUND_Y - 1), (fx + 10, GROUND_Y - 31), (fx + 16, GROUND_Y - 1)])
        elif obstacle.kind == "pond":
            pygame.draw.ellipse(self.screen, (75, 164, 214), (sx - 64, GROUND_Y - 28, 128, 42))
            pygame.draw.arc(self.screen, (210, 242, 255), (sx - 50, GROUND_Y - 22, 70, 21), 0.2, 2.7, 3)
        elif obstacle.kind == "food":
            pygame.draw.ellipse(self.screen, (232, 103, 82), (sx - 28, GROUND_Y - 16, 56, 22))
            pygame.draw.ellipse(self.screen, (255, 242, 219), (sx - 19, GROUND_Y - 20, 38, 14))
            for bx in [-12, 0, 12]:
                pygame.draw.circle(self.screen, (112, 70, 48), (sx + bx, GROUND_Y - 19), 4)
        elif obstacle.kind == "water":
            pygame.draw.rect(self.screen, (78, 145, 207), (sx - 22, GROUND_Y - 54, 44, 50), border_radius=7)
            pygame.draw.rect(self.screen, (191, 229, 250), (sx - 15, GROUND_Y - 39, 30, 23), border_radius=4)
            pygame.draw.circle(self.screen, (255, 255, 255), (sx + 9, GROUND_Y - 29), 3)

    def draw_dog(self) -> None:
        frame = int(self.dog.frame_time) % 2
        dog_surf = make_husky_surface(frame, self.current_dog)
        if self.dog.direction < 0:
            dog_surf = pygame.transform.flip(dog_surf, True, False)
        sx = int(self.dog.x - self.camera_x - 66)
        sy = int(self.dog.y - self.dog.z - 76)
        self.screen.blit(dog_surf, (sx, sy))

    def handle_collisions(self) -> None:
        dog_rect = self.dog.screen_rect(self.camera_x).move(self.camera_x, 0)
        now = pygame.time.get_ticks()
        for obstacle in self.obstacles:
            if obstacle.passed and obstacle.kind in {"ring", "fire", "pond"}:
                continue
            if abs(self.dog.x - obstacle.x) > 90:
                continue

            if obstacle.kind == "ring":
                inside_y = abs((self.dog.y - self.dog.z) - obstacle.y) < 46
                if inside_y:
                    obstacle.passed = True
                    self.score += 1
                    self.dog.happy = clamp(self.dog.happy + 8, 0, 100)
                    self.set_message(f"Beautiful ring run! Good {self.current_dog.name}!")
                    self.sound.play("success")
                elif not obstacle.passed and self.dog.x > obstacle.x + 28:
                    obstacle.passed = True
                    self.set_message(f"Close one! Try lining {self.current_dog.name} up with the next ring.")
            elif obstacle.kind in {"fire", "pond"} and dog_rect.colliderect(obstacle.rect):
                if self.dog.z > 32:
                    obstacle.passed = True
                    self.set_message("Nice jump!")
                    self.sound.play("bark")
                elif now > self.message_until - 1400:
                    self.dog.speed = max(0.9, self.dog.speed * 0.55)
                    self.dog.energy = max(0, self.dog.energy - 3)
                    self.set_message("No worries. Slow down, then press Space to jump.")
            elif obstacle.kind == "food" and dog_rect.colliderect(obstacle.rect.inflate(60, 35)):
                keys = pygame.key.get_pressed()
                if keys[pygame.K_f]:
                    self.dog.energy = clamp(self.dog.energy + 36, 0, 100)
                    self.set_message("Crunch crunch! Energy restored.")
                    self.sound.play("eat")
            elif obstacle.kind == "water" and dog_rect.colliderect(obstacle.rect.inflate(60, 35)):
                keys = pygame.key.get_pressed()
                if keys[pygame.K_w]:
                    self.dog.water = clamp(self.dog.water + 42, 0, 100)
                    self.set_message("Slurp! Nova is refreshed.")
                    self.sound.play("drink")

    def update(self, dt: float) -> None:
        if self.finished:
            self.update_finish_rest(dt)
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.dog.jump()
        old_x = self.dog.x
        self.dog.update(keys, dt, self.level.world_length)
        self.dog.direction = 1 if self.dog.x >= old_x else -1
        self.camera_x = clamp(self.dog.x - WIDTH * 0.34, 0, self.level.world_length - WIDTH)
        self.handle_collisions()

        now = pygame.time.get_ticks()
        if self.dog.energy < 18:
            self.sound.pant_if_ready(now)
            if now > self.message_until:
                self.set_message(f"{self.current_dog.name} is low on energy. Find food and press F/f.")
        elif self.dog.water < 18 and now > self.message_until:
            self.set_message(f"{self.current_dog.name} is thirsty. Find water and press W/w.")

        if self.dog.x > self.level.world_length - 150 and not self.finished:
            self.begin_finish_rest()

    def draw_finish(self) -> None:
        sx = int(self.level.world_length - 120 - self.camera_x)
        pygame.draw.rect(self.screen, (255, 255, 255), (sx, 215, 8, 180))
        for i in range(8):
            color = (36, 45, 52) if i % 2 else (255, 255, 255)
            pygame.draw.rect(self.screen, color, (sx + 8 + i * 14, 218, 14, 34))
        label = self.big_font.render("FINISH", True, (36, 45, 52))
        self.screen.blit(label, (sx - 26, 176))

    def draw_center_overlay(self, title: str, subtitle: str, panel: pygame.Rect | None = None) -> pygame.Rect:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((22, 33, 44, 115))
        self.screen.blit(shade, (0, 0))

        if panel is None:
            panel = pygame.Rect(WIDTH // 2 - 205, HEIGHT // 2 - 76, 410, 140)
        rounded_rect(self.screen, (255, 250, 218), panel, 8)
        pygame.draw.rect(self.screen, (37, 53, 67), panel, 3, border_radius=8)

        title_text = self.big_font.render(title, True, (37, 53, 67))
        subtitle_text = self.font.render(subtitle, True, (71, 89, 103))
        self.screen.blit(title_text, (panel.centerx - title_text.get_width() // 2, panel.y + 18))
        self.screen.blit(subtitle_text, (panel.centerx - subtitle_text.get_width() // 2, panel.y + 64))
        return panel

    def draw_object_key(self, panel: pygame.Rect) -> None:
        items = [
            ("ring", "Ring", "run through"),
            ("fire", "Fire", "jump over"),
            ("pond", "Pond", "jump over"),
            ("food", "Food", "press F/f"),
            ("water", "Water", "press W/w"),
        ]
        start_x = panel.x + 42
        y = panel.y + (188 if panel.height > 250 else 126)
        for index, (kind, title, hint) in enumerate(items):
            x = start_x + index * 101
            draw_legend_icon(self.screen, kind, (x + 34, y))
            title_text = self.font.render(title, True, (37, 53, 67))
            hint_text = self.small_font.render(hint, True, (71, 89, 103))
            self.screen.blit(title_text, (x + 34 - title_text.get_width() // 2, y + 38))
            self.screen.blit(hint_text, (x + 34 - hint_text.get_width() // 2, y + 62))

    def draw_start_overlay(self) -> None:
        panel = self.draw_center_overlay(
            "Click to Start",
            f"Help {self.current_dog.name} run {self.level.name}",
            pygame.Rect(WIDTH // 2 - 316, HEIGHT // 2 - 156, 632, 294),
        )
        dog_text = self.font.render(f"Dog: {self.current_dog.name}  [1/2]", True, (37, 53, 67))
        level_text = self.font.render(f"Level: {self.level.name}  [Tab]", True, (37, 53, 67))
        hint_text = self.small_font.render("Press 1/2 to choose a dog. Press Tab to choose a level.", True, (71, 89, 103))
        preview = make_husky_surface(0, self.current_dog)
        preview = pygame.transform.smoothscale(preview, (99, 69))
        self.screen.blit(preview, (panel.x + 54, panel.y + 76))
        self.screen.blit(dog_text, (panel.x + 174, panel.y + 84))
        self.screen.blit(level_text, (panel.x + 174, panel.y + 116))
        self.screen.blit(hint_text, (panel.centerx - hint_text.get_width() // 2, panel.y + 150))
        self.draw_object_key(panel)

    def draw_pause_overlay(self) -> None:
        self.draw_center_overlay("Paused", "Press P or click Resume")

    def draw(self) -> None:
        self.draw_background()
        for obstacle in self.obstacles:
            self.draw_obstacle(obstacle)
        self.draw_finish()
        self.draw_dog()
        if self.finished:
            text = self.big_font.render(self.level.finish.format(dog=self.current_dog.name), True, (255, 255, 255))
            panel = pygame.Rect(WIDTH // 2 - 230, 118, 460, 128)
            rounded_rect(self.screen, (49, 103, 82), panel, 8)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 128))

            if self.finish_walkback:
                rest_text = self.font.render(f"{self.current_dog.name} is walking back to rest.", True, (255, 250, 218))
            else:
                rest_text = self.font.render(f"{self.current_dog.name} is resting. Great run!", True, (255, 250, 218))
            self.screen.blit(rest_text, (WIDTH // 2 - rest_text.get_width() // 2, 164))

            rounded_rect(self.screen, (255, 250, 218), self.restart_button_rect, 8)
            pygame.draw.rect(self.screen, (37, 53, 67), self.restart_button_rect, 2, border_radius=8)
            button_text = self.font.render("Restart", True, (37, 53, 67))
            self.screen.blit(
                button_text,
                (
                    self.restart_button_rect.centerx - button_text.get_width() // 2,
                    self.restart_button_rect.centery - button_text.get_height() // 2,
                ),
            )
        self.draw_hud()
        if not self.started:
            self.draw_start_overlay()
        elif self.paused:
            self.draw_pause_overlay()
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_1 and not self.started:
                    self.selected_dog = 0
                    self.message = self.level.intro.format(dog=self.current_dog.name)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_2 and not self.started:
                    self.selected_dog = 1
                    self.message = self.level.intro.format(dog=self.current_dog.name)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and not self.started:
                    self.choose_level(1)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.toggle_pause()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.finished:
                    self.restart_game()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.started:
                        self.start_game()
                    elif self.finished and self.restart_button_rect.collidepoint(event.pos):
                        self.restart_game()
                    elif self.pause_button_rect.collidepoint(event.pos):
                        self.toggle_pause()
            if self.started and not self.paused:
                self.update(dt)
            self.draw()
        self.sound.stop_music()
        pygame.quit()


def run() -> None:
    Game().run()


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        pygame.quit()
        print(f"Husky Happy Run could not start: {exc}")
        sys.exit(1)
