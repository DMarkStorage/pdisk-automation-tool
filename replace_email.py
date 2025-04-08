import pandas as pd
import subprocess
import json 
import logging
from docopt import docopt
from prettytable import PrettyTable
logging.basicConfig(level=logging.INFO,  filename='logs.log', filemode='a', format='%(message)s  %(asctime)s', datefmt="%Y-%m-%d %T")
import csv, time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

__version__ = 'Beta 1'
__revision__ = '1.0'
__deprecated__ = False


all_not_ok = ['mmvdisk', 'pdisk', 'list', '--rg', 'all', '--not-ok']
replace = ['mmvdisk', 'pdisk', 'list', '--rg', 'all', '--replace']

list_pdisk = []
commands = []

def get_args():
	"""Function to get command line arguments.

	Defines arguments needed to run this program.

	:return: Dictionary with arguments
	:rtype: dict
	"""
	
	usage = """
	Usage:
        try.py --replace
        try.py --prepare
		try.py --dryrun
		try.py --email -e <EMAIL> 
		try.py --version
		try.py -h | --help

	Options:
		-h --help            Show this message and exit


	"""

	args = docopt(usage)
	return args	


def get_failed_pdisk(filename, command):
    with open(filename, 'r') as file:

        contents = file.read()

        if 'All pdisks are ok.' in contents:
            
            print(f"Command: {command} ---> All disk are OK!")
            logging.info(f"Command: {command} ---> Output: All disk are OK!")
            exit(1)

        elif 'No pdisks are marked for replacement.' in contents:
            print(f"Command: {command} ---> No pdisk are marked for replacement!")
            logging.info(f"Command: {command} ---> Output: No pdisk are marked for replacement!")
            exit(1)

        if 'declustered' in contents:
 
            contents = contents.replace('declustered', '')

        if 'mmvdisk: A lower priority value means a higher need for replacement.' in contents:
 
            contents = contents.replace('mmvdisk: A lower priority value means a higher need for replacement.', '')

    with open(filename, 'w') as file:
        file.write(contents)


    df = pd.read_csv(filename, sep='\s{2,}', engine='python')

    return df[["recovery group", "pdisk"]]

def command(command,filename,table):

    commands = ' '.join([str(elem) for elem in command])

    t = PrettyTable()
    t.field_names = ["Command: ",commands]
    t.add_row([' ', table])
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        output, error = process.communicate()

        if error:
            print(f"Command: {command} ---> Error: {error.decode('utf-8')}")
            exit(1)
        print(t)
        print(output.decode('utf-8'))
        with open(filename, 'w') as f:
            f.write(output.decode('utf-8'))
        
        return filename,commands
    
    except subprocess.CalledProcessError:
        return "Error running command."
    except FileNotFoundError:
        return "command not found."

def show_data(filename):
    with open(filename, "r") as f:
        json_data = f.read()

    data = json.loads(json_data)
    table = PrettyTable()
    table.field_names = ["Name", "RecoveryGroup", "state", "location", "hardware", "User location", "Server"]

    # Add rows to table
    for item in data:
        name = item["name"]
        recoveryGroup = item["recoveryGroup"]
        state = item["state"]
        location = item["location"]
        hardware = item["hardware"]
        user_loc = item["userLocation"]
        server = item["server"]



        table.add_row([name, recoveryGroup, state, location, hardware, user_loc, server])

    print(table)

def text_to_dict(text):
    d = {}
    if 'pdisk:' in text:
        text = text.replace('pdisk:', '')
    for line in text.split("\n"):
        
        if not line.strip():  # skip empty lines
            continue
        key, value = line.split("=")
        value = value.strip().strip("")
        key = key.strip()
        try:
            value = int(value)
        except ValueError:
            pass
        d[key] = value
    for key, value in d.items():
        if isinstance(value, str) and len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            d[key] = value[1:-1]
    return d

def create_file(filename, data):
    with open(filename, 'w') as f:

        json.dump(data, f, indent = 4)
    
    show_data(filename)
    
def get_pdisk_info(pdisk, group):

    output_ = subprocess.Popen(['mmvdisk', 'pdisk', 'list', '--rg', group, '--pdisk', pdisk, '-L'], stdout=subprocess.PIPE)
    output, error = output_.communicate()
    output = text_to_dict(output.decode('utf-8'))
    list_pdisk.append(output)

    
    
def replace_pdisk(args, pdisk, group, need_replace):
    

    command = ['mmvdisk', 'pdisk', 'replace ', '--prepare', '--rg', group, '--pdisk', pdisk]
    command = ' '.join([str(elem) for elem in command])
    commands.append(command)

    if args['--dryrun']:
        print(commands)
    elif args['--email']:
        send_emails(args['<EMAIL>'], need_replace)
    elif args['--prepare']:
        output_ = subprocess.Popen(['mmvdisk', 'pdisk', 'replace', '--prepare', '--rg', group, '--pdisk', pdisk], stdout=subprocess.PIPE)
        output, error = output_.communicate()
        
        if 'Reinsert carrier.' in output.decode('utf-8'):
            print(f"Successfully prepared pdisk for replace!\n Command: {command} --> OUTPUT: {output.decode('utf-8')} "  )
            logging.info(f"Successfully prepared pdisk for replace!\n Command: {command} --> OUTPUT: {output.decode('utf-8')}   ")

        else:
            print(f"Failed replacing pdisk!\n Command: {command} --> OUTPUT: {output.decode('utf-8')} ")
            logging.info(f"Failed replacing pdisk!\n Command: {command} --> OUTPUT: {output.decode('utf-8')} ")



    else:
        output_ = subprocess.Popen(['mmvdisk', 'pdisk', 'replace', '--recovery-group', group, '--pdisk', pdisk], stdout=subprocess.PIPE)
        output, error = output_.communicate()


        if 'not physically replaced with a new disk.' in output.decode('utf-8'):
            print(f"Failed replacing pdisk! Command: {command} --> Error: {output.decode('utf-8')}   ")
            logging.info(f"Failed replacing pdisk! Command: {command} --> Error: {output.decode('utf-8')}   ")

        else:
            print(f"Replacing pdisk! Command: {command} --> OUTPUT: {output.decode('utf-8')}   ")
            logging.info(f"Replacing pdisk! Command: {command} --> OUTPUT: {output.decode('utf-8')}   ")

   

def send_email(sender_email, sender_password, receiver_email, subject, message):


    # Create a multipart message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Add the message body
    msg.attach(MIMEText(message, "plain"))

    # Create SMTP session for sending the mail
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)

def send_emails(receiver_email, need_replace_disk):
    # Provide the necessary details
    sender_email = "your email address"
    sender_password = "your password"


    name = "Trial1"
    email = receiver_email
    subject = "Disk with issue"
    message = "Trial Message"

    send_email(sender_email, sender_password, email, subject, message)
    print(f"Email sent to {name} ({email})")

def display_state(dataframe, t_info):
    list_disk = []

    for index, row in dataframe.iterrows():
        if '--------' not in row['recovery group'] and '--------' not in row['pdisk']:
        
            output_ = subprocess.Popen(['mmvdisk', 'pdisk', 'list', '--rg', row['recovery group'], '--pdisk',  row['pdisk'], '-L'], stdout=subprocess.PIPE)
            output, error = output_.communicate()
            output1 = text_to_dict(output.decode('utf-8'))
            list_disk.append(output1)

    data_json = json.dumps(list_disk)

    data = json.loads(data_json)
    table = PrettyTable()
    table.field_names = ["Name", "RecoveryGroup", "state", "location", "hardware", "User location", "Server"]

    # Add rows to table
    for item in data:
        name = item["name"]
        recoveryGroup = item["recoveryGroup"]
        state = item["state"]
        location = item["location"]
        hardware = item["hardware"]
        user_loc = item["userLocation"]
        server = item["server"]

        table.add_row([name, recoveryGroup, state, location, hardware, user_loc, server])
    print(f"{t_info}")
    print(table)

    return data

def main(args):

    
    global replace
    all_not_ok_pdisk,command_ = command(all_not_ok,'not_ok_pdisk.txt','Disk not ok')
    all_replace_pdisk,command_ = command(replace,'replace_pdisk.txt','List of replace disks')

    first = get_failed_pdisk(all_not_ok_pdisk, command_)
    disk_not_ok = display_state(first,'List of Disks that are not ok')
    sec = get_failed_pdisk(all_replace_pdisk, command_)
    need_replace = display_state(sec,'List of disks needs replace')


    replace = ' '.join([str(elem) for elem in replace])
    commands.append(replace)
    print(f"List of pdisk needs to be replaced:\n Command: {commands}\n{sec}\n\t\t")
    logging.info(f"List of pdisk needs to be replaced:\n Command: {commands}\n{sec}\n\t\t")



    for index, row in sec.iterrows():
        if '--------' not in row['recovery group'] and '--------' not in row['pdisk']:
            replace_pdisk(args, row['pdisk'], row['recovery group'], need_replace)
            pdisk = row['pdisk']
            group =  row['recovery group']
            get_pdisk_info(pdisk, group)

    create_file('output1.txt', list_pdisk)

    
if __name__ == '__main__':
    ARGS = get_args()
    main(ARGS)



