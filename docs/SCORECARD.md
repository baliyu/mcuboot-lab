# Prediction scorecard

AI-assisted: drafted with Claude, checked by the author.

246 hits, 55 misses and 19 not scored, across 65 steps. The tally is computed by scripts/scorecard.py from docs/scorecard.csv, and every miss is written down below.

| Step | Topic | Hits | Misses | Not scored |
|---|---|---|---|---|
| 1 | Toolchain check | 2 | 4 | 0 |
| 2 | Board folder and repo contents | 3 | 1 | 0 |
| 3 | Repo state | 4 | 0 | 0 |
| 4 | Build inputs | 4 | 1 | 1 |
| 5 | Compare the two project copies | 2 | 2 | 0 |
| 6 | How the test images were built | 2 | 1 | 1 |
| 7 | Test variants | 3 | 1 | 0 |
| 8 | Build artifacts and tools | 3 | 1 | 0 |
| 9 | merge_images.py and tests | 3 | 0 | 0 |
| 10 | First push | 2 | 0 | 0 |
| 11 | gitignore for __pycache__ | 2 | 0 | 0 |
| 12 | main.c prints the generated version | 2 | 0 | 0 |
| 13 | First sysbuild build | 5 | 0 | 0 |
| 14 | Kconfig warning | 2 | 0 | 0 |
| 15 | build_images.py | 3 | 0 | 0 |
| 16 | Build v1.0.0 and v1.0.1 | 4 | 0 | 0 |
| 17 | imgtool arguments | 4 | 1 | 0 |
| 18 | make_update.py | 3 | 0 | 0 |
| 19 | Assemble and inspect the image | 5 | 0 | 0 |
| 20 | Replace the deprecated pad argument | 3 | 0 | 0 |
| 21 | Copy the image for flashing | 2 | 0 | 0 |
| 22 | USB IDs and bossac | 3 | 0 | 0 |
| 23 | Baseline flash | 3 | 1 | 0 |
| 24 | Read the baseline serial output | 3 | 0 | 0 |
| 25 | Windows Python tools | 3 | 0 | 0 |
| 26 | Feather sketch and driver | 2 | 0 | 0 |
| 27 | Compile and upload the Feather sketch | 3 | 0 | 0 |
| 28 | Wire the boards and first RESET timing | 0 | 1 | 3 |
| 29 | Why the port list was empty | 2 | 1 | 0 |
| 30 | portwatch.py | 2 | 0 | 0 |
| 31 | RESET timeline | 2 | 3 | 0 |
| 32 | Uncut update timing | 3 | 1 | 0 |
| 33 | portwatch --cut | 2 | 0 | 0 |
| 34 | First cut mid-copy | 3 | 0 | 0 |
| 35 | sweep.py | 2 | 0 | 0 |
| 36 | Three-trial pilot | 2 | 1 | 0 |
| 37 | Coarse sweep | 4 | 0 | 0 |
| 38 | Fine sweep | 3 | 1 | 0 |
| 39 | plot_sweep.py | 3 | 0 | 0 |
| 40 | First figure and data | 3 | 0 | 0 |
| 41 | requirements.txt and workflow | 2 | 0 | 0 |
| 42 | Scorecard script and commit | 2 | 1 | 0 |
| 43 | Fix the guard and commit | 3 | 0 | 0 |
| 44 | 20 ms power-cut sweep | 4 | 0 | 0 |
| 45 | 20 ms sweep figure and commit | 5 | 0 | 0 |
| 46 | README and layout check | 3 | 1 | 0 |
| 47 | First README update block | 0 | 0 | 5 |
| 48 | Repo check after the cut-off paste | 3 | 0 | 0 |
| 49 | README edits part 1 | 3 | 0 | 0 |
| 50 | README comparison table edits | 3 | 0 | 0 |
| 51 | README not tested and lessons edits | 3 | 0 | 0 |
| 52 | README new section part 1 | 3 | 0 | 0 |
| 53 | Find out why the window closed | 2 | 1 | 0 |
| 54 | README new section part 2 | 4 | 0 | 0 |
| 55 | README new section part 3 | 3 | 0 | 0 |
| 56 | README test and commit | 1 | 3 | 0 |
| 57 | Find the venv | 1 | 0 | 2 |
| 58 | README test and commit again | 4 | 0 | 0 |
| 59 | Push and CI | 4 | 0 | 0 |
| 60 | SBOM: what west spdx needs | 18 | 21 | 4 |
| 61 | SBOM: reading the output | 13 | 1 | 1 |
| 62 | make_sbom.py, --build and the Zephyr commit | 23 | 2 | 0 |
| 63 | Security policy and handling | 7 | 0 | 0 |
| 64 | OSV checker and triage | 11 | 3 | 2 |
| 65 | Merge and CI on main | 10 | 1 | 0 |

## Misses

- Step 1, P3 (90%): predicted a board folder named arduino_nano_33_ble*; it is zephyr/boards/arduino/nano_33_ble
- Step 1, P4 (40%): void, my grep had no path and searched everything, so its count meant nothing
- Step 1, P5 (70%): predicted bossac 1.9.1-arduino2 on the WSL PATH; it is not there
- Step 1, P6 (90%): predicted /mnt/c/mcuboot-lab did not exist; it already did
- Step 2, Q4 (55%): predicted mcuboot-lab held only a README or nothing; it was a full scaffold with source, overlays and three commits
- Step 4, S5b (60%): predicted the merge script lived outside the repo; no script existed anywhere
- Step 5, T2 (55%): predicted the build copy matched the repo; it held the keys and four test apps instead
- Step 5, T3 (80%): predicted a build folder in the build copy; there was none
- Step 6, U3 (40%): predicted a build folder under the repo; the builds were in the hello folders
- Step 7, V2 (65%): predicted hello_key2 differed from hello only in the key path; its overlays and sysbuild.conf differed too
- Step 8, W1 (70%): predicted a merged.hex in each build; there was none
- Step 17, F4 (70%): predicted --align 4; the build used --align 1
- Step 23, L3 (80%): predicted the output would contain app v1.0.1; the serial port refused to open, so nothing was read
- Step 28, Q1 (85%): predicted the port list would show the reset; my monitor printed nothing, and my first explanation of why was wrong
- Step 29, R1 (45%): predicted GetPortNames returned nothing; it returned COM3,COM14
- Step 31, T1 (85%): predicted COM3,COM14 at about 0 s; COM14 was already gone
- Step 31, T3 (70%): predicted COM7 would not appear; it appeared from 0.35 s to 0.59 s
- Step 31, T5 (60%): predicted the app port back at 2 to 6 s; it was back at 1.31 s
- Step 32, U4 (75%): predicted the COM7 window would last 0.2 to 0.3 s; it lasted 0.17 s
- Step 36, Y3 (70%): predicted every app_port_s would be 3.0 to 3.8; the 3.0 s cut gave 1.25 because the update had already finished
- Step 38, AA3 (25%): predicted at least one row between the two clusters; there was none
- Step 42, AF3 (75%): predicted a commit; my guard expected 2 AI-assisted lines but the script writes a third into its own report, so nothing was committed
- Step 46, AI4 (25%): predicted the README already mentioned 26,076 B; it only had the old 29,604 B
- Step 53, AP2 (35%): predicted the README was 134 lines so step 52 never ran; it was 152
- Step 56, AS1 (80%): predicted every check ok; the venv guard stopped the block first
- Step 56, AS2 (75%): predicted 56 passed; pytest never ran
- Step 56, AS3 (75%): predicted a commit; none was made
- Step 60, CD1 (half): west list works but my head -n 30 cut it off before MCUboot
- Step 60, CD2: predicted no SBOM tool was installed; spdx-tools 0.8.5 and reuse 6.2.0 were
- Step 60, CE2 (70%): predicted a build folder existed; there was none
- Step 60, CE3 (75%): predicted tinycrypt was a separate module; it is not in the manifest, and mbedtls has two variants
- Step 60, CG1 (75%): predicted the script builds under the Zephyr workspace; the caller picks the folder with --out
- Step 60, CH4 (60%): predicted west spdx works on the app image after init and build; the walker failed
- Step 60, CH5 (50%): same for the MCUboot image
- Step 60, CI1 (35%): predicted west spdx works on the top build folder; it failed
- Step 60, CI2 (65%): predicted a per-image init and CMake run is enough; replies appeared but the walker still failed
- Step 60, CI3 (60%): predicted the file names Zephyr 4.4.2; no file was written
- Step 60, CK1 (65%): predicted a zephyr.meta existed in the build; none did, because BUILD_OUTPUT_META was off
- Step 60, CL1 (80%): predicted the walker builds the meta path from a nearby variable; it reads KERNEL_META_PATH from the CMake cache
- Step 60, CL2 (55%): predicted a west command or script writes zephyr.meta; CMake does, under a Kconfig condition
- Step 60, CM1 (75%): predicted kernel.cmake passes --meta-out; it only names the file
- Step 60, CM2 (65%): predicted the write sits inside an if on a cache variable; the switch is the Kconfig option BUILD_OUTPUT_META
- Step 60, CN1 (80%): predicted zephyr.meta appears after the rebuild; the rebuild never ran
- Step 60, CN3 (75%): predicted west spdx works on the app image; it did not, there was no rebuild
- Step 60, CN4 (70%): same for the MCUboot image
- Step 60, CP1 (80%): predicted zephyr.meta appears; the rebuild failed again
- Step 60, CP3 (75%): predicted west spdx works on the app image; there was still no meta file
- Step 60, CP4 (70%): same for the MCUboot image
- Step 61, CT4 (40%): predicted mbedtls-sources has compiled files in the MCUboot image; none do
- Step 62, CV2 (50%): predicted all new tests pass first time; four failed on a fixture with an .invalid address
- Step 62, CV4 (55%): predicted a built document validates first time; the validator rejects a made-up download location
- Step 64, DE3 (60%): predicted the three current commits return 0 vulnerabilities; the MCUboot commit returned 7
- Step 64, DH1 (35%): predicted a version-based OSV query works; all four forms returned nothing
- Step 64, DJ1 (65%): predicted 94 passed; it was 93, I miscounted the new tests
- Step 65, DL2 (70%): predicted the scorecard notes columns hold free text with no required format; a row needs one note per miss and per unscored item, separated by a vertical bar, and the script refuses a row whose counts and notes disagree

## Not scored

- Step 4, S1: the key listing was missing from the paste
- Step 6, U2: the shell history output was cut off by tail
- Step 28, Q2: no data
- Step 28, Q3: no data
- Step 28, Q4: no data
- Step 47, AJ1: the terminal cut the paste off and the block never ran
- Step 47, AJ2: same
- Step 47, AJ3: same
- Step 47, AJ4: same
- Step 47, AJ5: same
- Step 57, AT2: output cut off by a slow search of /mnt/c
- Step 57, AT3: same
- Step 60, CK2 (60%): the grep showed only the error line, so where the walker looks was not shown
- Step 60, CK3 (70%): there was no file to read
- Step 60, CN2 (85%): the hashes matched but nothing was rebuilt, so it proved nothing
- Step 60, CP2 (85%): same, the rebuild had failed
- Step 61, CR4 (60%): my head -n 8 cut the list before MCUboot could show
- Step 64, DF2 (50%): only 1 of the 7 fix commits existed in the local clone, so it could not be scored
- Step 64, DH2 (50%): the empty answers proved nothing, because the known-bad version also returned nothing

## Other errors that were not predictions

- Step 3: Running total quoted as 6 hits and 8 misses after steps 1 to 3; the correct figure was 9 and 5. Every later total inherited the slip until it was found at step 42.
- Step 20: Not a prediction: merge_images.py used a deprecated pad argument that I did not predict; fixed in this step with identical output bytes.
- Step 44: 2 of 131 cut points (1.18 s and 1.58 s) ended in flash_fail before the cut and have no outcome
- Step 52: scored from the README state because the output was lost when the window closed
- Step 53: Every block I gave used exit in an interactive shell, which closed the WSL window whenever a guard tripped; blocks now run inside a bash wrapper
- Step 56: I guessed the venv location wrong; it is /home/astro/zephyrproject/.venv
- Step 59: AE3 from step 41 scored here: the first Actions run for 6710cac completed successfully
- Step 60: In steps 11 and 12 I blamed a missing source folder for the failed rebuild; the real cause was the missing --sysbuild flag, found in step 13
- Step 64: The OSV records were read from titles and summaries and the image configuration, not from the code of each flaw
