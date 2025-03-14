import { mount } from 'svelte'
import './app.css'
import Logs from './Logs.svelte'

const urlParams = new URLSearchParams(window.location.search);

const app = mount(Logs, {
  target: document.getElementById('app')!,
  props: {
    machine:urlParams.get("machine"),
    tags:urlParams.getAll("tags[]"),
  },
})

export default app
