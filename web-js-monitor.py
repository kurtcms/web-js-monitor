import requests
import hashlib
import smtplib, ssl
from sys import path, argv
from os import mkdir
from datetime import datetime
from bs4 import BeautifulSoup

# Setting the error message for when this script is called with one too many argument or less
errinvarg = 'This Python script takes one argument of a valid URL'

class monitor:
    # Setting the variables that will be referred to throughout the class
    dt = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    name = ['index.html']
    script = 'script'
    src = 'src'
    htmlp = 'html.parser'
    dash = '-'
    slash = '/'
    shasuffix = '-sha256hash'

    sslp = 465
    smtp = 'smtp.gmail.com'
    sender = 'web.js.monitor@gmail.com'
    receiver = 'kurtcms@gmail.com'
    pw = '(redacted)'
    title = ' has been updated'
    body = 'Updates are stored in separated files'
    subject = 'Subject: '

    def __init__(self, url):
        # Setting the variables that depend on the inputted URL
        self.url = url
        self.msg = f'{self.subject}{url + self.title}\n{self.body}'
        self.dname = url.split(self.slash*2)[-1].split(self.slash)[0]
        self.hname = self.dname + self.shasuffix

        # Download a copy of the URL and raise a system exit on connection error
        try:
            page = requests.get(url)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        self.soup = BeautifulSoup(page.content, self.htmlp)

        self.sources = [self.soup.prettify()]

        # Download a copy of the external JavaScript files if any that are referred to in the page
        for j in self.soup.find_all(self.script):
            jsrc = j.get(self.src)
            if not jsrc == None:
                # Append the FQDN to the URL of the JavaScript file if it is missing and raise a system exit on connection error
                try:
                    if self.slash*2 in jsrc:
                        p = requests.get(jsrc)
                    else:
                        p = requests.get(url + jsrc if url[-1] == self.slash else url + self.slash + jsrc)
                except requests.exceptions.RequestException as e:
                    raise SystemExit(e)
                s = BeautifulSoup(p.content, self.htmlp)
                self.name.append(j.get(self.src).split(self.slash)[-1])
                self.sources.append(s.prettify())

        # Generate a SHA 256-bit checksum of the downloaded contents
        self.hash = hashlib.sha256(str.encode(str(self.sources))).hexdigest()

    def match(self):
        # Create a directory named by the sanitised URL under the directory of the script before checking the downloaded contents for update
        try:
            mkdir(path[0] + self.slash + self.dname)
        except FileExistsError:
            pass
        finally:
            self.wd = path[0] + self.slash + self.dname + self.slash

        # Call the __write method to output the SHA 256-bit checksum and a copy of the downloaded contents if a previous SHA 256-bit checksum file is not found
        try:
            with open(self.wd + self.hname ,'r') as f:
                # Call the __email method to send an email notification if the SHA 256-bit checksum does not match a previous one and the __write method to overwrite the SHA 256-bit checksum file with the latest one and output a copy of the downloaded contents
                if f.read() != self.hash:
                    self.__write()
                    self.__email()
        except FileNotFoundError:
            self.__write()

    def __write(self):
        # Output the SHA 256-bit checksum and the rest of the downloaded contents by overwriting existing ones or creating new files
        try:
            with open(self.wd + self.hname, 'x') as f:
                f.write(self.hash)
        except FileExistsError:
            with open(self.wd + self.hname, 'w') as f:
                f.write(self.hash)

        i = 0
        for n in self.name:
            with open(self.wd + n + self.dash + self.dt, 'x') as f:
                f.write(self.sources[i])
            i += 1

    def __email(self):
        # Send an email notification
        c = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp, self.sslp, context=c) as server:
            server.login(self.sender, self.pw)
            server.sendmail(self.sender, self.receiver, self.msg)

if len(argv) == 2:
    # Create the object and subsequently call its corresponding method for matching if one and precisely one argument is supplied and raise a system exit if otherwise
    w = monitor(argv[1])
    w.match()
else:
    raise SystemExit(errinvarg)
