## Demo Cache Bundle

This bundle mirrors the local `DemoStore` cache layout used by Bigym.

Contents:

- 55 successful `MovePlate` lightweight demos
- downsampled to `50 Hz`
- truncated at the first successful timestep

Layout:

```text
demo_cache_2026-04-14/
  .bigym/
    demonstrations/
      0.9.0/
        .lock
        MovePlate/
          JointPositionActionMode_floating_pelvis_x_pelvis_y_pelvis_z_pelvis_rz_absolute/
            lightweight/
              50hz/
                *.safetensors
```

Install on another machine:

```bash
cp -r demo_cache_2026-04-14/.bigym ~/
```

After that, Bigym will see these files under `~/.bigym/demonstrations/0.9.0/...`.

Notes:

- The `.lock` file marks the cache as present for `DemoStore`.
- This is a custom partial cache bundle, not the full upstream demo release.
- If you only want to replay files manually, you can also open `tools/demo_player/main.py`
  and point it at the `50hz` directory directly.
