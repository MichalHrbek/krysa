import { expoOut } from "svelte/easing";

export const server_config = JSON.parse(localStorage.getItem("server_config") ?? "null") ?? {};

if (!server_config.url || !server_config.username || !server_config.password) {
  login_prompt();
}

export function get_encoded_credentials(): string {
  return btoa(`${server_config.username}:${server_config.password}`);
}

export function get_auth_header(): any {
  return {
    "Authorization": `Basic ${get_encoded_credentials()}`,
  }
}

export function login_prompt() {
  if (!server_config.url) {
    server_config.url = window.location.href.replace(/\/ui(?:\/.*)?$/, "/");
  }
  server_config.url = window.prompt("Server url:", server_config.url) ?? server_config.url;
  server_config.username = window.prompt("Username:", server_config.username) ?? server_config.username;
  server_config.password = window.prompt("Password:", server_config.password) ?? server_config.password;

  localStorage.setItem("server_config", JSON.stringify(server_config));
}

export function logout() {
  server_config.username = "";
  localStorage.setItem("server_config", JSON.stringify(server_config));
  login_prompt();
}