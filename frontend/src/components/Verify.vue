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

        <div v-if="userData" class="user-data structured">
          <h3>User Details</h3>
          <dl>
            <div class="row"><dt>ID</dt><dd>{{ filteredUser.id }}</dd></div>
            <div class="row"><dt>Email</dt><dd>{{ filteredUser.email }}</dd></div>
            <div class="row"><dt>Role</dt><dd>{{ filteredUser.role || 'user' }}</dd></div>
            <div class="row"><dt>Subscription</dt><dd>{{ filteredUser.subscriptionLevel || 'free' }}</dd></div>
            <div class="row"><dt>Active</dt><dd>{{ filteredUser.isActive ? 'Yes' : 'No' }}</dd></div>
            <div v-if="filteredUser.createdAt" class="row"><dt>Created</dt><dd>{{ formatDate(filteredUser.createdAt) }}</dd></div>
          </dl>

          <div v-if="projectsList.length" class="projects-summary">
            <h4>Projects</h4>
            <ul>
              <li v-for="p in projectsList" :key="p.id">{{ p.name }} <small class="muted">(#{{ p.id }})</small></li>
            </ul>
          </div>
        </div>

        <p v-if="message" :class="['message', isError ? 'error' : 'success']">{{ message }}</p>
      </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import api from '../services/api'

const props = defineProps({
  initialToken: String
})

const token = ref(props.initialToken || '')
const userData = ref(null)
const projectsList = ref([])
const message = ref('')
const isError = ref(false)
const loading = ref(false)

const filteredUser = computed(() => {
  if (!userData.value) return {}
  const copy = { ...userData.value }
  // remove sensitive fields if any
  delete copy.hashedPassword
  delete copy.password
  return copy
})

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
    const response = await api.get('/me', {
      headers: {
        'Authorization': `Bearer ${token.value}`
      }
    })
    userData.value = response.data
    message.value = 'Verification successful!'
    // try fetch projects for quick summary
    try {
      const projResp = await api.get('/projects', {
        headers: { 'Authorization': `Bearer ${token.value}` }
      })
      projectsList.value = projResp.data || []
    } catch (e) {
      // ignore projects fetch errors here
      projectsList.value = []
    }
  } catch (error) {
    isError.value = true
    message.value = error.response?.data?.detail || 'Verification failed'
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString()
  } catch (_e) {
    return dateString
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
