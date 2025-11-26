<template>
  <div class="card">
    <h2>Register</h2>
    <form @submit.prevent="register">
      <div class="form-group">
        <label>Email</label>
        <input v-model="email" type="email" required placeholder="Enter your email" />
      </div>
      <div class="form-group">
        <label>Password</label>
        <input v-model="password" type="password" required minlength="8" placeholder="Enter password (min 8 chars)" />
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Registering...' : 'Register' }}
      </button>
    </form>
    <p v-if="message" :class="['message', isError ? 'error' : 'success']">{{ message }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../services/api'

const email = ref('')
const password = ref('')
const message = ref('')
const isError = ref(false)
const loading = ref(false)

const register = async () => {
  loading.value = true
  message.value = ''
  isError.value = false
  
  try {
  const response = await api.post('/users', {
      email: email.value,
      password: password.value
    })
    message.value = `User created! ID: ${response.data.id}`
    email.value = ''
    password.value = ''
  } catch (error) {
    isError.value = true
    if (error.response?.status === 422) {
       const detail = error.response.data.detail
       message.value = Array.isArray(detail) 
         ? detail.map(e => e.msg).join(', ') 
         : detail
    } else {
       message.value = error.response?.data?.detail || 'Registration failed'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  padding: 2rem;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 350px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(to right, #fff, #aaa);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
}

label {
  font-size: 0.875rem;
  color: #aaa;
}

input {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.75rem;
  border-radius: 8px;
  color: white;
  font-size: 1rem;
  transition: all 0.2s;
}

input:focus {
  outline: none;
  border-color: #646cff;
  background: rgba(0, 0, 0, 0.4);
}

button {
  background: #646cff;
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #535bf2;
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.message {
  font-size: 0.875rem;
  margin: 0;
  padding: 0.5rem;
  border-radius: 4px;
}

.success {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.error {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}
</style>
