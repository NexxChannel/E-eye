<template>
  <div class="card">
    <h2>Verify User</h2>
    <div class="content">
      <div class="form-group">
        <label>Access Token</label>
        <textarea v-model="token" placeholder="Paste token here or login to auto-fill" rows="3"></textarea>
      </div>
      <button @click="verify" :disabled="loading || !token">
        {{ loading ? 'Verifying...' : 'Verify Me' }}
      </button>
      
      <div v-if="userData" class="user-data">
        <h3>User Details</h3>
        <pre>{{ JSON.stringify(userData, null, 2) }}</pre>
      </div>
      
      <p v-if="message" :class="['message', isError ? 'error' : 'success']">{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  initialToken: String
})

const token = ref(props.initialToken || '')
const userData = ref(null)
const message = ref('')
const isError = ref(false)
const loading = ref(false)

watch(() => props.initialToken, (newVal) => {
  if (newVal) {
    token.value = newVal
    // Auto verify if token is passed
    verify()
  }
})

const verify = async () => {
  if (!token.value) return
  
  loading.value = true
  message.value = ''
  isError.value = false
  userData.value = null
  
  try {
    const response = await axios.post('/me', {
      accessToken: token.value,
      tokenType: 'Bearer'
    })
    userData.value = response.data
    message.value = 'Verification successful!'
  } catch (error) {
    isError.value = true
    message.value = error.response?.data?.detail || 'Verification failed'
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
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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

textarea {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.75rem;
  border-radius: 8px;
  color: white;
  font-size: 0.875rem;
  font-family: monospace;
  resize: vertical;
  transition: all 0.2s;
}

textarea:focus {
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

.user-data {
  text-align: left;
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
}

.user-data h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #eee;
}

pre {
  margin: 0;
  font-size: 0.875rem;
  color: #aaa;
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
