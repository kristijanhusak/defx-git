scriptencoding utf-8
if exists('b:defx_git_loaded')
  finish
endif

let b:defx_git_loaded = 1

let g:defx_git#indicators = get(g:, 'defx_git#indicators', {
      \ 'Modified'  : '✹',
      \ 'Staged'    : '✚',
      \ 'Untracked' : '✭',
      \ 'Renamed'   : '➜',
      \ 'Unmerged'  : '═',
      \ 'Ignored'   : '☒',
      \ 'Deleted'   : '✖',
      \ 'Unknown'   : '?'
      \ })

let g:defx_git#column_length = get(g:, 'defx_git#column_length', 1)
let g:defx_git#show_ignored = get(g:, 'defx_git#show_ignored', 0)
let g:defx_git#raw_mode = get(g:, 'defx_git#raw_mode', 0)

let s:icons = join(values(g:defx_git#indicators), '\|')

function! s:search(dir) abort
  let l:direction = a:dir > 0 ? 'w' : 'bw'
  return search(printf('\(%s\)', s:icons), l:direction)
endfunction

nnoremap <buffer><silent><Plug>(defx-git-next) :<C-u>call <sid>search(1)<CR>
nnoremap <buffer><silent><Plug>(defx-git-prev) :<C-u>call <sid>search(-1)<CR>

if !hasmapto('<Plug>(defx-git-prev)') && maparg('[c', 'n') ==? ''
  silent! nmap <buffer><unique><silent> [c <Plug>(defx-git-prev)
endif

if !hasmapto('<Plug>(defx-git-next)') && maparg(']c', 'n') ==? ''
  silent! nmap <buffer><unique><silent> ]c <Plug>(defx-git-next)
endif
