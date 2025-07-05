# Krysa
Krysa is a RAT (remote acces trojan) targeted at linux systems running systemd. You can find more info in the client and server READMEs.

## [Client](client/README.md)
- Requires python3, pip, systemd
- Additionally includes packer (conceals malicious python in base64 and runs it in a separate process) and installer (downloads a list of files into a hidden directory and runs them)
- Capable of persistence (as a systemd service) and gaining root acces with [sudo stealing](https://gist.github.com/MichalHrbek/e1003235b6aef13e631158156263d044)

## [Server](server/README.md)
- Requires npm and python3 (or docker)
- Dashboard built using svelte
- C2 built using fastapi