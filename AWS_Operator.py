#!/usr/bin/python
#Python 2.7.6

import boto.ec2
import datetime
import os
import argparse

access_id = os.environ.get('AWS_ACCESS_KEY_ID')
access_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = os.environ.get('AWS_REGION_NAME')

try:
       ec2_conn = boto.ec2.connect_to_region(region_name,
                                             aws_access_key_id=access_id,
                                             aws_secret_access_key=access_secret)
except Exception as e:
       raise Exception('Connection Error. Please Check the Credentials')


def get_instances():
       reservations = ec2_conn.get_all_instances()
       instances = [inst for res in reservations for inst in res.instances]
       return instances

def get_volumes():
       return ec2_conn.get_all_volumes()

def get_snapshots():
       return ec2_conn.get_all_snapshots()

def get_instance_details(instance_id):

       for ins in get_instances():
              if instance_id == str(ins.id) :
                     r_instance = ins.tags
                     break
       return r_instance       

def create_AMI(instance_id):
       for ins in get_instances():
              if instance_id == str(ins.id): r_instance = ins; break
       if 'r_instance' in locals() :
              AMI_Name = 'ivyauto_' + r_instance.id \
                         + '_(' + r_instance.tags['Name']+')_' \
                         + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
              AMI_ID = ec2_conn.create_image(r_instance.id
                                             , AMI_Name
                                             , description = AMI_Name
                                             , no_reboot = True
                                             , block_device_mapping = None
                                             , dry_run = False)
              print "AMI ID : '" + AMI_ID + "' created for " + r_instance.tags['Name']
       else : print "***No Instance - " , instance_id

def create_snapshot(volume_id):

       for vol in get_volumes():
              if volume_id == str(vol.id): r_volume = vol; break
       if 'r_volume' in locals() :
              snapshot_Name = 'ivyauto_' + r_volume.id + '_'\
                              + (r_volume.attach_data.instance_id \
                                 if not r_volume.attach_data.instance_id == None else "None")\
                              + '(' + (str(get_instance_details(r_volume.attach_data.instance_id)['Name']) \
                                       if not r_volume.attach_data.instance_id == None else "None")+ ')' \
                              + ':' + str(r_volume.attach_data.device) + '(' + str(r_volume.attach_data.status) + ')_' \
                              + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
              snapshot_ID = ec2_conn.create_snapshot(r_volume.id
                                                     , description = snapshot_Name
                                                     , dry_run = False)
              snapshot_ID.add_tag("Name",snapshot_Name)
              print "Snapshot ID : '" + str(snapshot_ID) + "' created for " + r_volume.id
       else : print "***No Volume - " , volume_id

def delete_snap(snap):
       ec2_conn.delete_snapshot(snap.id, dry_run=False)
       print snap.description + "Deleted"


if __name__ == '__main__':
       parser = argparse.ArgumentParser(description="")
       parser.add_argument("-a","--create_ami", help="Creating AMI and paramaters are Instance names with ',' seperated Eg:python AWS_Operator -a 'inst1,inst2,inst3'")
       parser.add_argument("-p","--get_property", help="Generating the Instances and Volumes in a file. Path is provided as Paramater Eg:python AWS_Operator -p 'home/user/Desktop/'")
       parser.add_argument("-s","--create_snap", help="Creating Snapshots and paramaters are Volumes names with ',' seperated Eg:python AWS_Operator -s 'vol1,vol2,vol3'")
       parser.add_argument("-d","--delete_snap", help="Deleting Snapshots of particular days old Eg:python AWS_Operator -d 14, all the snapshots above 14days are deleted\
                           . Paramters must an Integer", type=int)
       args = parser.parse_args()
       if args.create_ami:
              for inst in (args.create_ami).split(','):
                     create_AMI(inst.split(' ')[0])
       if args.get_property:
              instances = [inst.id+' '+inst.tags['Name'] for inst in get_instances()]
              volumes = [volume.id+'__'\
                         +(get_instance_details(volume.attach_data.instance_id)['Name'] \
                           if not volume.attach_data.instance_id == None else "None")\
                         for volume in get_volumes()]
              with open(args.get_property+'/'+'aws.properties','w') as prop:
                     prop.write('instances='+','.join(instances))
                     prop.write('\nvolume='+','.join(volumes))
       if args.create_snap:
              for vol in (args.create_snap).split(','):
                     create_snapshot(vol.split('__')[0])
       if args.delete_snap:
              for snap in get_snapshots():
                     snap_date = datetime.strptime(snap.start_time,
                                                   '%Y-%m-%dT%H:%M:%S.%fZ').date()
                     to_date = date.today()
                     if (to_date - snap_date).days > int(args.delete_snap) and \
                        (snap.description).startswith('ivyauto_') :
                            delete_snap(snap)
