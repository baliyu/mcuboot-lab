# mcuboot-lab: MCUboot on an Arduino Nano 33 BLE

MCUboot running as a second-stage bootloader on an Arduino Nano 33 BLE (nRF52840) under Zephyr 4.4.2, kept behind the board's own Arduino bootloader so that USB flashing and double-tap recovery still work. Built to compare MCUboot with my own bootloader ([stm32l0-freertos-sensor-node](https://github.com/baliyu/stm32l0-freertos-sensor-node)).

Built with AI assistance (Claude). I ran the builds and the hardware, wrote down what each test showed, and checked the results. Everything marked "inferred" below is my reading of the evidence, not something the board reported.

## Flash layout

The Arduino bootloader at address 0 is never written. MCUboot sits after it, at the start of the area the Arduino bootloader jumps to.

| Address | Size | Contents |
|---|---|---|
| `0x00000` | 64 KB | Arduino bootloader (untouched) |
| `0x10000` | 64 KB | MCUboot |
| `0x20000` | 432 KB | slot 0, the running app |
| `0x8c000` | 432 KB | slot 1, reserved for updates (not used yet) |
| `0xf8000` | 32 KB | storage (unchanged board default) |

The layout is set by `boards/arduino_nano_33_ble.overlay` for the app and `sysbuild/mcuboot.overlay` for MCUboot. Both carry the same partitions.

## Configuration

- `sysbuild.conf`: MCUboot as the bootloader, ECDSA P-256 signatures, and the path to my own private signing key.
- `sysbuild/mcuboot.conf`: overwrite-only updates, downgrade prevention, and `CONFIG_BOOT_VALIDATE_SLOT0=y` (check the app in slot 0 on every boot).
- `VERSION`: the image version (1.0.0). `CONFIG_MCUBOOT_IMAGE_VERSION` does not exist in Zephyr 4.4.2.
- `prj.conf` and the overlay: console over USB (CDC ACM), so the app can print without extra hardware.

## Build

The signing key is not in this repository. Make your own and put its path in `sysbuild.conf`:

```
python3 ~/zephyrproject/bootloader/mcuboot/scripts/imgtool.py keygen -k lab-signing-key.pem -t ecdsa-p256
export ZEPHYR_BASE=$HOME/zephyrproject/zephyr
west build -b arduino_nano_33_ble --sysbuild .
```

## Flash

The Arduino bootloader's flasher writes at `0x10000` by itself, so I flash without an offset. MCUboot and the signed app are merged into one file that starts at `0x10000`. The merge refuses to write the file unless MCUboot starts at `0x10000` and ends below `0x20000`, and the app starts at `0x20000` and ends below `0x8c000`.

Then, with the board in bootloader mode (double-tap RESET until the orange LED fades), from PowerShell:

```
& $B --port=COM7 -U -i -e -w -v 'C:\zephyr_flash\lab_image.bin' -R
```

`$B` is the path to Arduino's `bossac.exe` (1.9.1-arduino2). A successful write ends with `Verify successful`.

## What I measured

| Item | Result |
|---|---|
| MCUboot size, first build | 29,604 B of its 64 KB region (45.17%). Not re-measured after adding the slot-0 check. |
| MCUboot RAM | 16,128 B (6.15%) |
| Signed test app | image payload 45,104 B (`0xb030`), 512-byte header, 150-byte signature block |
| Merged image | 111,302 B, from `0x10000` to `0x2b2c5` |
| Default signing key | the public development key from the MCUboot repository. Replaced with my own key. |

## Boot-time tests

The board has no console during MCUboot, so a refusal is seen only as "the app never started and its USB port never appeared".

| Test | Slot-0 check | Result |
|---|---|---|
| One bit flipped in the app, at `0x20400` | off | the app ran |
| The same bit flipped | on | no app, no USB port (inferred: refused) |
| Good image | on | runs, printing once a second |
| Intact image signed with a different key | on | no app, no USB port (inferred: refused by the signature check) |

The good image was reflashed after each failure and ran every time, so the board itself was not the cause.

## Compared with my own bootloader

| | My STM32L0 bootloader | MCUboot on this board |
|---|---|---|
| Size | 10,324 B | 29,604 B (first build) |
| Checks at boot | hash, signature and minimum version, every boot | only when `CONFIG_BOOT_VALIDATE_SLOT0` is on |
| Private key | off the device, backed up | off the device, not in this repository |
| Root of trust | bootloader write-protected, read-out protection Level 1 | none: the Arduino bootloader underneath is unsigned and unprotected |
| Update tested | power cut at 1,682 points of an install | not tested yet |

The two do different jobs, so the sizes are not a fair contest. MCUboot here is the overwrite-only build with ECDSA, and I have not looked at what else is compiled in.

## Not tested

- Updates from slot 1, and what happens if power is cut during one.
- Downgrade prevention: the setting is on, but I have not tried to install an older image.
- Swap-based updates (this build is overwrite-only).
- Other kinds of corruption. I flipped one bit, at one position.
- Any attack on the Arduino bootloader underneath, which can overwrite everything above it.
- One board and one app. Nothing here has been run on a second board.

## Lessons learned

- A stale `ZEPHYR_BASE` from an earlier project made the build read the wrong Zephyr tree and fail with confusing errors. Check it first.
- Zephyr aborts on any Kconfig warning, so an invented setting name stops the build. It also shows the setting name in the message.
- MCUboot's default signing key is public. Signing "works" with it, but anyone can sign an image the bootloader accepts.
- Slot-0 validation is not on by default here. With it off, an app with a flipped bit still ran.
- Sysbuild names the app's output folder after the project folder.
- Piping a long build into `head` can stop it early. Write the log to a file and search it.
- WSL and PowerShell take different syntax. Run each command in the window it was written for.

## Tools

Zephyr 4.4.2 · MCUboot · sysbuild · west · imgtool · Python (intelhex) · Arduino `bossac` 1.9.1-arduino2 · PuTTY · Arduino Nano 33 BLE
