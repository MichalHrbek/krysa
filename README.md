# Krysa
Krysa is a RAT (remote acces trojan) targeted at linux systems running systemd. You can find more info in the client and server READMEs.

## Showcase
<img src="https://michalhrbek.github.io/images/krysa/dashboard.png">
<img src="https://michalhrbek.github.io/images/krysa/machine.png">

## [Client](client/README.md)
- Requires python3, pip, systemd
- Additionally includes packer (conceals malicious python in base64 and runs it in a separate process) and installer (downloads a list of files into a hidden directory and runs them)
- Capable of persistence (as a systemd service) and gaining root acces with [sudo stealing](https://gist.github.com/MichalHrbek/e1003235b6aef13e631158156263d044)

## [Server](server/README.md)
- Requires npm and python3 (or docker)
- Dashboard built using svelte
- C2 built using fastapi

## Behaviour
Upon running an infected python script, the installer will attempt to download krysa, which is then placed inconspicuously into `~/.config/git/user.cfg` and then executed.
The rat then reaches out to a list of C2s and recieves an unique 128bit uid. After that krysa maintains contact with the C2 using a websocket connection.

## Shortcomings
The server doesn't have any protection against malicious requests from fake clients which results in DOS vulnerabilities (for example filling the disk up by uploading fake data or registering a lot of fake clients).