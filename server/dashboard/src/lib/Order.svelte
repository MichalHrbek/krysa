<script>
  let { id, pending=$bindable([]), done, name=$bindable(""), creation_date, selected_machines } = $props();
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