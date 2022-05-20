[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0d18ec4c208743df8101d08d4ce71b82)](https://www.codacy.com?utm_source=github.com&utm_medium=referral&utm_content=Travisivart/TGA-Bot&utm_campaign=Badge_Grade)

# The Galaxy Aces Discord Bot

## Table of Contents

-   [Installation](#installation)
    -   [Linux](#linux-install)
    -   [Windows](#windows-install)
        -   [Notes for Windows users](#notes-for-windows-users)
-   [Using the Bot](#using-the-bot)
    -   [Discord interface](#discord-interface)
    -   [Command Line Interface (CLI)](#command-line-interface-cli)
-   [Configuration](#configuration)
    -   [Minimum Configuration](#minimum-configuration)
    -   [Permissions](#permissions)
    -   [Running Multiple Bots](#running-multiple-bots)
-   [Appendix](#appendix)
    -   [Core Bot Parameters](#core-bot-parameters)
    -   [Music Feature](#music-feature)
    -   [Shared Feature Parameters](#shared-feature-parameters)

## Installation

### Linux

```sh
# Clone the repo
git clone git@github.com:Travisivart/TGA-Bot.git && cd TGA-Bot

# install any required dependencies and build the virtual environment
sudo ./build.sh
```

The build script should have created a config.yaml file in the current directory.
Modify your config.yaml with your bot parameters, your bot will need a custom name,
a discord API token, and a command_prefix.
See [Configuration](#configuration) for more details

**See the [Appendix](#appendix) for more details on the config.yaml parameters.**

```sh
# Activate the virtual environment
. venv/bin/activate

# Run the bot
python main.py
```

### Windows

If you are planning to use the Music feature then you will need to have ffmpeg available on your system.

If you have chocolately installed you can use it to install ffmpeg:

```powershell
 choco install ffmpeg
```

Otherwise you will need to follow the instructions on the [ffmpeg site](https://ffmpeg.org/) to add ffmpeg to your system.

```powershell
# Clone the repo
git clone git@github.com:Travisivart/TGA-Bot.git; cd TGA-Bot

# Build the virtual environment
.\build.ps1

```

The build script should have created a config.yaml file in the current directory.
Modify your config.yaml with your bot parameters, your bot will need a custom name,
a discord API token, and a command_prefix.
See [Configuration](#configuration) for more details

**See the [Appendix](#appendix) for more details on the config.yaml parameters.**

```powershell
# Activate the virtual environment
.\venv\Scripts\activate

# Run the bot
python main.py
```

#### Notes for Windows Users

Python 3.9 for windows may give you an error such as:

> error Microsoft Visual C++ 14.0 is required

Visit [this link](https://www.scivision.dev/python-windows-visual-c-14-required/) for more details and how to resolve the issue:

## Using the Bot

Once the bot is running you will be able to interact with it in multiple ways.

### Discord interface

Your bot will need to either have permissions to a text-channel in your discord server, or users will have to message the bot directly in order to interact with it. If your bot correctly has access to a text channel, you will should see it listed in the list of online users.

You can send your bot commands by typing: `<command prefix> command`. For example, if you wanted to play music and your bot's command prefix were !, you would type:

`!music play Daft Punk`

You can use `!help` to see the various commands and also use !help command to see the various subcommands under each command.

### Command Line Interface (CLI)

The CLI gives an administrator who is running the bot access to bot controls and commands without needing access to discord. When running the bot you will see a prompt like this:

```sh
The Galaxy Aces Bot: >>>
```

You can enter help at the prompt to list all the commands and perform various actions. Entering q or quit will shutdown the bot(s).

## Configuration

### Minimum Configuration

Your config.yaml file will at minimum need:

-   name
-   token
-   command_prefix

Before it is able to run.

### Permissions

Permissions allow you to configure which roles can use which commands for each feature. For example, if you wanted everyone to be able to use the insult command then you would have a single line with "@everyone" as the role under the permission insult. If you only wanted users with a certain role to use torment, you would list only that role under the permission torment. You can also list multiple roles if desired. The default if no roles are listed is to disallow the command.

Example:

```yaml
permissions:
  insult:
    - "@everyone"
  torment:
    - Server Booster
  untorment:
    - Server Booster
    - Admin

```

### Running Multiple Bots

To run multiple bots on your server simply add additional bot configuration to your config.yaml like so.
Keep in mind that each bot needs to have a unique token.
It is also recommended but not required that each bot have a unique command prefix.

```yaml
- name: The Galaxy Aces Bot
  token: this_bots_token
  command_prefix: "!"
  logging:
    enabled: True
    logging_level: DEBUG
  enabled_features:
    insult:
      enabled: True
      permissions:
        insult:
          - "@everyone"
        torment:
          - "@everyone"
        untorment:
          - "@everyone"
    music:
      enabled: True
      permissions:
        music:
          - "@everyone"
        play:
          - "@everyone"
        queue:
          - "@everyone"
        next:
          - "@everyone"
        previous:
          - "@everyone"
        stop:
          - "@everyone"
        pause:
          - "@everyone"
        resume:
          - "@everyone"
        current:
          - "@everyone"
        shuffle:
          - "@everyone"
        volume:
          - "@everyone"
        come:
          - "@everyone"
      local_path: /music
      search_frequency: 300
      audio_types:
        - .flac
        - .mp3
        - .mp4
        - .ogg
        - .wav
        - .wmv
    utility:
      enabled: True
      permissions:
        utility:
          - "@everyone"
        roll:
          - "@everyone"
- name: The Galaxy Aces Other Bot
  token: this_other_bots_token
  command_prefix: "."
  logging:
    enabled: True
    logging_level: DEBUG
  enabled_features:
    insult:
      enabled: True
      permissions:
        insult:
          - "@everyone"
        torment:
          - "Admin"
          - "Server Booster"
        untorment:
          - "Admin"
          - "Server Booster"
    music:
      enabled: True
      permissions:
        music:
          - "@everyone"
        play:
          - "@everyone"
        queue:
          - "@everyone"
        next:
          - "@everyone"
        previous:
          - "@everyone"
        stop:
          - "@everyone"
        pause:
          - "@everyone"
        resume:
          - "@everyone"
        current:
          - "@everyone"
        shuffle:
          - "@everyone"
        volume:
          - "@everyone"
        come:
          - "@everyone"
      local_path: /music
      search_frequency: 300
      audio_types:
        - .flac
        - .mp3
        - .mp4
        - .ogg
        - .wav
        - .wmv
    utility:
      enabled: True
      permissions:
        utility:
          - "@everyone"
        roll:
          - "@everyone"
```

## Appendix

### Parameter Descriptions for config.yaml

#### Core Bot Parameters

| Parameter      | Default Value(s) | Description                                                                                                                                                              |
| -------------- | :--------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| name           |      `null`      | A name for the bot. It can be unique if you want, but is not required. However it will be more difficult to distingush multiple bots if you are running multiple.        |
| token          |      `null`      | A discord developer API token. You can get one [here](https://discord.com/developers/applications)                                                                       |
| command_prefix |       `"!"`      | A single character which you will use to preface all commands for this bot e.g. `!music` _Note: It's best to wrap your command prefix in quotes to ensure compatability_ |
| logging        |     `NOTSET`     | The level of logging. Possible options: NOTSET, INFO, WARNING, ERROR, DEBUG                                                                                              |

#### Music Feature

| Parameter        |              Default Value(s)              | Description                                                                                                                                                                                                                                                                             |
| ---------------- | :----------------------------------------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| local_path       |                  `/music`                  | A system path pointing to a local library of music. Ideally the directory structure will be `local_path/Artists/Albums/songs` But any structure should work. The music feature will search this directory for songs which match the **audio_types** every **search_frequency** seconds. |
| search_frequency |                    `300`                   | How frequently you want the music feature to search for new music. This value is in seconds. Default is 300 seconds (5 minutes)                                                                                                                                                         |
| audio_types      | `.flac` `.mp3` `.mp4` `.ogg` `.wav` `.wmv` | The different audio formats you want the music feature to search for. These audio types must be readable by ffmpeg.                                                                                                                                                                     |

#### Shared Feature Parameters

| Parameter   | Default Value(s) | Description                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ----------- | :--------------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| permissions |    `@everyone`   | Permissions are setup on a command by command basis and each command can have zero or more roles associated with it. Under each command, you can add an additional role which will grant any users with that role access to use the feature. If no permissions are listed for a command, then that command will not be useable by any users. Special roles such as @everyone must be surrounded by double quotes: "@everyone" |
