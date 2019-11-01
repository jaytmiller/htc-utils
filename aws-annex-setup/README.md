# AWS setup for condor_annex

## Overview 

This set of scripts and pre-fab configuration files creates a basic
condor_annex setup capable of spawning EC2 worker nodes automatically
and running jobs on them.  

The fundamental HTCondor configuration for AWS comes from the
condor_annex system; these instructions and scripts attempt to sort
out the Annex installation process for one working configuration as
a starting point for beginners.

This is a modernization and consolidation of these Annex setup links:

  - [Cloud seeded Annex,  scratch AMI] (https://htcondor-wiki.cs.wisc.edu/index.cgi/wiki?p=CondorInTheCloudSeedConstruction)
  - [HTCondor Uwisc rpm Repo Setup] (https://research.cs.wisc.edu/htcondor/instructions/el/7/development/)
  - [Multi-platform Uwisc Repo Setup, also Debian + Ubuntu] (https://research.cs.wisc.edu/htcondor/instructions/)
  - [First Annex time setup and use] (https://research.cs.wisc.edu/htcondor/manual/v8.7/UsingCondorannexfortheFirstTime.html)
  - [Cloud seeded Annex,  pre-built AMI] (https://htcondor.readthedocs.io/en/v8_8_4/cloud-computing/condor-in-the-cloud.html)
  - [LSST Unified Setup Instructions] (https://confluence.lsstcorp.org/display/DM/Setting+up+HTCondor+and+condor_annex)

It scripts some of the rote processes and file transformations documented
in this wealth of instructions.

These notes and files exist because I was not able to get ANY of the
aforementioned setup processes to work without modification.  In my
view the LSST unified setup instructions came closest to a coherent
narrative but these scripts are derived from earlier investigations
with only 1-2 security insights from LSST.

**NOTE:** At this time, the resulting HTCondor system still has
significant security vulnerabilities:

  - Ports 22 (ssh) and 9618 (HTCondor) are open to the world.

  - Private IP addresses 172.31.*.* are trusted as worker nodes with
    HTCondor ALLOW_WRITE

  - The recommended HTCondor master node identity has full account permissions.

## Set up master EC2 node

First create and EC2 instance to host the HTCondor master processes.  Depending on the size
of the instance,  it can also run worker processes.

### Arbitrary setup choices

1. EC2 instance:  t2.micro
2. Official AMI image RHEL-7.7 (RHEL-7.7_HVM-20190923-x86_64-0-Hourly2-GP2 (ami-029c0fbe456d58bd1))
3. Storage: 10G SSD GP2 100 IOPS
4. Network Security Group   (ssh-only for now)
5. Public / Private Key identity name (condor-annex)
6. Master node login:  ec2-user with full sudo

Other yum based distributions such as centos and amazon2 may be
adaptable but have not been demonstrated as working.  Same for Debian
and Ubuntu.

## Ssh to master node, clone these utils,  run setup script

## Create annex-user and set up Key files

To download a new pair of security tokens for condor_annex to use, go to the IAM console at the following URL; log in if you need to:

https://console.aws.amazon.com/iam/home?region=us-east-1#/users

The following instructions assume you are logged in as a user with the privilege to create new users. (The ‘root’ user for any account has this privilege; other accounts may as well.)
Click the “Add User” button.
Enter name in the User name box; “annex-user” is a fine choice.
Click the check box labelled “Programmatic access”.
Click the button labelled “Next: Permissions”.
Select “Attach existing policies directly”.
Type “AdministratorAccess” in the box labelled “Filter”.
Click the check box on the single line that will appear below (labelled “AdministratorAccess”).
Click the “Next: review” button (you may need to scroll down).
Click the “Create user” button.
From the line labelled “annex-user”, copy the value in the column labelled “Access key ID” to the file publicKeyFile.
On the line labelled “annex-user”, click the “Show” link in the column labelled “Secret access key”; copy the revealed value to the file privateKeyFile.
Hit the “Close” button.
The ‘annex-user’ now has full privileges to your account.

## Perform condor_annex Setup and Checkout

These scripts will create artifacts in CloudFormation:

./startup_annex

## Add HTCondor security group

One of the artifacts created by startup_annex is a network security
group which opens HTCondor port 9618 and ssh port 22 to the world.

Using the AWS consolte, add the master EC2 node being created here to
this security group.  Remove redundant groups like ssh-only, etc.


