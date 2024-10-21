# Source for jsteward.moe

Live here: https://jsteward.moe

The fastest way to build this is as a Nix flake.  Pushes to this repo will trigger the [flakes](https://github.com/KireinaHoro/flakes) repository to automatically bump and deploy.

## Development demo

Enable the git hook to automatically update `Modified` field of articles:

```shell
$ git config --local core.hooksPath .githooks/
```

Build the project:

```shell
$ nix build
$ python3 -m http.server --directory result --bind 127.0.0.1
```

The deployment root is located in `result/`.
