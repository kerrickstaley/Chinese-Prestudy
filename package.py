#!/usr/bin/env python3
import glob
import os
import re
import requests
import shutil
import subprocess
import tempfile
from urllib import request

SOURCE_FILES = [
  '__init__.py',
]

DEPENDENCIES_PYPI = [
  'jieba',
  'cached_property',
]

DEPENDENCIES_LOCAL = [
  'chinese_vocab_list',
  'chineseflashcards',
  'pystache',
  'yaml',
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


def copy_dependencies_from_pypi():
  for dep_pkg_name in DEPENDENCIES_PYPI:
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

def _extract_version(path):
  dirname = os.path.split(path)[-1]
  return re.search(r'[0-9]+(\.[0-9]+)*', dirname).group(0)

def _version_to_tuple(ver_str):
  return tuple(int(piece) for piece in ver_str.split('.'))

def copy_dependencies_from_local():
  for dep_pkg_name in DEPENDENCIES_LOCAL:
    dirpaths = glob.glob(f'/usr/lib/python3.6/site-packages/{dep_pkg_name}*')
    if len(dirpaths) > 1:
      dirpaths.sort(key=lambda p: _version_to_tuple(_extract_version(p)))
    dirpath = dirpaths[-1]
    subdirpath = os.path.join(dirpath, dep_pkg_name)
    if os.path.exists(subdirpath):
      dirpath = subdirpath
    shutil.copytree(dirpath, f'package/{dep_pkg_name}', ignore=shutil.ignore_patterns('__pycache__'))

def create_package_zip_file():
  subprocess.check_call(['zip', '../package.zip', '-r', '.'], cwd='package')


prepare_package_dir_and_zip()
copy_source_files()
copy_dependencies_from_pypi()
copy_dependencies_from_local()
create_package_zip_file()
