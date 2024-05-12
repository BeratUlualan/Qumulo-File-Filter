
import datetime
import json
import os
import logging
import pathlib
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Logging Details
logging.basicConfig(filename='file_filter.log', level=logging.INFO,
    format='%(asctime)s,%(levelname)s,%(message)s')

# Time settings for Snapshot creation
t = datetime.datetime.now() + datetime.timedelta(hours=2)
expiration_time = t.isoformat("T") +"Z"

#  Qumulo Python libraries
try:
    import qumulo
    from qumulo.rest_client import RestClient
    from qumulo.lib.auth import Credentials
    import qumulo.lib.identity_util as id_util
except ImportError as error:
    logging.error(
        "Unable to import the required Qumulo api bindings. Please run the following command: pip3 install qumulo_api"
    )
    sys.exit()

# Read credentials
# Read and parse JSON credentials
with open('cluster_credentials.json', 'r') as json_file:
    cluster_credentials = json.load(json_file)


# Function to initialize and return a RestClient object
def initialize_rest_client(credentials):
    if credentials['access_token']:
        return RestClient(credentials['cluster_address'], credentials['port_number'], Credentials(credentials['access_token']))
    elif credentials['username'] and credentials['password']:
        client = RestClient(credentials['cluster_address'], credentials['port_number'])
        client.login(credentials['username'], credentials['password'])
        return client
    else:
        raise ValueError("Invalid credentials")

# Read and parse JSON credentials
with open('cluster_credentials.json', 'r') as json_file:
    cluster_credentials = json.load(json_file)

# Initialize RestClient and log connection
try:
    rc = initialize_rest_client(cluster_credentials)
    logging.info(f"Connected to {cluster_credentials['cluster_address']}")
except Exception as e:
    logging.error(f"Connection failed: {e}")
    sys.exit(1)


# File filter configurations
db_directory = cluster_credentials['main_directory']
quarantine_directory = cluster_credentials['quarantine_directory']
credentials_file = cluster_credentials['credentials_file']


# # #Email Settings
# smtp_server = cluster_credentials['smtp_server']
# smtp_port = cluster_credentials['smtp_port']
# domain = cluster_credentials['domain']
# mail_server = smtplib.SMTP(smtp_server, int(smtp_port))
# mail_server.starttls()
# email_username = cluster_json_object['email_username']
# email_password = cluster_json_object['email_password']
# mail_server.login(email_username, email_password)


# Read and parse JSON credentials
with open('policy_credentials.json', 'r') as json_file:
    policy_credentials = json.load(json_file)


# # Email Function for Sending Warning Message to The User Who Created a Banned File
# def mail_send(username, new_file_path, email_subject, email_message):
#     mail_msg = MIMEMultipart()
#     mail_msg['From'] = email_username
#     mail_msg['Subject'] = email_subject
#     mail_message = "<p>Dear " + username + ",</p><p>" + email_message + "</p>" + new_file_path
#     mail_msg.attach(MIMEText(mail_message, 'html'))

#     if send_mail_user == True and send_mail_admin == True:
#         mail_msg['To'] = admin_email + ";" + username + "@" + domain
#         mail_server.send_message(mail_msg)
#     else:
#         if send_mail_admin == True :
#             mail_msg['To'] = admin_email
#             mail_server.send_message(mail_msg)
#         else:
#             pass
#     return ()

def parse_file_extension(rc, new_file_path):
        new_filename, new_file_extension = os.path.splitext(new_file_path)
        if "." + file_extension.lower() == new_file_extension.lower():
            try:
                new_file_id = rc.fs.get_file_attr(new_file_path)['id']
                new_file_directory = pathlib.Path(new_file_path).parent.absolute()
                excepted_directory_file = 0
                for excepted_directory in exception_dir_path:
                    if str(new_file_directory).startswith(excepted_directory):
                        excepted_directory_file = 1
                    if excepted_directory_file == 0:
                        file_name_only = os.path.basename(new_file_path)
                        logging.info('A new file was found. File name: {}'.format(file_name_only))
                        new_file_directory_structure = str(new_file_directory).split('/')
                        directory_check = quarantine_directory
                        for n in range(len(new_file_directory_structure)):
                            if new_file_directory_structure[n]:
                                directory_check_1 = directory_check + "/" + str(new_file_directory_structure[n])
                                try:
                                    file_id = rc.fs.get_file_attr(directory_check_1)['id']
                                except qumulo.lib.request.RequestError:
                                    file_id = "null"
                                    rc.fs.create_directory(new_file_directory_structure[n], directory_check)
                                directory_check = directory_check_1
                        # Copy
                        copy_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
                        file_name_timestamp = file_name_only + "." + copy_time
                        rc.fs.create_file(file_name_timestamp, directory_check)
                        target_path = quarantine_directory + new_file_path + "." + copy_time
                        rc.fs.copy(source_path=new_file_path, target_path=target_path)
                        logging.info('{} file was copied to {}'.format(file_name_only, target_path))
                        file_acl = rc.fs.get_acl_v2(new_file_path)
                        rc.fs.set_acl_v2(file_acl, target_path)

                        owner_sid = rc.fs.get_file_attr(new_file_path)['owner_details']['id_value']
                        #username = rc.ad.sid_to_username_get(sid=owner_sid)
                        #username = rc.auth.expand_identity(id_util.Identity(owner_sid))['id']['name'].split('\\',1)[1]
                        # mail_send(username, new_file_path, email_subject, email_message)

                        rc.fs.delete(new_file_path)
                        logging.info('{} file was deleted'.format(new_file_path))
                    else:
                        logging.info(
                            '{} file is in a excepted directory. This file won\'t be move to the quarantine directory.'.format(
                                new_file_path))
            except: 
                        logging.info('{} file has already been deleted'.format(new_file_path))
    
            
def snapshot_operations(rc,policy_name):
    rc.snapshot.create_snapshot(name=policy_name, expiration=expiration_time, path=directory_path)
    snapshots = rc.snapshot.list_snapshots()
    snapshot_id_list = []
    sorted_snapshot_id_list = []

    for snapshot in snapshots['entries']:
        if snapshot['name'].endswith(policy_name):
            snapshot_id_list.append(snapshot['id'])
    sorted_snapshot_id_list = sorted(snapshot_id_list)

    newer_snapshot_id = sorted_snapshot_id_list[-1]
    logging.info('A new snapshot was created. snapshot ID is {} for {}'.format(newer_snapshot_id, directory_path))

    older_snapshot_id = sorted_snapshot_id_list[-2]

    created_files = rc.snapshot.get_snapshot_tree_diff(newer_snapshot_id, older_snapshot_id)
    logging.info(
        'New files were listed with Qumulo SnapDiff API for {} - {}'.format(newer_snapshot_id, older_snapshot_id))
    return (created_files)


media_file_list = []
executable_file_list = []
custom_file_list = []

with open(os.path.join("./config/file_types.json")) as type_file:
    file_types = json.load(type_file)
    media_file_list = file_types['media_files']
    executable_file_list = file_types['executable_files']

for policy in policy_credentials:
    directory_path = policy['directory_path']
    exception_dir_path = policy['exception_dir_path']
    policy_name = policy['policy_name']
    send_mail_admin = policy['send_mail_admin']
    admin_email = policy['admin_email']
    send_mail_user = policy['send_mail_user']
    email_subject = policy['email_subject']
    email_message = policy['email_message']

    banned_formats = []
    media_files = policy['media_files']
    if media_files:
        for file_type in media_file_list:
            banned_formats.append(file_type)

    executable_files = policy['executable_files']
    if executable_files:
        for file_type in executable_file_list:
            banned_formats.append(file_type)

    custom_files = policy['custom_files']
    if custom_files:
        custom_file_list = policy['custom_file_types']
        for file_type in custom_file_list:
            banned_formats.append(file_type)

    delta_files = snapshot_operations(rc, policy_name)
    if delta_files['entries']:
        logging.info(f'File extension scan job has started for {directory_path} directory')
        for file in delta_files['entries']:
            if file['op'] == "CREATE":
                new_file = file['path']

                file_type = rc.fs.get_file_attr(new_file)['type']
                if file_type == "FS_FILE_TYPE_DIRECTORY":
                    logging.info(f'A new directory was found. Directory name: {new_file}')
                    for file_extension in banned_formats:
                        for entry in rc.fs.tree_walk_preorder(new_file):
                            new_file_path = entry['path']
                            parse_file_extension(rc, new_file_path)
                elif file_type == "FS_FILE_TYPE_FILE":
                    for file_extension in banned_formats:
                        new_file_path = new_file
                        parse_file_extension(rc, new_file_path)
            else:
                logging.info('There is no more new created file or directory')
    else:
        logging.info('There is no new created file or directory')
