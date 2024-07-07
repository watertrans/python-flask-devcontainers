# python-flask-devcontainers
This is a template project for development in python.

## Prerequisites
- Windows 10 64-bit or Windows 11 64-bit.
- Enable hardware virtualization in BIOS.
- Install Windows Terminal.
- Install [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) and set up a user name and password for your Linux distribution running in WSL 2.
    - Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script) on Linux (WSL 2).
    - Add current user into `docker` group: `sudo usermod -aG docker $USER`
- Install the VS Code.
    - Turn on `Dev Containers: Execute In WSL` in Preference -> Settings.
- Install the VS Code WSL extension.
- Install the VS Code Dev Containers extension.
- Install the VS Code Docker extension.

## Develop
- Open the `src` folder in VSCode.
- Use Command Palette (F1) to select `Dev Containers: Reopen in Container`.
- Start debugging using the `F5` key.

## Build
`docker build --tag python-devcontainers .`

## Run
`docker run -it --rm python-devcontainers`
