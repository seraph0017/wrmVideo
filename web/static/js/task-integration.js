/**
 * 任务组件集成脚本
 * 用于将现有的AI校验和解说文案生成功能与统一的任务组件进行集成
 */

// 任务类型常量
const TASK_TYPES = {
    AI_VALIDATION: 'ai_validation',
    SCRIPT_GENERATION: 'script_generation'
};

// 全局任务管理器实例
let taskStatusManager = null;
let taskLogViewer = null;

/**
 * 任务集成管理器 - 统一管理所有任务相关功能
 * 提供统一的API接口来管理不同类型的任务
 */
class TaskIntegrationManager {
    constructor() {
        this.tasks = new Map();
        this.components = new Map();
        this.eventHandlers = new Map();
        this.unifiedComponents = new Map();
        
        this.init();
    }
    
    /**
     * 初始化任务集成管理器
     */
    init() {
        this.setupEventListeners();
        this.initializeExistingTasks();
        this.initializeUnifiedComponents();
    }
    
    /**
     * 初始化统一任务组件
     */
    initializeUnifiedComponents() {
        // 初始化AI校验任务组件
        const aiValidationContainer = document.getElementById('aiValidationTaskContainer');
        if (aiValidationContainer) {
            const taskComponent = aiValidationContainer.querySelector('.unified-task-component');
            if (taskComponent) {
                const unifiedComponent = new UnifiedTaskComponent(taskComponent, {
                    taskType: 'ai_validation',
                    progressType: 'basic',
                    showTimeline: true,
                    autoRefresh: true
                });
                this.unifiedComponents.set('ai_validation', unifiedComponent);
            }
        }
        
        // 初始化解说文案生成任务组件
        const scriptGenerationContainer = document.getElementById('scriptGenerationTaskContainer');
        if (scriptGenerationContainer) {
            const taskComponent = scriptGenerationContainer.querySelector('.unified-task-component');
            if (taskComponent) {
                const unifiedComponent = new UnifiedTaskComponent(taskComponent, {
                    taskType: 'script_generation',
                    progressType: 'multi-stage',
                    showTimeline: true,
                    showStats: true,
                    autoRefresh: true
                });
                this.unifiedComponents.set('script_generation', unifiedComponent);
            }
        }
    }
    
    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 监听任务状态变化
        document.addEventListener('taskStatusChanged', (event) => {
            this.handleTaskStatusChange(event.detail);
        });
    }
    
    /**
     * 初始化现有任务
     */
    initializeExistingTasks() {
        // 扫描页面中的现有任务并注册
        const existingTasks = document.querySelectorAll('[data-task-id]');
        existingTasks.forEach(element => {
            const taskId = element.dataset.taskId;
            const taskType = element.dataset.taskType;
            if (taskId && taskType) {
                this.registerTask(taskId, taskType, element);
            }
        });
    }
    
    /**
     * 注册任务
     */
    registerTask(taskId, taskType, element) {
        this.tasks.set(taskId, {
            id: taskId,
            type: taskType,
            element: element,
            status: 'pending',
            createdAt: new Date()
        });
    }
    
    /**
     * 处理任务状态变化
     */
    handleTaskStatusChange(taskData) {
        const task = this.tasks.get(taskData.taskId);
        if (task) {
            task.status = taskData.status;
            task.lastUpdated = new Date();
            
            // 更新统一组件
            const unifiedComponent = this.unifiedComponents.get(task.type);
            if (unifiedComponent) {
                unifiedComponent.updateStatus(taskData);
            }
        }
    }
}

// 全局任务集成管理器实例
let taskIntegrationManager = null;

/**
 * 初始化任务组件
 */
function initializeTaskComponents() {
    // 初始化任务状态管理器
    taskStatusManager = new TaskStatusManager();
    
    // 初始化任务日志查看器
    taskLogViewer = new TaskLogViewer('taskLogViewer');
    
    // 初始化任务集成管理器
    taskIntegrationManager = new TaskIntegrationManager();
    
    console.log('任务组件初始化完成');
}

/**
 * AI校验相关函数
 */

/**
 * 显示AI校验状态
 * @param {string} taskId - 任务ID
 */
function showAIStatus(taskId) {
    if (!taskStatusManager) {
        console.error('任务状态管理器未初始化');
        return;
    }
    
    // 在AI校验模态框中显示任务状态
    const container = document.getElementById('aiValidationTaskContainer');
    if (container) {
        taskStatusManager.renderTaskStatus(container, {
            taskId: taskId,
            taskType: TASK_TYPES.AI_VALIDATION,
            title: 'AI校验任务',
            description: '正在执行AI校验任务...'
        });
    }
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('aiValidationModal'));
    modal.show();
}

/**
 * 显示AI校验模态框
 */
function showAIValidationModal() {
    const modal = new bootstrap.Modal(document.getElementById('aiValidationModal'));
    modal.show();
}

/**
 * 执行AI校验
 */
function executeAIValidation() {
    const form = document.getElementById('aiValidationForm');
    const formData = new FormData(form);
    
    // 获取校验选项
    const validationParameters = {
        // 页面需求：映射到 python validate_narration.py data/XXX --auto-fix
        auto_fix: true,
        // 其他可选校验项（后端目前默认脚本已包含字数校验）
        check_closeup_length: formData.get('check_narration_length') === 'on',
        check_total_length: formData.get('check_total_length') === 'on'
    };
    
    // 发送校验请求
    fetch(`/video/novels/${window.novelId}/ai-validation/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            parameters: validationParameters
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 显示任务状态
            showAIStatus(data.task_id);
            
            // 更新任务ID显示
            const taskIdElement = document.getElementById('currentValidationTaskId');
            if (taskIdElement) {
                taskIdElement.textContent = data.task_id;
            }
            
            // 开始轮询任务状态
            pollTaskStatus(data.task_id, TASK_TYPES.AI_VALIDATION);
        } else {
            alert('启动AI校验失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('AI校验请求失败:', error);
        alert('AI校验请求失败，请重试');
    });
}

/**
 * 解说文案生成相关函数
 */

/**
 * 生成解说文案
 */
function generateScript() {
    const modal = new bootstrap.Modal(document.getElementById('scriptParametersModal'));
    modal.show();
}

/**
 * 执行解说文案生成
 */
function executeScriptGeneration() {
    const form = document.getElementById('scriptParametersForm');
    const formData = new FormData(form);
    
    // 获取生成参数
    const generationParams = {
        chapters: parseInt(formData.get('chapters')),
        limit: formData.get('limit') ? parseInt(formData.get('limit')) : null,
        workers: parseInt(formData.get('workers')),
        max_retries: parseInt(formData.get('max_retries')),
        min_length: parseInt(formData.get('min_length')),
        max_length: parseInt(formData.get('max_length')),
        validate_only: formData.get('validate_only') === 'on',
        regenerate: formData.get('regenerate') === 'on'
    };
    
    // 发送生成请求
    fetch(`/video/novels/${window.novelId}/generate-script/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            parameters: generationParams
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 显示任务状态
            showScriptGenerationStatus(data.task_id);
            
            // 更新任务ID显示
            const taskIdElement = document.getElementById('currentScriptTaskId');
            if (taskIdElement) {
                taskIdElement.textContent = data.task_id;
            }
            
            // 开始轮询任务状态
            pollTaskStatus(data.task_id, TASK_TYPES.SCRIPT_GENERATION);
        } else {
            alert('启动解说文案生成失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('解说文案生成请求失败:', error);
        alert('解说文案生成请求失败，请重试');
    });
}

/**
 * 显示解说文案生成状态
 * @param {string} taskId - 任务ID
 */
function showScriptGenerationStatus(taskId) {
    if (!taskStatusManager) {
        console.error('任务状态管理器未初始化');
        return;
    }
    
    // 在解说文案生成模态框中显示任务状态
    const container = document.getElementById('scriptGenerationTaskContainer');
    if (container) {
        taskStatusManager.renderTaskStatus(container, {
            taskId: taskId,
            taskType: TASK_TYPES.SCRIPT_GENERATION,
            title: '解说文案生成任务',
            description: '正在生成解说文案...'
        });
    }
}

/**
 * 通用任务管理函数
 */

/**
 * 轮询任务状态
 * @param {string} taskId - 任务ID
 * @param {string} taskType - 任务类型
 */
function pollTaskStatus(taskId, taskType) {
    const pollInterval = setInterval(() => {
        fetch(`/api/task-status/${taskId}/`)
            .then(response => response.json())
            .then(data => {
                if (taskStatusManager) {
                    taskStatusManager.updateTaskStatus(taskId, data);
                }
                
                // 如果任务完成或失败，停止轮询
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);
                    
                    // 显示结果
                    showTaskResult(taskId, taskType, data);
                }
            })
            .catch(error => {
                console.error('获取任务状态失败:', error);
            });
    }, 2000); // 每2秒轮询一次
}

/**
 * 显示任务结果
 * @param {string} taskId - 任务ID
 * @param {string} taskType - 任务类型
 * @param {Object} taskData - 任务数据
 */
function showTaskResult(taskId, taskType, taskData) {
    let resultContainer;
    
    if (taskType === TASK_TYPES.AI_VALIDATION) {
        resultContainer = document.getElementById('aiValidationResultContainer');
    } else if (taskType === TASK_TYPES.SCRIPT_GENERATION) {
        resultContainer = document.getElementById('scriptGenerationResultContainer');
    }
    
    if (resultContainer) {
        resultContainer.classList.remove('task-hidden');
        
        const contentElement = resultContainer.querySelector('div:last-child');
        if (contentElement) {
            if (taskData.status === 'completed') {
                contentElement.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        任务执行成功！
                    </div>
                    <div class="task-result-details">
                        ${taskData.result || '任务已完成'}
                    </div>
                `;
            } else if (taskData.status === 'failed') {
                contentElement.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        任务执行失败
                    </div>
                    <div class="task-error-details">
                        ${taskData.error || '未知错误'}
                    </div>
                `;
            }
        }
    }
}

/**
 * 显示任务日志
 * @param {string} taskId - 任务ID
 * @param {string} taskType - 任务类型
 */
function showTaskLog(taskId, taskType) {
    if (!taskLogViewer) {
        console.error('任务日志查看器未初始化');
        return;
    }
    
    // 设置任务类型
    const taskTypeElement = document.getElementById('currentTaskType');
    if (taskTypeElement) {
        const typeNames = {
            [TASK_TYPES.AI_VALIDATION]: 'AI校验',
            [TASK_TYPES.SCRIPT_GENERATION]: '解说文案生成'
        };
        taskTypeElement.textContent = typeNames[taskType] || taskType;
    }
    
    // 加载任务日志
    taskLogViewer.loadTaskLog(taskId);
    
    // 显示日志模态框
    const modal = new bootstrap.Modal(document.getElementById('taskLogModal'));
    modal.show();
}

/**
 * 导出任务日志
 */
function exportTaskLog() {
    if (taskLogViewer) {
        taskLogViewer.exportLog();
    }
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保其他脚本已加载
    setTimeout(initializeTaskComponents, 100);
});

// 导出全局函数供HTML调用
window.showAIStatus = showAIStatus;
window.showAIValidationModal = showAIValidationModal;
window.executeAIValidation = executeAIValidation;
window.generateScript = generateScript;
window.executeScriptGeneration = executeScriptGeneration;
window.showTaskLog = showTaskLog;
window.exportTaskLog = exportTaskLog;
window.taskIntegrationManager = taskIntegrationManager;