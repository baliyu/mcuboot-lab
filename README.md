# mcuboot-lab: MCUboot on an Arduino Nano 33 BLE

MCUboot running as a second-stage bootloader on an Arduino Nano 33 BLE (nRF52840) under Zephyr 4.4.2, kept behind the board's own Arduino bootloader so that USB flashing and double-tap recovery still work. Built to compare MCUboot with my own bootloader ([stm32l0-freertos-sensor-node](https://github.com/baliyu/stm32l0-freertos-sensor-node)).

Built with AI assistance (Claude). I ran the builds and the hardware, wrote down what each test showed, and checked the results. Everything marked "inferred" below is my reading of the evidence, not something the board reported.

## Flash layout

The Arduino bootloader at address 0 is never written. MCUboot sits after it, at the start of the area the Arduino bootloader jumps to.

| Address | Size | Contents |
|---|---|---|
| `0x00000` | 64 KB | Arduino bootloader (untouched) |
| `0x10000` | 64 KB | MCUboot |
| `0x20000` | 128 KB | slot 0, the running app |
| `0x40000` | 128 KB | slot 1, where an update is placed |
| `0x60000` to `0xf7fff` | 608 KB | unused |
| `0xf8000` | 32 KB | storage (unchanged board default) |

The layout is set by `boards/arduino_nano_33_ble.overlay` for the app and `sysbuild/mcuboot.overlay` for MCUboot. Both carry the same partitions.

## Configuration

- `sysbuild.conf`: MCUboot as the bootloader, ECDSA P-256 signatures, the path to my own private signing key, and `SB_CONFIG_MCUBOOT_MODE_OVERWRITE_ONLY=y`. The update mode has to be set here. Setting `CONFIG_BOOT_UPGRADE_ONLY` in `sysbuild/mcuboot.conf` alone was overridden: sysbuild had chosen swap-using-offset.
- `sysbuild/mcuboot.conf`: downgrade prevention and `CONFIG_BOOT_VALIDATE_SLOT0=y` (check the app in slot 0 on every boot).
- `VERSION`: the image version. `CONFIG_MCUBOOT_IMAGE_VERSION` does not exist in Zephyr 4.4.2.
- `prj.conf` and the overlay: console over USB (CDC ACM), so the app can print without extra hardware.

## Build

The signing key is not in this repository. Make your own and put its path in `sysbuild.conf`:

```
python3 ~/zephyrproject/bootloader/mcuboot/scripts/imgtool.py keygen -k lab-signing-key.pem -t ecdsa-p256
export ZEPHYR_BASE=$HOME/zephyrproject/zephyr
west build -b arduino_nano_33_ble --sysbuild .
```

## Flash

The Arduino bootloader's flasher writes at `0x10000` by itself, so I flash without an offset. MCUboot, the app in slot 0 and, for an update test, the update in slot 1 are merged into one file that starts at `0x10000`. The merge refuses to write the file unless MCUboot starts at `0x10000` and ends below `0x20000`, and the app starts at `0x20000` and ends below `0x40000`.

An update is prepared with `imgtool sign --pad --slot-size 0x20000`, which also writes the "update waiting" marker at the end of the slot. The result is placed at `0x40000`.

Then, with the board in bootloader mode (double-tap RESET until the orange LED fades), from PowerShell:

```
& $B --port=COM7 -U -i -e -w -v 'C:\zephyr_flash\lab_image.bin' -R
```

`$B` is the path to Arduino's `bossac.exe` (1.9.1-arduino2). A successful write ends with `Verify successful`.

## Tests

The board has no console during MCUboot, so a refusal is seen only as "the app never started and its USB port never appeared". Two builds were tested, and each row names its build.

**Build A: swap-using-offset (sysbuild's default), 432 KB slots**

| Test | Slot-0 check | Result |
|---|---|---|
| One bit flipped in the app, at `0x20400` | off | the app ran |
| The same bit flipped | on | no app, no USB port (inferred: refused) |
| Good image | on | runs, printing once a second |
| Intact image signed with a different key | on | no app, no USB port (inferred: refused by the signature check) |
| Update from slot 1 | on | ignored (inferred: this mode wants the update at the second sector of slot 1; I did not test that) |

**Build B: overwrite-only, 128 KB slots**

| Test | Slot-0 check | Result |
|---|---|---|
| Good image | on | runs v1.0.0 |
| v1.0.1 signed and placed in slot 1, v1.0.0 in slot 0 | on | the board printed v1.0.1, so the update installed |
| v0.9.0 signed and placed in slot 1, v1.0.1 in slot 0 | on | the board kept printing v1.0.1 (inferred: downgrade refused) |
| One bit flipped in the app, at `0x20400` | on | no app (inferred: refused) |
| Intact image signed with a different key | on | not yet run on this build |

The good image was reflashed after each failure and ran every time, so the board itself was not the cause.

## What I measured

| Item | Result |
|---|---|
| MCUboot size, first build (swap-using-offset) | 29,604 B of its 64 KB region (45.17%). Not re-measured on the overwrite-only build. |
| MCUboot RAM, first build | 16,128 B (6.15%) |
| Signed test app | image payload 45,104 B (`0xb030`), 512-byte header, 150-byte signature block |
| Image written for a test | 111,302 B for MCUboot plus one app; 327,680 B when slot 1 is included |
| Default signing key | the public development key from the MCUboot repository. Replaced with my own key. |

## Compared with my own bootloader

| | My STM32L0 bootloader | MCUboot on this board |
|---|---|---|
| Size | 10,324 B | 29,604 B (first build) |
| Checks at boot | hash, signature and minimum version, every boot | only when `CONFIG_BOOT_VALIDATE_SLOT0` is on |
| Update | overwrite, power cut simulated at 1,682 points | overwrite-only update installed; no power-cut test |
| Downgrade | refused, tested on hardware | refused (inferred), tested on hardware |
| Private key | off the device, backed up | off the device, not in this repository |
| Root of trust | bootloader write-protected, read-out protection Level 1 | none: the Arduino bootloader underneath is unsigned and unprotected |

The two do different jobs, so the sizes are not a fair contest. I have not looked at what else is compiled into MCUboot.

## Not tested

- Power cut during an update.
- Swap-based updates with rollback. Build A was swap-using-offset, but its update never ran.
- A wrong-key image on the overwrite-only build.
- Other kinds of corruption. I flipped one bit, at one position.
- Any attack on the Arduino bootloader underneath, which can overwrite everything above it.
- One board and one app. Nothing here has been run on a second board.

## Lessons learned

- A stale `ZEPHYR_BASE` from an earlier project made the build read the wrong Zephyr tree and fail with confusing errors. Check it first.
- Zephyr aborts on any Kconfig warning, so an invented setting name stops the build.
- With sysbuild, the update mode is a sysbuild setting. Putting an MCUboot setting in `mcuboot.conf` was silently overridden. I only found out by reading the finished `.config`.
- MCUboot's default signing key is public. Signing "works" with it, but anyone can sign an image the bootloader accepts.
- Slot-0 validation is not on by default here. With it off, an app with a flipped bit still ran.
- A 950 KB write to the Arduino bootloader failed three times at 89%; a 320 KB write flashed fine. I changed the layout at the same time, so I cannot say the length alone was the cause.
- Leave slot 1 blank before a refusal test, or an old update there can change the result.
- Sysbuild names the app's output folder after the project folder.
- Piping a long build into `head` can stop it early. Write the log to a file and search it.
- WSL and PowerShell take different syntax. Run each command in the window it was written for.

## Tools

Zephyr 4.4.2 · MCUboot · sysbuild · west · imgtool · Python (intelhex) · Arduino `bossac` 1.9.1-arduino2 · PuTTY · Arduino Nano 33 BLE
