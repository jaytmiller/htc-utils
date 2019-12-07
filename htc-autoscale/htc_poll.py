"""
This module implements a crude autoscaler for htcondor annex.   Based on the number of queued jobs
and available slots,  it automatically creates new worker nodes with relatively aggressive idle
termination times.
"""

import os, sys, time
from pprint import pprint as pp

import pysh

# ========================================================================

class Struct(dict):
    """A dictionary which supports dotted access to members."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, val):
        self[name] = val

# ========================================================================

def get_htc_status():
    status_out_str = pysh.out("condor_status")
    return parse_htc_status(status_out_str)

def get_htc_queue():
    queue_out_str = pysh.out("condor_q")
    return parse_htc_queue(queue_out_str)

# ========================================================================

_TEST_STATUS = """
    Name                               OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime

slot1@ip-172-31-21-35.ec2.internal LINUX      X86_64 Claimed   Busy      0.000 7947  0+00:00:03
slot2@ip-172-31-21-35.ec2.internal LINUX      X86_64 Claimed   Busy      0.000 7947  0+00:00:03
slot3@ip-172-31-21-35.ec2.internal LINUX      X86_64 Claimed   Busy      0.000 7947  0+00:00:03
slot4@ip-172-31-21-35.ec2.internal LINUX      X86_64 Claimed   Busy      0.000 7947  0+00:00:03

               Machines Owner Claimed Unclaimed Matched Preempting  Drain

  X86_64/LINUX        4     0       4         0       0          0      0

         Total        4     0       4         0       0          0      0
"""

_RESULT_STATUS = """
{'machines': [{'Claimed': '4',
                   'Class': 'X86_64/LINUX',
                   'Drain': '0',
                   'Machines': '4',
                   'Matched': '0',
                   'Owner': '0',
                   'Preempting': '0',
                   'Unclaimed': '0'},
                  {'Claimed': '4',
                   'Class': 'Total',
                   'Drain': '0',
                   'Machines': '4',
                   'Matched': '0',
                   'Owner': '0',
                   'Preempting': '0',
                   'Unclaimed': '0'}],
     'slots': [{'Activity': 'Busy',
                'ActvtyTime': '0+00:00:03',
                'Arch': 'X86_64',
                'LoadAv': '0.000',
                'Mem': '7947',
                'Name': 'slot1@ip-172-31-21-35.ec2.internal',
                'OpSys': 'LINUX',
                'State': 'Claimed'},
               {'Activity': 'Busy',
                'ActvtyTime': '0+00:00:03',
                'Arch': 'X86_64',
                'LoadAv': '0.000',
                'Mem': '7947',
                'Name': 'slot2@ip-172-31-21-35.ec2.internal',
                'OpSys': 'LINUX',
                'State': 'Claimed'},
               {'Activity': 'Busy',
                'ActvtyTime': '0+00:00:03',
                'Arch': 'X86_64',
                'LoadAv': '0.000',
                'Mem': '7947',
                'Name': 'slot3@ip-172-31-21-35.ec2.internal',
                'OpSys': 'LINUX',
                'State': 'Claimed'},
               {'Activity': 'Busy',
                'ActvtyTime': '0+00:00:03',
                'Arch': 'X86_64',
                'LoadAv': '0.000',
                'Mem': '7947',
                'Name': 'slot4@ip-172-31-21-35.ec2.internal',
                'OpSys': 'LINUX',
                'State': 'Claimed'}]}
"""

def parse_htc_status(status_str):
    """
    >>> parse_htc_status(_TEST_STATUS) == eval(_RESULT_STATUS)
    True
    """
    machine_words, slot_words = [], []

    for line in status_str.splitlines():
        words = line.split()
        if not words:
            continue
        if words[0] == "Name":
            slot_colnames = words
        elif words[0] == "Machines":
            machine_colnames = ["Class"] + words
        elif words[0].startswith("slot"):
            slot_words += [words]
        else:
            machine_words += [words]
    slot_objs = [ Struct(zip(slot_colnames, words))
                  for words in slot_words ]
    machine_objs =  [ Struct(zip(machine_colnames, words))
                      for words in machine_words ]
    return  Struct({
        "slots" : slot_objs,
        "machines" : machine_objs,
        })

# ========================================================================

_TEST_QUEUE = """
-- Schedd: ip-172-31-83-21.ec2.internal : <35.175.246.184:9618?... @ 12/05/19 08:44:17
OWNER  BATCH_NAME    SUBMITTED   DONE   RUN    IDLE  TOTAL JOB_IDS
centos ID: 309     12/5  08:42      _      1      _      1 309.0
centos ID: 310     12/5  08:42      _      1      _      1 310.0
centos ID: 311     12/5  08:42      _      1      _      1 311.0
centos ID: 312     12/5  08:42      _      1      _      1 312.0
centos ID: 313     12/5  08:42      _      _      1      1 313.0
centos ID: 314     12/5  08:42      _      _      1      1 314.0
centos ID: 315     12/5  08:42      _      _      1      1 315.0
centos ID: 316     12/5  08:42      _      _      1      1 316.0

Total for query: 8 jobs; 0 completed, 0 removed, 4 idle, 4 running, 0 held, 0 suspended
Total for centos: 8 jobs; 0 completed, 0 removed, 4 idle, 4 running, 0 held, 0 suspended
Total for all users: 8 jobs; 0 completed, 0 removed, 4 idle, 4 running, 0 held, 0 suspended
"""

_RESULT_QUEUE = """
{'job_info': [{'batch_name': '309',
               'done': '_',
               'idle': '_',
               'job_id': '309.0',
               'owner': 'centos',
               'run': '1',
               'submitted': '12/5 08:42',
               'total': '1'},
              {'batch_name': '310',
               'done': '_',
               'idle': '_',
               'job_id': '310.0',
               'owner': 'centos',
               'run': '1',
               'submitted': '12/5 08:42',
               'total': '1'},
              {'batch_name': '311',
               'done': '_',
               'idle': '_',
               'job_id': '311.0',
               'owner': 'centos',
               'run': '1',
               'submitted': '12/5 08:42',
               'total': '1'},
              {'batch_name': '312',
               'done': '_',
               'idle': '_',
               'job_id': '312.0',
               'owner': 'centos',
               'run': '1',
               'submitted': '12/5 08:42',
               'total': '1'},
              {'batch_name': '313',
               'done': '_',
               'idle': '1',
               'job_id': '313.0',
               'owner': 'centos',
               'run': '_',
               'submitted': '12/5 08:42',
               'total': '1'},
              {'batch_name': '314',
               'done': '_',
               'idle': '1',
               'job_id': '314.0',
               'owner': 'centos',
               'run': '_',
               'submitted': '12/5 08:42',
               'total': '1'},
              {'batch_name': '315',
               'done': '_',
               'idle': '1',
               'job_id': '315.0',
               'owner': 'centos',
               'run': '_',
               'submitted': '12/5 08:42',
               'total': '1'},
              {'batch_name': '316',
               'done': '_',
               'idle': '1',
               'job_id': '316.0',
               'owner': 'centos',
               'run': '_',
               'submitted': '12/5 08:42',
               'total': '1'}],
 'queue_info': {'Total for all users': {'completed': 0,
                                        'held': 0,
                                        'idle': 4,
                                        'jobs': 8,
                                        'removed': 0,
                                        'running': 4,
                                        'suspended': 0},
                'Total for centos': {'completed': 0,
                                     'held': 0,
                                     'idle': 4,
                                     'jobs': 8,
                                     'removed': 0,
                                     'running': 4,
                                     'suspended': 0},
                'Total for query': {'completed': 0,
                                    'held': 0,
                                    'idle': 4,
                                    'jobs': 8,
                                    'removed': 0,
                                    'running': 4,
                                    'suspended': 0}}}
"""

def parse_htc_queue(queue_str):
    """
    >>> parse_htc_queue(_TEST_QUEUE) == eval(_RESULT_QUEUE)
    True
    """
    job_info = []
    queue_info = Struct()
    for line in queue_str.splitlines():
        words = line.split()
        if not words:
            continue
        elif words[0] == "--":
            continue
        elif words[0] == "OWNER":
            continue
        elif line.startswith("Total"):
            name, remainder = line.split(":")
            jobs, queue = remainder.split(";")
            job_count = int(jobs.split()[0])
            queue_fields = queue.split(",")
            queue_dict = Struct({ words.split()[1]:int(words.split()[0])
                            for words in queue_fields })
            queue_dict.jobs = job_count
            queue_info[name] = queue_dict
        else:  # job data line
            job = Struct()
            job.owner = words[0]
            job.batch_name = words[2]
            job.submitted = " ".join(words[3:5])
            job.done = words[5]
            job.run = words[6]
            job.idle = words[7]
            job.total = words[8]
            job.job_id = words[9]
            job_info.append(job)
    return Struct({
        "job_info": job_info,
        "queue_info": queue_info
        })

# ========================================================================

class _CondorStatus:
    """
    >>> s = parse_htc_status(_TEST_STATUS)
    >>> q = parse_htc_queue(_TEST_QUEUE)
    >>> c = _CondorStatus(s, q)
    
    >>> c.idle_jobs
    4
    >>> c.total_slots
    4
    >>> c.claimed_slots
    4
    >>> c.idle_slots
    0
    >>> c.unique_ips
    {'ip-172-31-21-35.ec2.internal'}
    """
    def __init__(self, status, queue):
        self.status = status
        self.queue = queue

    @property
    def idle_jobs(self):
        return self.queue.queue_info["Total for all users"].idle

    @property
    def total_slots(self):
        return len(self.status.slots)

    @property
    def claimed_slots(self):
        return len([slot for slot in self.status.slots
                    if slot.State == "Claimed"])
    @property
    def unclaimed_slots(self):
        return len([slot for slot in self.status.slots
                    if slot.State == "Unclaimed"])

    @property
    def unique_ips(self):
        return { slot.Name.split("@")[1]
                 for slot in self.status.slots }

class CondorStatus(_CondorStatus):
    def __init__(self):
        super(CondorStatus, self).__init__(
            get_htc_status(),
            get_htc_queue())

def test():
    import doctest
    import htc_poll
    return doctest.testmod(htc_poll)

if __name__ == "__main__":
    print(test())
