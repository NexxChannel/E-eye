<template>
  <div v-if="image" class="fullscreen-viewer">
    <img :src="image.filePath" :alt="image.name" class="fullscreen-image" />
    <button class="info-btn" @click="showInfo = !showInfo">ⓘ</button>
    <div v-if="showInfo" class="image-info">
      <h3>{{ image.name }}</h3>
      <p>{{ formatDate(image.createdAt) }}</p>
    </div>
  </div>
  <div v-else class="error-screen">
    <p>No image data available</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const image = ref(null)
const showInfo = ref(false)

const formatDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString()
  } catch (_e) {
    return dateString
  }
}

onMounted(() => {
  // Retrieve image data from sessionStorage
  const data = sessionStorage.getItem('imageViewerData')
  if (data) {
    try {
      image.value = JSON.parse(data)
    } catch (e) {
      console.error('Failed to parse image data:', e)
    }
  }
})
</script>

<style scoped>
.fullscreen-viewer {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  overflow: auto;
  width: 100%;
  height: 100%;
}

.fullscreen-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
}

.info-btn {
  position: fixed;
  top: 1rem;
  right: 1rem;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: rgba(100, 181, 246, 0.2);
  color: #64b5f6;
  border: 1px solid rgba(100, 181, 246, 0.4);
  font-size: 1.2rem;
  cursor: pointer;
  z-index: 10001;
  transition: background 0.2s, transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-btn:hover {
  background: rgba(100, 181, 246, 0.3);
  transform: scale(1.1);
}

.image-info {
  position: fixed;
  top: 4rem;
  right: 1rem;
  color: #fff;
  background: rgba(0, 0, 0, 0.8);
  padding: 1rem 1.5rem;
  border-radius: 8px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  z-index: 10002;
  min-width: 250px;
}

.image-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #64b5f6;
  word-break: break-word;
}

.image-info p {
  margin: 0;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.error-screen {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.2rem;
  z-index: 10000;
}
</style>
