import os
import subprocess
import tarfile
import boto3
import datetime
import paramiko
from botocore.exceptions import NoCredentialsError


# give the specific information

instance_ip = input("Enter the public ip to connect.  ")
instance_user = input("Please enter the username, recommended username - ubuntu.   ")
application_folder = input("Please enter the folder location where your files are located in remote server.  ")
s3_bucket = input("Enter your bucket name.  ")
private_key_file = input("Please specify your keypair.pem file in .pem format. ")
AWS_ACCESS_KEY_ID = input("Enter the aws accsess key.  ")
AWS_SECRET_ACCESS_KEY = input("Enter the aws secret access key.  ")
backup_on_server = input("What do you want to name your backup file? Name the backup file and " +
                         "give '.tar.gz' in suffix, ex - backup.tar.gz.  ")
after_downloaded_file_path = f'backup/{backup_on_server}'
s3_Object_key = backup_on_server


'''
The basic idea is to firstly find the folder contains files which are need to be backed up and then 
we create a tar file for compression and storage optimisation on the remote server. Basically we use 
ssh client to connect to the remote server by giving the necessary information and running commands 
in the remote server. after creating the tar file we download the file to our local machine and then 
it is being uploaded to the s3 bucket.
Here create_backup function basically creates the tar file and stores it to the local machine
and Load_backup_on_S3 uploads the file to the s3 bucket.
'''


def Create_Backup(instance_ip, instance_user, private_key_file):
    # ssh configuration
    ssh_config = paramiko.SSHConfig()
    # creating ssh client
    ssh_client = paramiko.SSHClient()

    try:
        # Load known host keys from the configuration file
        ssh_client.load_system_host_keys()

        # Get the host key from the configuration
        host_key = ssh_config.lookup(instance_ip).get('hostkey')

        # Add the host key to the client's host key list
        ssh_client.get_host_keys().add(instance_ip, 'ssh-rsa', host_key)
        ssh_client.connect(hostname=instance_ip, username=instance_user, key_filename=private_key_file)
        print("Connected to the remote server.")

        # You can now perform actions on the EC2 instance using the ssh_client object
        # For example, you can run commands on the remote server using the exec_command method:

        # Create the tar.gz file on the remote server
        command = f"tar czf {backup_on_server} -C {application_folder} ."
        stdin, stdout, stderr = ssh_client.exec_command(command)
        # stdin shows the input, stdout shos the output and stderr shows the error

        # Wait for the command to finish
        print("status of creating tar file ", stdout.channel.recv_exit_status())

        # Check if the tar.gz file was created successfully
        if stdout.channel.recv_exit_status() == 0:
            print("Backup created successfully on the remote server.")
        else:
            print("Error creating backup on the remote server:", stderr.read().decode())

        
        # Download the tar.gz file from the remote server to local machine using SSH
        remote_download_path = f"./{backup_on_server}"  # Path of the tar.gz file on the remote server
        local_download_path = f"backup/{backup_on_server}"  # Path to save the file on the local machine

        ftp_client = ssh_client.open_sftp()
        ftp_client.get(remote_download_path, local_download_path)
        ftp_client.close()

        print("Backup downloaded to local machine successfully in ", local_download_path)


    except paramiko.AuthenticationException:
        print("Authentication failed. Check your private key file or username.")
    except paramiko.SSHException as e:
        print("Error occurred while establishing SSH connection:", str(e))
    finally:
        # Close the SSH connection
        ssh_client.close()


def Load_backup_on_S3():
    # Specify the name of the S3 bucket
    bucket_name = s3_bucket

    # Specify the local file path of the test file to be uploaded
    local_file_path = after_downloaded_file_path

    # Specify the desired S3 object key for the uploaded file
    s3_object_key = s3_Object_key

    try:
        # Create an S3 client using your AWS credentials
        s3_client = boto3.client('s3',
                                 aws_access_key_id=AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

        # Upload the test file to the S3 bucket
        s3_client.upload_file(local_file_path, bucket_name, s3_object_key)

        # Print success message if the file was uploaded
        print(f"Test file uploaded to S3 bucket: {bucket_name}")

    except NoCredentialsError:
        # Print error message if AWS credentials are missing or incorrect
        print("AWS credentials not found or invalid")



# executing the script
Create_Backup(instance_ip, instance_user, private_key_file)
Load_backup_on_S3()