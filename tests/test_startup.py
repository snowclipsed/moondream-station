import pexpect
import logging
import shutil
import os
GLOBAL_TIMEOUT = 300

logging.basicConfig(filename='test_startup.log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def clean_files(folder = "$HOME/.local/share/MoondreamStation"):
    if os.path.exists(folder):
        logging.debug(f"Attempting to clean folder...{folder}")
        shutil.rmtree(folder)
    if not os.path.exists(folder):
        logging.debug(f"Successfully cleaned {folder}")
        return
    else:
        logging.debug(f"Folder was not cleaned.")

def start_server():
    child = pexpect.spawn('./moondream_station')
    logging.debug("Starting up Moondream Station...")
    child.expect('moondream>', timeout=30)
    return child

def end_server(child):
    # just check for exit message, don't wait for process to die, since bad shutdown in a known bug.
    child.sendline('exit')
    child.expect(r'Exiting Moondream CLI', timeout=10)
    
    # force close for now
    if child.isalive():
        child.close(force=True)
    
def check_health(child):
    child.sendline('health')
    child.expect('moondream>', timeout=30)
    health_prompt = child.before.decode()
    logging.debug("Health Check.")
    logging.debug(health_prompt)
    return child

def test_server_startup():
    clean_files()

    child = start_server()
    child = check_health(child)
    
    end_server(child)

test_server_startup()