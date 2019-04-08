if !has("python3")
  echo "should with python3 support to run this script"
  finish
endif

let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

py3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
from sync_repo import *
EOF

function! sync_repo#syncrepo()
  py3 SyncRepo(auto_search=True).synchronise_repo()
  echo "Synchronise git repo done!"
endfunction

function! sync_repo#synccurrentfile()
  py3 import vim
  py3 SyncRepo(auto_search=True).synchronise_file(vim.eval('expand("%:p")'))
  echo "Synchronise current file done!"
endfunction
