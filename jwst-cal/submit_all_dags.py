import os

rootdir = os.getcwd()

def mk_parent_job(jobfile, datafile, dataset):
	with open(jobfile,'w') as job:
		job.write(f"""
Executable=/bin/bash
Arguments=take_a_rest.sh parent

Universe=vanilla
Log=parent_{dataset}.condor_log
+Out = "ALOG_parent_{dataset}.out"
+Err = "ALOG_parent_{dataset}.err"
+Instances=1
getenv=True
transfer_executable=false
transfer_input_files=take_a_rest.sh
Notification=Never
Queue
	""")	
	return None

def mk_level1b_pvw_job(jobfile, datafile, dataset):
        with open(jobfile,'w') as job:
                job.write(f"""
Executable=/bin/bash
Arguments=pvw_wrapper.sh s3://dmd-test-condor-prototype-data/input/{datafile} s3://dmd-test-condor-prototype-data/output

Universe=vanilla
Log=level1b_pvw_{dataset}.condor_log
+Out = "ALOG_level1b_pvw_{dataset}.out"
+Err = "ALOG_level1b_pvw_{dataset}.err"
+Instances=1
getenv=True
transfer_executable=false
transfer_input_files=pvw_wrapper.sh
Notification=Never
Queue
        """)
        return None

def mk_level2a_job(jobfile, datafile, dataset):
        with open(jobfile,'w') as job:
                job.write(f"""
Executable=/bin/bash
Arguments=strun_wrapper.sh  jwst.pipeline.Detector1Pipeline s3://dmd-test-condor-prototype-data/input/{datafile} --output_dir s3://dmd-test-condor-prototype-data/output

Universe=vanilla
Log=level2a_{dataset}.condor_log
+Out = "ALOG_level2a_{dataset}.out"
+Err = "ALOG_level2a_{dataset}.err"
+Instances=1
getenv=True
transfer_executable=false
transfer_input_files=strun_wrapper.sh
Notification=Never
Queue
        """)
        return None

def mk_level2a_pvw_job(jobfile, datafile, dataset):
        with open(jobfile,'w') as job:
                job.write(f"""
Executable=/bin/bash
Arguments=pvw_wrapper.sh s3://dmd-test-condor-prototype-data/output/{datafile.replace("_uncal.fits","_rate.fits")} s3://dmd-test-condor-prototype-data/output

Universe=vanilla
Log=level2a_pvw_{dataset}.condor_log
+Out = "ALOG_level2a_pvw_{dataset}.out"
+Err = "ALOG_level2a_pvw_{dataset}.err"
+Instances=1
getenv=True
transfer_executable=false
transfer_input_files=pvw_wrapper.sh
Notification=Never
Queue
""")
        return None

def mk_dag(dagfile, datafile, dataset):
	with open(dagfile, 'w') as f:
		f.write(f"""
JOB INITIAL parent-{dataset}.job
JOB LEVEL1B_PVW level1b_pvw-{dataset}.job
JOB LEVEL2A level2a-{dataset}.job
JOB LEVEL2A_PVW level2a_pvw-{dataset}.job

PARENT INITIAL CHILD LEVEL1B_PVW LEVEL2A
PARENT LEVEL2A CHILD LEVEL2A_PVW

PRIORITY INITIAL 120
PRIORITY LEVEL1B_PVW 121
PRIORITY LEVEL2A 122
PRIORITY LEVEL2A_PVW 123
""")
	return None

# looping over list of data to process
with open('./s3_data_list.txt','r') as f:
	for line in f.readlines():
		datafile=line.split(' ')[-1].strip()
		dataset=datafile.split('.')[0].strip()

		jobdir = dataset
		cmd = f'rm -rf {jobdir}'
		os.system(cmd)
		if not os.path.exists(jobdir):
			os.makedirs(jobdir)

		jobfile=f'{jobdir}/parent-{dataset}.job'	
		mk_parent_job(jobfile, datafile, dataset)

		jobfile=f'{jobdir}/level1b_pvw-{dataset}.job'
		mk_level1b_pvw_job(jobfile, datafile, dataset)


		jobfile=f'{jobdir}/level2a-{dataset}.job'
		mk_level2a_job(jobfile, datafile, dataset)

		jobfile=f'{jobdir}/level2a_pvw-{dataset}.job'
		mk_level2a_pvw_job(jobfile, datafile, dataset)

		dagfile=f'{jobdir}/{dataset}.dag'
		mk_dag(dagfile, datafile, dataset)

		os.system(f"cp strun_wrapper.sh {jobdir}")
		os.system(f"cp pvw_wrapper.sh {jobdir}")
		os.system(f"cp take_a_rest.sh {jobdir}")
		os.chdir(jobdir)
		cmd = f"condor_submit_dag {dataset}.dag"
		os.system(cmd)
		os.chdir(rootdir)
	
