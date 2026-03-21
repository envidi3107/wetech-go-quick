## 🌐 Frontend Guide - CCCD API Integration

### 📖 Complete Guide for Frontend Developers

This guide explains how to integrate the CCCD Extractor API into your frontend application with real-time progress tracking.

---

## 📢 Recent Changes (v1.1)

### Breaking Change: `/read-quick` is now async

The `/read-quick` endpoint has been updated to support job-based processing for better scalability and progress tracking.

**Before (v1.0):** Synchronous - waits for result and returns data directly
```
POST /read-quick → {...extracted data...}  [blocks until complete]
```

**After (v1.1):** Asynchronous - returns job_id, requires polling
```
POST /read-quick → {job_id, progress_url}  [returns immediately - HTTP 202]
GET /job-progress/{job_id} → {...job status and results...}  [poll for results]
```

✅ **Benefits:**
- Non-blocking: Frontend doesn't freeze waiting for response
- Progress tracking: Get real-time progress updates
- Better scalability: Supports multiple concurrent requests
- Cancellation: Can cancel jobs if needed

📝 **Migration:** See "Quick Read (Async)" section for new example code

---

## 🎯 API Overview

### Base URL
```
http://localhost:5000/api/go-quick
```

### Authentication
✅ No authentication required (CORS enabled)

---

## 📡 Endpoints

### 1. Health Check
```
GET /api/go-quick/health

Response:
{
  "status": "success",
  "message": "ID Quick API is running",
  "version": "1.0"
}
```

### 2. Quick Read - Single CCCD (Async with Job ID)
```
POST /api/go-quick/read-quick

Request:
- Form Data (multipart)
- mt: File (image) - Front side
- ms: File (image) - Back side
( File test in folder DATASET!!!!)
Response (Accepted - 202):
{
  "status": "success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Job đã được tạo. Kiểm tra tiến độ tại /api/go-quick/job-progress/{job_id}",
  "progress_url": "/api/go-quick/job-progress/{job_id}"
}

Response (Error - 400/500):
{
  "status": "error",
  "message": "Error description"
}

⚠️ NOTE: This endpoint now returns a job_id (HTTP 202 Accepted). 
You must poll /job-progress/{job_id} to get results.
See "Get Job Progress (Polling)" section below for details.
```

### 3. Process CCCD - Batch (Async with Job ID)
```
POST /api/go-quick/process-cccd

Request:
- Form Data (multipart)
- file: File (zip/pdf/excel) - Can contain multiple CCCD images

Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

### 4. Get Job Progress (Polling)
```
GET /api/go-quick/job-progress/{job_id}

Parameters:
- job_id: Returned from /process-cccd

Response:
{
  "status": "success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",           // pending, running, completed, failed, cancelled
    "progress": 45,               // 0-100%
    "message": "Processing image 2 of 5",
    "result": null,               // Only when completed
    "error": null,                // Only when failed
    "total_cccd": 5,
    "processed_cccd": 2,
    "total_images": 10,
    "processed_images": 4,
    "created_at": "2024-03-20T10:30:00",
    "updated_at": "2024-03-20T10:30:45"
  }
}
```

### 5. Cancel Job
```
POST /api/go-quick/job-cancel/{job_id}

Response:
{
  "status": "success",
  "message": "Job cancelled successfully",
  "cancelled": true
}
```

### 6. List All Jobs
```
GET /api/go-quick/jobs-list

Response:
{
  "status": "success",
  "total": 15,
  "jobs": [
    {
      "job_id": "abc123",
      "status": "completed",
      "progress": 100,
      ...
    },
    {
      "job_id": "def456",
      "status": "running",
      "progress": 45,
      ...
    }
  ]
}
```

---

## 💻 Implementation Examples

### JavaScript - Fetch API

#### 1. Quick Read (Async with Progress Polling)
```javascript
async function quickReadCCCD(mtFile, msFile) {
  const formData = new FormData();
  formData.append('mt', mtFile);
  formData.append('ms', msFile);
  
  try {
    const response = await fetch(
      'http://localhost:5000/api/go-quick/read-quick',
      {
        method: 'POST',
        body: formData
      }
    );
    
    const result = await response.json();
    
    if (result.status === 'success') {
      console.log('Job created:', result.job_id);
      return result.job_id;  // Return job_id to poll progress
    } else {
      console.error('Error:', result.message);
      return null;
    }
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
}

// Usage - Submit job and poll for results
const mtFile = document.getElementById('mtInput').files[0];
const msFile = document.getElementById('msInput').files[0];
const jobId = await quickReadCCCD(mtFile, msFile);

if (jobId) {
  // Now poll for results
  pollProgress(
    jobId,
    (info) => {
      console.log(`Progress: ${info.progress}% - ${info.message}`);
      document.getElementById('progressBar').style.width = info.progress + '%';
    },
    (result) => {
      console.log('CCCD Data:', result);
      displayCCCDInfo(result);
    },
    (error) => {
      console.error('Error:', error);
    }
  );
}
```

#### 2. Batch Process with Progress Polling
```javascript
// Submit job
async function submitBatchJob(zipFile) {
  const formData = new FormData();
  formData.append('file', zipFile);
  
  const response = await fetch(
    'http://localhost:5000/api/go-quick/process-cccd',
    {
      method: 'POST',
      body: formData
    }
  );
  
  const result = await response.json();
  return result.job_id;  // Return job ID for polling
}

// Poll progress
async function pollProgress(jobId, onProgress, onComplete, onError) {
  const pollInterval = 1000;  // Poll every 1 second
  let pollCount = 0;
  const maxPolls = 3600;      // Max 1 hour of polling
  
  const poll = async () => {
    try {
      const response = await fetch(
        `http://localhost:5000/api/go-quick/job-progress/${jobId}`
      );
      
      const result = await response.json();
      
      if (result.status === 'success') {
        const job = result.data;
        
        // Call progress callback
        if (onProgress) {
          onProgress({
            progress: job.progress,
            message: job.message,
            status: job.status,
            processed: job.processed_cccd,
            total: job.total_cccd
          });
        }
        
        // Check if completed
        if (job.status === 'completed') {
          if (onComplete) {
            onComplete(job.result);
          }
          return;
        }
        
        if (job.status === 'failed') {
          if (onError) {
            onError(job.error || 'Processing failed');
          }
          return;
        }
        
        if (job.status === 'cancelled') {
          if (onError) {
            onError('Job was cancelled');
          }
          return;
        }
      }
      
      // Continue polling if not completed
      pollCount++;
      if (pollCount < maxPolls) {
        setTimeout(poll, pollInterval);
      } else {
        if (onError) {
          onError('Polling timeout');
        }
      }
    } catch (error) {
      console.error('Poll error:', error);
      if (onError) {
        onError('Network error while polling');
      }
    }
  };
  
  poll();  // Start polling
}

// Usage
const jobId = await submitBatchJob(zipFile);

pollProgress(
  jobId,
  // onProgress callback
  (info) => {
    console.log(`Progress: ${info.progress}% - ${info.message}`);
    document.getElementById('progressBar').style.width = info.progress + '%';
  },
  // onComplete callback
  (result) => {
    console.log('Processing complete!', result);
    alert('Job completed successfully!');
  },
  // onError callback
  (error) => {
    console.error('Job failed:', error);
    alert('Error: ' + error);
  }
);
```

#### 3. Cancel Job
```javascript
async function cancelJob(jobId) {
  try {
    const response = await fetch(
      `http://localhost:5000/api/go-quick/job-cancel/${jobId}`,
      {
        method: 'POST'
      }
    );
    
    const result = await response.json();
    if (result.cancelled) {
      console.log('Job cancelled successfully');
      return true;
    }
    return false;
  } catch (error) {
    console.error('Cancel error:', error);
    return false;
  }
}

// Usage
document.getElementById('cancelBtn').onclick = async () => {
  await cancelJob(currentJobId);
};
```

#### 4. Complete UI Class
```javascript
class CCCDProcessor {
  constructor(baseUrl = 'http://localhost:5000/api/go-quick') {
    this.baseUrl = baseUrl;
    this.currentJobId = null;
    this.pollInterval = null;
  }
  
  async quickRead(mtFile, msFile) {
    const formData = new FormData();
    formData.append('mt', mtFile);
    formData.append('ms', msFile);
    
    const response = await fetch(`${this.baseUrl}/read-quick`, {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    if (result.status === 'success') {
      this.currentJobId = result.job_id;
      return result.job_id;  // Return job_id to poll
    }
    throw new Error(result.message || 'Quick read failed');
  }
  
  async submitBatch(zipFile) {
    const formData = new FormData();
    formData.append('file', zipFile);
    
    const response = await fetch(`${this.baseUrl}/process-cccd`, {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    this.currentJobId = result.job_id;
    return result.job_id;
  }
  
  pollProgress(callbacks = {}) {
    const {
      onProgress = () => {},
      onComplete = () => {},
      onError = () => {}
    } = callbacks;
    
    const poll = async () => {
      try {
        const response = await fetch(
          `${this.baseUrl}/job-progress/${this.currentJobId}`
        );
        const result = await response.json();
        
        if (result.status === 'success') {
          const job = result.data;
          onProgress(job);
          
          if (job.status === 'completed') {
            onComplete(job);
            this.stopPolling();
          } else if (job.status === 'failed' || job.status === 'cancelled') {
            onError(job.error || 'Processing failed');
            this.stopPolling();
          }
        }
      } catch (error) {
        onError(error);
        this.stopPolling();
      }
    };
    
    this.pollInterval = setInterval(poll, 1000);
    poll();  // First poll immediately
  }
  
  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }
  
  async cancel() {
    if (!this.currentJobId) return false;
    
    const response = await fetch(
      `${this.baseUrl}/job-cancel/${this.currentJobId}`,
      { method: 'POST' }
    );
    
    const result = await response.json();
    this.stopPolling();
    return result.cancelled;
  }
  
  async listJobs() {
    const response = await fetch(`${this.baseUrl}/jobs-list`);
    return await response.json();
  }
}

// Usage in your app
const processor = new CCCDProcessor();

// Quick read
const result = await processor.quickRead(mtFile, msFile);

// Or batch with progress
const jobId = await processor.submitBatch(zipFile);
processor.pollProgress({
  onProgress: (job) => updateUI(job),
  onComplete: (job) => showSuccess(),
  onError: (err) => showError(err)
});
```

---

## 🎨 UI Components

### HTML Template with Progress
```html
<div class="cccd-upload-container">
  <div class="upload-section">
    <div class="file-input-group">
      <label>
        Mặt Trước (MT)
        <input type="file" id="mtFile" accept="image/*" />
      </label>
      <label>
        Mặt Sau (MS)
        <input type="file" id="msFile" accept="image/*" />
      </label>
    </div>
    
    <button id="quickReadBtn" onclick="handleQuickRead()">
      Đọc Nhanh
    </button>
    <button id="batchBtn" onclick="handleBatch()">
      Xử Lý Batch
    </button>
  </div>
  
  <div id="progressSection" class="progress-section" style="display: none;">
    <div class="progress-info">
      <span id="statusText">Đang xử lý...</span>
      <span id="progressPercent">0%</span>
    </div>
    
    <div class="progress-bar">
      <div id="progressFill" class="progress-fill" style="width: 0%"></div>
    </div>
    
    <div id="messageText" class="message-text"></div>
    <div id="statsText" class="stats-text"></div>
    
    <button id="cancelBtn" onclick="handleCancel()">
      Hủy
    </button>
  </div>
  
  <div id="resultSection" class="result-section" style="display: none;">
    <div id="resultData" class="result-data"></div>
  </div>
</div>

<style>
  .progress-bar {
    width: 100%;
    height: 30px;
    background: #f0f0f0;
    border-radius: 15px;
    overflow: hidden;
    margin: 10px 0;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #45a049);
    width: 0%;
    transition: width 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
  }
  
  .progress-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-weight: bold;
  }
  
  .message-text {
    color: #666;
    margin: 10px 0;
    font-size: 14px;
  }
  
  .stats-text {
    color: #999;
    margin: 5px 0;
    font-size: 12px;
  }
</style>
```

### JavaScript Functions
```javascript
const processor = new CCCDProcessor();

async function handleQuickRead() {
  const mtFile = document.getElementById('mtFile').files[0];
  const msFile = document.getElementById('msFile').files[0];
  
  if (!mtFile || !msFile) {
    alert('Vui lòng chọn cả 2 file ảnh');
    return;
  }
  
  showProgressUI();
  
  try {
    const jobId = await processor.quickRead(mtFile, msFile);
    console.log('Quick read job created:', jobId);
    
    processor.pollProgress({
      onProgress: (job) => {
        document.getElementById('progressFill').style.width = job.progress + '%';
        document.getElementById('progressPercent').textContent = job.progress + '%';
        document.getElementById('statusText').textContent = job.status.toUpperCase();
        document.getElementById('messageText').textContent = job.message;
      },
      onComplete: (job) => {
        showResult(job.result);
        hideProgressUI();
      },
      onError: (error) => {
        alert('Lỗi: ' + error);
        hideProgressUI();
      }
    });
  } catch (error) {
    alert('Lỗi: ' + error);
    hideProgressUI();
  }
}

async function handleBatch() {
  const file = document.getElementById('batchFile').files[0];
  
  if (!file) {
    alert('Vui lòng chọn file');
    return;
  }
  
  showProgressUI();
  
  const jobId = await processor.submitBatch(file);
  
  processor.pollProgress({
    onProgress: (job) => {
      document.getElementById('progressFill').style.width = job.progress + '%';
      document.getElementById('progressPercent').textContent = job.progress + '%';
      document.getElementById('statusText').textContent = job.status.toUpperCase();
      document.getElementById('messageText').textContent = job.message;
      document.getElementById('statsText').textContent = 
        `${job.processed_cccd}/${job.total_cccd} CCCD xử lý`;
    },
    onComplete: (job) => {
      showResult(job.result);
      hideProgressUI();
    },
    onError: (error) => {
      alert('Lỗi: ' + error);
      hideProgressUI();
    }
  });
}

function handleCancel() {
  processor.cancel();
  hideProgressUI();
}

function showProgressUI() {
  document.getElementById('progressSection').style.display = 'block';
  document.getElementById('resultSection').style.display = 'none';
}

function hideProgressUI() {
  document.getElementById('progressSection').style.display = 'none';
}

function showResult(data) {
  const resultHtml = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  document.getElementById('resultData').innerHTML = resultHtml;
  document.getElementById('resultSection').style.display = 'block';
}
```

---

## 🔄 Common Workflows

### Workflow 1: Single CCCD Quick Read (Async with Polling)
```
User selects 2 files (MT, MS)
    ↓
POST /read-quick
    ↓
Get job_id back (HTTP 202 Accepted)
    ↓
Poll GET /job-progress/{job_id} every 1 second
    ↓
Update progress bar based on response
    ↓
When status = "completed", display extracted CCCD data
```

### Workflow 2: Batch Process with Polling
```
User selects ZIP file
    ↓
POST /process-cccd
    ↓
Get job_id back
    ↓
Poll GET /job-progress/{job_id} every 1-2 seconds
    ↓
Update progress bar based on response
    ↓
When status = "completed", display final results
```

---

## ⚠️ Error Handling

### Handle Different Status Codes
```javascript
async function makeRequest(url, options = {}) {
  try {
    const response = await fetch(url, options);
    
    if (response.status === 404) {
      console.error('Job not found');
      return null;
    }
    
    if (response.status === 500) {
      console.error('Server error');
      return null;
    }
    
    if (response.status === 400) {
      console.error('Bad request');
      return null;
    }
    
    const data = await response.json();
    
    if (data.status === 'error') {
      console.error('API error:', data.message);
      return null;
    }
    
    return data;
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
}
```

---

## 🧪 Testing Local

See `TEST_FRONTEND.html` for a complete working example.

---

## 📋 Response Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success - request completed immediately |
| 202 | Accepted - job created, polling required |
| 400 | Bad request (missing files, invalid format) |
| 404 | Job not found |
| 500 | Server error |

---

## ⏱️ Timeout Handling

```javascript
const TIMEOUT = 5 * 60 * 1000;  // 5 minutes
const START_TIME = Date.now();

function checkTimeout() {
  if (Date.now() - START_TIME > TIMEOUT) {
    console.error('Request timeout');
    processor.cancel();
    showError('Xử lý tòi quá lâu, vui lòng thử lại');
  }
}
```

---

## 🔗 CORS Notes

✅ CORS is enabled on the server  
✅ Can call from any frontend URL  
✅ Cookies not required  

---

## 📱 Mobile Considerations

✅ Works on mobile browsers  
✅ File upload supported  
✅ Progress display responsive  

---

## 🚀 Performance Tips

1. **Polling interval**: Use 1-2 seconds for balance
2. **Debouncing**: Debounce rapid file selections
3. **Cancelation**: Always provide cancel button
4. **Timeout**: Set realistic timeout (5-10 minutes)
5. **Caching**: Cache completed jobs locally if needed

---

**Happy coding!** 🎉
