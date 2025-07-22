<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { server_config } from "./lib/auth";
  import '@xterm/xterm/css/xterm.css';
  import { Terminal } from '@xterm/xterm';

  let {machine}:
  {
    machine: string | null,
  } = $props();

  let terminalDiv: HTMLDivElement;
  let term: Terminal;
  let socket: WebSocket;


  onMount(() => {
    term = new Terminal({ cursorBlink: true });
    term.open(terminalDiv);

    // Connect to backend WebSocket (adjust URL as needed)
    socket = new WebSocket(server_config.url.replace(/^https/, "ws") + "api/shell/" + machine);

    socket.addEventListener("open", (event) => {
      socket.send(JSON.stringify({username:server_config.username,password:server_config.password}));
    });

    socket.onmessage = (event) => {
      term.write(event.data);
    };

    term.onData((data) => {
      socket.send(data);
    });
  });

  onDestroy(() => {
    socket?.close();
    term?.dispose();
  });
</script>

<div bind:this={terminalDiv} class="terminal-container"></div>