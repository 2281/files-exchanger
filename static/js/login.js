// Показать сообщение над формой
function showMessage(text, type) {
    const message = document.getElementById('message');
    message.className = `alert alert-${type}`;
    message.textContent = text;
}

// POST JSON и разбор ответа; при ошибке выбрасывает Error с текстом из API
async function postJson(url, body) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Проверьте введённые данные');
    }
    return data;
}

document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');

    document.getElementById('loginForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        try {
            await postJson('/api/auth/login', { email: emailInput.value, password: passwordInput.value });
            window.location.href = '/';
        } catch (error) {
            showMessage(error.message, 'danger');
        }
    });

    const requestButton = document.getElementById('requestPasswordBtn');
    requestButton.addEventListener('click', async function() {
        if (!emailInput.reportValidity()) {
            return;
        }
        requestButton.disabled = true;
        try {
            const data = await postJson('/api/auth/request-password', { email: emailInput.value });
            showMessage(`${data.message}. Введите его в поле «Пароль».`, 'success');
            passwordInput.focus();
        } catch (error) {
            showMessage(error.message, 'danger');
        } finally {
            requestButton.disabled = false;
        }
    });
});
