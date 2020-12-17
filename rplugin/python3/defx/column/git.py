# ============================================================================
# FILE: git.py
# AUTHOR: Kristijan Husak <husakkristijan at gmail.com>
# License: MIT license
# ============================================================================

import typing
import subprocess
from defx.base.column import Base, Highlights
from defx.context import Context
from defx.view import View
from defx.util import Nvim, Candidate, len_bytes
from functools import cmp_to_key
from pathlib import PurePath


class Column(Base):

    def __init__(self, vim: Nvim) -> None:
        super().__init__(vim)

        self.name = 'git'
        self.has_get_with_highlights = True
        self.vars = {
            'indicators': {
                'Modified': '✹',
                'Staged': '✚',
                'Untracked': '✭',
                'Renamed': '➜',
                'Unmerged': '═',
                'Ignored': '☒',
                'Deleted': '✖',
                'Unknown': '?'
            },
            'column_length': 1,
            'show_ignored': False,
            'raw_mode': False,
            'max_indicator_width': None,
            'git_commit': 'HEAD',
        }

        custom_opts = ['indicators', 'column_length', 'show_ignored',
                       'raw_mode', 'max_indicator_width']

        for opt in custom_opts:
            if 'defx_git#' + opt in self.vim.vars:
                self.vars[opt] = self.vim.vars['defx_git#' + opt]

        self.cache: typing.List[str] = []
        self.git_root = ''
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

    def on_init(self, view: View, context: Context) -> None:
        # Set vim global variable for search mappings matching indicators
        self.vim.vars['defx_git_indicators'] = self.vars['indicators']

        if not self.vars.get('max_indicator_width'):
            # Find longest indicator
            self.vars['max_indicator_width'] = len(
                max(self.vars['indicators'].values(), key=len))

        min_column_length = 2 if self.vars['raw_mode'] else 1
        self.column_length = max(min_column_length, self.vars['column_length'])

    def get_with_highlights(
            self, context: Context, candidate: Candidate
    ) -> typing.Tuple[str, Highlights]:
        default = (
            ''.ljust(self.column_length + self.vars['max_indicator_width'] - 1),
            []
        )
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
        state = self.get_indicator_name(entry[0], entry[1])

        if self.vars['raw_mode']:
            return self.format(entry[:2], state)

        return self.format(self.vars['indicators'][state], state)

    def length(self, context: Context) -> int:
        return self.column_length

    def highlight_commands(self) -> typing.List[str]:
        commands: typing.List[str] = []
        for name, icon in self.vars['indicators'].items():
            commands.append(('silent! syntax clear {0}_{1}')
                            .format(self.highlight_name, name))
            if self.vars['raw_mode']:
                commands.append((
                    'syntax match {0}_{1} /{2}/ contained containedin={3}'
                ).format(self.highlight_name, name, self.colors[name]['match'],
                         self.syntax_name))
            else:
                commands.append((
                    'syntax match {0}_{1} /[{2}]/ contained containedin={3}'
                ).format(self.highlight_name, name, icon, self.syntax_name))

            commands.append('highlight default {0}_{1} {2}'.format(
                self.highlight_name, name, self.colors[name]['color']
            ))

        return commands

    def find_in_cache(self, candidate: dict) -> str:
        action_path = PurePath(candidate['action__path']).as_posix()
        path = str(action_path).replace(f'{self.git_root}/', '')
        path += '/' if candidate['is_directory'] else ''
        for item in self.cache:
            item_path = item[3:]
            if ' ' in item_path and item_path[0] == '"':
                item_path = item_path.strip('"')

            if item[0] == 'R':
                item_path = item_path.split(' -> ')[1]

            if item_path.startswith(path):
                return item

        return ''

    def cache_status(self, path: str) -> None:
        self.cache = []

        if not self.git_root or not str(path).startswith(self.git_root):
            self.git_root = PurePath(self.run_cmd(
                ['git', 'rev-parse', '--show-toplevel'], path
            )).as_posix()

        if not self.git_root:
            return None

        if self.vars['git_commit'].upper() != 'HEAD':
            diff_cmd = ['git', 'diff', '--name-status', self.vars['git_commit']]
            results = [
                f" {line}".replace("\t", " ")
                for line
                in self.run_cmd(diff_cmd, self.git_root).split('\n')
                if line != ''
            ]

            untracked_cmd = ['git', 'ls-files', '--exclude-standard', '--others']
            if self.vars['show_ignored']:
                untracked_cmd += ['--ignored']

            results += [
                f"?? {line}"
                for line
                in self.run_cmd(untracked_cmd, self.git_root).split('\n')
                if line != ''
            ]

        else:
            cmd = ['git', 'status', '--porcelain', '-u']
            if self.vars['show_ignored']:
                cmd += ['--ignored']
            status = self.run_cmd(cmd, self.git_root)

            results = [line.replace('\t', ' ') for line in status.split('\n') if line != '']

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

    def format(self, column: str, indicator_name) -> str:
        icon = format(column, f'<{self.column_length}')
        return (icon,
            [(
                f'{self.highlight_name}_{indicator_name}',
                self.start, len_bytes(icon)
            )]
        )

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
        except:
            return ''

        decoded = p.stdout.decode('utf-8')

        if not decoded:
            return ''

        return decoded.strip('\n')
