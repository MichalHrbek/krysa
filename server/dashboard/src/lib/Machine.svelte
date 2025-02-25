<script>
  let { id, version, connected, connections, classs, orders, selected=false, hidden=false } = $props();
  let expanded = $state(false);
  
</script>

<div class="machine {connected ? 'connected' : 'disconnected'} {expanded ? 'expanded' : ''} {selected ? 'selected' : ''}" hidden={hidden}>
  <div class="buttons">
    <button aria-expanded={expanded} onclick={() => expanded = !expanded} aria-label='expand/shrink'>
      <svg viewBox="0 0 20 20" fill="none" >
        <path class="vert" d="M10 1V19" stroke="black" stroke-width="2"/>
        <path d="M1 10L19 10" stroke="black" stroke-width="2"/>
      </svg>
    </button>
    <input type="checkbox" name="selected" bind:checked={selected}>
  </div>
  <p><b>Id:</b> {id}</p>
  <p><b>Version:</b> {version}</p>
  <p><b>Last connection:</b> {new Date(Math.max(...Object.values(connections).flat()) * 1000).toLocaleString()}</p>
  {#if expanded}
  <h3>Connections:</h3>
  <ul>
    {#each Object.entries(connections) as [ip, timestamps] (ip)}
    <li>
      <h4>{ip}</h4>
      <div class="horizontal-list">
        {#each [...timestamps].sort().reverse() as t, index}
        {#if index === 0}
        <span>{t}&nbsp;({Math.round(t-Date.now()/1000)})</span>
        {:else}
        <span>{t}</span>
        {/if}
        {/each}
      </div>
    </li>
    {/each}
  </ul>

  <h3>Orders: </h3>
  <ul>
    {#each orders as order}
    <li><pre>{order}</pre></li>
    {/each}
  </ul>
  {/if}
</div>

<style>
  .machine {
    border-radius: 5px;
    padding: 1em;
    flex-grow: 0;
    box-sizing: border-box;
  }

  .connected {
    order: 2;
    background-color: lightblue;
  }

  .disconnected {
    order: 3;
    background-color: lightcoral;
  }

  .expanded {
    position: absolute;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    flex: none;
    padding: 2em;
    border-radius: 0;
    z-index: 10;
  }

  button[aria-expanded="true"] .vert {
    display: none;
  }

  button {
    background-color: transparent;
    color: #282828;
    display: inline-flex;
    justify-content: space-between;
    margin: 0;
    padding: 0.5em 0.5em;
    border: 2px solid;
  }

  svg {
    height: 0.7em;
    width: 0.7em;
  }

  .horizontal-list {
    display: flex;
    flex-direction: row;
    gap: 1em;
    overflow: auto;
    padding-bottom: 1em;
  }

  .selected {
    order: 1;
  }

  input[type=checkbox] {
    margin: 0;
    width: 1.7em;
    height: 1.7em;
    border: 2px solid;
  }

  .buttons {
    width: 100%;
    align-items: center;
    display: inline-flex;
    justify-content: space-between;
  }
</style>