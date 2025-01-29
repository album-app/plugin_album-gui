from album.runner.api import setup

env_file = """channels:
  - conda-forge
dependencies:
  - python=3.10
"""

setup(group="group", name="name", version="version", album_api_version="0.5.5", dependencies={'environment_file': env_file})
