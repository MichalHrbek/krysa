<script lang="ts">
  import { server_config, get_auth_header} from "./auth";
  import type { MachineType } from "./types/MachineType";

  let { id, pending, done, name, creation_date, selected_machines, machines }:
  {
    id: string,
    pending: string[],
    done: string[],
    name: string,
    creation_date: number,
    selected_machines: Record<string, boolean>,
    machines: Record<string, MachineType>
  } = $props();

  async function send_to_selected(force=false) {
    for (const [machine_id, selected] of Object.entries(selected_machines)) {
      if (selected) {
        if ((force || !done.includes(machine_id)) && !pending.includes(machine_id)) {
          pending.push(machine_id);
        }
      }
    }
    await fetch(server_config.url + "api/orders/" + id, {
      method: "PATCH",
      headers: get_auth_header({
        "Content-Type": "application/json"
      }),
      body: JSON.stringify({pending: pending}),
    })
  }
</script>

<details>
  <summary><h3>{name} | {id}</h3></summary>
  <br>
  <button title="Send to selected machines that haven't already completed this order" onclick={async() => await send_to_selected()}>Send to selected</button>
  <button title="Send to selected machines even if they already completed this order" onclick={async() => await send_to_selected(true)}>Force send to selected</button>
  <button onclick={async () => {
    await fetch(server_config.url + "api/orders/" + id, {
      method: "DELETE",   
      headers: get_auth_header(),
    })
  }}>Delete</button>
  <button onclick={async () => {
      await fetch(server_config.url + "api/orders/" + id, {
        method: "PATCH",
        headers: get_auth_header({
          "Content-Type": "application/json"
        }),
        body: JSON.stringify({name: prompt("New name: ", name) ?? name}),
      })
    }}>Rename</button>
    <br>
    <br>

    <div class="horizontal-list">
      <b>Pending: </b>
      {#each pending as machine_id}
        <span class='{selected_machines[machine_id] ? "selected " : ""}{machines[machine_id].connected ? "active" : "inactive"}'>{machine_id}</span>
      {/each}
    </div>

    <div class="horizontal-list">
      <b>Done: </b>
      {#each done as machine_id}
        <span class='{selected_machines[machine_id] ? "selected " : ""}{machines[machine_id].connected ? "active" : "inactive"}'>{machine_id}</span>
      {/each}
    </div>

    <textarea>Code</textarea>
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
</style>