#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File            : sync_repo.py
# Author          : Kai Wang <wkcosmology@gmail.com>
# Date            : 04.02.2019
# Last Modified By: Kai Wang <wkcosmology@gmail.com>
"""
This is a script to synchronise the git repo to the server
"""
import fnmatch
import os
import configparser
import warnings

import paramiko


class SyncRepo:

    """synchronise the git repo with server using scp"""

    def __init__(self, hostname=None, username=None, port=None, keyfile=None, remotepath=None, localpath=None, config_path=None, auto_search=False):
        """initialize the object

        Parameters
        ----------
        hostname : string
            the host name of the server
        username : string
            the user name
        port : int
            the port number
        keyfile : string
            the file path to the public key file
        remotepath : string
            the remote repo path on the server
        localpath : string
            the local repo path
        config_path : string
            the path of the config file
        auto_search : bool
            if True, then auto search the config file from current path
        """
        if auto_search:
            path = os.path.abspath(os.path.curdir)
            while True:
                if os.path.exists(os.path.join(path, ".git")):
                    break
                elif path == '/':
                    raise Exception("This file is not in a git repo")
                else:
                    path = os.path.dirname(path)
            config_path = os.path.join(path, ".sync_repo.conf")
            if not os.path.exists(config_path):
                raise Exception("Absence of the file: {0:s}".format(config_path))
            self._read_config(config_path)
        elif config_path is not None:
            self._read_config(config_path)
        else:
            self._hostname = hostname
            self._username = username
            self._port = port
            self._keyfile = keyfile
            self._remotepath = remotepath
            self._localpath = localpath
        if not os.path.exists(self._localpath):
            raise Exception("The local file path does not exist!")
        if not os.path.exists(os.path.join(self._localpath, ".git")):
            raise Exception("The local file path is not a git repo!")
        # connect to the server
        warnings.filterwarnings("ignore")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self._hostname, self._port, self._username, key_filename=self._keyfile)
        self._sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
        if not sftp_file_exist(self._sftp, self._remotepath):
            raise Exception("The remote file path does not exist!")

    def _read_config(self, config_path):
        """read the config file

        Parameters
        ----------
        config_path : string
            the file path to the config file
        """
        cf = configparser.ConfigParser()
        cf.read(config_path)
        self._hostname = cf.get("DEFAULT", "hostname")
        self._username = cf.get("DEFAULT", "username")
        self._port = cf.getint("DEFAULT", "port")
        self._keyfile = None
        self._remotepath = cf.get("DEFAULT", "remotepath")
        self._localpath = cf.get("DEFAULT", "localpath")


    def synchronise_repo(self):
        """synchronise the git repo"""
        local_files = get_repo_file_list(self._localpath)
        remote_files = replace_root(local_files, self._localpath, self._remotepath)
        for local_file, remote_file in zip(local_files, remote_files):
            if os.path.isdir(local_file) and not sftp_file_exist(self._sftp, remote_file):
                self._sftp.mkdir(remote_file)
            if os.path.isfile(local_file):
                self._sftp.put(local_file, remote_file)

    def synchronise_file(self, local_file):
        """synchronise the current file

        Parameters
        ----------
        local_file : string
            the local file need to synchronise
        """
        if os.path.commonprefix([self._localpath, local_file]) != self._localpath:
            raise Exception("This file is not in the git repo.")
        if not os.path.exists(local_file):
            raise Exception("the file {0:s} does not exist!".format(local_file))
        remote_file = replace_root([local_file], self._localpath, self._remotepath)[0]
        if not sftp_file_exist(self._sftp, os.path.dirname(remote_file)):
            sftp_makefiles(self._sftp, os.path.dirname(remote_file))
        self._sftp.put(local_file, remote_file)


def sftp_makefiles(sftp_client, path):
    """mkdir recursively though sftp client

    Parameters
    ----------
    sftp_client : SFTPClient
        the SFTPClient
    path : string
        the dir need to make
    """
    if sftp_file_exist(sftp_client, path):
        pass
    elif sftp_file_exist(sftp_client, os.path.dirname(path)):
        sftp_client.mkdir(path)
    else:
        sftp_makefiles(sftp_client, os.path.dirname(path))
        sftp_makefiles(sftp_client, path)


def sftp_file_exist(sftp_client, file_path):
    """test if the file is exist

    Parameters
    ----------
    sftp_client : SFTPClient
        the SFTPClient that has ssh connection
    file_path : string
        the path of the file, including the file name
    """
    try:
        sftp_client.stat(file_path)
        return True
    except IOError as e:
        # errno 2 means no such file
        if e.errno == 2:
            return False
        # if it is not no such file error, keep raise
        raise


def walk_tree_with_ignore(root_dir, ignore_list):
    """walk though the file tree with ignorence

    Parameters
    ----------
    root_dir : string
        the root directory to walk
    ignore_list : list
        the list contains the ignorence

    Returns
    -------
    the list contain the file path without ignorence

    """
    dirs = os.walk(root_dir)
    files_list = []
    for root, dirs, files in dirs:
        if fnmatch.fnmatch(root, '*.git*'):
            continue
        for d in dirs:
            if fnmatch.fnmatch(d, "*.git*"):
                continue
            files_list.append(os.path.join(root, d))
        for f in files:
            files_list.append(os.path.join(root, f))
    for ignore in ignore_list:
        ignore_path = os.path.join(root_dir, ignore)
        if ignore_path[-1] == '/':
            files_list = [f for f in files_list if not fnmatch.fnmatch(f, ignore_path[:-1])]
            files_list = [f for f in files_list if not fnmatch.fnmatch(f, ignore_path + "*")]
        else:
            files_list = [f for f in files_list if not fnmatch.fnmatch(f, ignore_path)]
    return files_list


def get_repo_file_list(root_dir):
    """get the file list of a git repo filter by the .gitignore

    Parameters
    ----------
    root_dir: string
        the root directory

    Returns
    -------
    the file list in the repo, considering the .gitignore

    """
    if not os.path.exists(os.path.join(root_dir, '.git')):
        raise Exception("This is not a git repo")
    ignore_list = []
    ignore_file = os.path.join(root_dir, '.gitignore')
    if os.path.exists(ignore_file):
        with open(ignore_file, "r") as f:
            for line in f.readlines():
                if not line.strip() or line[0] == '#':
                    continue
                ignore_list.append(line.strip())
    files_list = walk_tree_with_ignore(root_dir, ignore_list)
    return files_list


def replace_root(files_list, old_root, new_root):
    """replace the root of the path

    Parameters
    ----------
    files_list : list
        the file_list starts with the old_root
    old_root : string
        the old root directory
    new_root : string
        the new root directory

    Returns
    -------
    the file list starts with the new root

    """
    relpath_list = [os.path.relpath(file, old_root) for file in files_list]
    return [os.path.join(new_root, relpath) for relpath in relpath_list]
