// 许愿小程序前端逻辑
class WishApp {
    constructor() {
        this.apiBaseUrl = window.location.port === '8080' ? 
            'http://localhost:8000' : 'http://localhost:8000';
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadWishes();
        this.setupCharCounter();
    }

    bindEvents() {
        // 提交愿望
        document.getElementById('submitWish').addEventListener('click', () => {
            this.submitWish();
        });

        // 回车提交
        document.getElementById('wishInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.submitWish();
            }
        });
    }

    setupCharCounter() {
        const textarea = document.getElementById('wishInput');
        const counter = document.getElementById('charCount');

        textarea.addEventListener('input', () => {
            const length = textarea.value.length;
            counter.textContent = `${length}/500`;
            
            if (length > 480) {
                counter.style.color = '#dc3545';
            } else {
                counter.style.color = '#999';
            }
        });
    }

    async submitWish() {
        const textarea = document.getElementById('wishInput');
        const content = textarea.value.trim();

        if (!content) {
            this.showMessage('请输入愿望内容', 'error');
            return;
        }

        if (content.length > 500) {
            this.showMessage('愿望内容不能超过500字符', 'error');
            return;
        }

        const submitBtn = document.getElementById('submitWish');
        this.setSubmitButtonState(submitBtn, true);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/wishes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            });

            const result = await response.json();

            if (response.ok) {
                textarea.value = '';
                document.getElementById('charCount').textContent = '0/500';
                this.showMessage('许愿成功！', 'success');
                this.loadWishes(); // 重新加载愿望列表
            } else {
                throw new Error(result.detail || '提交失败');
            }
        } catch (error) {
            console.error('提交愿望失败:', error);
            this.showMessage(error.message || '提交失败，请稍后重试', 'error');
        } finally {
            this.setSubmitButtonState(submitBtn, false);
        }
    }

    setSubmitButtonState(button, loading) {
        if (loading) {
            button.disabled = true;
            button.textContent = '提交中...';
        } else {
            button.disabled = false;
            button.textContent = '许愿 ✨';
        }
    }

    async loadWishes() {
        try {
            const container = document.getElementById('wishesContainer');
            container.innerHTML = '<div class="loading">加载中...</div>';

            const response = await fetch(`${this.apiBaseUrl}/api/wishes`);
            const wishes = await response.json();

            if (response.ok) {
                this.renderWishes(wishes);
            } else {
                throw new Error('加载愿望失败');
            }
        } catch (error) {
            console.error('加载愿望失败:', error);
            const container = document.getElementById('wishesContainer');
            container.innerHTML = `
                <div class="error-message">
                    加载失败，请刷新页面重试
                </div>
            `;
        }
    }

    renderWishes(wishes) {
        const container = document.getElementById('wishesContainer');
        
        if (wishes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>还没有愿望，快来许下第一个愿望吧！</p>
                </div>
            `;
            return;
        }

        container.innerHTML = wishes.map(wish => this.createWishCard(wish)).join('');
        
        // 为每个点赞按钮绑定事件
        document.querySelectorAll('.like-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const wishId = parseInt(e.currentTarget.dataset.wishId);
                this.toggleLike(wishId, e.currentTarget);
            });
        });
    }

    createWishCard(wish) {
        const date = new Date(wish.created_at);
        const formattedDate = date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });

        return `
            <div class="wish-card" data-wish-id="${wish.id}">
                <div class="wish-content">
                    ${this.escapeHtml(wish.content)}
                </div>
                <div class="wish-meta">
                    <span class="create-time">${formattedDate}</span>
                    <div class="like-section">
                        <button class="like-btn ${wish.liked_by_user ? 'liked' : ''}" 
                                data-wish-id="${wish.id}">
                            <span class="like-icon">❤️</span>
                            <span class="like-text">${wish.liked_by_user ? '已赞' : '点赞'}</span>
                            <span class="like-count">${wish.likes}</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async toggleLike(wishId, buttonElement) {
        // 防止重复点击
        if (buttonElement.classList.contains('loading')) {
            return;
        }

        // 添加加载状态
        buttonElement.classList.add('loading');
        buttonElement.disabled = true;

        try {
            const isLiked = buttonElement.classList.contains('liked');
            const method = isLiked ? 'DELETE' : 'POST';
            const url = `${this.apiBaseUrl}/api/wishes/${wishId}/like`;

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const result = await response.json();
                
                // 更新按钮状态
                if (isLiked) {
                    buttonElement.classList.remove('liked');
                    buttonElement.querySelector('.like-text').textContent = '点赞';
                    // 减少点赞数
                    let count = parseInt(buttonElement.querySelector('.like-count').textContent);
                    buttonElement.querySelector('.like-count').textContent = count - 1;
                } else {
                    buttonElement.classList.add('liked');
                    buttonElement.querySelector('.like-text').textContent = '已赞';
                    // 增加点赞数
                    let count = parseInt(buttonElement.querySelector('.like-count').textContent);
                    buttonElement.querySelector('.like-count').textContent = count + 1;
                }
            } else {
                const error = await response.json();
                throw new Error(error.detail || '操作失败');
            }
        } catch (error) {
            console.error('点赞操作失败:', error);
            this.showMessage(error.message || '操作失败，请稍后重试', 'error');
        } finally {
            buttonElement.classList.remove('loading');
            buttonElement.disabled = false;
        }
    }

    showMessage(message, type = 'info') {
        // 移除现有的消息
        const existingMessage = document.querySelector('.message');
        if (existingMessage) {
            existingMessage.remove();
        }

        const messageEl = document.createElement('div');
        messageEl.className = `message ${type}`;
        messageEl.textContent = message;

        const formSection = document.querySelector('.wish-form-section');
        formSection.parentNode.insertBefore(messageEl, formSection.nextSibling);

        // 3秒后自动消失
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.remove();
            }
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new WishApp();
});

// 导出类以便调试
window.WishApp = WishApp;