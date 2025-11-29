<template>
  <div v-if="image" class="fullscreen-viewer" @wheel.prevent="onWheel">
    <!-- 图片容器，支持缩放和平移 -->
    <div 
      class="image-container"
      :style="{
        transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
        transformOrigin: 'center center'
      }"
    >
      <img 
        :src="image.filePath" 
        :alt="image.name" 
        class="fullscreen-image"
        :style="{ cursor: calibratingScale ? 'crosshair' : 'grab' }"
        @click="onImageClick"
        @load="onImageLoad"
        @mousedown="startPan"
      />
    </div>
    
    <!-- 右侧工具栏 -->
    <div class="toolbar">
      <button class="info-btn" @click="showInfo = !showInfo" title="图片信息">ⓘ</button>
      <button 
        class="calibrate-btn" 
        :class="{ active: calibratingScale }"
        @click="toggleCalibration"
        title="校准比例尺"
      >
        📏
      </button>
      <button class="reset-btn" @click="resetZoom" title="重置缩放">⟲</button>
    </div>

    <!-- 图片信息 -->
    <div v-if="showInfo" class="image-info">
      <h3>{{ image.name }}</h3>
      <p>{{ formatDate(image.createdAt) }}</p>
    </div>

    <!-- 校准状态 -->
    <div v-if="calibratingScale" class="calibration-status">
      <p>点击图片上的两个点来定义比例尺</p>
      <p v-if="calibrationPoints.length > 0">已选择 {{ calibrationPoints.length }}/2 个点</p>
      <div v-if="calibrationPoints.length === 2" class="distance-input">
        <label>两点间实际距离 (m):</label>
        <input 
          v-model.number="actualDistance" 
          type="number" 
          placeholder="输入距离"
          @keyup.enter="confirmCalibration"
        />
        <button @click="confirmCalibration">确认</button>
        <button @click="cancelCalibration" class="cancel-btn">取消</button>
      </div>
    </div>

    <!-- 左下角比例尺显示（固定位置，不受缩放平移影响） -->
    <div v-if="scaleInfo" class="scale-display">
      <div class="scale-bar">
        <div class="bar" :style="{ width: scaleInfo.barWidth + 'px' }"></div>
      </div>
      <p>{{ scaleInfo.text }}</p>
    </div>

    <!-- 缩放级别显示 -->
    <div class="zoom-level">{{ (zoom * 100).toFixed(0) }}%</div>

    <!-- 校准点标记 -->
    <svg v-if="calibrationPoints.length > 0" class="calibration-overlay">
      <circle 
        v-for="(point, idx) in calibrationPoints" 
        :key="idx"
        :cx="point.screenX" 
        :cy="point.screenY" 
        r="5" 
        class="calibration-point"
      />
      <line 
        v-if="calibrationPoints.length === 2"
        :x1="calibrationPoints[0].screenX"
        :y1="calibrationPoints[0].screenY"
        :x2="calibrationPoints[1].screenX"
        :y2="calibrationPoints[1].screenY"
        class="calibration-line"
      />
    </svg>
  </div>
  <div v-else class="error-screen">
    <p>No image data available</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import api from '../services/api'

const image = ref(null)
const showInfo = ref(false)
const calibratingScale = ref(false)
const calibrationPoints = ref([])
const actualDistance = ref('')
const imageElement = ref(null)
const scaleInfo = ref(null)
const isSaving = ref(false)
const imgRect = ref(null)  // 存储图片的屏幕位置

// 缩放和平移
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const minZoom = 0.5
const maxZoom = 5
const zoomSpeed = 0.1

// 平移状态
const isPanning = ref(false)
const panStartX = ref(0)
const panStartY = ref(0)
const panStartPanX = ref(0)
const panStartPanY = ref(0)

const formatDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString()
  } catch (_e) {
    return dateString
  }
}

// 滚轮缩放（支持鼠标滚轮和触控板）
const onWheel = (event) => {
  if (calibratingScale.value) return
  
  event.preventDefault()
  
  // 获取鼠标相对于视口的位置
  const rect = event.currentTarget.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const mouseY = event.clientY - rect.top
  
  // 计算缩放中心（相对于容器中心）
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  
  const oldZoom = zoom.value
  
  // 根据滚轮方向调整缩放
  // deltaY 为负时是向上滚动（放大），为正时是向下滚动（缩小）
  const direction = event.deltaY > 0 ? -1 : 1
  zoom.value = Math.max(minZoom, Math.min(maxZoom, zoom.value + direction * zoomSpeed))
  
  // 调整平移，使缩放中心保持在鼠标位置
  const zoomDelta = zoom.value - oldZoom
  panX.value -= (mouseX - centerX) * (zoomDelta / oldZoom)
  panY.value -= (mouseY - centerY) * (zoomDelta / oldZoom)
}

// 开始平移
const startPan = (event) => {
  if (calibratingScale.value || zoom.value === 1) return
  if (event.button !== 0) return  // 只响应左键
  
  isPanning.value = true
  panStartX.value = event.clientX
  panStartY.value = event.clientY
  panStartPanX.value = panX.value
  panStartPanY.value = panY.value
  
  // 改变光标样式
  event.currentTarget.style.cursor = 'grabbing'
}

// 鼠标移动（平移）
const onMouseMove = (event) => {
  if (!isPanning.value) return
  
  const deltaX = event.clientX - panStartX.value
  const deltaY = event.clientY - panStartY.value
  
  panX.value = panStartPanX.value + deltaX
  panY.value = panStartPanY.value + deltaY
}

// 停止平移
const onMouseUp = (event) => {
  if (event.target && event.target.classList) {
    event.target.style.cursor = calibratingScale.value ? 'crosshair' : 'grab'
  }
  isPanning.value = false
}

// 重置缩放和平移
const resetZoom = () => {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
}

onMounted(async () => {
  // Retrieve image data from sessionStorage
  const data = sessionStorage.getItem('imageViewerData')
  if (data) {
    try {
      image.value = JSON.parse(data)
      
      // 尝试从数据库加载比例尺
      if (image.value && image.value.id && image.value.pixelsPerMeter) {
        try {
          const scaleData = JSON.parse(image.value.pixelsPerMeter)
          generateScaleDisplay(scaleData)
        } catch (e) {
          console.error('Failed to parse pixelsPerMeter from database:', e)
        }
      } else {
        // 如果数据库没有，尝试从 sessionStorage 恢复
        const savedScale = sessionStorage.getItem('imageScale')
        if (savedScale) {
          const scale = JSON.parse(savedScale)
          generateScaleDisplay(scale)
        }
      }
    } catch (e) {
      console.error('Failed to parse image data:', e)
    }
  }

  // 添加 window resize 监听器，更新比例尺显示
  const handleResize = () => {
    const scale = sessionStorage.getItem('imageScale')
    if (scale && scaleInfo.value) {
      try {
        generateScaleDisplay(JSON.parse(scale))
      } catch (e) {
        console.error('Failed to update scale on resize:', e)
      }
    }
  }

  window.addEventListener('resize', handleResize)
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)

  // 清理监听器
  return () => {
    window.removeEventListener('resize', handleResize)
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
})

const toggleCalibration = () => {
  if (calibratingScale.value) {
    // 取消校准
    cancelCalibration()
  } else {
    // 开始校准
    calibratingScale.value = true
    calibrationPoints.value = []
    actualDistance.value = ''
  }
}

const onImageLoad = (event) => {
  // 图片加载完成时更新 imgRect 信息
  const img = event.target
  const rect = img.getBoundingClientRect()
  imgRect.value = {
    left: rect.left,
    top: rect.top,
    width: rect.width,
    height: rect.height,
    naturalWidth: img.naturalWidth,
    naturalHeight: img.naturalHeight
  }

  // 如果已有比例尺数据，重新生成显示
  const scale = sessionStorage.getItem('imageScale')
  if (scale && scaleInfo.value) {
    try {
      generateScaleDisplay(JSON.parse(scale))
    } catch (e) {
      console.error('Failed to update scale on image load:', e)
    }
  }
}

const onImageClick = (event) => {
  if (!calibratingScale.value) return

  const img = event.currentTarget
  const rect = img.getBoundingClientRect()
  
  // 保存图片的屏幕矩形信息，用于 SVG 坐标转换
  imgRect.value = {
    left: rect.left,
    top: rect.top,
    width: rect.width,
    height: rect.height,
    naturalWidth: img.naturalWidth,
    naturalHeight: img.naturalHeight
  }
  
  // 鼠标在屏幕上的绝对位置
  const mouseX = event.clientX
  const mouseY = event.clientY
  
  // 相对于图片左上角的屏幕坐标
  const relativeX = mouseX - rect.left
  const relativeY = mouseY - rect.top
  
  // 将屏幕坐标转换为原始图片坐标
  const scaleX = img.naturalWidth / rect.width
  const scaleY = img.naturalHeight / rect.height
  
  const imageX = relativeX * scaleX
  const imageY = relativeY * scaleY
  
  if (calibrationPoints.value.length < 2) {
    calibrationPoints.value.push({ 
      imageX: imageX,  // 原始图片坐标（用于计算距离）
      imageY: imageY,
      screenX: mouseX,  // 屏幕绝对坐标（用于 SVG 显示）
      screenY: mouseY
    })
  }
}

const confirmCalibration = async () => {
  if (calibrationPoints.value.length !== 2 || !actualDistance.value) {
    alert('请选择两个点并输入距离')
    return
  }

  // 计算像素距离（使用原始图片坐标）
  const p1 = calibrationPoints.value[0]
  const p2 = calibrationPoints.value[1]
  const pixelDistance = Math.sqrt(
    Math.pow(p2.imageX - p1.imageX, 2) + Math.pow(p2.imageY - p1.imageY, 2)
  )

  // 计算像素/米的比例
  const scale = {
    pixelsPerMeter: pixelDistance / actualDistance.value,
    actualDistance: actualDistance.value,
    pixelDistance: pixelDistance
  }

  // 保存到数据库
  if (image.value && image.value.id) {
    isSaving.value = true
    try {
      const headers = {}
      if (image.value.token) {
        headers['Authorization'] = `Bearer ${image.value.token}`
      }
      await api.post(`/drawings/${image.value.id}/calibrate-scale`, scale, { headers })
      console.log('Scale calibration saved to database')
    } catch (error) {
      console.error('Failed to save scale calibration:', error)
      alert('保存比例尺失败，但本地已保存')
    } finally {
      isSaving.value = false
    }
  }

  // 保存到 sessionStorage
  sessionStorage.setItem('imageScale', JSON.stringify(scale))

  generateScaleDisplay(scale)
  calibratingScale.value = false
  calibrationPoints.value = []
  actualDistance.value = ''
}

const cancelCalibration = () => {
  calibratingScale.value = false
  calibrationPoints.value = []
  actualDistance.value = ''
}

const generateScaleDisplay = (scale) => {
  // 根据当前图片显示尺寸动态计算比例尺条形宽度
  if (!imgRect.value) {
    // 如果没有图片信息，使用默认值
    const barWidthPx = 100
    const actualLen = (barWidthPx / scale.pixelsPerMeter).toFixed(2)
    scaleInfo.value = {
      barWidth: barWidthPx,
      text: `${actualLen} m`
    }
    return
  }

  // 使用屏幕上显示的 100 像素对应的实际距离
  // 注意：barWidthPx 是屏幕像素，需要转换为原始图片像素来计算实际距离
  const barWidthScreenPx = 100  // 屏幕上显示 100px 的条形
  
  // 屏幕像素转原始图片像素的缩放因子
  const scaleX = imgRect.value.naturalWidth / imgRect.value.width
  
  // 100 个屏幕像素在原始图片上对应的像素数
  const barWidthImagePx = barWidthScreenPx * scaleX
  
  // 计算这些像素对应的实际距离
  const actualLen = (barWidthImagePx / scale.pixelsPerMeter).toFixed(2)
  
  scaleInfo.value = {
    barWidth: Math.min(barWidthScreenPx, window.innerWidth - 40),  // 不超过屏幕宽度
    text: `${actualLen} m`
  }
}
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
  overflow: hidden;
  width: 100%;
  height: 100%;
}

.image-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.05s ease-out;
}

.fullscreen-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
  user-select: none;
}

.toolbar {
  position: fixed;
  top: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 10001;
}

.info-btn,
.calibrate-btn,
.reset-btn {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: rgba(100, 181, 246, 0.2);
  color: #64b5f6;
  border: 1px solid rgba(100, 181, 246, 0.4);
  font-size: 1.2rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-btn:hover,
.calibrate-btn:hover,
.reset-btn:hover {
  background: rgba(100, 181, 246, 0.3);
  transform: scale(1.1);
}

.calibrate-btn.active {
  background: rgba(76, 175, 80, 0.3);
  color: #4caf50;
  border-color: rgba(76, 175, 80, 0.5);
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

.calibration-status {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.9);
  border: 2px solid rgba(76, 175, 80, 0.5);
  padding: 2rem;
  border-radius: 12px;
  z-index: 10003;
  text-align: center;
  color: #fff;
  min-width: 300px;
}

.calibration-status p {
  margin: 0.5rem 0;
  font-size: 1rem;
}

.distance-input {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.distance-input label {
  font-size: 0.9rem;
  color: #64b5f6;
}

.distance-input input {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(100, 181, 246, 0.3);
  color: #fff;
  border-radius: 6px;
  font-size: 1rem;
}

.distance-input input:focus {
  outline: none;
  border-color: #64b5f6;
  background: rgba(100, 181, 246, 0.1);
}

.distance-input button {
  padding: 0.75rem 1rem;
  background: #4caf50;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.distance-input button:hover {
  background: #45a049;
}

.distance-input button.cancel-btn {
  background: #f44336;
}

.distance-input button.cancel-btn:hover {
  background: #da190b;
}

.zoom-level {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  background: rgba(0, 0, 0, 0.7);
  color: #64b5f6;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid rgba(100, 181, 246, 0.3);
  z-index: 10002;
  font-size: 0.875rem;
  font-weight: 600;
}

.scale-display {
  position: fixed;
  bottom: 1rem;
  left: 1rem;
  background: rgba(0, 0, 0, 0.7);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(76, 175, 80, 0.3);
  z-index: 10002;
  min-width: 150px;
}

.scale-bar {
  height: 3px;
  background: #4caf50;
  border-radius: 2px;
  margin-bottom: 0.5rem;
  width: 100px;
}

.scale-bar .bar {
  height: 100%;
  background: #4caf50;
  border-radius: 2px;
}

.scale-display p {
  margin: 0;
  color: #fff;
  font-size: 0.875rem;
  text-align: center;
}

.calibration-overlay {
  position: fixed;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
  pointer-events: none;
}

.calibration-point {
  fill: #4caf50;
  stroke: #fff;
  stroke-width: 2;
}

.calibration-line {
  stroke: #4caf50;
  stroke-width: 2;
  stroke-dasharray: 5,5;
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
