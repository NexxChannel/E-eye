<template>
  <div class="card projects-card">
    <h2>Projects</h2>
    
    <!-- Create Project Form -->
    <form @submit.prevent="createProject" class="create-form">
      <div class="form-group">
        <label>Project Name</label>
        <input v-model="newProjectName" type="text" required placeholder="Enter project name" />
      </div>
      <button type="submit" :disabled="loading || !newProjectName.trim()">
        {{ loading ? 'Creating...' : 'Create Project' }}
      </button>
    </form>

    <p v-if="message" :class="['message', isError ? 'error' : 'success']">{{ message }}</p>

    <!-- Projects List -->
    <div class="projects-list" v-if="projects.length > 0">
      <h3>Your Projects</h3>
      <ul>
        <li v-for="project in projects" :key="project.id" @click="viewProject(project.id)" class="project-item">
          <span class="project-name">{{ project.name }}</span>
          <span class="project-date">{{ formatDate(project.createdAt) }}</span>
        </li>
      </ul>
    </div>
    <p v-else-if="!loading && hasFetched" class="no-projects">No projects yet. Create one above!</p>

    <!-- Project Detail Modal -->
    <div v-if="selectedProject" class="project-detail">
      <h3>Project Details</h3>
      <button class="close-btn" @click="selectedProject = null">&times;</button>
      <table class="project-table">
        <tbody>
          <tr><th>Name</th><td>{{ selectedProject.name }}</td></tr>
          <tr><th>ID</th><td>{{ selectedProject.id }}</td></tr>
          <tr><th>Owner</th><td>{{ ownerEmail }}</td></tr>
          <tr><th>Created At</th><td>{{ formatFullDate(selectedProject.createdAt) }}</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../services/api'

const props = defineProps({
  token: String
})

const newProjectName = ref('')
const projects = ref([])
const selectedProject = ref(null)
const ownerEmail = ref('')
const message = ref('')
const isError = ref(false)
const loading = ref(false)
const hasFetched = ref(false)

const getAuthHeaders = () => ({
  headers: { 'Authorization': `Bearer ${props.token}` }
})

const fetchProjects = async () => {
  if (!props.token) return
  
  loading.value = true
  try {
    const response = await api.get('/projects', getAuthHeaders())
    let projectsData = response.data || []
    // sort by createdAt desc (newest first)
    projectsData.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    projects.value = projectsData
    hasFetched.value = true
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  } finally {
    loading.value = false
  }
}

const createProject = async () => {
  console.log('createProject called, token:', props.token ? 'exists' : 'missing')
  
  if (!props.token) {
    isError.value = true
    message.value = 'Please login first to create projects'
    return
  }
  
  if (!newProjectName.value.trim()) {
    isError.value = true
    message.value = 'Project name is required'
    return
  }
  
  loading.value = true
  message.value = ''
  isError.value = false
  
  try {
    console.log('Sending request to /projects/create')
    const response = await api.post('/projects/create', 
      { name: newProjectName.value.trim() },
      getAuthHeaders()
    )
    console.log('Response:', response.data)
    message.value = `Project "${response.data.name}" created!`
    newProjectName.value = ''
    await fetchProjects()
  } catch (error) {
    console.error('Create project error:', error)
    isError.value = true
    message.value = error.response?.data?.detail || error.message || 'Failed to create project'
  } finally {
    loading.value = false
  }
}

const viewProject = async (projectId) => {
  if (!props.token) return
  try {
    const response = await api.get(`/projects/${projectId}`, getAuthHeaders())
    selectedProject.value = response.data
    // fetch user info for email
    try {
      const userResp = await api.get('/me', getAuthHeaders())
      ownerEmail.value = userResp.data.email || userResp.data.id || ''
    } catch (e) {
      ownerEmail.value = selectedProject.value.ownerId
    }
  } catch (error) {
    isError.value = true
    message.value = error.response?.data?.detail || 'Failed to load project'
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}
const formatFullDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString()
  } catch (_e) {
    return dateString
  }
}

watch(() => props.token, (newToken) => {
  if (newToken) {
    fetchProjects()
  } else {
    projects.value = []
    hasFetched.value = false
  }
})

onMounted(() => {
  if (props.token) {
    fetchProjects()
  }
})
</script>

<style scoped>
.card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  padding: 2rem;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.projects-card {
  position: relative;
}

h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(to right, #fff, #aaa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #eee;
}

.create-form {
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

.projects-list {
  text-align: left;
}

.projects-list ul {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
}

.project-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}

.project-item:hover {
  background: rgba(0, 0, 0, 0.4);
}

.project-name {
  font-weight: 500;
  color: #fff;
}

.project-date {
  font-size: 0.75rem;
  color: #888;
}

.no-projects {
  color: #888;
  font-size: 0.875rem;
  text-align: center;
}

.project-detail {
  position: relative;
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem;
  border-radius: 8px;
  text-align: left;
}

.project-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.5rem;
}
.project-table th {
  text-align: left;
  vertical-align: top;
  padding: 0.25rem 0.5rem 0.25rem 0;
  color: #ccc;
  width: 35%;
}
.project-table td {
  padding: 0.25rem 0.5rem;
  color: #fff;
}

.close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: transparent;
  border: none;
  color: #888;
  font-size: 1.25rem;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
}

.close-btn:hover {
  color: #fff;
  background: transparent;
}
</style>
