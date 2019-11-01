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
narrative.

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
2. CentOS-7 AMI image (CentOS Linux 7 x86_64 HVM EBS ENA 1901_01-b7ee8a69-ee97-4a49-9e68-afaee216db2e-ami-05713873c6794f575.4 (ami-02eac2c0129f6376b))
3. Storage: 20G SSD GP2 100 IOPS
4. Network Security Group   (ssh-only for now)
5. Public / Private Key identity name (condor-annex)
6. Master node login:  centos with full sudo

Other yum based distributions such as amazon2 may be adaptable but
have not been demonstrated as working.  Same for Debian and Ubuntu.

### Ssh to master node, clone these utils,  run setup script

```
sudo yum update
sudo yum install wget 
sudo yum install git 
sudo yum install emacs
git clone https://github.com/jaytmiller/htc-utils.git
cd htc-utils/aws-annex-setup

sudo ./install_annex   # hopefully follow along and occasionally hit "y"
```

**NOTE:** some of the configuration files explitly name the EC2 user and
are currently configured with "centos".

### Create annex-user and set up Key files

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

### Try out condor_master

```
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_status
Name                         OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime

ip-172-31-94-54.ec2.internal LINUX      X86_64 Unclaimed Idle      0.000  989  0+00:00:03

               Machines Owner Claimed Unclaimed Matched Preempting  Drain

  X86_64/LINUX        1     0       0         1       0          0      0

         Total        1     0       0         1       0          0      0


[centos@ip-172-31-94-54 aws-annex-setup]$ condor_q


-- Schedd: ip-172-31-94-54.ec2.internal : <184.73.40.122:9618?... @ 11/01/19 21:29:38
OWNER BATCH_NAME      SUBMITTED   DONE   RUN    IDLE   HOLD  TOTAL JOB_IDS

Total for query: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended 
Total for centos: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended 
Total for all users: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended

```

### Perform condor_annex Setup and Checkout

The setup_annex script runs condor_annex commands used to initialize the annex
and check it.  It produces 4 cloud formation artifacts.

```
./setup_annex

Setting up condor_annex...
Creating configuration bucket (this takes less than a minute)..... complete.
Creating Lambda functions (this takes about a minute)...... complete.
Creating instance profile (this takes about two minutes)................ complete.
Creating security group (this takes less than a minute).... complete.
Setup successful.
Checking condor_annex...
Checking security configuration... OK.
Checking for configuration bucket... OK.
Checking for Lambda functions... OK.
Checking for instance profile... OK.
Checking for security group... OK.
Your setup looks OK.
```

### Add HTCondor security group

One of the artifacts created by startup_annex is a network security
group which opens HTCondor port 9618 and ssh port 22 to the world.

Using the AWS console, add the master EC2 node being created here to
this security group.  Remove redundant groups like ssh-only, etc.

### Create EC2 worker nodes

Run the start_annex script.   This will create a default EC2 worker instance.

Dump the script for more info on parameters.

```
$ ./start_annex
Will request 1 t2.micro on-demand instance for 8.00 hours.  Each instance will terminate after being idle for 8.00 hours.
Is that OK?  (Type 'yes' or 'no'): yes
Starting annex...
Annex started.  Its identity with the cloud provider is 'MyFirstAnnex_7af2f955-ae1a-41b5-869d-2e5ff771a2cc'.  It will take about three minutes for the new machines to join the pool.
```

You can repeat this command multiple times to establish multiple
workers. Using parameters you can choose other EC2 instance types with
more cores or RAM.

### Check Annex Status

Wait a few minutes and check the status of your cluster.

**NOTE:**  As you create new worker EC2s it's a good idea to go to the AWS
web console and add a Name tag something like e.g. condor-worker-1

```
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_status
Name                          OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime

ip-172-31-84-204.ec2.internal LINUX      X86_64 Unclaimed Idle      0.000  983  0+00:00:03
ip-172-31-94-54.ec2.internal  LINUX      X86_64 Unclaimed Idle      0.000  989  0+00:29:36

               Machines Owner Claimed Unclaimed Matched Preempting  Drain

  X86_64/LINUX        2     0       0         2       0          0      0

         Total        2     0       0         2       0          0      0
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_q


-- Schedd: ip-172-31-94-54.ec2.internal : <184.73.40.122:9618?... @ 11/01/19 21:58:11
OWNER BATCH_NAME      SUBMITTED   DONE   RUN    IDLE   HOLD  TOTAL JOB_IDS

Total for query: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended 
Total for centos: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended 
Total for all users: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended

```

### Run Example Jobs

Use the condor_submit command to start some example jobs.

```
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit 
Submitting job(s).
1 job(s) submitted to cluster 1.
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit 
Submitting job(s).
1 job(s) submitted to cluster 2.
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit 
Submitting job(s).
1 job(s) submitted to cluster 3.
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit 
Submitting job(s).
1 job(s) submitted to cluster 4.
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit 
Submitting job(s).
1 job(s) submitted to cluster 5.
```

Wait a minute and check the queue status to see how jobs are running:

```
[centos@ip-172-31-94-54 aws-annex-setup]$ condor_q

-- Schedd: ip-172-31-94-54.ec2.internal : <184.73.40.122:9618?... @ 11/01/19 22:01:24
OWNER  BATCH_NAME    SUBMITTED   DONE   RUN    IDLE  TOTAL JOB_IDS
centos ID: 1       11/1  22:00      _      1      _      1 1.0
centos ID: 2       11/1  22:00      _      1      _      1 2.0
centos ID: 3       11/1  22:00      _      _      1      1 3.0
centos ID: 4       11/1  22:00      _      _      1      1 4.0
centos ID: 5       11/1  22:00      _      _      1      1 5.0

Total for query: 5 jobs; 0 completed, 0 removed, 3 idle, 2 running, 0 held, 0 suspended 
Total for centos: 5 jobs; 0 completed, 0 removed, 3 idle, 2 running, 0 held, 0 suspended 
Total for all users: 5 jobs; 0 completed, 0 removed, 3 idle, 2 running, 0 held, 0 suspended

```
