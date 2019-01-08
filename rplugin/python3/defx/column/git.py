# ============================================================================
# FILE: git.py
# AUTHOR: Kristijan Husak <husakkristijan at gmail.com>
# License: MIT license
# ============================================================================

import typing
import subprocess
from defx.base.column import Base
from defx.context import Context
from neovim import Nvim
from functools import cmp_to_key


class Column(Base):

    def __init__(self, vim: Nvim) -> None:
        super().__init__(vim)

        self.name = 'git'
        self.cache: typing.List[str] = []
        self.git_root = ''
        self.indicators = self.vim.vars['defx_git#indicators']
        self.show_ignored = self.vim.vars['defx_git#show_ignored']
        self.raw_mode = self.vim.vars['defx_git#raw_mode']
        self.colors = {
            'Modified': {
                'color': 'guifg=#fabd2f ctermfg=214',
                'match': ' M'
            },
            'Staged': {
                'color': 'guifg=#b8bb26 ctermfg=142',
                'match': '\(M\|A\|C\).'
            },
            'Renamed': {
                'color': 'guifg=#fabd2f ctermfg=214',
                'match': 'R.'
            },
            'Unmerged': {
                'color': 'guifg=#fb4934 ctermfg=167',
                'match': '\(UU\|AA\|DD\)'
            },
            'Deleted': {
                'color': 'guifg=#fb4934 ctermfg=167',
                'match': ' D'
            },
            'Untracked': {
                'color': 'guifg=NONE guibg=NONE ctermfg=NONE ctermbg=NONE',
                'match': '??'
            },
            'Ignored': {
                'color': 'guifg=NONE guibg=NONE ctermfg=NONE ctermbg=NONE',
                'match': '!!'
            },
            'Unknown': {
                'color': 'guifg=NONE guibg=NONE ctermfg=NONE ctermbg=NONE',
                'match': 'X '
            }
        }
        min_column_length = 2 if self.raw_mode else 1
        self.column_length = max(min_column_length,
                                 self.vim.vars['defx_git#column_length'])

    def get(self, context: Context, candidate: dict) -> str:
        default = self.format('')
        if candidate.get('is_root', False):
            self.cache_status(candidate['action__path'])
            return default

        if not self.cache:
            return default

        entry = self.find_in_cache(candidate)

        if not entry:
            return default

        return self.get_indicator(entry)

    def get_indicator(self, entry: str) -> str:
        if self.raw_mode:
            return self.format(entry[:2])

        return self.format(
            self.indicators[self.get_indicator_name(entry[0], entry[1])]
        )

    def length(self, context: Context) -> int:
        return self.column_length

    def highlight(self) -> None:
        for name, icon in self.indicators.items():
            self.vim.command(f'silent! syntax clear {self.syntax_name}_{name}')
            if self.raw_mode:
                self.vim.command((
                    'syntax match {0}_{1} /{2}/ contained containedin={0}'
                ).format(self.syntax_name, name, self.colors[name]['match']))
            else:
                self.vim.command((
                    'syntax match {0}_{1} /[{2}]/ contained containedin={0}'
                ).format(self.syntax_name, name, icon))

            self.vim.command('highlight default {0}_{1} {2}'.format(
                self.syntax_name, name, self.colors[name]['color']
            ))

    def find_in_cache(self, candidate: dict) -> str:
        path = str(candidate['action__path']).replace(f'{self.git_root}/', '')
        path += '/' if candidate['is_directory'] else ''
        for item in self.cache:
            item_path = item[3:]
            if item[0] == 'R':
                item_path = item_path.split(' -> ')[1]

            if item_path.startswith(path):
                return item

        return ''

    def cache_status(self, path: str) -> None:
        self.cache = []

        if not self.git_root or not str(path).startswith(self.git_root):
            self.git_root = self.run_cmd(
                ['git', 'rev-parse', '--show-toplevel'], path
            )

        if not self.git_root:
            return None

        cmd = ['git', 'status', '--porcelain', '-u']
        if self.show_ignored:
            cmd += ['--ignored']

        status = self.run_cmd(cmd, self.git_root)
        results = [line for line in status.split('\n') if line != '']
        self.cache = sorted(results, key=cmp_to_key(self.sort))

    def sort(self, a, b) -> int:
        if a[0] == 'U' or a[1] == 'U':
            return -1

        if (a[0] == 'M' or a[1] == 'M') and not (b[0] == 'U' or b[1] == 'U'):
            return -1

        if ((a[0] == '?' and a[1] == '?') and not
                (b[0] in ['M', 'U'] or b[1] in ['M', 'U'])):
            return -1

        return 1

    def format(self, column: str) -> str:
        return format(column, f'<{self.column_length}')

    def get_indicator_name(self, us: str, them: str) -> str:
        if us == '?' and them == '?':
            return 'Untracked'
        elif us == ' ' and them == 'M':
            return 'Modified'
        elif us in ['M', 'A', 'C']:
            return 'Staged'
        elif us == 'R':
            return 'Renamed'
        elif us == '!':
            return 'Ignored'
        elif (us == 'U' or them == 'U' or us == 'A' and them == 'A'
              or us == 'D' and them == 'D'):
            return 'Unmerged'
        elif them == 'D':
            return 'Deleted'
        else:
            return 'Unknown'

    def run_cmd(self, cmd: typing.List[str], cwd=None) -> str:
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, cwd=cwd)
        except subprocess.CalledProcessError:
            return ''

        decoded = p.stdout.decode('utf-8')

        if not decoded:
            return ''

        return decoded.strip('\n')
