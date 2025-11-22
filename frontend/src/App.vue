<template>
  <div class="app-container">
    <header>
      <h1>E-eye MVP</h1>
      <p>Frontend Demo</p>
    </header>
    
    <main>
      <div class="grid">
        <Register />
        <Login @login-success="handleLoginSuccess" />
        <Verify :initial-token="accessToken" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Register from './components/Register.vue'
import Login from './components/Login.vue'
import Verify from './components/Verify.vue'

const accessToken = ref('')

const handleLoginSuccess = (token) => {
  accessToken.value = token
}
</script>

<style>
:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color-scheme: dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
  background: linear-gradient(to bottom right, #1a1a1a, #2a2a2a);
}

#app {
  width: 100%;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}
</style>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  align-items: center;
  width: 100%;
}

header h1 {
  font-size: 3.2rem;
  line-height: 1.1;
  background: linear-gradient(to right, #646cff, #42b883);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

header p {
  font-size: 1.2rem;
  color: #aaa;
  margin: 0;
}

.grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 2rem;
  width: 100%;
  max-width: 1200px;
}
</style>
