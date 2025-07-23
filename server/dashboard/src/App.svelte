<script lang="ts">
  import Machine from './lib/Machine.svelte';
  import Order from './lib/Order.svelte';
  import type { OrderType } from './lib/types/OrderType';
  import type { MachineType } from './lib/types/MachineType';
  import { server_config, login_prompt, logout, get_auth_header } from './lib/auth';
  

  let machines: Record<string, MachineType> = $state({});
  let orders: Record<string, OrderType> = $state({});
  let selected: Record<string, boolean> = $state({});
  let versions: Record<string, boolean> = $state({});
  let show_connected = $state(true);
  let show_disconnected = $state(true);
  

  let socket: WebSocket;
  
  function register_machine(machine: MachineType) {
    if(!versions.hasOwnProperty(machine.version)) versions[machine.version] = true;
    selected[machine.id] = false;
  }

  async function authed_get(url: string) {
    const response = await fetch(url, {headers: get_auth_header()});
  
    if (!response.ok) {
      if (response.status == 401) alert("Wrong login");
      else alert("Problem with reaching the server at " + server_config.url);
    }
    
    return await response.json();
  }
  
  async function main()
  {
    let new_machines: Record<string, MachineType> = await authed_get(server_config.url + "machines");
    for (const [id, machine] of Object.entries(new_machines)) {
      register_machine(machine);
    }
    machines = new_machines;

    orders = await authed_get(server_config.url + "orders");


    if(socket && socket.readyState === WebSocket.OPEN) await socket.close();
    socket = new WebSocket(server_config.url.replace(/^https/, "ws") + "ws");

    socket.addEventListener("open", (event) => {
      socket.send(JSON.stringify({username:server_config.username,password:server_config.password}));
    });
      
    socket.addEventListener("message", (event) => {
      const e = JSON.parse(event.data);
      if (e.event == "delete") {
        if (e.order) {
          delete orders[e.order.id];
        }
      }
      else if (e.event == "update") {
        if (e.order) {
          orders[e.order.id] = e.order;
        }
        if (e.machine) {
          if (!machines.hasOwnProperty(e.machine.id)) register_machine(e.machine);
          machines[e.machine.id] = e.machine;
        }
      }
    });
  }

  function is_shown(machine_id: string) {
    return versions[machines[machine_id].version] && ((machines[machine_id].connected && show_connected) || (!machines[machine_id].connected && show_disconnected));
  }

  function num_selected() {
    return Object.values(selected).filter(value => value).length;
  }

  main();

</script>

<div class="app">
  <article class="left">
    <header>
      <div>
        <h2>Filters</h2>
        <label for="connected">Connected</label>
        <input type="checkbox" name="connected" bind:checked={show_connected}><br>
        <label for="disconnected">Disconnected</label>
        <input type="checkbox" name="disconnected" bind:checked={show_disconnected}><br>
        <details>
          <summary>Versions</summary>
          {#each Object.keys(versions) as v}
          <label for="v{v}">v{v}</label>
          <input type="checkbox" name="v{v}" bind:checked={versions[v]}>
          {/each}
        </details>
      </div>
  
      <div>
        <h2>Selection</h2>
        <button onclick={() => Object.keys(selected).forEach(id => selected[id] = true)}>Select all</button>
        <button onclick={() => Object.keys(selected).forEach(id => selected[id] = false)}>Deselect all</button>
        <br>
        <button onclick={() => Object.keys(selected).forEach(id => selected[id] = is_shown(id) ? true : selected[id])}>Select visible</button>
        <button onclick={() => Object.keys(selected).forEach(id => selected[id] = is_shown(id) ? false : selected[id])}>Deselect visible</button>
      </div>
  
      <div>
        <h2>Server</h2>
        <button onclick={() => {
          login_prompt();
          main();
        }}>Login</button>
        <br>
        <button onclick={() => {
          logout();
          main();
        }}>Logout</button>
      </div>
    </header>
  
    <main class="machines">
      {#each Object.keys(machines) as id (id)}
      {#if is_shown(id)}
      <Machine bind:machine={machines[id]} {orders} bind:selected={selected[id]}/>
      {/if}
      {/each}
    </main>
  </article>
  
  <article class="right">
    <header>
      <div>
        <h2>Orders</h2>
        <label for="ordername"></label>
        <input type="text" name="ordername" id="ordername" placeholder="Order name">
        <button onclick={() => {
          return fetch(server_config.url + "orders/create", {
              method: "PUT",
              body: JSON.stringify({name:(document.getElementById("ordername") as HTMLInputElement).value}),
              headers: get_auth_header({
                "Content-Type": "application/json",
              }),
          }).then(response => {
            if (!response.ok) {
              alert("Problem creating order")
            }
            return response.json()
          }).then(order => {
            orders[order.id] = order;
          })
        }}>
        Create order</button>
      </div>

    </header>
    <main>
      {#each Object.keys(orders) as id (id)}
      <Order bind:order={orders[id]} selected_machines={selected} {machines}/>
      {/each}
    </main>
  </article>
</div>


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

  .app {
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    align-items: stretch;
  }

  .left {
    resize: horizontal;
    overflow-y: scroll;
    overflow-x: hidden;
    width: 75%;
    padding-right: 1em;
    border-right: 1px solid black;
  }

  .right {
    padding-left: 1em;
    width: 25%;
    flex: 1;
  }
</style>