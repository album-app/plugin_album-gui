# album-gui

A graphical user interface plugin for [Album](https://album.solutions/).

Browse catalogs, install and run solutions visually. The plugin adds the `album gui` and
`album add-shortcut` commands to the Album CLI.

## Installation

1. [Install Album](https://docs.album.solutions/en/latest/installation-instructions.html)
2. Activate the Album environment:

```
micromamba activate album
```

3. Install the album-gui plugin:

```
micromamba install album-gui -c conda-forge
```

Or via pip:

```
pip install album-gui
```

## Usage

Launch the graphical interface:

```
album gui
```

Create a desktop shortcut for a solution:

```
album add-shortcut group:name:version
```

## Links

- [Album documentation](https://docs.album.solutions)
- [Album framework](https://gitlab.com/album-app/album)
- [Album website](https://album.solutions)

