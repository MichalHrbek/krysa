<script lang="ts">
  let { id, pending, done, name, creation_date, selected_machines, auth_headers }:
  {
    id: string,
    pending: string[],
    done: string[],
    name: string,
    creation_date: number,
    selected_machines: any,
    auth_headers: any,
  } = $props();

  async function send_to_selected(force=false) {
    for (const [machine_id, selected] of Object.entries(selected_machines)) {
      if (selected) {
        if ((force || !done.includes(machine_id)) && !pending.includes(machine_id)) {
          pending.push(id);
        }
      }
    }
  }
</script>

<details>
  <summary><h3>{name} | {id}</h3></summary>
  <!-- <h3></h3> -->
  <button title="Send to selected machines that haven't already completed this order">Send to selected</button>
  <button title="Send to selected machines even if they already completed this order">Force send to selected</button>
  <button>Delete</button>
</details>
<br>

<style>
  summary h3 {
    display: inline;
  }
</style>