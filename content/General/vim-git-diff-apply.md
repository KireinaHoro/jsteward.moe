Title: Separate whitespace problems from real change in git with vim
Date: 2021-08-10 01:27
Modified: 2021-08-10 01:27
Category: General
Tags: vim, git
Slug: vim-git-diff-apply
Status: published

Whitespace changes can be annoying, especially when we have colleagues that do not care so much about them.  If we care about whitespace correctness, we probably have whitespace indicators and trimmers configured in vim:

```vim
" Removes trailing spaces
function! TrimWhiteSpace()
    " Only strip if the b:noStripWhitespace variable isn't set
    if exists('b:noStripWhitespace')
        return
    endif
    %s/\s*$//
    ''
endfunction

" Control characters expansion
set list listchars=tab:»-,trail:.,eol:↲,extends:»,precedes:«,nbsp:%
au FileType diff let b:noStripWhitespace=1
au FileWritePre * call TrimWhiteSpace()
au FileAppendPre * call TrimWhiteSpace()
au FilterWritePre * call TrimWhiteSpace()
au BufWritePre * call TrimWhiteSpace()
```

Then our fixer will fix the whitespace errors our colleagues introduced as we work.  Great, but things break down quickly when we try to use the `--patch` option of `git-add(1)`, `git-checkout(1)`, or similar utilities to selectively and interactively manipulate our changes, either for staging changes for commit, or partially dropping changes: whitespace corrections spam the interactive sessions, making it extremely difficult to navigate through.  Well, with a bit of experience in editting `diff`s, this situation can be neatly handled using vim's pipe read and write functionality.

Note: this post is based on these two StackOverflow posts: [this](https://stackoverflow.com/questions/6571643/how-can-you-combine-git-add-patch-p-mode-with-diffs-ignore-all-space) and [this](https://stackoverflow.com/questions/24442069/is-there-a-way-to-show-only-whitespace-differences-with-git-diff/63904526#63904526).

## Reading in a clean diff without whitespace changes

What we want to do here is to get the real changes free of whitespace corrections for editting.  The basic Ex command is:

```
:set ft=diff | r !git diff -U0 -w
```

Piece by piece:

- `set ft=diff` sets the current file type to diff, triggering any `autocmd`s there may be in our local config (e.g. to disable the space trimmer).  This also gets us syntax highlighting.
- `r` reads the output of `git-diff(1)` into the current (anonymous) buffer for editting.
- `-U0` makes git generate 0 lines of context for the resulting patch.  This is important!  See the explanation below.
- finally, `-w` ignores all *whitespace changes* in our diff, leaving them for process at a later time.

Refer to the manual page for detailed explanations of options.  Note that the 0 line context option is important because as we're ignoring whitespace changes, the context may be out of sync with HEAD.  By dropping the contexts we make the patch applicable.

We can now proceed to edit the patches as normal, just like what we'd do using the `e` action during `--patch`.

## To stage a subset of changes (add to cache)

We want to delete all currently unwanted changes in the patch.  Use the following Ex command to stage the changes:

```
:w !git apply --unidiff-zero --ignore-whitespace --cached
```

Piece by piece:

- `w` writes the buffer to the input of `git-apply(1)`.
- `--unidiff-zero` makes git accept the `-U0` patch generated earlier.
- `--ignore-whitespace` makes git ignore whitespaces in context lines.
- `--cached` makes git apply into the staging area, keeping the tree untouched.  This is essentially the `git-add(1)` behavior.

## To drop changes from working tree

We want to delete everything other than the changes we want to drop.  The resulting patch is then applied **in reverse** with the following:

```
:w !git apply -R --unidiff-zero --ignore-whitespace
```

Piece by piece:

- `-R` applies the patch in reverse, essentially reverting the changes.
- no `--cached` option means that we operate on the working tree.

It is recommended to stash the working tree beforehand to avoid any unexpected loss of work.
