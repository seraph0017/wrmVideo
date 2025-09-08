/**
 * 统一任务界面组件JavaScript
 * 用于AI生成、AI校验等任务的界面交互
 */

/**
 * 任务状态管理器
 */
class TaskStatusManager {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            autoRefresh: true,
            refreshInterval: 2000,
            showProgress: true,
            showLogs: true,
            maxLogLines: 100,
            ...options
        };
        
        this.taskId = null;
        this.status = 'pending';
        this.progress = 0;
        this.refreshTimer = null;
        this.logLines = [];
        
        this.init();
    }
    
    /**
     * 初始化组件
     */
    init() {
        if (!this.container) {
            console.error('Task status container not found');
            return;
        }
        
        this.render();
        this.bindEvents();
    }
    
    /**
     * 渲染界面
     */
    render() {
        this.container.innerHTML = `
            <div class="task-status-container">
                <div class="task-info">
                    <div class="task-info-left">
                        <span class="task-status-badge status-pending" id="taskStatusBadge">准备中</span>
                        <span class="task-progress-text" id="taskProgressText">0%</span>
                    </div>
                    <div class="task-info-right">
                        <div class="task-action-buttons">
                            <button class="task-btn btn-outline-primary" id="showLogBtn" style="display: none;">查看日志</button>
                            <button class="task-btn btn-outline-secondary" id="pauseBtn" style="display: none;">暂停</button>
                            <button class="task-btn btn-danger" id="stopBtn" style="display: none;">停止</button>
                        </div>
                    </div>
                </div>
                
                ${this.options.showProgress ? `
                <div class="task-progress-container">
                    <div class="task-progress-bar">
                        <div class="task-progress-fill" id="taskProgressFill" style="width: 0%"></div>
                    </div>
                </div>
                ` : ''}
                
                <div class="task-status-text" id="taskStatusText">等待任务开始...</div>
                
                ${this.options.showLogs ? `
                <div class="task-log-container task-hidden" id="taskLogContainer">
                    <div id="taskLogContent"></div>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        const showLogBtn = this.container.querySelector('#showLogBtn');
        const pauseBtn = this.container.querySelector('#pauseBtn');
        const stopBtn = this.container.querySelector('#stopBtn');
        
        if (showLogBtn) {
            showLogBtn.addEventListener('click', () => this.toggleLogs());
        }
        
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.togglePause());
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopTask());
        }
    }
    
    /**
     * 开始任务
     */
    startTask(taskId, taskName = '任务') {
        this.taskId = taskId;
        this.updateStatus('running', `${taskName}正在执行中...`);
        this.showButton('showLogBtn');
        this.showButton('stopBtn');
        
        if (this.options.autoRefresh) {
            this.startRefresh();
        }
        
        this.addLog('info', `任务已启动，任务ID: ${taskId}`);
    }
    
    /**
     * 更新任务状态
     */
    updateStatus(status, message = '', progress = null) {
        this.status = status;
        
        const statusBadge = this.container.querySelector('#taskStatusBadge');
        const statusText = this.container.querySelector('#taskStatusText');
        const progressFill = this.container.querySelector('#taskProgressFill');
        const progressText = this.container.querySelector('#taskProgressText');
        
        // 更新状态徽章
        if (statusBadge) {
            statusBadge.className = `task-status-badge status-${status}`;
            statusBadge.textContent = this.getStatusText(status);
        }
        
        // 更新状态文本
        if (statusText) {
            statusText.textContent = message;
        }
        
        // 更新进度
        if (progress !== null) {
            this.updateProgress(progress);
        }
        
        // 根据状态更新按钮显示
        this.updateButtonsVisibility();
        
        // 添加状态变化动画
        this.container.querySelector('.task-status-container').classList.add('task-fade-in');
    }
    
    /**
     * 更新进度
     */
    updateProgress(progress) {
        this.progress = Math.max(0, Math.min(100, progress));
        
        const progressFill = this.container.querySelector('#taskProgressFill');
        const progressText = this.container.querySelector('#taskProgressText');
        
        if (progressFill) {
            progressFill.style.width = `${this.progress}%`;
            
            // 根据状态设置进度条样式
            progressFill.className = `task-progress-fill ${this.status === 'running' ? 'animated' : ''}`;
            
            if (this.status === 'success') {
                progressFill.classList.add('success');
            } else if (this.status === 'failed') {
                progressFill.classList.add('failed');
            }
        }
        
        if (progressText) {
            progressText.textContent = `${this.progress}%`;
        }
    }
    
    /**
     * 添加日志
     */
    addLog(level, message, timestamp = null) {
        if (!this.options.showLogs) return;
        
        const logEntry = {
            level,
            message,
            timestamp: timestamp || new Date().toLocaleTimeString()
        };
        
        this.logLines.push(logEntry);
        
        // 限制日志行数
        if (this.logLines.length > this.options.maxLogLines) {
            this.logLines = this.logLines.slice(-this.options.maxLogLines);
        }
        
        this.renderLogs();
    }
    
    /**
     * 渲染日志
     */
    renderLogs() {
        const logContent = this.container.querySelector('#taskLogContent');
        if (!logContent) return;
        
        logContent.innerHTML = this.logLines.map(entry => `
            <div class="log-entry ${entry.level}">
                <span class="log-timestamp">${entry.timestamp}</span>
                <span class="log-level">${entry.level.toUpperCase()}</span>
                <span class="log-message">${entry.message}</span>
            </div>
        `).join('');
        
        // 自动滚动到底部
        logContent.scrollTop = logContent.scrollHeight;
    }
    
    /**
     * 切换日志显示
     */
    toggleLogs() {
        const logContainer = this.container.querySelector('#taskLogContainer');
        const showLogBtn = this.container.querySelector('#showLogBtn');
        
        if (logContainer.classList.contains('task-hidden')) {
            logContainer.classList.remove('task-hidden');
            showLogBtn.textContent = '隐藏日志';
        } else {
            logContainer.classList.add('task-hidden');
            showLogBtn.textContent = '查看日志';
        }
    }
    
    /**
     * 切换暂停状态
     */
    togglePause() {
        const pauseBtn = this.container.querySelector('#pauseBtn');
        
        if (this.options.autoRefresh) {
            this.stopRefresh();
            pauseBtn.textContent = '继续';
            this.addLog('warning', '已暂停自动刷新');
        } else {
            this.startRefresh();
            pauseBtn.textContent = '暂停';
            this.addLog('info', '已恢复自动刷新');
        }
    }
    
    /**
     * 停止任务
     */
    stopTask() {
        if (!this.taskId) return;
        
        if (confirm('确定要停止当前任务吗？')) {
            this.addLog('warning', '正在停止任务...');
            
            // 发送停止请求
            fetch('/video/stop-task/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ task_id: this.taskId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateStatus('stopped', '任务已停止');
                    this.addLog('info', '任务已成功停止');
                } else {
                    this.addLog('error', `停止任务失败: ${data.message}`);
                }
            })
            .catch(error => {
                this.addLog('error', `停止任务失败: ${error.message}`);
            });
        }
    }
    
    /**
     * 开始自动刷新
     */
    startRefresh() {
        if (this.refreshTimer) return;
        
        this.options.autoRefresh = true;
        this.refreshTimer = setInterval(() => {
            this.refreshStatus();
        }, this.options.refreshInterval);
    }
    
    /**
     * 停止自动刷新
     */
    stopRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
        this.options.autoRefresh = false;
    }
    
    /**
     * 刷新任务状态
     */
    refreshStatus() {
        if (!this.taskId) return;
        
        fetch(`/video/task-status/?task_id=${this.taskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.updateStatus(data.status, data.message || '', data.progress);
                
                // 如果有新日志，添加到显示中
                if (data.logs && Array.isArray(data.logs)) {
                    data.logs.forEach(log => {
                        this.addLog(log.level, log.message, log.timestamp);
                    });
                }
                
                // 如果任务完成，停止刷新
                if (['success', 'failed', 'stopped'].includes(data.status)) {
                    this.stopRefresh();
                    this.hideButton('stopBtn');
                    
                    if (data.status === 'success') {
                        this.addLog('success', '任务执行完成！');
                    } else if (data.status === 'failed') {
                        this.addLog('error', `任务执行失败: ${data.error || '未知错误'}`);
                    }
                }
            }
        })
        .catch(error => {
            this.addLog('error', `获取任务状态失败: ${error.message}`);
        });
    }
    
    /**
     * 获取状态文本
     */
    getStatusText(status) {
        const statusMap = {
            'pending': '准备中',
            'running': '运行中',
            'success': '已完成',
            'failed': '失败',
            'stopped': '已停止'
        };
        return statusMap[status] || status;
    }
    
    /**
     * 更新按钮显示状态
     */
    updateButtonsVisibility() {
        const showLogBtn = this.container.querySelector('#showLogBtn');
        const pauseBtn = this.container.querySelector('#pauseBtn');
        const stopBtn = this.container.querySelector('#stopBtn');
        
        if (this.status === 'running') {
            this.showButton('showLogBtn');
            this.showButton('pauseBtn');
            this.showButton('stopBtn');
        } else {
            this.hideButton('pauseBtn');
            this.hideButton('stopBtn');
        }
    }
    
    /**
     * 显示按钮
     */
    showButton(buttonId) {
        const button = this.container.querySelector(`#${buttonId}`);
        if (button) {
            button.style.display = 'inline-flex';
        }
    }
    
    /**
     * 隐藏按钮
     */
    hideButton(buttonId) {
        const button = this.container.querySelector(`#${buttonId}`);
        if (button) {
            button.style.display = 'none';
        }
    }
    
    /**
     * 获取CSRF Token
     */
    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    /**
     * 清理资源
     */
    destroy() {
        this.stopRefresh();
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

/**
 * 任务日志查看器
 */
class TaskLogViewer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            maxLines: 1000,
            autoScroll: true,
            showTimestamp: true,
            showLevel: true,
            filterLevels: ['info', 'warning', 'error', 'debug'],
            ...options
        };
        
        this.logs = [];
        this.filteredLogs = [];
        this.currentFilter = 'all';
        
        this.init();
    }
    
    /**
     * 初始化组件
     */
    init() {
        if (!this.container) {
            console.error('Task log container not found');
            return;
        }
        
        this.render();
        this.bindEvents();
    }
    
    /**
     * 渲染界面
     */
    render() {
        this.container.innerHTML = `
            <div class="task-log-viewer">
                <div class="log-controls">
                    <div class="log-filter-buttons">
                        <button class="task-btn btn-outline-secondary active" data-filter="all">全部</button>
                        <button class="task-btn btn-outline-secondary" data-filter="info">信息</button>
                        <button class="task-btn btn-outline-secondary" data-filter="warning">警告</button>
                        <button class="task-btn btn-outline-secondary" data-filter="error">错误</button>
                        <button class="task-btn btn-outline-secondary" data-filter="debug">调试</button>
                    </div>
                    <div class="log-action-buttons">
                        <button class="task-btn btn-outline-secondary" id="clearLogsBtn">清空</button>
                        <button class="task-btn btn-outline-secondary" id="downloadLogsBtn">下载</button>
                        <label class="task-btn btn-outline-secondary">
                            <input type="checkbox" id="autoScrollCheck" ${this.options.autoScroll ? 'checked' : ''}>
                            自动滚动
                        </label>
                    </div>
                </div>
                <div class="task-log-container" id="logContainer">
                    <div id="logContent"></div>
                </div>
            </div>
        `;
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 过滤按钮
        this.container.querySelectorAll('[data-filter]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter(e.target.dataset.filter);
            });
        });
        
        // 清空日志
        const clearBtn = this.container.querySelector('#clearLogsBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearLogs());
        }
        
        // 下载日志
        const downloadBtn = this.container.querySelector('#downloadLogsBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadLogs());
        }
        
        // 自动滚动
        const autoScrollCheck = this.container.querySelector('#autoScrollCheck');
        if (autoScrollCheck) {
            autoScrollCheck.addEventListener('change', (e) => {
                this.options.autoScroll = e.target.checked;
            });
        }
    }
    
    /**
     * 添加日志
     */
    addLog(level, message, timestamp = null) {
        const logEntry = {
            level,
            message,
            timestamp: timestamp || new Date().toISOString()
        };
        
        this.logs.push(logEntry);
        
        // 限制日志数量
        if (this.logs.length > this.options.maxLines) {
            this.logs = this.logs.slice(-this.options.maxLines);
        }
        
        this.applyFilter();
        this.renderLogs();
    }
    
    /**
     * 设置过滤器
     */
    setFilter(filter) {
        this.currentFilter = filter;
        
        // 更新按钮状态
        this.container.querySelectorAll('[data-filter]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        this.applyFilter();
        this.renderLogs();
    }
    
    /**
     * 应用过滤器
     */
    applyFilter() {
        if (this.currentFilter === 'all') {
            this.filteredLogs = [...this.logs];
        } else {
            this.filteredLogs = this.logs.filter(log => log.level === this.currentFilter);
        }
    }
    
    /**
     * 渲染日志
     */
    renderLogs() {
        const logContent = this.container.querySelector('#logContent');
        if (!logContent) return;
        
        logContent.innerHTML = this.filteredLogs.map(entry => {
            const timestamp = this.options.showTimestamp ? 
                `<span class="log-timestamp">${new Date(entry.timestamp).toLocaleTimeString()}</span>` : '';
            const level = this.options.showLevel ? 
                `<span class="log-level">${entry.level.toUpperCase()}</span>` : '';
            
            return `
                <div class="log-entry ${entry.level}">
                    ${timestamp}
                    ${level}
                    <span class="log-message">${entry.message}</span>
                </div>
            `;
        }).join('');
        
        // 自动滚动
        if (this.options.autoScroll) {
            logContent.scrollTop = logContent.scrollHeight;
        }
    }
    
    /**
     * 清空日志
     */
    clearLogs() {
        this.logs = [];
        this.filteredLogs = [];
        this.renderLogs();
    }
    
    /**
     * 下载日志
     */
    downloadLogs() {
        const logText = this.logs.map(entry => {
            const timestamp = new Date(entry.timestamp).toLocaleString();
            return `[${timestamp}] [${entry.level.toUpperCase()}] ${entry.message}`;
        }).join('\n');
        
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `task-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

/**
 * 工具函数
 */
const TaskUtils = {
    /**
     * 格式化时间
     */
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleString('zh-CN');
    },
    
    /**
     * 格式化持续时间
     */
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}小时${minutes}分钟${secs}秒`;
        } else if (minutes > 0) {
            return `${minutes}分钟${secs}秒`;
        } else {
            return `${secs}秒`;
        }
    },
    
    /**
     * 获取状态颜色
     */
    getStatusColor(status) {
        const colorMap = {
            'pending': '#ffc107',
            'running': '#007bff',
            'success': '#28a745',
            'failed': '#dc3545',
            'stopped': '#6c757d'
        };
        return colorMap[status] || '#6c757d';
    },
    
    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        // 这里可以集成第三方通知库，如 toastr
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
};

// 导出到全局
window.TaskStatusManager = TaskStatusManager;
window.TaskLogViewer = TaskLogViewer;
window.TaskUtils = TaskUtils;