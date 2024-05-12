# Qumulo-File-Filter

This script can help Qumulo customer who wants to filter specific file types and move them a quarantine directory. It can also inform the file owner and Qumulo admins about this filtering operations via email.  

## Installation
1. Copy **file_filter.py**, **config**,  **policy_credentials.json**, and **cluster_credentials.json** files into a folder in a machine (Linux, MacOS, Windows) which has **Qumulo Python SDK**. If you haven't deployed it yet, please follow the additional steps section below. 
2. Edit the **cluster_credentials.json**  file with your Qumulo cluster credentials. 
```sh
{
	"cluster_address": "CLUSTER HOSTNAME or IP ADDRESS",
	"port_number": 8000,
	"username": "USERNAME",
	"password": "PASSWORD",
	"access_token": "ACCESS_TOKEN",
	"main_directory": "/opt/Qumulo/",
	"quarantine_directory": "/quarantine",
	"credentials_file": "credentials.json",
	"smtp_server": "SMTP SERVER",
	"smtp_port": 587,
	"domain": "LOCAL DOMAIN"
}
```
`quarantine_directory` is the directory that you can store the unauthorized files temporarily in the cluster. Create this directory before you run the **file_filter.py** script. 
If you need a username and password for e-mail settings, please append below parameters in to this file. 
```sh
"email_username": "E-MAIL ADDRESS", 
"email_password": "E-MAIL PASSWORD"
```
3. Add a new policy for each top directory into the **policy_credentials.json** file.
```sh
[{
	"policy_name": "POLICY NAME",
	"directory_path": "DIRECTORY PATH",
	"exception_dir_path": ["none"],
	"send_mail_admin": true,
	"admin_email": "ADMIN E-MAIL ADDRESS",
	"send_mail_user": true,
	"email_subject": "Unauthorized File Matching",
	"email_message": "The system detected that your user saved a banned file format on file storage. The below file type is not permitted on the system. The file was removed from the file storage.", 
	"executable_files": true, 
	"custom_files": true, 
	"custom_file_types": ["jpg", "txt", "bmp"] 
}]
```
- If you don't want to send an e-mail to Qumulo admin user please set`"send_mail_admin": false`. You can leave empty `"admin_email": ""`, if send_mail_admin is false
- If you don't want to send an e-mail to the file owner please set`"send_mail_user": false`. 
- You can write your own email subject and message with editing `email_subject` and `email_message` definitions. 
- If you want to filter the pre-defined media and executable files, please set `media_files` and `executable_files` definitions `true`. Otherwise, you can set them `false`
- If you want to filter more file type, you can use `custom_file_types` definition for this purpose. You need to set `custom_files` definitions `true`. Otherwise, you can set it `false`

4. Edit the **file_type.json** file inside the **config** directory which has the pre-defined media and executable file types. You can add new file media and executable files into this files. Other files can be defined in the **policy_credentials.json** file as we mentioned above.
```sh
{
	"media_files": ["mp1", "mp2", "mp3", "mp4", "mpa", "avi", "mov", "mpe", "mpeg", "mpg", "swf", "mid", "asx", "wma", "wmv"],
	"executable_files": ["wim", "zoo", "sit", "eml", "msg", "oft", "ost", "pst", "bat", "cmd", "com", "exe", "inf", "js", "msi", "msp", "ocx", "ps1", "vb", "vbs", "wsf", "wsh", "jse", "acm", "dll", "ocx", "sys", "vxd", "asp", "aspx", "css", "dhtml", "php"]
}
```
## How it works
This script can help Qumulo customer who wants to filter specific file types and move them a quarantine directory. It can also inform the file owner and Qumulo admins about this filtering operations via email.  

Qumulo API capabilities allow you to write your own automation until Qumulo announces native automation for this purpose. 

**file_filter.py** script uses Qumulo's SnapDiff API (https://care.qumulo.com/hc/en-us/articles/360004815093-Snapshots-Identify-File-Changes-between-Snapshots) for identifying new created files and folders. This API call gives this list easily without any tree walk activity and also it can create a snapshot to protect files from any unwanted file movement activities. 

You can change the duration period of the snapshots with editing below line in the **file_filter.py**.

```rc.snapshot.create_snapshot(policy_name, '', '2hours', directory_path)``` 

Duration after which to expire the snapshot, in format **quantity** **units**, where **quantity** is a positive integer less than 100 and **units** is one of **months, weeks, days, hours, minutes**, e.g. > 5days or 1hours.

The script check their file extensions and identify unauthorized files. If you want to create another pre-defined file type set, please add this into the **file_type.json** and you need to write additional lines like below into the **file_filter_py** file. 

```sh
.......
executable_file_list = []
custom_file_list = []
new_file_list = []
....
....
media_file_list = file_types['media_files']
executable_file_list = file_types['executable_files']
new_file_list = file_types['new_files']
....
....
media_files = value['media_files']
	if media_files:
		for file_type in media_file_list:
			banned_formats.append(file_type)

executable_files = value['executable_files']
	if executable_files:
		for file_type in executable_file_list:
			banned_formats.append(file_type)

new_files = value['new_files']
	if new_files:
		for file_type in new_file_list:
			banned_formats.append(file_type)
....
```
When the **file_filter.py** script find an unauthorized file type, it moves this file into `quarantine_directory` within the file/folder hierarchy with adding a timestamp to file name. This can allow the script to move the same file name again again.

The **file_filter.py** script create a log file in main directory. If you want to create logs in another directory, please edit ```filename``` parameter as shown the line below. 

```sh
logging.basicConfig(filename='file_filter.log', level=logging.INFO,
    format='%(asctime)s,%(levelname)s,%(message)s')
```
	
You need to add your crontab entry to run **file_filter_py** periodically.

Crontab entry example for hourly run:

`0 * * * * /usr/bin/python3 /opt/Qumulo/file_filter.py`

You can create your own definition by using https://crontab-generator.org/


## Consideration
The script doesn't delete the files under `quarantine_directory`. So you need to do this manually or via another script. 

## Additional Steps
#### Qumulo Python SDK Installation 
To install the Python 3.10 version of the Qumulo Python SDK, you can simply run the following command:

```pip3 install qumulo_api==x.x.x```

Replace "x.x.x" is the version of the SDK you wish to install. Qumulo recommends keeping the version of the SDK that you're using in sync with the version of your cluster.

# Logging Details
logging.basicConfig(filename='file_filter.log', level=logging.INFO,
    format='%(asctime)s,%(levelname)s,%(message)s')



