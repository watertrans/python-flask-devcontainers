# python-flask-devcontainers
This repository serves as a template project for developing web applications using Python and Flask.  
It is built on [Visual Studio Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers), making it easy to standardize the development environment across a team.  

## Features
This template includes the following modules and features:

- **Python 3.12**
- **Flask:** A lightweight wep application framework.
- **Flask-Session:** Provides support for server-side sessions.
- **Flask-SQLAlchemy:** A SQL toolkit and Object-Relational Mapper (ORM).
- **Flask-WTF:** A flexible library for form validation and rendering.
- **Gunicorn:** An HTTP server for WSGI applications, ideal for running in Docker environments.
- **pytest:** A popular testing framework for Python.
- **Python Dotenv:** A library for loading environment variables from a .env file.
- **python-inject:** A fast and simple Dependency Injection library.
- **PyYAML:** A library for parsing and writing YAML files.
- **Supabase:** A Backend-as-a-Service (BaaS) platform, serving as an alternative to Firebase.

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
- Open the `src` folder in Visual Studio Code.
- Use Command Palette (F1) and select `Dev Containers: Reopen in Container`.
- Start debugging by pressing the `F5` key.

## Build
Access WSL through your terminal, navigate to the src folder as your working directory, and execute the following command:
```bash
docker build --tag python-flask-devcontainers .
```

## Run
Access WSL through your terminal, navigate to the src folder as your working directory, and execute the following command:
```bash
docker run -p 80:8000 -it --rm python-flask-devcontainers
```
**Note:** Ensure that port 80 on your host is available or change it to an available port.
