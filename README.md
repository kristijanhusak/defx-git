# defx-git
Git status implementation for [defx.nvim](http://github.com/Shougo/defx.nvim).

## Usage
Just append `git` to your columns when starting defx:
```
:Defx -columns=git:mark:filename:type
```

## Options
### g:defx_git#indicators

Which indicators (icons) to use for each status. These are the defaults:
```vimL
let g:defx_git#indicators = {
  \ 'Modified'  : '✹',
  \ 'Staged'    : '✚',
  \ 'Untracked' : '✭',
  \ 'Renamed'   : '➜',
  \ 'Unmerged'  : '═',
  \ 'Ignored'   : '☒',
  \ 'Deleted'   : '✖',
  \ 'Unknown'   : '?'
  \ }
```

### g:defx_git#column_length

How many space should git column take. Default is `1` (Defx adds a single space between columns):
```vimL
let g:defx_git#column_length = 1
```
Missing characters to match this length are populated with spaces, which means
`✹` becomes `✹ `, etc.

Note: Make sure indicators are not longer than the column_length

### g:defx_git#show_ignored

This flag determines if ignored files should be marked with indicator. Default is `false`:

```vimL
let g:defx_git#show_ignored = 0
```

### g:defx_git#raw_mode

Show git status in raw mode (Same as first two chars of `git status --porcelain` command). Default is `0`:

```vimL
let g:defx_git#raw_mode = 1
```

## Highlighting

Each indicator type can be overridden with the custom highlight. These are the defaults:

```vimL
hi Defx_git_Untracked guibg=NONE guifg=NONE ctermbg=NONE ctermfg=NONE
hi Defx_git_Ignored guibg=NONE guifg=NONE ctermbg=NONE ctermfg=NONE
hi Defx_git_Unknown guibg=NONE guifg=NONE ctermbg=NONE ctermfg=NONE
hi Defx_git_Renamed ctermfg=214 guifg=#fabd2f
hi Defx_git_Modified ctermfg=214 guifg=#fabd2f
hi Defx_git_Unmerged ctermfg=167 guifg=#fb4934
hi Defx_git_Deleted ctermfg=167 guifg=#fb4934
hi Defx_git_Staged ctermfg=142 guifg=#b8bb26
```

To use for example red for untracked files, add this **after** your colorscheme setup:

```vimL
colorscheme gruvbox
hi Defx_git_Untracked guifg=#FF0000
```

## Mappings

There are two mappings:
* `<Plug>(defx-git-next)` - Goes to the next file that has a git status
* `<Plug>(defx-git-prev)` - Goes to the prev file that has a git status

If these are not manually mapped by the user, defaults are:

```vimL
nnoremap <buffer><silent> [c <Plug>(defx-git-prev)
nnoremap <buffer><silent> ]c <Plug>(defx-git-next)
```
