# Husky Happy Run

A gentle Python/Pygame obstacle-course game where Nova or Hurley the Husky runs through rings, jumps over fire and ponds, and needs food and water when energy runs low.

## Quick Start

This project is set up for [uv](https://docs.astral.sh/uv/), which keeps the Python version and game dependencies together so new users do not have to manage a virtual environment by hand.

1. Install uv.

   Windows PowerShell:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Open this folder:

   ```powershell
   cd C:\Repos\DogGame
   ```

3. Start the game:

   ```powershell
   uv run main.py
   ```

uv reads `.python-version`, creates a local `.venv`, installs Pygame, and runs the game with the correct Python version.

## Local Fallback

On this machine, the default `python` is Python 3.14, which may not install Pygame cleanly yet. Python 3.9 already has Pygame available here, so this also works locally:

```powershell
py -3.9 main.py
```

Avoid using plain `python main.py` on this machine unless you have changed your default Python to a Pygame-compatible version.

## Controls

- Click: start the game from the opening screen.
- 1/2: choose Nova or Hurley from the opening screen.
- Tab: choose the level from the opening screen.
- Arrow keys: steer Nova and adjust speed. Hold Left to slow her all the way to a full stop, and press Right to speed up again.
- Space: jump.
- F/f: eat food when nearby.
- W/w: drink water when nearby.
- P: pause or resume.
- Pause/Resume button: pause or resume with the mouse.
- Esc: quit.
- R or Restart button: restart after finishing.

When the selected dog completes the course, they automatically walk back toward the middle of the screen and rest. Use `R` or the Restart button to run again.

## Dogs and Levels

- Nova: the original blue-eyed gray-and-white Husky.
- Hurley: a mostly white Husky with warm brown eyes, charcoal back patches, a white-tipped tail, and teal harness.
- Happy Course: the original gentle run.
- Pine Trail: a longer second level with a different obstacle rhythm and more rings.

## Sound

The game includes generated bark, pant, eating, drinking, and success sounds, plus a gentle 20-second soundtrack that loops after the player clicks to start. The music pauses and resumes with the game.

## Object Key

| Object | What it means | What to do |
| --- | --- | --- |
| ![Ring](assets/images/legend_ring.png) | Ring | Run the dog through it for a happy success. |
| ![Fire](assets/images/legend_fire.png) | Fire | Press Space to jump over it. |
| ![Pond](assets/images/legend_pond.png) | Pond | Press Space to jump over it. |
| ![Food](assets/images/legend_food.png) | Food bowl | Stand near it and press F/f to restore energy. |
| ![Water](assets/images/legend_water.png) | Water bottle | Stand near it and press W/w to restore water. |

## Git Notes

The repository is configured to track the game source and small bundled assets, including Husky images and sound effects. It ignores local virtual environments, Python caches, and build output.

If this folder is not a Git repo yet, install Git and run:

```powershell
git init
git add .
git commit -m "Initial Husky Happy Run game"
```

When uv is installed, generate the lockfile with:

```powershell
uv lock
```

Commit `uv.lock` so future setup stays reproducible.

## Future Release Build

For the easiest experience for players, a future step can package the game with PyInstaller so it can be downloaded and launched as a Windows `.exe` without installing Python.
