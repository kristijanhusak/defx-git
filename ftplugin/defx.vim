scriptencoding utf-8
if exists('b:defx_git_loaded')
  finish
endif

let b:defx_git_loaded = 1

function! s:search(dir) abort
  let l:column_opts = defx#custom#_get().column
  let l:icons = get(get(l:column_opts, 'git', {}), 'indicators', {})
  let l:icons_pattern = join(values(l:icons), '\|')

  if !empty(l:icons_pattern)
    let l:direction = a:dir > 0 ? 'w' : 'bw'
    return search(printf('\(%s\)', l:icons_pattern), l:direction)
  endif
endfunction

nnoremap <buffer><silent><Plug>(defx-git-next) :<C-u>call <sid>search(1)<CR>
nnoremap <buffer><silent><Plug>(defx-git-prev) :<C-u>call <sid>search(-1)<CR>

if !hasmapto('<Plug>(defx-git-prev)') && maparg('[c', 'n') ==? ''
  silent! nmap <buffer><unique><silent> [c <Plug>(defx-git-prev)
endif

if !hasmapto('<Plug>(defx-git-next)') && maparg(']c', 'n') ==? ''
  silent! nmap <buffer><unique><silent> ]c <Plug>(defx-git-next)
endif
