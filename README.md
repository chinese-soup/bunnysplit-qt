# Bunnysplit-qt
## About
### Bunnysplit-qt is a GUI timer with splits which serves exclusively as a front-end for BXT's BunnySplit on Linux.

## Motivation
* There was no existing "native" integration with BXT's BunnySplit, even though Steam runs can be done on the native Linux version of Half-Life and its expansions.
* *Why not just extend an RTA existing timer like urn/llainfair?*
  * Just to learn something new - PySide6 (Qt), QML, dataclasses, etc.

## Requirements
* ipcqueue
* PySide6
* JSONWizard



## TODO
- [ ] Best time
- [ ] Gold splits
- [ ] ListView & ScrollView for splits in QML instead of Repeater
- [ ] General refactoring
- [ ] Graceful quitting (stopping Worker thread etc.), signal handling