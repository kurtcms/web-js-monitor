# Web Monitoring: Monitor a JavaScript Rendered Web Page for Updates

This Python app is containerised with [Docker Compose](https://docs.docker.com/compose/) for a modular and cloud native deployment that fits in any microservice architecture.

It does the following:

1. Use the Python libraries, [Requests](https://github.com/psf/requests) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/), to download a copy of the web page of interest and any JavaScript files that are referred to in the page;
2. Use the [hashlib](https://docs.python.org/3/library/hashlib.html) module to compute a SHA 256-bit checksum with the downloaded contents; and
3. Compare the checksum with a previous build, if one exists, and on mismatch save the checksum and a copy of the downloaded contents, before using the [smtplib](https://docs.python.org/3/library/smtplib.html) module to send a notification email to the predefined recipient if it is required. Otherwise if no previous checksum exists, save the checksum the rest of the downloaded contents for future matching and references.

A detailed walk-through is available [here](https://kurtcms.org/web-monitoring-monitor-a-javascript-rendered-web-page-for-updates/).

## Table of Content

- [Getting Started](#getting-started)
  - [Git Clone](#git-clone)
  - [Environment Variable](#environment-variables)
  - [Crontab](#crontab)
  - [Docker Container](#docker-container)
	  - [Docker Compose](#docker-compose)
	  - [Build and Run](#build-and-run)
  - [Standalone Python Script](#standalone-python-script)
    - [Dependencies](#dependencies)
    - [Usage and Option](#usage-and-option)
    - [Cron](#cron)
- [Checksum and the Downloaded Contents](#checksum-and-the-downloaded-contents)
- [Reference](#reference)

## Getting Started

Get started in three simple steps:

1. [Download](#git-clone) a copy of the app;
2. Create the [environment variables](#environment-variables) for email notification if needed and modify the [crontab](#crontab); and
3. [Docker Compose](#docker-compose) or [build and run](#build-and-run) the image manually to start the app, or alternatively run the Python script as a standalone service.

### Git Clone

Download a copy of the script with `git clone`. Be sure to pass the `--recurse-submodules` argument to initialise and update each submodule in the repository.

```shell
$ git clone --recurse-submodules https://github.com/kurtcms/web-js-monitor /app/web-js-monitor/
```

### Environment Variables

If email notification is required, the app expects the SMTPS port number, SMTP server address, the notification receiver email address, the notification sender email address and password as environment variables in a `.env` file in the same directory.

Create the `.env` file.

```shell
$ nano /app/web-js-monitor/.env
```

And define the variables accordingly.

```
EMAIL_SSL_PORT = 465
EMAIL_SMTP_SERVER = 'smtp.kurtcms.org'
EMAIL_SENDER = 'alert@kurtcms.org'
EMAIL_RECEIVER = 'noc@kurtcms.org'
EMAIL_SENDER_PASSWORD = '(redacted)'
```

### Crontab

By default the app is scheduled with [cron](https://linux.die.net/man/8/cron) to pull a copy of the web page and check for changes every 15 minutes, with `stdout` and `stderr` redirected to the main process for `Docker logs`.

Modify the `crontab` to feed in the URL of interest, and signify to the Python script whether email notification is needed. Change to a different schedule if required.

```shell
$ nano /app/web-js-monitor/crontab
```

And define the variables accordingly.

```
*/15 * * * * /usr/bin/python3 /app/web-js-monitor/web-js-monitor.py -u https://lookingglass.pccwglobal.com/ > /proc/1/fd/1 2>/proc/1/fd/2
#
# Usage: web-js-monitor.py [-e] -u <url>
#
# Option:
#   -h
#     Display usage
#   -e, --email
#     Send email notification on changes
#   -u, --url
#     The URL of interest
```

### Docker Container

Packaged as a container, the app is a standalone, executable package that may be run on Docker Engine. Be sure to have [Docker](https://docs.docker.com/engine/install/) installed.

#### Docker Compose

With Docker Compose, the app may be provisioned with a single command.

Install [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) with the [Bash](https://github.com/gitGNU/gnu_bash) script that comes with app.

```shell
$ chmod +x /app/web-js-monitor/docker-compose/docker-compose.sh \
    && /app/web-js-monitor/docker-compose/docker-compose.sh
```

Start the containers with Docker Compose.

```shell
$ docker-compose -f /app/web-js-monitor/docker-compose.yml up -d
```

Stopping the container is as simple as a single command.

```shell
$ docker-compose -f /app/web-js-monitor/docker-compose.yml down
```

#### Build and Run

Otherwise the Docker image can also be built manually.

```shell
$ docker build -t web-js-monitor /app/web-js-monitor/
```

Run the image with Docker once it is ready.

```shell
$ docker run -it --rm --name web-js-monitor web-js-monitor
```

### Standalone Python Script

Alternatively the `web-js-monitor.py` script may be deployed as a standalone service.

#### Dependencies

In which case be sure to install the following required libraries:

1. [Requests](https://github.com/psf/requests)
2. [Python-dotenv](https://github.com/theskumar/python-dotenv)
3. [Beautiful Soup](https://code.launchpad.net/~leonardr/beautifulsoup/bs4)

Install them with [`pip3`](https://github.com/pypa/pip):

```shell
$ pip3 install requests python-dotenv bs4
```

#### Usage and Option

The script reads the URL of interest from the `-u` argument and sends email notification on changes if the `-e` option is given.

```
Usage: web-js-monitor.py [-e] -u <url>

Option:
  -h
    Display usage
  -e, --email
    Send email notification on changes
  -u, --url
    The URL of interest
```

#### Cron

It may then be executed with a task scheduler such as [cron](https://linux.die.net/man/8/cron) that runs it once every 15 minutes for example.

```shell
$ (crontab -l; echo "*/15 * * * * /usr/bin/python3 /app/web-js-monitor/web-js-monitor.py -u https://lookingglass.pccwglobal.com/") | crontab -
```

## Checksum and the Downloaded Contents

The SHA 256-bit checksum and the rest of the downloaded contents will be saved as separate files on a `Docker volume` that is mounted in the same directory of the `docker-compose.yml` file on the Docker host. If the Python script is run as a standalone service, the files will be in the same directory of the script instead.

In any case, the files are stored under a directory by the URL of the web page of interest, with the checksum stored in a file directly under it and the rest of the downloaded contents in a nested directory named by the full date and time of the download to ease access.

```
.
└── url/
    ├── url-sha256hash
    └── YYYY-MM-DD-HH-MM-SS/
        ├── index.html
        ├── javaScript1.js
        ├── javaScript2.js
        └── javaScript3.js
```

## Reference

- [Requests Documentation](https://docs.python-requests.org/en/latest/)
- [Beautiful Soup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)