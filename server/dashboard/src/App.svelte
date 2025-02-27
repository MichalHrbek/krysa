<script>
  import Machine from './lib/Machine.svelte';

  let server_url = localStorage.getItem("server_url");
  let username = localStorage.getItem("username");
  let password = localStorage.getItem("password");
  if (!server_url || !username || !password) {
    login();
  }

  function login() {
    if (!server_url) {
      server_url = window.location.href.replace(/\/ui(?:\/.*)?$/, "/");
    }
    server_url = window.prompt("Server url:", server_url);
    localStorage.setItem("server_url", server_url);

    username = window.prompt("Username:", username)
    localStorage.setItem("username", username);

    password = window.prompt("Password:", password)
    localStorage.setItem("password", password);
  }

  let machines = $state({});
  let selected = $state({});
  let versions = $state({});
  let show_connected = $state(true);
  let show_disconnected = $state(true);

  let socket;
  
  
  async function main()
  {
    const encodedCredentials = btoa(`${username}:${password}`);
    const response = await fetch(server_url + "api/machines", {
      headers: {
        "Authorization": `Basic ${encodedCredentials}`,
      }
    });

    machines = await response.json();
    if (!response.ok) {
      if (response.status == 401) alert("Wrong login");
      else alert("Problem with reaching the server at " + server_url);
      return;
    }

    versions = Object.fromEntries(Object.values(machines).map(v => [v.version, true]));
    selected = Object.fromEntries(Object.values(machines).map(v => [v.id, false]));

    if(socket && socket.readyState === WebSocket.OPEN) await socket.close();
    socket = new WebSocket(server_url.replace(/^https/, "ws") + "ws");

    socket.addEventListener("open", (event) => {
      socket.send(JSON.stringify({username:username,password:password}));
    });
      
    socket.addEventListener("message", (event) => {
      const e = JSON.parse(event.data);
      machines[e.machine.id] = e.machine;
    });
  }

  function sendOrder(order)
  {
    if (confirm(`Are you sure? (${num_selected()} machines selected)`))
    {
      socket.send(JSON.stringify({event:"order", machine_ids: Object.keys(selected).filter(id => selected[id]), order: order}));
    }
  }

  function is_shown(machine_id) {
    return versions[machines[machine_id].version] && ((machines[machine_id].connected && show_connected) || (!machines[machine_id].connected && show_disconnected));
  }

  function num_selected() {
    return Object.values(selected).filter(value => value).length;
  }

  main();

</script>

<main>
  <header>
    <div>
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

    <div>
      <h2>Selection</h2>
      <button onclick={() => Object.keys(selected).forEach(id => selected[id] = true)}>Select all</button>
      <button onclick={() => Object.keys(selected).forEach(id => selected[id] = false)}>Deselect all</button>
      <br>
      <button onclick={() => Object.keys(selected).forEach(id => selected[id] = is_shown(id) ? true : selected[id])}>Select visible</button>
      <button onclick={() => Object.keys(selected).forEach(id => selected[id] = is_shown(id) ? false : selected[id])}>Deselect visible</button>
      <br>
      <button onclick={() => {
        if (confirm(`Are you sure? (${num_selected()} machines selected)`)) {
          for (const [machine_id, sel] of Object.entries(selected)) {
            // if (sel) 
          }
        }
      }}>Cancel orders</button>
    </div>

    <div>
      <h2>Server</h2>
      <button onclick={() => {
        login();
        main();
      }}>Login</button>
      <br>
      <button onclick={() => {
        password = "";
        localStorage.setItem("password", "");
        login();
        main();
      }}>Logout</button>
    </div>

    <div>
      <h2>Run python</h2>
      <button onclick={() => sendOrder({name:"python", code: window.python.value})}>Send</button>
      <br>
      <textarea id="python"></textarea>
    </div>
  </header>
  
  <div class="machines">
    {#each Object.values(machines) as { id, version, connected, connections, orders } (id)}
    <Machine id={id} version={version} connected={connected} connections={connections} orders={orders} bind:selected={selected[id]} hidden={!is_shown(id)}/>
    {/each}
  </div>
</main>

<style>
  .machines {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 0.5em;
  }

  header {
    width: 100%;
    padding-bottom: 2em;
    display: flex;
    gap: 2em;
  }
</style>