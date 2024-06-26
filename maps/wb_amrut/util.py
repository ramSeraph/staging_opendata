import time
import subprocess
from pathlib import Path

def run_external(cmd):
    print(f'running cmd - {cmd}')
    start = time.time()
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end = time.time()
    print(f'STDOUT: {res.stdout}')
    print(f'STDERR: {res.stderr}')
    print(f'command took {end - start} secs to run')
    if res.returncode != 0:
        raise Exception(f'command {cmd} failed')


def compress_file(file, sfile):
    cfile = Path(str(file) + '.7z')
    if not cfile.exists():
        run_external(f'7z a -m0=PPMd "{cfile}" "{file}"')
        file.unlink()
    sfile.write_text('compressed')


def transfer_file(data_folder_name, file, sfile, bucket_name):
    cfile = Path(str(file) + '.7z')
    suffix = str(cfile).removeprefix(f'{data_folder_name}/')
    if cfile.exists():
        to = f'gs://{bucket_name}/{suffix}'
        run_external(f'gsutil -m cp "{cfile}" "{to}"')
        cfile.unlink()
    sfile.write_text('done')


success_states = ['done', 'not_layer', 'ignore']

def mark_as_done(data_folder, layer_file, layer_file_status):
    status = layer_file_status.read_text().strip()
    if status == 'downloaded':
        status = 'done'
        layer_file_status.write_text(status)
    return status in success_states


def compress_and_push_to_gcs(data_folder, layer_file, layer_file_status, bucket_name=None):
    if bucket_name is None:
        raise Exception('bucket name needs to be provided')

    status = layer_file_status.read_text().strip()
    if status == 'downloaded':
        compress_file(layer_file, layer_file_status)
    status = layer_file_status.read_text().strip()
    if status == 'compressed':
        transfer_file(str(data_folder), layer_file, layer_file_status, bucket_name)
    status = layer_file_status.read_text().strip()
    return status in success_states
