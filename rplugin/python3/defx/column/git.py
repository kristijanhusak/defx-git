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

COLORS = {
    'Modified': 'guifg=#fabd2f ctermfg=214',
    'Added': 'guifg=#b8bb26 ctermfg=142',
    'Unmerged': 'guifg=#fb4934 ctermfg=167',
    'Default': 'guifg=NONE guibg=NONE ctermfg=NONE ctermbg=NONE'
}

INDICATORS = {
    'Modified': {'icon': '✹ ', 'color': COLORS['Modified']},
    'Staged': {'icon': '✚ ', 'color': COLORS['Added']},
    'Untracked': {'icon': '✭ ', 'color': COLORS['Default']},
    'Renamed': {'icon': '➜ ', 'color': COLORS['Modified']},
    'Unmerged': {'icon': '═ ', 'color': COLORS['Unmerged']},
    'Ignored': {'icon': '☒ ', 'color': COLORS['Default']},
    'Unknown': {'icon': '? ', 'color': COLORS['Default']},
}


def _get_indicator(us: str, them: str) -> str:
    if us == '?' and them == '?':
        return 'Untracked'
    elif us == ' ' and them == 'M':
        return 'Modified'
    elif us == '[MAC]':
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


def run_command(commands: typing.List[str]) -> typing.List[str]:
    try:
        p = subprocess.run(commands,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return []

    decoded = p.stdout.decode('utf-8')

    if not decoded:
        return []

    return [line for line in decoded.split('\n') if line != '']


class Column(Base):

    def __init__(self, vim: Nvim) -> None:
        super().__init__(vim)

        self.name = 'git'
        self.cache: typing.List[str] = []

    def _cache_status(self, path: str) -> None:
        self.cache = run_command(['git', 'status', '--porcelain', '-u', path])

    def get(self, context: Context, candidate: dict) -> str:
        default = '  '
        if candidate.get('is_root', False):
            self._cache_status(candidate['action__path'])
            return default

        if not self.cache:
            return default

        entry = self.find_cache_entry(candidate)

        if not entry:
            return default

        return INDICATORS[_get_indicator(entry[0], entry[1])]['icon']

    def find_cache_entry(self, candidate: dict) -> str:
        cwd = self.vim.call('getcwd')
        path = str(candidate['action__path']).replace(f'{cwd}/', '')
        for item in self.cache:
            if path in item[3:]:
                return item

        return ''

    def length(self, context: Context) -> int:
        return 2

    def highlight(self) -> None:
        icons = '\\\|'.join([x['icon'][:1] for x in INDICATORS.values()])
        self.vim.command(
            'nnoremap <silent><buffer> ]f :call search(\'\({}\)\')<CR>'
            .format(icons))
        self.vim.command(
            'nnoremap <silent><buffer> [f :call search(\'\({}\)\', \'b\')<CR>'
            .format(icons))
        for name, indicator in INDICATORS.items():
            self.vim.command(('syntax match {0}_{1} /[{2}]/ ' +
                              'contained containedin={0}').format(
                                 self.syntax_name, name, indicator['icon']
                             ))
            self.vim.command('highlight default {0}_{1} {2}'.format(
                self.syntax_name, name, indicator['color']
            ))
