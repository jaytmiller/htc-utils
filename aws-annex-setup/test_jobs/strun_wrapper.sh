#! /bin/sh

export AWS_DEFAULT_REGION=us-east-1
export CRDS_SERVER_URL=https://jwst-serverless.stsci.edu
export CRDS_S3_ENABLED=1
export CRDS_S3_RETURN_URI=1
export CRDS_MAPPING_URI=s3://dmd-test-crds/mappings/jwst
export CRDS_REFERENCE_URI=s3://dmd-test-crds/references/jwst
export CRDS_CONFIG_URI=s3://dmd-test-crds/config/jwst

/usr/local/bin/strun  $*


