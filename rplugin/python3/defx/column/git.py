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
        self.cwd = self.vim.call('getcwd')
        self.indicators = self.vim.vars['defx_git#indicators']
        self.column_length = self.vim.vars['defx_git#column_length']
        self.show_ignored = self.vim.vars['defx_git#show_ignored']
        self.colors = {
            'Modified': 'guifg=#fabd2f ctermfg=214',
            'Staged': 'guifg=#b8bb26 ctermfg=142',
            'Renamed': 'guifg=#fabd2f ctermfg=214',
            'Unmerged': 'guifg=#fb4934 ctermfg=167',
            'Untracked': 'guifg=NONE guibg=NONE ctermfg=NONE ctermbg=NONE',
            'Ignored': 'guifg=NONE guibg=NONE ctermfg=NONE ctermbg=NONE',
            'Unknown': 'guifg=NONE guibg=NONE ctermfg=NONE ctermbg=NONE'
        }

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

        return self.format(
            self.indicators[self.get_indicator_name(entry[0], entry[1])]
        )

    def length(self, context: Context) -> int:
        return self.column_length

    def highlight(self) -> None:
        for name, icon in self.indicators.items():
            self.vim.command((
                'syntax match {0}_{1} /[{2}]/ contained containedin={0}'
            ).format(self.syntax_name, name, icon))

            self.vim.command('highlight default {0}_{1} {2}'.format(
                self.syntax_name, name, self.colors[name]
            ))

    def find_in_cache(self, candidate: dict) -> str:
        path = str(candidate['action__path']).replace(f'{self.cwd}/', '')
        path += '/' if candidate['is_directory'] else ''
        for item in self.cache:
            if item[3:].startswith(path):
                return item

        return ''

    def cache_status(self, path: str) -> None:
        self.cache = []
        try:
            cmd = ['git', 'status', '--porcelain', '-u']
            if self.show_ignored:
                cmd += ['--ignored']

            cmd += [path]
            p = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            return None

        decoded = p.stdout.decode('utf-8')

        if not decoded:
            return None

        results = [line for line in decoded.split('\n') if line != '']
        self.cache = sorted(results, key=cmp_to_key(self.sort))

    def sort(self, a, b) -> int:
        if a[0] == 'U' or a[1] == 'U':
            return -1

        if (a[0] == 'M' or a[1] == 'M') and not (b[0] == 'U' or b[1] == 'U'):
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
        else:
            return 'Unknown'
