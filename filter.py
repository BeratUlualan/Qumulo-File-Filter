import qumulo
import datetime
import json
import os
import logging
import pathlib
import json
from qumulo.rest_client import RestClient

# Logging Details
logging.basicConfig(filename='file_filter.log', level=logging.INFO,
    format='%(asctime)s,%(levelname)s,%(message)s')

# Read credentials
json_file = open('credentials.json','r')
json_data = json_file.read()
json_object = json.loads(json_data)

# Parse cluster credentials
cluster_address = json_object['cluster_address']
port_number = json_object['port_number']
username = json_object['username']
password = json_object['password']

# File filter configurations
db_directory = json_object['db_directory']
quarantine_directory = json_object['quarantine_directory']
credentials_file = json_object['credentials_file']

# Connect to the cluster
rc = RestClient(cluster_address, port_number)
rc.login(username, password)
logging.info('Connection established with {}'.format(cluster_address))

def parse_file_extension(new_file_path):
    new_filename, new_file_extension = os.path.splitext(new_file_path)
    if "."+file_extension.lower() == new_file_extension.lower():
        new_file_directory = pathlib.Path(new_file_path).parent.absolute()
        excepted_directory_file = 0
        for excepted_directory in directory_exceptions:
            if str(new_file_directory).startswith(excepted_directory):
                excepted_directory_file = 1
            if excepted_directory_file == 0:
                file_name_only = os.path.basename(new_file_path)
                logging.info('A new file was found. File name: {}'.format(file_name_only))
                new_file_directory_structure = str(new_file_directory).split('/')
                directory_check = quarantine_directory
                for n in range(len(new_file_directory_structure)):
                    if new_file_directory_structure[n]:
                        directory_check_1 = directory_check +"/"+str(new_file_directory_structure[n])
                        try:
                            file_id = rc.fs.get_file_attr(directory_check_1)['id']
                        except qumulo.lib.request.RequestError:
                            file_id = "null"
                            rc.fs.create_directory(new_file_directory_structure[n], directory_check)
                        directory_check = directory_check_1
                # Copy
                copy_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
                file_name_timestamp = file_name_only + "." + copy_time
                rc.fs.create_file(file_name_timestamp,directory_check)
                target_path = quarantine_directory + new_file_path + "." + copy_time
                rc.fs.copy(source_path=new_file_path,target_path=target_path)
                logging.info('{} file was copied to {}'.format(file_name_only,target_path))
                file_acl = rc.fs.get_acl_v2(new_file_path)
                rc.fs.set_acl_v2(file_acl,target_path)
                rc.fs.delete(new_file_path)
                logging.info('{} file was deleted'.format(new_file_path))
            else:
                logging.info('{} file is in a excepted directory. This file won\'t be move to the quarantine directory.'.format(new_file_path))

def snapshot_operations(policy_name):
    rc.snapshot.create_snapshot(policy_name,'','7days',search_directory)
    snapshots = rc.snapshot.list_snapshots()
    snapshot_id_list = []
    sorted_snapshot_id_list = []

    for individual_snapshot in snapshots['entries']:
        if policy_name == individual_snapshot['name']:
            snapshot_id_list.append(individual_snapshot['id'])
    sorted_snapshot_id_list = sorted(snapshot_id_list)

    newer_snapshot_id = sorted_snapshot_id_list[-1]
    logging.info('A new snapshot was created. snapshot ID is {} for {}'.format(newer_snapshot_id, search_directory))

    older_snapshot_id = sorted_snapshot_id_list[-2]

    created_files = rc.snapshot.get_snapshot_tree_diff(newer_snapshot_id,older_snapshot_id)
    logging.info('New files were listed with Qumulo SnapDiff API for {} - {}'.format(newer_snapshot_id,older_snapshot_id))        
    return(created_files)

with open(os.path.join(db_directory,credentials_file)) as json_file:
    data = json.load(json_file)
    logging.info('Configurations has been taken from {}{}'.format(db_directory,credentials_file))

    file_filtering_values = data['file_filtering']

    for r in range(len(file_filtering_values)):
        search_directory = file_filtering_values[r]['search_directory']
    
        directory_exceptions = file_filtering_values[r]['directory_exceptions']
        banned_formats = file_filtering_values[r]['banned_format']
        policy_name = file_filtering_values[r]['snapshot_name']

        created_files = snapshot_operations(policy_name)
        if created_files['entries']: 
            logging.info('File extension scan job has started for {} directory'.format(search_directory))    
            for individual_file in created_files['entries']:
                if individual_file['op'] == "CREATE":
                    new_file = individual_file['path']
 
                    file_type = rc.fs.get_file_attr(new_file)['type']
                    if file_type == "FS_FILE_TYPE_DIRECTORY":
                        logging.info('A new directory was found. Directory name: {}'.format(new_file))
                        for file_extension in banned_formats:
                            for entry in rc.fs.tree_walk_preorder(new_file):
                                new_file_path = entry['path']
                                parse_file_extension(new_file_path)
                    elif file_type == "FS_FILE_TYPE_FILE":
                        for file_extension in banned_formats:
                            new_file_path = new_file
                            parse_file_extension(new_file_path)
                '''
                else:
                    logging.info('There is no new created file or directory under {}'. format(search_directory))
                '''
        else:
            logging.info('There is no new created file or directory')
