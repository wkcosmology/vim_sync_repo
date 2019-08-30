# Introduction
This package is to synchronize the local git repository to remote, like Linux server. This package only synchronize files allowed by the .gitignore file.

The goal of this package is to let people write their code on your laptop and run the program on server. Though git itself can synchronize the file to the server, but you need to commit the modification first and push it. Consequently, it is not convenient for debugging. This package only supports one-way file transformation, since this will avoid any problem in synchronization.

  > WARNING:
  > When you synchronize the repository, it will delete all the files in the git repository, so you need to save your result or data file in the path outside.

Besides, this file also need a `.sync_repo.conf` file in the same path of `.git` file. For example
```py
[DEFAULT]
hostname = server.address
username = username
port = port
remotepath = /remote/path/to/git/repo/
localpath = /local/path/to/git/repo
```

# Commands

1. `:SyncRepo`: This command will first delete all the files in the remote path and upload all the files recursively allowed by the `.gitignore` file to the remote path.
2. `:SyncFile`: This command will synchronize current activate buffer to the remote path.
