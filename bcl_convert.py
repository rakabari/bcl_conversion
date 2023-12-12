#!/home/sbsuser/venv/bin/python3.11
import grp
import logging
import os
import pwd
import shutil
import subprocess
from time import sleep
from utils.global_vars import NGSDATA
from utils.mnt_win import mount_drive
from utils.run_validation import is_recent_run, is_run_complete, is_b2f_complete


def rename_samplesheet(rfpath: str) -> None:
    """
    Renames the SampleSheet by removing extra identifiers
    """
    for file in os.listdir(rfpath):
        if file.endswith('.csv') and 'samplesheet' in file.lower():
            os.rename(os.path.join(rfpath, file),
                      os.path.join(rfpath, 'SampleSheet.csv'))
            print(f'INFO: {os.path.basename(rfpath)}: SampleSheet renamed')


def copy_index_bin(rfpath: str) -> None:
    """
    Copies the IndexMetricsOut.bin to the InterOp directory for SAV indexing viewings
    """
    index_str = 'bclConvert/Reports/IndexMetricsOut.bin'
    index_bin = os.path.join(rfpath, index_str)
    shutil.copy2(index_bin, os.path.join(rfpath, 'InterOp'))
    print(f'INFO: {rfpath.split("/")[-1]}: IndexMetrics copied')


def read_bclconvert_error(rfpath: str):
    """
    reads error log produced by bcl-convert
    """
    error_log = os.path.join(rfpath, 'bclConvert/Logs/Errors.log')
    with open(error_log, 'r') as e:
        return e.read()


def get_user_group(path):
    """
    Retrieve the user and group associated with a given file or directory.
    """
    stat_info = os.stat(path)
    uid = stat_info.st_uid
    gid = stat_info.st_gid
    user = pwd.getpwuid(uid)[0]
    group = grp.getgrgid(gid)[0]

    return f'{user}:{group}'


def bcl_convert(rfpath: str, strict_mode='true') -> None:
    """
    Runs Illumina's bcl-convert tool in a Docker container
    """
    # Command to run the `bcl-convert` inside docker
    bcl_convert_cmd = f"docker run -d --rm \
    -v {rfpath}:/mnt/run \
    -v { os.path.join(rfpath, 'bclConvert')}:/mnt/output \
    -it --name bcl-convert rakabari/bcl-convert:3.9.3 \
            bcl-convert \
                --bcl-input-directory /mnt/run \
                --output-directory /mnt/output \
                --strict-mode {strict_mode} \
                --force \
                --no-lane-splitting true \
    &> /dev/null"
    subprocess.run('sudo systemctl start docker', shell=True, check=True)
    subprocess.run(bcl_convert_cmd, shell=True, check=True)


def run_bclconvert(rfpath: str):
    """
    Processes a single Illumina sequencing run by checking its status and converting its
    basecall files to FASTQ format if necessary.
    """
    rf = os.path.basename(rfpath)

    if not is_recent_run(rfpath, n=24):  # 24
        print(f'INFO: {rf}: Run is not recent or valid')
        return

    # print(f'INFO: {rf}: Run recent_Checking if run is complete...')
    if not is_run_complete(rfpath, n=300):  # 300
        print(f'INFO: {rf}: Run has not completed yet')
        return

    # print(f'INFO: {rf}: Checking if basecall conversion complete...')
    if is_b2f_complete(rfpath, n=20):  # 20
        print(f'INFO: {rf}: Basecall conversion already completed')
        return

    rename_samplesheet(rfpath)
    if not os.path.exists(os.path.join(rfpath, 'SampleSheet.csv')):
        print(f'ERROR: {rf}: No SampleSheet found!')
        return

    print(f'INFO: {rf}: Starting basecall conversion...')
    bcl_convert(rfpath)

    # Wait until the conversion completes on a detached process
    sleep(120)  # 120

    if is_b2f_complete(rfpath, n=20):  # 20
        print(f'INFO: {rf}: Basecall conversion completed')

        # Copy the `IndexMetricsOut.bin` file
        copy_index_bin(rfpath)

        # Change permissions to run, so it can later be moved
        user_group = get_user_group(rfpath)
        subprocess.run(f'sudo chown -R {user_group} {rfpath}',
                       shell=True, check=True)
    else:
        print(f'INFO: {rf}: Basecall conversion did not complete')
        print(f'ERROR: {rf}: {read_bclconvert_error(rfpath)}')


def run_bclconvert_on_output(output_dir: str):
    """
    To be able run the bcl-convert on a different directory
    """

    try:
        for rf in os.listdir(output_dir):
            run_bclconvert(os.path.join(output_dir, rf))
    except Exception as e:
        logging.exception(f'{e}')


if __name__ == '__main__':
    run_bclconvert_on_output(NGSDATA)
