// 登录页面专用JavaScript

// 页面加载完成后添加特殊样式类
document.addEventListener('DOMContentLoaded', function () {
    document.body.classList.add('login-page');
});

// 登录表单提交
document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    try {
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // 使用全局通知系统显示成功消息
            GlobalNotificationSystem.showNotification('success', '登录成功！正在跳转...', { duration: 1500 });

            // 跳转到主页面
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } else {
            // 使用全局通知系统显示错误消息
            GlobalNotificationSystem.showNotification('danger', data.message || '登录失败');
        }
    } catch (error) {
        // 使用全局通知系统显示错误消息
        GlobalNotificationSystem.showNotification('danger', '登录失败，请稍后重试');
    }
});

// 显示注册模态框
function showRegisterModal() {
    const modal = new bootstrap.Modal(document.getElementById('registerModal'));
    modal.show();
}

// 提交注册
async function submitRegister() {
    const form = document.getElementById('registerForm');
    const formData = new FormData(form);

    // 验证密码确认
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        GlobalNotificationSystem.showNotification('warning', '两次输入的密码不一致');
        return;
    }

    try {
        const response = await fetch('/api/v1/auth/register', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            GlobalNotificationSystem.showNotification('success', '注册成功！请使用新账号登录', { duration: 3000 });

            // 关闭模态框并清空表单
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
                form.reset();
            }, 1500);
        } else {
            GlobalNotificationSystem.showNotification('danger', data.message || '注册失败');
        }
    } catch (error) {
        GlobalNotificationSystem.showNotification('danger', '注册失败，请稍后重试');
    }
}