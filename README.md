# Web Monitoring: Monitor a JavaScript Rendered Web Page for Updates

This Python script is designed to be executed by a task scheduler such as [cron](https://crontab.guru/) and it does the following:

1. Use the Python library, [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/), to download a copy of the web page of interest and any external JavaScript files that are referred to in the page.
2. Use the [hashlib](https://docs.python.org/3/library/hashlib.html) module to compute a SHA 256-bit checksum with the downloaded contents.
3. Compare the checksum with a previous build if one exists and on mismatch save the checksum and a copy of the downloaded contents before using the [smtplib](https://docs.python.org/3/library/smtplib.html) module to send a notification email to the predefined recipient. Otherwise if no previous build exists, save the checksum the rest of the downloaded contents for future matching and reference.

A detailed walk-though is available [here](https://kurtcms.org/web-monitoring-monitor-a-javascript-rendered-web-page-for-updates/).

![alt text](https://kurtcms.org/git/web-js-monitor/web-js-monitor-screenshot.png)
