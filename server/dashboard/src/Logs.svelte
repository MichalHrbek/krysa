<script lang="ts">
  import { server_config } from "./lib/auth";

  let {machine,tags=[]}:
  {
    machine: string | null,
    tags: Array<string>,
  } = $props();

  const socket = new WebSocket(server_config.url.replace(/^https/, "ws") + "logs/ws" + window.location.search);
  const logs: Array<any> = $state([]);
  
  async function main()
  {
    socket.addEventListener("open", (event) => {
      socket.send(JSON.stringify({username:server_config.username,password:server_config.password}));
    });
      
    socket.addEventListener("message", (event) => {
      const data = JSON.parse(event.data);
      logs.push(data);
    });
  }

  main();
</script>


<div>
  <h1>Logs</h1>
  <h2>Machine: {machine ?? "all"}</h2>
  <h2>Tags: {tags.length == 0 ? "all" : tags}</h2>
  <hr>

  <div class="logs">
    {#each logs as log}
      <pre>Machine: {log.machine}</pre>
      <pre>Tags: {log.tags}</pre>
      {#if log.data}
      <pre>Data: {JSON.stringify(log.data, null, "\t")}</pre>  
      {/if}
      <hr>
    {/each}
  </div>
</div>


<style>
  .logs {
    display: flexbox;
    flex-direction: column;
    gap: 1em;
  }
</style>