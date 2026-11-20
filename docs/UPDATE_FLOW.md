# Update flow of the overwrite-only build

This diagram shows what the board did in the overwrite-only build (Build B in the README): MCUboot at `0x10000`, slot 0 at `0x20000`, slot 1 at `0x40000`, slot-0 check on. Each arrow says whether I saw it on the hardware (tested) or worked it out from timings or from what the board printed (inferred). I never read the flash, and the board has no console during MCUboot.

```mermaid
stateDiagram-v2
    [*] --> ArduinoBootloader : reset
    ArduinoBootloader --> ArduinoBootloader : double tap keeps it in bootloader mode (tested)
    ArduinoBootloader --> MCUboot : no double tap, MCUboot runs from about 0.6 s (inferred from port timings)
    MCUboot --> UpdateCheck : starts
    UpdateCheck --> Install : update waiting marker in slot 1, newer version (tested)
    UpdateCheck --> CheckSlot0 : no update waiting (tested)
    UpdateCheck --> CheckSlot0 : older version in slot 1, update skipped (inferred)
    Install --> CheckSlot0 : slot 1 copied to slot 0, done at about 2.455 s (tested)
    Install --> MCUboot : reset during the copy, install starts again (inferred from timing)
    CheckSlot0 --> AppRuns : slot 0 check passes (tested)
    CheckSlot0 --> NoApp : one bit flipped in the app (inferred)
    AppRuns --> [*]
    NoApp --> [*]
    note right of AppRuns : USB port up at 1.31 s with no update, 3.41 s after an update
    note right of NoApp : no app and no USB port
```

## Where each arrow comes from

| Arrow | Evidence |
|---|---|
| Install, then CheckSlot0 | v1.0.1 in slot 1 and v1.0.0 in slot 0: the board printed v1.0.1 |
| Reset during the copy | 177 trials updated; cuts up to 2.44 s gave a port about 3.4 s later, the same as an uninterrupted update |
| Reset after the copy | cuts from 2.46 s gave a port about 1.2 s later, so the update had finished |
| Older version skipped | v0.9.0 in slot 1 and v1.0.1 in slot 0: the board kept printing v1.0.1 |
| NoApp | one bit flipped at `0x20400`: no app and no USB port, read as a refusal |
| Stays in bootloader | cuts at 0.4 s and 0.5 s: the board stayed in the Arduino bootloader |

## Not drawn, because it was not tested

- Swap-based updates with rollback. Build A was swap-using-offset, but its update never ran.
- A wrong-key image on the overwrite-only build.
- Which step of MCUboot each reset hit.
- A real power cut or brownout. The test used a reset.
