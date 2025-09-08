/**
 * 通用任务进度条和状态指示器组件JavaScript
 * 提供统一的进度显示和状态管理功能
 */

/**
 * 进度指示器组件类
 */
class ProgressIndicator {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) {
            throw new Error('Progress indicator container not found');
        }
        
        this.options = {
            type: 'basic', // basic, multi-stage, circular
            showPercentage: true,
            showDetails: true,
            animated: true,
            theme: 'primary', // primary, success, warning, danger
            size: 'normal', // small, normal, large
            ...options
        };
        
        this.currentProgress = 0;
        this.stages = [];
        this.currentStage = 0;
        this.isCompleted = false;
        this.hasError = false;
        
        this.init();
    }
    
    /**
     * 初始化进度指示器
     */
    init() {
        this.container.innerHTML = '';
        this.render();
        this.bindEvents();
    }
    
    /**
     * 渲染进度指示器
     */
    render() {
        let template;
        
        switch (this.options.type) {
            case 'multi-stage':
                template = this.getMultiStageTemplate();
                break;
            case 'circular':
                template = this.getCircularTemplate();
                break;
            default:
                template = this.getBasicTemplate();
        }
        
        this.container.innerHTML = template;
        
        if (this.options.type === 'multi-stage') {
            this.renderStages();
        }
        
        this.applyTheme();
        this.applySize();
    }
    
    /**
     * 获取基础进度条模板
     */
    getBasicTemplate() {
        return `
            <div class="progress-container mb-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="progress-label">进度</span>
                    ${this.options.showPercentage ? '<span class="progress-percentage">0%</span>' : ''}
                </div>
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar progress-bar-striped ${this.options.animated ? 'progress-bar-animated' : ''}" 
                         role="progressbar" 
                         style="width: 0%" 
                         aria-valuenow="0" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                    </div>
                </div>
                ${this.options.showDetails ? '<div class="progress-details mt-1"><small class="text-muted progress-info">等待开始...</small></div>' : ''}
            </div>
        `;
    }
    
    /**
     * 获取多阶段进度条模板
     */
    getMultiStageTemplate() {
        return `
            <div class="multi-stage-progress mb-3">
                <div class="stage-indicators mb-2">
                    <!-- 阶段指示器将动态生成 -->
                </div>
                <div class="progress" style="height: 10px;">
                    <div class="progress-bar progress-bar-striped ${this.options.animated ? 'progress-bar-animated' : ''}" 
                         role="progressbar" 
                         style="width: 0%" 
                         aria-valuenow="0" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                    </div>
                </div>
                <div class="stage-details mt-2">
                    <div class="current-stage-info">
                        <small class="text-muted">当前阶段: <span class="current-stage-name">准备中</span></small>
                    </div>
                    <div class="stage-progress-info">
                        <small class="text-muted">阶段进度: <span class="stage-progress-text">0/0</span></small>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 获取圆形进度条模板
     */
    getCircularTemplate() {
        const size = this.options.size === 'small' ? 60 : this.options.size === 'large' ? 120 : 80;
        const radius = (size - 10) / 2;
        const circumference = 2 * Math.PI * radius;
        
        return `
            <div class="circular-progress-container text-center">
                <div class="circular-progress" data-percentage="0">
                    <svg class="circular-progress-svg" width="${size}" height="${size}">
                        <defs>
                            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" style="stop-color:#007bff;stop-opacity:1" />
                                <stop offset="100%" style="stop-color:#6610f2;stop-opacity:1" />
                            </linearGradient>
                        </defs>
                        <circle class="circular-progress-bg" 
                                cx="${size/2}" cy="${size/2}" r="${radius}" 
                                fill="none" 
                                stroke="#e9ecef" 
                                stroke-width="6">
                        </circle>
                        <circle class="circular-progress-bar" 
                                cx="${size/2}" cy="${size/2}" r="${radius}" 
                                fill="none" 
                                stroke="url(#progressGradient)" 
                                stroke-width="6" 
                                stroke-linecap="round" 
                                stroke-dasharray="${circumference}" 
                                stroke-dashoffset="${circumference}">
                        </circle>
                    </svg>
                    <div class="circular-progress-text">
                        <span class="percentage">0%</span>
                    </div>
                </div>
                ${this.options.showDetails ? '<div class="circular-progress-label mt-2"><small class="text-muted">处理中...</small></div>' : ''}
            </div>
        `;
    }
    
    /**
     * 渲染多阶段指示器
     */
    renderStages() {
        const stageContainer = this.container.querySelector('.stage-indicators');
        if (!stageContainer || !this.stages.length) return;
        
        stageContainer.innerHTML = '';
        
        this.stages.forEach((stage, index) => {
            const stageElement = document.createElement('div');
            stageElement.className = 'stage-indicator';
            stageElement.innerHTML = `
                <div class="stage-icon">
                    <i class="${stage.icon || 'fas fa-circle'}"></i>
                </div>
                <div class="stage-label">${stage.name}</div>
            `;
            
            if (index < this.currentStage) {
                stageElement.classList.add('completed');
            } else if (index === this.currentStage) {
                stageElement.classList.add('active');
            }
            
            stageContainer.appendChild(stageElement);
        });
    }
    
    /**
     * 应用主题样式
     */
    applyTheme() {
        const progressBar = this.container.querySelector('.progress-bar');
        if (!progressBar) return;
        
        // 移除现有主题类
        progressBar.classList.remove('bg-primary', 'bg-success', 'bg-warning', 'bg-danger');
        
        // 应用新主题
        switch (this.options.theme) {
            case 'success':
                progressBar.classList.add('bg-success');
                break;
            case 'warning':
                progressBar.classList.add('bg-warning');
                break;
            case 'danger':
                progressBar.classList.add('bg-danger');
                break;
            default:
                progressBar.classList.add('bg-primary');
        }
    }
    
    /**
     * 应用尺寸样式
     */
    applySize() {
        const progress = this.container.querySelector('.progress');
        if (!progress) return;
        
        switch (this.options.size) {
            case 'small':
                progress.style.height = '4px';
                break;
            case 'large':
                progress.style.height = '16px';
                break;
            default:
                progress.style.height = '8px';
        }
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 可以在这里添加事件监听器
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.stage-indicator')) {
                const stageIndex = Array.from(e.target.closest('.stage-indicators').children)
                    .indexOf(e.target.closest('.stage-indicator'));
                this.emit('stageClick', { stageIndex, stage: this.stages[stageIndex] });
            }
        });
    }
    
    /**
     * 设置阶段
     */
    setStages(stages) {
        this.stages = stages;
        if (this.options.type === 'multi-stage') {
            this.renderStages();
        }
        return this;
    }
    
    /**
     * 更新进度
     */
    updateProgress(percentage, details = '') {
        this.currentProgress = Math.max(0, Math.min(100, percentage));
        
        const progressBar = this.container.querySelector('.progress-bar');
        const progressPercentage = this.container.querySelector('.progress-percentage');
        const progressInfo = this.container.querySelector('.progress-info');
        const circularProgressLabel = this.container.querySelector('.circular-progress-label small');
        
        if (progressBar) {
            progressBar.style.width = `${this.currentProgress}%`;
            progressBar.setAttribute('aria-valuenow', this.currentProgress);
        }
        
        if (progressPercentage && this.options.showPercentage) {
            progressPercentage.textContent = `${Math.round(this.currentProgress)}%`;
        }
        
        if (progressInfo && details && this.options.showDetails) {
            progressInfo.textContent = details;
        }
        
        if (circularProgressLabel && details && this.options.showDetails) {
            circularProgressLabel.textContent = details;
        }
        
        // 圆形进度条特殊处理
        if (this.options.type === 'circular') {
            this.updateCircularProgress();
        }
        
        this.emit('progressUpdate', { percentage: this.currentProgress, details });
        return this;
    }
    
    /**
     * 更新圆形进度条
     */
    updateCircularProgress() {
        const circle = this.container.querySelector('.circular-progress-bar');
        const percentageText = this.container.querySelector('.percentage');
        
        if (circle) {
            const circumference = parseFloat(circle.getAttribute('stroke-dasharray'));
            const offset = circumference - (this.currentProgress / 100) * circumference;
            circle.style.strokeDashoffset = offset;
        }
        
        if (percentageText) {
            percentageText.textContent = `${Math.round(this.currentProgress)}%`;
        }
    }
    
    /**
     * 设置当前阶段
     */
    setCurrentStage(stageIndex, stageProgress = 0) {
        this.currentStage = stageIndex;
        
        if (this.options.type === 'multi-stage') {
            this.renderStages();
            
            const currentStageName = this.container.querySelector('.current-stage-name');
            const stageProgressText = this.container.querySelector('.stage-progress-text');
            
            if (currentStageName && this.stages[stageIndex]) {
                currentStageName.textContent = this.stages[stageIndex].name;
            }
            
            if (stageProgressText) {
                const total = this.stages[stageIndex]?.total || 0;
                const current = Math.round((stageProgress / 100) * total);
                stageProgressText.textContent = `${current}/${total}`;
            }
        }
        
        this.emit('stageChange', { stageIndex, stage: this.stages[stageIndex], progress: stageProgress });
        return this;
    }
    
    /**
     * 完成进度
     */
    complete(message = '已完成') {
        this.isCompleted = true;
        this.updateProgress(100, message);
        
        const progressBar = this.container.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-success');
        }
        
        this.emit('complete', { message });
        return this;
    }
    
    /**
     * 设置错误状态
     */
    setError(message = '执行失败') {
        this.hasError = true;
        
        const progressBar = this.container.querySelector('.progress-bar');
        const progressInfo = this.container.querySelector('.progress-info');
        const circularProgressLabel = this.container.querySelector('.circular-progress-label small');
        
        if (progressBar) {
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-danger');
        }
        
        if (progressInfo) {
            progressInfo.textContent = message;
            progressInfo.classList.add('text-danger');
        }
        
        if (circularProgressLabel) {
            circularProgressLabel.textContent = message;
            circularProgressLabel.classList.add('text-danger');
        }
        
        this.emit('error', { message });
        return this;
    }
    
    /**
     * 暂停进度
     */
    pause(message = '已暂停') {
        const progressBar = this.container.querySelector('.progress-bar');
        const progressInfo = this.container.querySelector('.progress-info');
        
        if (progressBar) {
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-warning');
        }
        
        if (progressInfo && message) {
            progressInfo.textContent = message;
            progressInfo.classList.add('text-warning');
        }
        
        this.emit('pause', { message });
        return this;
    }
    
    /**
     * 恢复进度
     */
    resume(message = '继续执行') {
        const progressBar = this.container.querySelector('.progress-bar');
        const progressInfo = this.container.querySelector('.progress-info');
        
        if (progressBar) {
            progressBar.classList.remove('bg-warning');
            if (this.options.animated) {
                progressBar.classList.add('progress-bar-animated');
            }
        }
        
        if (progressInfo && message) {
            progressInfo.textContent = message;
            progressInfo.classList.remove('text-warning');
        }
        
        this.emit('resume', { message });
        return this;
    }
    
    /**
     * 重置进度
     */
    reset() {
        this.currentProgress = 0;
        this.currentStage = 0;
        this.isCompleted = false;
        this.hasError = false;
        
        const progressBar = this.container.querySelector('.progress-bar');
        const progressPercentage = this.container.querySelector('.progress-percentage');
        const progressInfo = this.container.querySelector('.progress-info');
        
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', 0);
            progressBar.className = `progress-bar progress-bar-striped ${this.options.animated ? 'progress-bar-animated' : ''}`;
            this.applyTheme();
        }
        
        if (progressPercentage) {
            progressPercentage.textContent = '0%';
        }
        
        if (progressInfo) {
            progressInfo.textContent = '等待开始...';
            progressInfo.className = 'text-muted progress-info';
        }
        
        if (this.options.type === 'multi-stage') {
            this.renderStages();
        }
        
        if (this.options.type === 'circular') {
            this.updateCircularProgress();
        }
        
        this.emit('reset');
        return this;
    }
    
    /**
     * 获取当前状态
     */
    getStatus() {
        return {
            progress: this.currentProgress,
            stage: this.currentStage,
            isCompleted: this.isCompleted,
            hasError: this.hasError,
            stages: this.stages
        };
    }
    
    /**
     * 销毁组件
     */
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
        }
        this.emit('destroy');
    }
    
    /**
     * 事件发射器
     */
    emit(eventName, data = {}) {
        const event = new CustomEvent(`progress:${eventName}`, {
            detail: { ...data, instance: this }
        });
        this.container.dispatchEvent(event);
    }
    
    /**
     * 事件监听器
     */
    on(eventName, callback) {
        this.container.addEventListener(`progress:${eventName}`, callback);
        return this;
    }
    
    /**
     * 移除事件监听器
     */
    off(eventName, callback) {
        this.container.removeEventListener(`progress:${eventName}`, callback);
        return this;
    }
}

/**
 * 状态徽章组件类
 */
class StatusBadge {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) {
            throw new Error('Status badge container not found');
        }
        
        this.options = {
            showIcon: true,
            showText: true,
            size: 'normal', // small, normal, large
            style: 'filled', // filled, outline
            ...options
        };
        
        this.currentStatus = 'pending';
        
        this.init();
    }
    
    init() {
        this.render();
    }
    
    render() {
        const sizeClass = this.options.size === 'small' ? 'badge-sm' : 
                         this.options.size === 'large' ? 'badge-lg' : '';
        const styleClass = this.options.style === 'outline' ? 'badge-outline' : '';
        
        this.container.innerHTML = `
            <div class="status-badge-container">
                <span class="badge status-badge ${sizeClass} ${styleClass}" data-status="${this.currentStatus}">
                    ${this.options.showIcon ? '<i class="fas fa-clock me-1"></i>' : ''}
                    ${this.options.showText ? '<span class="status-text">等待中</span>' : ''}
                </span>
            </div>
        `;
    }
    
    updateStatus(status, text = '', icon = '') {
        this.currentStatus = status;
        
        const badge = this.container.querySelector('.status-badge');
        const statusText = this.container.querySelector('.status-text');
        const iconElement = this.container.querySelector('i');
        
        if (badge) {
            badge.setAttribute('data-status', status);
        }
        
        if (statusText && this.options.showText) {
            statusText.textContent = text || this.getStatusText(status);
        }
        
        if (iconElement && this.options.showIcon) {
            iconElement.className = icon || this.getStatusIcon(status);
        }
        
        this.emit('statusChange', { status, text, icon });
        return this;
    }
    
    getStatusText(status) {
        const statusTexts = {
            pending: '等待中',
            running: '进行中',
            completed: '已完成',
            failed: '失败',
            paused: '已暂停',
            cancelled: '已取消'
        };
        return statusTexts[status] || status;
    }
    
    getStatusIcon(status) {
        const statusIcons = {
            pending: 'fas fa-clock me-1',
            running: 'fas fa-spinner fa-spin me-1',
            completed: 'fas fa-check-circle me-1',
            failed: 'fas fa-exclamation-circle me-1',
            paused: 'fas fa-pause-circle me-1',
            cancelled: 'fas fa-times-circle me-1'
        };
        return statusIcons[status] || 'fas fa-circle me-1';
    }
    
    /**
     * 事件发射器
     */
    emit(eventName, data = {}) {
        const event = new CustomEvent(`status:${eventName}`, {
            detail: { ...data, instance: this }
        });
        this.container.dispatchEvent(event);
    }
    
    /**
     * 事件监听器
     */
    on(eventName, callback) {
        this.container.addEventListener(`status:${eventName}`, callback);
        return this;
    }
}

/**
 * 任务时间线组件类
 */
class TaskTimeline {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) {
            throw new Error('Task timeline container not found');
        }
        
        this.options = {
            title: '任务时间线',
            showTime: true,
            maxItems: 50,
            ...options
        };
        
        this.items = [];
        
        this.init();
    }
    
    init() {
        this.render();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="task-timeline">
                <div class="timeline-header mb-3">
                    <h6 class="mb-0">${this.options.title}</h6>
                </div>
                <div class="timeline-content">
                    <!-- 时间线项目将动态生成 -->
                </div>
            </div>
        `;
    }
    
    addItem(title, description = '', status = 'completed', time = null) {
        const item = {
            id: Date.now() + Math.random(),
            title,
            description,
            status,
            time: time || new Date(),
            timestamp: Date.now()
        };
        
        this.items.unshift(item);
        
        // 限制最大项目数
        if (this.items.length > this.options.maxItems) {
            this.items = this.items.slice(0, this.options.maxItems);
        }
        
        this.renderItems();
        this.emit('itemAdded', { item });
        return this;
    }
    
    renderItems() {
        const timelineContent = this.container.querySelector('.timeline-content');
        if (!timelineContent) return;
        
        timelineContent.innerHTML = this.items.map(item => `
            <div class="timeline-item ${item.status}" data-id="${item.id}">
                <div class="timeline-marker">
                    <i class="fas fa-circle"></i>
                </div>
                <div class="timeline-content">
                    ${this.options.showTime ? `
                        <div class="timeline-time">
                            <small class="text-muted">${this.formatTime(item.time)}</small>
                        </div>
                    ` : ''}
                    <div class="timeline-title">
                        <strong>${item.title}</strong>
                    </div>
                    ${item.description ? `
                        <div class="timeline-description">
                            <small class="text-muted">${item.description}</small>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }
    
    formatTime(time) {
        if (!(time instanceof Date)) {
            time = new Date(time);
        }
        return time.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    clear() {
        this.items = [];
        this.renderItems();
        this.emit('cleared');
        return this;
    }
    
    /**
     * 事件发射器
     */
    emit(eventName, data = {}) {
        const event = new CustomEvent(`timeline:${eventName}`, {
            detail: { ...data, instance: this }
        });
        this.container.dispatchEvent(event);
    }
    
    /**
     * 事件监听器
     */
    on(eventName, callback) {
        this.container.addEventListener(`timeline:${eventName}`, callback);
        return this;
    }
}

/**
 * 任务统计组件类
 */
class TaskStats {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) {
            throw new Error('Task stats container not found');
        }
        
        this.options = {
            showIcons: true,
            animated: true,
            ...options
        };
        
        this.stats = {
            total: 0,
            completed: 0,
            running: 0,
            failed: 0
        };
        
        this.init();
    }
    
    init() {
        this.render();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="task-stats-container">
                <div class="row g-3">
                    <div class="col-md-3">
                        <div class="stat-card total-tasks text-center p-3 border rounded">
                            ${this.options.showIcons ? `
                                <div class="stat-icon mb-2">
                                    <i class="fas fa-tasks text-primary"></i>
                                </div>
                            ` : ''}
                            <div class="stat-value">
                                <h5 class="mb-0 total-tasks-count">0</h5>
                            </div>
                            <div class="stat-label">
                                <small class="text-muted">总任务数</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card completed-tasks text-center p-3 border rounded">
                            ${this.options.showIcons ? `
                                <div class="stat-icon mb-2">
                                    <i class="fas fa-check-circle text-success"></i>
                                </div>
                            ` : ''}
                            <div class="stat-value">
                                <h5 class="mb-0 completed-tasks-count">0</h5>
                            </div>
                            <div class="stat-label">
                                <small class="text-muted">已完成</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card running-tasks text-center p-3 border rounded">
                            ${this.options.showIcons ? `
                                <div class="stat-icon mb-2">
                                    <i class="fas fa-spinner text-warning"></i>
                                </div>
                            ` : ''}
                            <div class="stat-value">
                                <h5 class="mb-0 running-tasks-count">0</h5>
                            </div>
                            <div class="stat-label">
                                <small class="text-muted">进行中</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card failed-tasks text-center p-3 border rounded">
                            ${this.options.showIcons ? `
                                <div class="stat-icon mb-2">
                                    <i class="fas fa-exclamation-circle text-danger"></i>
                                </div>
                            ` : ''}
                            <div class="stat-value">
                                <h5 class="mb-0 failed-tasks-count">0</h5>
                            </div>
                            <div class="stat-label">
                                <small class="text-muted">失败</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    updateStats(stats) {
        this.stats = { ...this.stats, ...stats };
        
        const totalElement = this.container.querySelector('.total-tasks-count');
        const completedElement = this.container.querySelector('.completed-tasks-count');
        const runningElement = this.container.querySelector('.running-tasks-count');
        const failedElement = this.container.querySelector('.failed-tasks-count');
        
        if (this.options.animated) {
            this.animateNumber(totalElement, this.stats.total);
            this.animateNumber(completedElement, this.stats.completed);
            this.animateNumber(runningElement, this.stats.running);
            this.animateNumber(failedElement, this.stats.failed);
        } else {
            if (totalElement) totalElement.textContent = this.stats.total;
            if (completedElement) completedElement.textContent = this.stats.completed;
            if (runningElement) runningElement.textContent = this.stats.running;
            if (failedElement) failedElement.textContent = this.stats.failed;
        }
        
        this.emit('statsUpdated', { stats: this.stats });
        return this;
    }
    
    animateNumber(element, targetValue) {
        if (!element) return;
        
        const currentValue = parseInt(element.textContent) || 0;
        const increment = targetValue > currentValue ? 1 : -1;
        const duration = 500;
        const steps = Math.abs(targetValue - currentValue);
        const stepDuration = steps > 0 ? duration / steps : 0;
        
        let current = currentValue;
        
        const timer = setInterval(() => {
            current += increment;
            element.textContent = current;
            
            if (current === targetValue) {
                clearInterval(timer);
            }
        }, stepDuration);
    }
    
    /**
     * 事件发射器
     */
    emit(eventName, data = {}) {
        const event = new CustomEvent(`stats:${eventName}`, {
            detail: { ...data, instance: this }
        });
        this.container.dispatchEvent(event);
    }
    
    /**
     * 事件监听器
     */
    on(eventName, callback) {
        this.container.addEventListener(`stats:${eventName}`, callback);
        return this;
    }
}

/**
 * 进度指示器工厂函数
 */
function createProgressIndicator(container, options = {}) {
    return new ProgressIndicator(container, options);
}

/**
 * 状态徽章工厂函数
 */
function createStatusBadge(container, options = {}) {
    return new StatusBadge(container, options);
}

/**
 * 任务时间线工厂函数
 */
function createTaskTimeline(container, options = {}) {
    return new TaskTimeline(container, options);
}

/**
 * 任务统计工厂函数
 */
function createTaskStats(container, options = {}) {
    return new TaskStats(container, options);
}

// 导出组件类（避免重复声明）
if (typeof window !== 'undefined') {
    if (!window.ProgressIndicator) {
        window.ProgressIndicator = ProgressIndicator;
    }
    if (!window.StatusBadge) {
        window.StatusBadge = StatusBadge;
    }
    if (!window.TaskTimeline) {
        window.TaskTimeline = TaskTimeline;
    }
    if (!window.TaskStats) {
        window.TaskStats = TaskStats;
    }
    
    window.createProgressIndicator = createProgressIndicator;
    window.createStatusBadge = createStatusBadge;
    window.createTaskTimeline = createTaskTimeline;
    window.createTaskStats = createTaskStats;
}

// 模块导出（如果支持）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ProgressIndicator,
        StatusBadge,
        TaskTimeline,
        TaskStats,
        createProgressIndicator,
        createStatusBadge,
        createTaskTimeline,
        createTaskStats
    };
}