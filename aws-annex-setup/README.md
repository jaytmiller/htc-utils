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

  - [Cloud Seeded Annex,  scratch AMI] (https://htcondor-wiki.cs.wisc.edu/index.cgi/wiki?p=CondorInTheCloudSeedConstruction)
  - [HTCondor Uwisc rpm Repo Setup] (https://research.cs.wisc.edu/htcondor/instructions/el/7/development/)
  - [Multi-platform Uwisc Repo Setup, also Debian + Ubuntu] (https://research.cs.wisc.edu/htcondor/instructions/)
  - [First Annex time setup and use] (https://research.cs.wisc.edu/htcondor/manual/v8.7/UsingCondorannexfortheFirstTime.html)
  - [Cloud seeded Annex,  pre-built AMI] (https://htcondor.readthedocs.io/en/v8_8_4/cloud-computing/condor-in-the-cloud.html)
  - [LSST Unified Setup Instructions] (https://confluence.lsstcorp.org/display/DM/Setting+up+HTCondor+and+condor_annex)

It scripts some of the rote processes and file transformations documented
in this wealth of instructions.

**NOTE:** At this time, this is a prototype installation only, not
intended for production use.  The resulting HTCondor system still has
significant security vulnerabilities:

  - Ports 22 (ssh) and 9618 (HTCondor) are open to the world.

  - Private IP addresses 172.31.*.* are trusted as worker nodes with
    HTCondor ALLOW_WRITE

  - The recommended HTCondor master node identity has full account permissions.

## Set up master EC2 node

First create an EC2 instance to host the HTCondor master processes.  Depending on the size
of the instance,  it can also run worker processes.   By default,  these instructions
produce a master node which DOES NOT run jobs.

### Arbitrary setup choices

1. Condor Public / Private Key identity name (annex-user,  AdministratorAccess)
2. Master node login:  ec2-user with full sudo

### Create condor-master network security group

Create a new network secruity group condor-master:

1. Open ssh to appropriate hosts (e.g. 0.0.0.0,  world)
2. Open condor port 9618 to appropriate hosts (e.g. 0.0.0.0, world)

### Create condor-annex-master EC2 node

Launch an annex master EC2 instance

1. EC2 instance:  t2.micro
2. Amazon Linux 2 AMI (HVM), SSD Volume Type ami-00068cd7555f543d5 (64-bit x86)
3. Storage: 8G SSD GP2 100 IOPS
4. Network Security Group   (condor-master)
5. Any key pair for ssh access

For large numbers of job slots, it may be necessary to use a larger master node
since condor currently runs a process on master for every worker process to
gather the logs, etc.

### Ssh to master node, update EC2,  clone these utils

```
sudo yum install wget
sudo yum install git
git clone https://github.com/jaytmiller/htc-utils.git
cd htc-utils/aws-annex-setup
```

**NOTE:** some of the configuration files explitly name the EC2 user and
are currently configured with "ec2-user".  To switch to an alternate distribution
you can run a perl snippet over all files to rename the user, e.g.:

```
find . -type f | xargs perl -pi -e's/ec2-user/ec2-user/g'
```

### Create annex-user and set up Key files for condor annex install

To download a new pair of security tokens for condor_annex to use, go
to the IAM console at the following URL; log in if you need to:

https://console.aws.amazon.com/iam/home?region=us-east-1#/users

The following instructions assume you are logged in as a user with the
privilege to create new users. (The ‘root’ user for any account has
this privilege; other accounts may as well.)

Click the “Add User” button.

Enter name in the User name box; “annex-user” is a fine choice.

Click the check box labelled “Programmatic access”.

Click the button labelled “Next: Permissions”.

Select “Attach existing policies directly”.

Type “AdministratorAccess” in the box labelled “Filter”.

Click the check box on the single line that will appear below (labelled “AdministratorAccess”).

Click the “Next: review” button (you may need to scroll down).

Click the “Create user” button.

**IMPORTANT:** From the line labelled “annex-user”, copy the value in the column
labelled “Access key ID” to the file
supporting_files/dot_condor/publicKeyFile.

**IMPORTANT:** On the line labeled “annex-user”, click the “Show” link in the column
labelled “Secret access key”; copy the revealed value to the file
supporting_files/dot_condor/privateKeyFile.

**IMPORTANT:** Set aside the annex-user keys in a local file on you laptop,
similar to a .pem key.

Hit the “Close” button.

When the install script is run, the ‘annex-user’ will have full
privileges to your account.

### Run install_condor

The install_condor script performs the initial steps of installing condor
via rpms from the uwisc repository.  It also starts the condor service and
master and defines the condor password.  Finally,  it sets up some config
in $HOME/.condor.  This step uses predefined condor configuration files,
particularly supporting_files/local.

```
./install_condor
```


### Try out basic condor commands

Try out condor_status and condor_q.   Since the default configuration no longer runs
jobs on the master node,  condor_status should return no output but does check
communication with the master daemons.

```
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_status
```

Since no jobs have been queued, likewise condor_q has little to report.

```
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_q

-- Schedd: ip-172-31-94-54.ec2.internal : <184.73.40.122:9618?... @ 11/01/19 21:29:38
OWNER BATCH_NAME      SUBMITTED   DONE   RUN    IDLE   HOLD  TOTAL JOB_IDS

Total for query: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended
Total for ec2-user: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended
Total for all users: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended
```

If you do want the master node to run jobs,  edit supporting_files/local and change the
DAEMON_LIST to include STARTD.  Then re-run ./install_condor.

### Perform condor_annex Setup and Checkout

The setup_annex script runs condor_annex commands used to initialize the annex
and check it.   Run it now:

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

setup_annex produces 4 cloud formation artifacts which have generic names:

- HTCondorAnnex-SecurityGroup
- HTCondorAnnex-InstanceProfile
- HTCondorAnnex-LambdaFunctions
- HTCondorAnnex-ConfigurationBucket

Note that setup checking doesn't appear to verify correct operation of the 4
artifacts,  merely that they exist.  If you're debugging,  make sure to delete
the cloud formations before re-running condor_annex.

You may want to tighten up the security group once you prove condor is working.

### Create EC2 worker nodes

Run the start_annex script.   This will create a default EC2 worker instance.

```
$ ./start_annex
Will request 1 t2.micro on-demand instance for 8.00 hours.  Each instance will terminate after being idle for 8.00 hours.
Is that OK?  (Type 'yes' or 'no'): yes
Starting annex...
Annex started.  Its identity with the cloud provider is 'MyFirstAnnex_7af2f955-ae1a-41b5-869d-2e5ff771a2cc'.  It will take about three minutes for the new machines to join the pool.
```

You can repeat this command multiple times to establish multiple
workers, or just run it once with the desired worker count.

Dump the script for more info on parameters which can be used to specify
instance count, type, duration, and shutdown idle time.

The start_annex script also specifies the exact AWS AMI which will be run,
which currently also defines the version of CAL code pre-installed on the AMI.

**IMPORTANT:**

As you create your annex nodes,  they will be assigned a role like:

   arn:aws:iam::162808325377:role/HTCondorAnnex-InstancePro-InstanceConfigurationRol-JZTES9L6Y1YH

Any additional permissions/policies required to run your jobs should be added
to that role using the IAM console.  In particular, running the JWST CAL code
requires S3FullAccess in order to fetch inputs and store output files.

### Check Annex Status

Wait a few minutes and check the status of your cluster.

**NOTE:**  As you create new worker EC2s it's a good idea to go to the AWS
web console and add a Name tag something like e.g. condor-worker-1

Since you now have at least one compute node,  condor_status will report the state of those resources:

```
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_status
Name                          OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime

ip-172-31-84-204.ec2.internal LINUX      X86_64 Unclaimed Idle      0.000  983  0+00:00:03

               Machines Owner Claimed Unclaimed Matched Preempting  Drain

  X86_64/LINUX        1     0       0         1       0          0      0

         Total        1     0       0         1       0          0      0

[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_q


-- Schedd: ip-172-31-94-54.ec2.internal : <184.73.40.122:9618?... @ 11/01/19 21:58:11
OWNER BATCH_NAME      SUBMITTED   DONE   RUN    IDLE   HOLD  TOTAL JOB_IDS

Total for query: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended
Total for ec2-user: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended
Total for all users: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended

```

### Run Example Jobs

Use the condor_submit command to start some example jobs.

```
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit
Submitting job(s).
1 job(s) submitted to cluster 1.
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit
Submitting job(s).
1 job(s) submitted to cluster 2.
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit
Submitting job(s).
1 job(s) submitted to cluster 3.
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit
Submitting job(s).
1 job(s) submitted to cluster 4.
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_submit test_jobs/sleep.submit
Submitting job(s).
1 job(s) submitted to cluster 5.
```

Check the queue status to see how jobs are running:

```
[ec2-user@ip-172-31-94-54 aws-annex-setup]$ condor_q

-- Schedd: ip-172-31-94-54.ec2.internal : <184.73.40.122:9618?... @ 11/01/19 22:01:24
OWNER  BATCH_NAME    SUBMITTED   DONE   RUN    IDLE  TOTAL JOB_IDS
ec2-user ID: 1       11/1  22:00      _      1      _      1 1.0
ec2-user ID: 2       11/1  22:00      _      -      1      1 2.0
ec2-user ID: 3       11/1  22:00      _      _      1      1 3.0
ec2-user ID: 4       11/1  22:00      _      _      1      1 4.0
ec2-user ID: 5       11/1  22:00      _      _      1      1 5.0

Total for query: 5 jobs; 0 completed, 0 removed, 4 idle, 1 running, 0 held, 0 suspended
Total for ec2-user: 5 jobs; 0 completed, 0 removed, 4 idle, 1 running, 0 held, 0 suspended
Total for all users: 5 jobs; 0 completed, 0 removed, 4 idle, 1 running, 0 held, 0 suspended

```

## Tear Down

This condor annex setup can be torn down by:

0. Stopping all the EC2s
1. Going to S3 and deleting the contents of any htcondorannex-.... buckets created by condor annex
2. Going to Cloud Formation and deleting the 4 different HTCondorAnnex.... stacks created by condor annex
3. Deleting worker EC2s created by condor annex
4. Deleting the master EC2 created by you
5. Deleting the annex-user user created by you
6. Deleting the condor-master security group created by you
7. Deleting the HTCondorAnnex... security group created by condor annex

NOTE: If the S3 bucket is not empty the cloudformation step which attempts to delete it will fail.
Hence I added an explicit step to remove the S3 bucket manually.
Non-empty S3 may be tied to running workers.
