# Source for jsteward.moe

Live here: https://jsteward.moe

The fastest way to build this is as a Nix flake.  Pushes to this repo will trigger the [flakes](https://github.com/KireinaHoro/flakes) repository to automatically bump and deploy.

## Development demo

Build the project:

```shell
$ nix build
```

The deployment root is located in `result/`.
