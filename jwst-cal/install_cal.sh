cd ~
mkdir tmp
cd tmp/

sudo yum install -y emacs gcc gcc-c++ python3 python3-devel htop wget git libpng-devel libjpeg-devel libcurl-devel make gcc-gfortran tar


git clone https://github.com/healpy/cfitsio.git
cd cfitsio && git checkout 8838182 && sudo ./configure --prefix=/usr/local && sudo make && sudo make install
cd ..
rm -rf cfitsio

wget http://tdc-www.harvard.edu/software/wcstools/wcstools-3.9.5.tar.gz
tar -zxf wcstools-3.9.5.tar.gz
cd wcstools-3.9.5 && sudo make
sudo mkdir -p /usr/local/include/libwcs
sudo cp wcstools-3.9.5/libwcs/*.h /usr/local/include/libwcs
sudo cp wcstools-3.9.5/libwcs/*.a /usr/local/lib
cd ..
rm -rf wcstools-3.9.5*

git clone https://github.com/spacetelescope/fitscut
cd fitscut && git checkout c76680d && sudo ./configure && sudo make && sudo make install
cd ..
rm -rf fitscut

echo /usr/local/lib | sudo tee -a /etc/ld.so.conf
sudo ldconfig

echo '#!/usr/bin/env python

import argparse
import os
import subprocess
import sys
import re
from glob import glob
from time import sleep
import logging
import json
import tempfile

from astropy.io import fits


LOGGER = logging.getLogger(__name__)

AUTOSCALE=99.5

OUTPUT_FORMATS = [
    ("_thumb", 128),
    ("", -1)
]


def generate_image_preview(input_path, output_path, size):
    cmd = [
        "fitscut",
        "--all",
        "--jpg",
        f"--autoscale={AUTOSCALE}",
        "--asinh-scale",
        f"--output-size={size}",
        "--badpix",
        input_path
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode > 0:
        LOGGER.error("fitscut failed for %s with status %s: %s", input_path, process.returncode, stderr)
        raise RuntimeError()

    with open(output_path, "wb") as f:
        f.write(stdout)


def generate_image_previews(input_path, output_dir, filename_base):
    output_paths = []
    for suffix, size in OUTPUT_FORMATS:
        output_path = os.path.join(output_dir, f"{filename_base}{suffix}.jpg")
        try:
            generate_image_preview(input_path, output_path, size)
        except Exception:
            LOGGER.exception("Preview file not generated for %s (%s)", input_path, size)
        else:
            output_paths.append(output_path)
    return output_paths


def generate_spectral_previews(input_path, output_dir, filename_base):
    cmd = [
        "make_jwst_spec_previews",
        "-v", "-o", output_dir, input_path
    ]

    try:
        output = subprocess.check_output(cmd)
        return [p for p in output.split() if filename_base in p and "fits" not in p.lower()]
    except Exception:
        LOGGER.exception("Preview file not generated for %s", input_path)
        return []


def generate_previews(input_path, output_dir, filename_base):
    with fits.open(input_path) as hdul:
        naxis = hdul[1].header["NAXIS"]
        ext = hdul[1].header["XTENSION"]

    if naxis == 2 and ext == "BINTABLE":
        return generate_spectral_previews(input_path, output_dir, filename_base)
    elif naxis >= 2 and ext == "IMAGE":
        return generate_image_previews(input_path, output_dir, filename_base)
    else:
        LOGGER.warning("Unable to determine FITS file type")
        return []


def split_uri(uri):
    assert uri.startswith("s3://")
    return uri.replace("s3://", "").split("/", 1)


def list_fits_uris(uri_prefix):
    bucket_name, key = split_uri(uri_prefix)
    result = subprocess.check_output([
        "aws", "s3api", "list-objects",
        "--bucket", bucket_name,
        "--prefix", key,
        "--output", "json",
        "--query", "Contents[].Key"
    ])
    return [f"s3://{bucket_name}/{k}" for k in json.loads(result) if k.lower().endswith(".fits")]


def parse_args():
    parser = argparse.ArgumentParser(description="Create image and spectral previews")

    parser.add_argument("input_uri_prefix", help="S3 URI prefix containing FITS images that require previews")
    parser.add_argument("output_uri_prefix", help="S3 URI prefix for writing previews")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    input_uris = list_fits_uris(args.input_uri_prefix)
    LOGGER.info("Processing %s FITS files from prefix %s", len(input_uris), args.input_uri_prefix)

    tempdir = tempfile.gettempdir()

    for input_uri in input_uris:
        LOGGER.info("Processing %s", input_uri)
        filename = os.path.basename(input_uri)
        input_path = os.path.join(tempdir, filename)
        subprocess.check_call([
            "aws", "s3", "cp", input_uri, input_path
        ])
        filename_base, _ = os.path.splitext(filename)
        output_paths = generate_previews(input_path, tempdir, filename_base)
        LOGGER.info("Generated %s output files", len(output_paths))
        for output_path in output_paths:
            output_uri = os.path.join(args.output_uri_prefix, os.path.basename(output_path))
            subprocess.check_call([
                "aws", "s3", "cp", output_path, output_uri
            ])
' > create_previews

sudo cp create_previews /usr/local/bin

cd ~
wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-4.7.12-Linux-x86_64.sh -O ~/miniconda.sh
/bin/bash ~/miniconda.sh -b -p ~/conda 
rm ~/miniconda.sh 

echo "export CRDS_SERVER_URL=https://jwst-serverless.stsci.edu" >> .bashrc
echo "export CRDS_S3_ENABLED=1" >> .bashrc
echo "export CRDS_S3_RETURN_URI=1" >> .bashrc
echo "export CRDS_MAPPING_URI=s3://dmd-test-crds/mappings/jwst" >> .bashrc
echo "export CRDS_REFERENCE_URI=s3://dmd-test-crds/references/jwst" >> .bashrc
echo "export CRDS_CONFIG_URI=s3://dmd-test-crds/config/jwst" >> .bashrc

echo "name: jwst
channels:
- defaults
dependencies:
- python==3.7.5
- pip==19.3.1
- pip:
  - git+https://github.com/eslavich/stsci-aws-utils.git@eslavich-disable-md5-check
  - git+https://github.com/spacetelescope/crds.git@7.4.1.3#egg=crds[aws]
  - git+https://github.com/eslavich/jwst.git@eslavich-write-output-to-s3#egg=jwst[aws]
  - git+https://github.com/spacetelescope/spec_plots.git" > environment.yml

echo ". ~/conda/etc/profile.d/conda.sh" >> .bashrc

. ~/conda/etc/profile.d/conda.sh && conda env create -f environment.yml
rm ~/environment.yml

echo "export AWS_DEFAULT_REGION=us-east-1" >> .bashrc

source ~/.bashrc 
conda activate jwst
