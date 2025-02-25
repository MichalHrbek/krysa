<script>
  import {
    SvelteMap,
    SvelteSet,
  } from 'svelte/reactivity';
  import Machine from './lib/Machine.svelte';
  var machines = $state({});
  var versions = $state({});
  var show_connected = $state(true);
  var show_disconnected = $state(true);

  const URL = "127.0.0.1:8000/dashboard/"
  const socket = new WebSocket("ws://" + URL + "ws");

  socket.addEventListener("message", (event) => {
    const e = JSON.parse(event.data);
    machines[e.machine.uid] = e.machine;
  });
  
  async function main()
  {
    const response = await fetch("http://" + URL + "api/machines");
    machines = await response.json();
    versions = Object.fromEntries(Object.values(machines).map(v => [v.version, true]));
  }

  main();

  $effect(() => {
    
  })

</script>

<main>
  <div class="filters">
    <h2>Filters</h2>
    <label for="connected">Connected</label>
    <input type="checkbox" name="connected" bind:checked={show_connected}><br>
    <label for="disconnected">Disconnected</label>
    <input type="checkbox" name="disconnected" bind:checked={show_disconnected}><br>
    <label for="versions">Versions:</label>
    {#each Object.keys(versions) as v}
      <label for="v{v}">v{v}</label>
      <input type="checkbox" name="v{v}" bind:checked={versions[v]}>
    {/each}
  </div>

  <div class="machines">
    {#each Object.values(machines) as { uid, version, connected, connections, orders } (uid)}
    <Machine id={uid} version={version} connected={connected} connections={connections} orders={orders} hidden={!(versions[version] && ((connected && show_connected) || (!connected && show_disconnected)))}/>
    {/each}
  </div>
</main>

<style>
  .machines {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 10px 10px;
  }

  .filters {
    width: 100%;
    padding-bottom: 2em;
  }
</style>