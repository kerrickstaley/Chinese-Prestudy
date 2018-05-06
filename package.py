#!/usr/bin/env python3
import os
import requests
import shutil
import subprocess
import tempfile
from urllib import request

SOURCE_FILES = [
  '__init__.py',
]

DEPENDENCIES = [
  'jieba',
  'cached_property',
  'genanki',
]

PACKAGE_CACHE_DIR = 'package_cache'


def prepare_package_dir_and_zip():
  shutil.rmtree('package', ignore_errors=True)
  os.mkdir('package')
  try:
    os.remove('package.zip')
  except OSError as e:
    if e.errno != 2:
      raise


def copy_source_files():
  for f in SOURCE_FILES:
    dirname, filename = os.path.split(f)
    target_dirname = os.path.join('package', dirname)
    os.makedirs(target_dirname, exist_ok=True)
    shutil.copy(f, target_dirname)


def retrieve_with_cache(url, dest_path):
  os.makedirs(PACKAGE_CACHE_DIR, exist_ok=True)

  filename = url.split('/')[-1]
  cached_path = os.path.join(PACKAGE_CACHE_DIR, filename)

  if not os.path.exists(cached_path):
    request.urlretrieve(url, cached_path)

  shutil.copy(cached_path, dest_path)


def copy_dependencies():
  for dep_pkg_name in DEPENDENCIES:
    metadata = requests.get(f'https://pypi.org/pypi/{dep_pkg_name}/json').json()
    latest_release = metadata['info']['version']
    url = metadata['releases'][latest_release][-1]['url']
    filename = url.split('/')[-1]

    tmpdir = tempfile.mkdtemp()
    retrieve_with_cache(url, os.path.join(tmpdir, filename))

    if filename.endswith('.zip'):
      subprocess.check_output(['unzip', filename], cwd=tmpdir)
      dirname = filename[:-len('.zip')]
    elif filename.endswith('.tar.gz'):
      subprocess.check_output(['tar', '-xzf', filename], cwd=tmpdir)
      dirname = filename[:-len('.tar.gz')]
    else:
      raise Exception(f'Unrecognized package format! {filename}')

    try:
      # this works if it's a directory
      shutil.move(os.path.join(tmpdir, dirname, dep_pkg_name), 'package')
    except FileNotFoundError:
      # this works if it's a simple .py file
      shutil.move(os.path.join(tmpdir, dirname, f'{dep_pkg_name}.py'), 'package')


def create_package_zip_file():
  subprocess.check_call(['zip', '../package.zip', '-r', '.'], cwd='package')


prepare_package_dir_and_zip()
copy_source_files()
copy_dependencies()
create_package_zip_file()
