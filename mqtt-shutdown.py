import os
import paho.mqtt.client as mqtt
import sys
import time
import signal
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

#####################################################
def shutdown():
    global shutdown_desired
    global shutdown_on_hold
    global shutdown_disabled

    if shutdown_desired:
        if shutdown_disabled:
            print("[S] Shutdown is disabled, ending shutdown routine.")
        elif shutdown_on_hold:
            print("[S] Shutdown is on hold, ending shutdown routine for now.")
        else:
            print("[S] Shutting down system.")
            os.system("poweroff")
    else:
        print("[S] Shutdown not desired, ending shutdown routine.")
#####################################################
def on_file_created(event):
    global tmp_dir
    global hold_file
    global disabled_file
    global shutdown_on_hold
    global shutdown_disabled

    if not event.src_path.startswith(tmp_dir + "/"):
        return 1

    changed_file = event.src_path[len(tmp_dir)+1:]

    if changed_file == hold_file:
        print("[S] Shutdown on hold by anonymous hold file.")
        shutdown_on_hold = True
    elif changed_file == disabled_file:
        print("[S] Shutdown disabled by disable file.")
        shutdown_disabled = True
    elif changed_file.startswith(hold_file):
        print("[S] Shutdown on hold by named hold file.")
        shutdown_on_hold = True
    else:
        return 1

def on_file_deleted(event):
    global tmp_dir
    global hold_file
    global disabled_file
    global shutdown_on_hold
    global shutdown_disabled
    has_change = False

    if event.src_path == tmp_dir + "/" + disabled_file:
        print("[S] Shutdown enabled by removal of disable file.")
        shutdown_disabled = False
        has_change = True
    else:
        has_anon = False
        has_named = False
        for f in os.listdir(tmp_dir):
            if f == hold_file:
                has_anon = True
            elif f.startswith(hold_file):
                has_named = True
        if event.src_path == tmp_dir + "/" + hold_file:
            if not has_named:
                print("[S] Shutdown hold stopped by removal of anonymous hold file.")
                shutdown_on_hold = False
                has_change = True
            else:
                print("[S] Shutdown hold from anonymous hold file removed.")
        elif not has_named and shutdown_on_hold:
            if not has_anon:
                print("[S] Shutdown hold stopped by removal of named hold file.")
                shutdown_on_hold = False
                has_change = True
            else:
                print("[S] Shutdown hold from a named hold file removed.")

    if has_change:
        shutdown()
#####################################################
def on_message(client, usr, msg):
    global shutdown_desired

    recv = msg.payload.decode("utf-8")
    topic = msg.topic
    print("[R] Received", recv, "on", topic)
    if recv == "OFF" or recv == "Offline":
        print("    Received expected message for shutdown, running shutdown routine...")
        shutdown_desired = True
        shutdown()
    elif recv == "ON" or recv == "Online":
        print("    Received expected message for start, cancelling shutdown...")
        shutdown_desired = False

#####################################################
def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscription")
#####################################################
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        print("[C] Connected OK")
        result=client.subscribe(topic, qos)
        print("[T] Subscribed to topic", topic)
    else:
        print("[C] Bad connection: Returned code=", rc)
#####################################################
def on_disconnect(client, userdata, rc):
    print("[C] Disconnected: ", rc)
    client.connected_flag = False
#####################################################
def interrupt_handler(sig, frame):
    print("Received interrupt, terminating...")
    client.disconnect()
    observer.stop()
    observer.join()
    exit()
#####################################################

# Get iterator for command line arguments and skip first item (script call)
arg_it = iter(sys.argv)
next(arg_it)

# Flags for shutdown execution
shutdown_desired = False
shutdown_on_hold = False
shutdown_disabled = False
tmp_dir = "/etc/mqtt-integration/shutdown-service"
disabled_file = "disable"
hold_file = "hold"

for f in os.listdir(tmp_dir):
    if not shutdown_disabled and f == disabled_file:
        print("[S] Shutdown initially disabled.")
        shutdown_disabled = True
    if not shutdown_on_hold and (f == hold_file or f.startswith(hold_file)):
        print("[S] Shutdown initially on hold.")
        shutdown_on_hold = True

# Listen to interrupt and termination
signal.signal(signal.SIGINT, interrupt_handler)
signal.signal(signal.SIGTERM, interrupt_handler)

# Set default values
broker_address="localhost"
port=1883
qos=1
topic=None

user_set = False
password_set = False

# Parse environment variables
topic = os.environ.get('MQTT_TOPIC')
broker_address = os.getenv('MQTT_BROKER', broker_address)
port = int(os.getenv('MQTT_PORT', port))
qos = int(os.getenv('MQTT_QOS', qos))
user = os.environ.get('MQTT_USER')
password = os.environ.get('MQTT_PASSWORD')

if user != None:
    user_set = True

if password != None:
    password_set = True

#################################################
# Parse command line arguments
#################################################
for arg in arg_it:
    if arg == '-a':
        broker_address=next(arg_it)

    elif arg == '-q':
        qos=next(arg_it)

    elif arg == '-p':
        port = next(arg_it)

    elif arg == '-u':
        user = next(arg_it)
        user_set = True

    elif arg == '-pw' or arg == '-P':
        password = next(arg_it)
        password_set = True

    elif arg == "-t":
        topic = next(arg_it)

    elif arg == '-f':
        import configparser
        configParser = configparser.RawConfigParser()
        configParser.read(next(arg_it))

        if configParser.has_option('settings', 'address'):
            broker_address = configParser.get('settings', 'address')

        if configParser.has_option('settings', 'qos'):
            qos = configParser.getint('settings', 'qos')

        if configParser.has_option('settings', 'port'):
            port = configParser.getint('settings', 'port')

        if configParser.has_option('settings', 'user'):
            user = configParser.get('settings', 'user')
            user_set = True

        if configParser.has_option('settings', 'password'):
            password = configParser.get('settings', 'password')
            password_set = True

        if configParser.has_option('settings', 'topic'):
            topic = configParser.get('settings', 'topic')

    elif arg == '-h':
        print("Usage:", sys.argv[0], "[-f <broker-config-file>] [-a <ip>] [-p <port>] [-q <qos>] [-u <username>] [-pw <password>]")
        exit()

    else:
        print("Use \'", sys.argv[0], " -h\' to print available arguments.")
        exit()

if topic == None:
    print("Topic needs to be set for listening")
    exit()

# User and password need to be set both or none
if user_set != password_set:
    print("Please set either both username and password or none of those")
    exit()

############################################
# Watch file changes for hold/disable
############################################
patterns = "*"
ignore_patterns = ""
ignore_directories = True
case_sensitive = True
event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
event_handler.on_created = on_file_created
event_handler.on_deleted = on_file_deleted
#event_handler.on_modified = on_file_modified
#event_handler.on_moved = on_file_moved
go_recursively = False
observer = Observer()
observer.schedule(event_handler, tmp_dir, recursive=go_recursively)
observer.start()

############################################
# Set up MQTT client
############################################
client = mqtt.Client()
client.on_message = on_message
#client.on_subscribe = on_subscribe
client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Set username and password
if user_set and password_set:
    client.username_pw_set(user, password)

# Connect to broker
client.connect(broker_address, port)
# Start client loop (automatically reconnects after connection loss)
client.loop_forever()
