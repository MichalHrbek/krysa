import { mount } from 'svelte'
import './app.css'
import Shell from './Shell.svelte'

const urlParams = new URLSearchParams(window.location.search);

const app = mount(Shell, {
  target: document.getElementById('app')!,
  props: {
    machine:urlParams.get("machine")
  },
})

export default app
