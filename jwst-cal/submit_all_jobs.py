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
            job.write('Executable=/home/ec2-user/conda/envs/jwst/bin/strun\n')
            job.write(f'Arguments=jwst.pipeline.Detector1Pipeline s3://dmd-test-condor-prototype-data/input/{datafile} --output_dir s3://dmd-test-condor-prototype-data/output\n')
            job.write('\n')
            job.write('Universe=vanilla\n')
            job.write(f'Log={dataset}.condor_log\n')
            job.write(f'+Out = "ALOG_{dataset}.out"\n')
            job.write(f'+Err = "ALOG_{dataset}.err"\n')
            job.write(f'+Instances=1\n')
            job.write('getenv=True\n')
            job.write('Notification=Never\n')
            job.write('Queue')
            
        os.chdir(jobdir)
        cmd = f'condor_submit {dataset}.job'
        #print(cmd)
        os.system(cmd)
    
        os.chdir(rootdir)
    

