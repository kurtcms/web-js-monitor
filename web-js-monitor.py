import requests
import smtplib, ssl
from sys import path, argv
from getopt import getopt, GetoptError
from textwrap import dedent
from hashlib import sha256
from os import mkdir, environ
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from bs4 import BeautifulSoup

class monitor:
    ERR_USAGE = '''\
    Usage: web-js-monitor.py [-e] -u <url>

    Option:
      -h
        Display usage
      -e, --email
        Send email notification for changes
      -u, --url
        The URL of interest
    '''
    ERR_USAGE = dedent(ERR_USAGE)
    '''
    Usage example of this script
    '''

    ERR_INVALID_ENV = 'Problem locating the .env file'
    '''
    Error message to display when python-dotenv fails to read
    environment variables
    '''

    def __init__(self, argv):
        '''
        Read the argument(s) supplied and set variables depending
        on their values
        '''
        try:
            opts, args = getopt(argv, 'heu:',['email', 'url='])
        except GetoptError:
            '''
            Raise a system exit with the script usage
            on error reading the arguments
            '''
            raise SystemExit(self.ERR_USAGE)

        self.email_noti = False
        for opt, arg in opts:
            if opt == '-h':
                raise SystemExit(self.ERR_USAGE)
            elif opt in ('-e', '--email'):
                self.email_noti = True
            elif opt in ('-u', '--url'):
                self.url = arg

        if not hasattr(self, 'url'):
            '''
            Raise a system exit with the script usage in the
            absence of an URL supplied by the -u or --url argument
            '''
            raise SystemExit(self.ERR_USAGE)

        if self.email_noti == True:
            '''
            Construct the email message and read environment variables
            with python-dotenv if email notification is requested
            '''
            self.email_msg = f'''\
                Subject: {self.url} has been updated\n
                Updates are stored in separated files'''
            self.email_msg = dedent(self.email_msg)

            if load_dotenv(find_dotenv()) == False:
                '''
                Raise a system exit on error reading the
                environment variables
                '''
                raise SystemExit(self.ERR_INVALID_ENV)

            try:
                '''
                Read and set the environment variables needed for
                email notification
                '''
                self.email_sslp = environ['EMAIL_SSL_PORT']
                self.email_smtp = environ['EMAIL_SMTP_SERVER']
                self.email_sender = environ['EMAIL_SENDER']
                self.email_receiver = environ['EMAIL_RECEIVER']
                self.email_sender_pw = environ['EMAIL_SENDER_PASSWORD']
            except KeyError as e:
                '''
                Raise a system exit on error reading the environment variables
                '''
                raise SystemExit(e)

        '''
        Download a copy of the URL and raise a system exit
        on connection error
        '''
        try:
            page = requests.get(self.url)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        self.url_soup = BeautifulSoup(page.content, 'html.parser')
        self.url_sources = self.url_soup.prettify()

        '''
        Download a copy of the external JavaScript files if any
        that are referred to in the page
        '''
        self.page_dict = {}
        self.page_dict['index.html'] = self.url_sources
        for js in self.url_soup.find_all('script'):
            js_src_url = js.get('src')
            if not js_src_url == None:
                '''
                Append the FQDN to the URL of the JavaScript file if
                it is missing and download a copy of it. Raise a system
                exit on connection error.
                '''
                try:
                    if '//' in js_src_url:
                        js_file = requests.get(js_src_url)
                    else:
                        js_file = requests.get(self.url + js_src_url
                            if self.url[-1] == '/'
                            else self.url + '/' + js_src_url)
                except requests.exceptions.RequestException as e:
                    raise SystemExit(e)

                js_key = js_src_url.split('/')[-1]
                js_soup = BeautifulSoup(js_file.content, 'html.parser')
                self.page_dict[js_key] = js_soup.prettify()

        '''
        Generate a SHA 256-bit checksum of the downloaded contents
        '''
        self.page_dict_value = ''
        for each in self.page_dict:
            self.page_dict_value += self.page_dict[each]

        self.page_dict_value_hash = sha256(self.page_dict_value.encode()
                                        ).hexdigest()

        '''
        Set the file name for the SHA 256-bit checksum file
        '''
        self.dir_name_url_domain = self.url.split('//')[-1].split('/')[0]
        self.file_name_url_sources_hash = self.dir_name_url_domain \
                                            + '-sha256hash'

    def match(self):
        '''
        Call the __write method to write the SHA 256-bit checksum
        and a copy of the downloaded contents if a previous checksum
        is not found. Otherwise read and match the previous checksum
        against the current one and on mismatch call the __write method
        to overwrite the checksum file and write a copy of the downloaded
        contents. Call the __email method to send an email notification
        if it is requested
        '''

        try:
            mkdir(path[0] + '/' + self.dir_name_url_domain)
        except FileExistsError:
            pass
        finally:
            self.working_dir = path[0] + '/' + self.dir_name_url_domain + '/'

        try:
            with open(self.working_dir \
            + self.file_name_url_sources_hash,'r') as f:
                if f.read() != self.page_dict_value_hash:
                    self.__write()
                    if self.email_noti == True:
                        self.__email()
        except FileNotFoundError:
            self.__write()

    def __write(self):
        '''
        Write the SHA 256-bit checksum in a directory named by the
        sanitised URL and the rest of the downloaded contents in a
        nested directory named by the full date and time now to
        ease access
        .
        └── url/
            ├── url-sha256hash
            └── YYYY-MM-DD-HH-MM-SS/
                ├── index.html
                ├── javaScript1.js
                ├── javaScript2.js
                └── javaScript3.js
        '''
        try:
            with open(self.working_dir \
            + self.file_name_url_sources_hash, 'x') as f:
                f.write(self.page_dict_value_hash)
        except FileExistsError:
            with open(self.working_dir \
            + self.file_name_url_sources_hash, 'w') as f:
                f.write(self.page_dict_value_hash)

        time_now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        try:
            working_dir_time_now = self.working_dir + time_now + '/'
            mkdir(working_dir_time_now)
        except FileExistsError:
            pass

        for each in self.page_dict:
            with open(working_dir_time_now + each, 'x') as f:
                f.write(self.page_dict[each])

    def __email(self):
        '''
        Send an email notification
        '''
        ssl_context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.email_smtp, self.email_sslp,
        context=ssl_context) as server:
            server.login(self.email_sender, self.email_sender_pw)
            server.sendmail(self.email_sender, self.email_receiver,
                            self.email_msg)

if __name__ == '__main__':
    '''
    Create the object and subsequently call its corresponding
    method for matching
    '''
    web = monitor(argv[1:])
    web.match()
