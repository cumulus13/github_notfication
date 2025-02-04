import sys
from ctraceback import CTraceback
sys.excepthook = CTraceback()
from github import Github
import time
from pathlib import Path
from configset import configset
from rich.console import Console
console = Console()
from sendgrowl import Growl
from datetime import datetime

import os
import signal
from gntplib import Publisher, SocketCallback

class Callback(SocketCallback):
    def __init__(self, notification):
        SocketCallback.__init__(self, notification)
    def on_click(self, response):
        self.context.mark_as_read()

# Configuration
CONFIG = configset(str(Path.cwd() / 'gitnotify.ini') if (Path(__file__).parent / 'gitnotify.ini').is_file() else str(Path(__file__).parent / 'gitnotify.ini'))
GITHUB_ACCESS_TOKEN = CONFIG.get_config('auth', 'token') or os.getenv('GITHUB_TOKEN') or console.input(f"[white on red]TOKEN:[/] ")
if GITHUB_ACCESS_TOKEN and GITHUB_ACCESS_TOKEN.strip().lower() in ['q', 'quit', 'exit', 'x']: os.kill(os.getpid(), signal.SIGTERM)
ERROR = False
if not GITHUB_ACCESS_TOKEN:
    while 1:
        GITHUB_ACCESS_TOKEN = CONFIG.get_config('auth', 'token') or console.input(f"[#00FFFF bold]x|exit|q|quit = exit/quit[/] [white on red]TOKEN:[/] ")
        if GITHUB_ACCESS_TOKEN:
            if GITHUB_ACCESS_TOKEN.strip().lower() in ['q', 'quit', 'exit', 'x']:
                ERROR = True   
                break
            else:
                CONFIG.write_config('auth', 'token', GITHUB_ACCESS_TOKEN)
            break
else:
    CONFIG.write_config('auth', 'token', GITHUB_ACCESS_TOKEN)
    
if ERROR:
    os.kill(os.getpid(), signal.SIGTERM)
    
CHECK_INTERVAL = CONFIG.get_config('interval', 'seconds') or 60  # in seconds

def get_date():
    return datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f')

def mark_as_read(notification):
    notification.mark_as_read()
    
def notify(notification, host = None):
    host = host or CONFIG.get_config_as_list('growl', 'host') or ['127.0.0.1']
    
    if isinstance(host, list or tuple) and len(host) > 0:
        for h in host:
            # print("h:", h)
            NOTIFY = Publisher('Github Notify', ['New Notification'], icon = str(Path(__file__).parent / 'icon.png'), host = h if h not in ['127.0.0.1', 'localhost'] else None)
            try:
                NOTIFY.register()
            except Exception as e:
                console.log(f"[white on blue]Error registering !:[/] [white on red]{e}[/]")
                os.kill(os.getpid(), signal.SIGTERM)            
    elif not isinstance(host, list or tuple):
        NOTIFY = Publisher('Github Notify', ['New Notification'], icon = str(Path(__file__).parent / 'icon.png'), host = host if host not in ['127.0.0.1', 'localhost'] else None)
        try:
            NOTIFY.register()
        except Exception as e:
            console.log(f"[white on blue]Error registering !:[/] [white on red]{e}[/]")
            os.kill(os.getpid(), signal.SIGTERM)            
        
        NOTIFY.publish("New Notification", f"{notification.subject.title} ({notification.reason})", on_click = lambda: mark_as_read(notification))
    
def monitor(max_try = 2):
    console.print(f"[bold #00FFFF]{get_date()}[/] - [bold #FFFF00]START monitoring ...[/]")
    github_client = Github(GITHUB_ACCESS_TOKEN)
    notifications = github_client.get_user().get_notifications()
    notification_dones = []    
    NOTIFY = Publisher('Github Notify', ['New Notification'], icon = str(Path(__file__).parent / 'icon.png'))
    try:
        NOTIFY.register()
    except Exception as e:
        console.log(f"[white on blue]Error registering !:[/] [white on red]{e}[/]")
        os.kill(os.getpid(), signal.SIGTERM)            
    max_try = max_try or CONFIG.get_config('try', 'max') or 2
    for notification in notifications:
        if CONFIG.get_config_as_list('subject', 'exceptions') and list(filter(lambda k: k.lower() in notification.repository.full_name.lower(), CONFIG.get_config_as_list('subject', 'exceptions'))):
            console.print(f"[bold #FFAA00]{get_date()}[/] - [bold #00FFFF]{notification.subject.title}:[/] [bold #FFFF00]{notification.repository.full_name}[/] [link={notification.subject.url}]:point_right:[/]")
            if CONFIG.get_config('status', 'clear') == 1:
                notification_dones = []
                CONFIG.write_config('status', 'clear', '0')         
                if sys.platform == 'win32':
                    os.system('cls')
                else:
                    os.system('clear')
                    
            if not notification.subject.title in notification_dones:
                try:
                    NOTIFY.publish("New Notification", f"{notification.subject.title} ({notification.repository.full_name})", gntp_callback=Callback(notification), sticky = CONFIG.get_config('growl', 'sticky') or False)
                except Exception as e:
                    if not str(e).lower() == 'timed out':
                        console.print(f"[bold #FFAA00]{get_date()}[/] - [bold #00FFFF] [bold white on red]\[{e}][/] - {notification.subject.title}:[/] [bold #FFFF00]{notification.repository.full_name}[/]")
                        
                notification_dones.append(notification.subject.title)
        else:
            notification.mark_as_read()            
    console.print(f"[bold #00FFFF]{get_date()}[/] - [bold #FFAA00]END monitoring ...[/]")

def main():
    try:
        while True:
            try:
                monitor()
                time.sleep(CONFIG.get_config('interval', 'seconds') or CHECK_INTERVAL or 60)
            except KeyboardInterrupt:
                os.kill(os.getpid(), signal.SIGTERM)        
            except Exception as e:
                console.log(f"[white on red]{e}[/]")
                if "HTTPSConnectionPool" in str(e): console.log("[black on #FFFF00]re-connection ...[/]")
                time.sleep(5)
            
    except KeyboardInterrupt:
        os.kill(os.getpid(), signal.SIGTERM)        
    except Exception as e:
        console.log(f"[white on red]{e}[/]")
        
if __name__ == "__main__":
    # monitor()
    main()
