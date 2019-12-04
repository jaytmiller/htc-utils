import os

rootdir = os.getcwd()

with open('./s3_data_list.txt','r') as f:
    for line in f.readlines():
        datafile=line.split(' ')[-1].strip()
        dataset=datafile.split('.')[0].strip()
    
        jobdir = dataset
        cmd = f'rm -rf {jobdir}'
        os.system(cmd)
        #print(jobdir)
        if not os.path.exists(jobdir):
            os.makedirs(jobdir)

        jobfile=f'{jobdir}/{dataset}.job'
        #print(jobfile)
        with open(jobfile,'w') as job:
            job.write(f"""
Executable=/bin/bash
Arguments=strun_wrapper.sh  jwst.pipeline.Detector1Pipeline s3://dmd-test-condor-prototype-data/input/{datafile} --output_dir s3://dmd-test-condor-prototype-data/output

Universe=vanilla
Log={dataset}.condor_log
+Out = "ALOG_{dataset}.out"
+Err = "ALOG_{dataset}.err"
+Instances=1
getenv=True
transfer_executable=false
transfer_input_files=strun_wrapper.sh
Notification=Never
Queue
""")
        os.system(f"cp strun_wrapper.sh {jobdir}")
        os.chdir(jobdir)
        cmd = f'condor_submit {dataset}.job'
        #print(cmd)
        os.system(cmd)
    
        os.chdir(rootdir)
    

